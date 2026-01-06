# Phase 5 实现计划 - 市场数据获取和缓存系统

**版本**: v1.0
**日期**: 2025-11-18
**预计耗时**: 4-5小时

---

## 1. 目标概述

实现智能市场数据获取和三级缓存系统，为后续技术指标计算和交易分析提供数据支持。

### 1.1 核心功能

1. **数据获取**
   - yfinance API 集成（主要数据源）
   - Alpha Vantage API 集成（备用数据源）
   - OHLCV 历史数据获取
   - 期权 Greeks 数据（如可用）

2. **三级缓存系统**
   - L1: 内存缓存（dict，运行时有效）
   - L2: 数据库缓存（market_data 表，持久化）
   - L3: 磁盘缓存（pickle 文件，快速恢复）

3. **批量优化**
   - 分析数据库中的 symbols 和日期范围
   - 批量预加载避免重复请求
   - 智能限流和重试机制

4. **期权支持**
   - 期权 symbol → underlying symbol 映射
   - 同时获取期权和标的数据

---

## 2. 数据分析

### 2.1 当前数据库统计

从数据库中发现：
- **总交易数**: 2,006 笔
- **总持仓数**: 1,505 个
- **交易标的**: ~99 个不同 symbols
- **主要标的** (交易次数 > 40):
  - TSLL (274), AAPL (84), FIG (84)
  - 09988 (82), HIMS (72), 01810 (68)
  - INOD (68), BMNR (52), SVXY (52)

### 2.2 期权标的识别

从 symbol 格式判断，以下是期权：
- 格式: `{UNDERLYING}{YYMMDD}[CP]{STRIKE}`
- 示例: `AAPL250117C150000` → AAPL 标的期权

需要提取 underlying symbol 并同时获取数据。

### 2.3 日期范围需求

需要获取的数据范围：
- 最早交易日期 → 当前日期
- 为计算技术指标，需要额外获取前 200 天数据（MA200 需要）

---

## 3. 架构设计

### 3.1 模块结构

```
src/data_sources/
├── __init__.py
├── base_client.py          # 抽象基类
├── yfinance_client.py      # yfinance 实现
├── alpha_vantage_client.py # Alpha Vantage 实现（备用）
├── cache_manager.py        # 三级缓存管理器
└── batch_fetcher.py        # 批量数据获取器
```

### 3.2 类设计

#### 3.2.1 BaseDataClient (抽象基类)

```python
from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
from datetime import date

class BaseDataClient(ABC):
    """数据源客户端抽象基类"""

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """获取OHLCV数据"""
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> dict:
        """获取股票基本信息"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass
```

#### 3.2.2 YFinanceClient

```python
import yfinance as yf

class YFinanceClient(BaseDataClient):
    """yfinance 数据客户端"""

    def __init__(self, rate_limit: int = 2000):
        """
        Args:
            rate_limit: 每小时请求限制（yfinance 约2000/小时）
        """
        self.rate_limit = rate_limit
        self.request_count = 0
        self.last_reset = datetime.now()

    def get_ohlcv(self, symbol: str, start_date, end_date, interval='1d'):
        """获取OHLCV数据"""
        # 限流检查
        self._check_rate_limit()

        # 下载数据
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval
        )

        # 标准化列名
        df = self._standardize_columns(df)

        return df

    def _check_rate_limit(self):
        """检查并更新限流"""
        # 每小时重置计数
        if (datetime.now() - self.last_reset).seconds > 3600:
            self.request_count = 0
            self.last_reset = datetime.now()

        if self.request_count >= self.rate_limit:
            raise RateLimitError("达到请求限制，请稍后重试")

        self.request_count += 1
```

#### 3.2.3 CacheManager

```python
class CacheManager:
    """三级缓存管理器"""

    def __init__(self, db_session, cache_dir='cache/market_data'):
        self.session = db_session
        self.cache_dir = Path(cache_dir)

        # L1: 内存缓存
        self.memory_cache = {}  # {cache_key: DataFrame}

        # L2: 数据库缓存（通过 session 访问）
        # L3: 磁盘缓存
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, symbol: str, start_date, end_date) -> Optional[pd.DataFrame]:
        """从缓存获取数据（按优先级：L1 → L2 → L3）"""
        cache_key = self._make_cache_key(symbol, start_date, end_date)

        # L1: 内存缓存
        if cache_key in self.memory_cache:
            logger.debug(f"L1 cache hit: {cache_key}")
            return self.memory_cache[cache_key]

        # L2: 数据库缓存
        df = self._load_from_db(symbol, start_date, end_date)
        if df is not None and not df.empty:
            logger.debug(f"L2 cache hit: {cache_key}")
            self.memory_cache[cache_key] = df  # 写入L1
            return df

        # L3: 磁盘缓存
        df = self._load_from_disk(cache_key)
        if df is not None:
            logger.debug(f"L3 cache hit: {cache_key}")
            self.memory_cache[cache_key] = df  # 写入L1
            return df

        return None

    def set(self, symbol: str, df: pd.DataFrame):
        """写入所有缓存层"""
        cache_key = self._make_cache_key(
            symbol,
            df.index.min().date(),
            df.index.max().date()
        )

        # L1: 内存
        self.memory_cache[cache_key] = df

        # L2: 数据库
        self._save_to_db(symbol, df)

        # L3: 磁盘
        self._save_to_disk(cache_key, df)

    def _load_from_db(self, symbol, start_date, end_date):
        """从数据库加载数据"""
        query = self.session.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date >= start_date,
            MarketData.date <= end_date
        ).order_by(MarketData.timestamp)

        records = query.all()
        if not records:
            return None

        # 转换为DataFrame
        data = []
        for r in records:
            data.append({
                'Date': r.timestamp,
                'Open': float(r.open) if r.open else None,
                'High': float(r.high) if r.high else None,
                'Low': float(r.low) if r.low else None,
                'Close': float(r.close),
                'Volume': r.volume
            })

        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        return df
```

#### 3.2.4 BatchFetcher

```python
class BatchFetcher:
    """批量数据获取器"""

    def __init__(self, client: BaseDataClient, cache_manager: CacheManager):
        self.client = client
        self.cache = cache_manager

    def fetch_required_data(self, session: Session):
        """分析数据库，批量获取所需数据"""
        # 1. 分析需要的 symbols 和日期范围
        requirements = self._analyze_requirements(session)

        # 2. 检查缓存，过滤已有数据
        missing = self._filter_missing(requirements)

        # 3. 批量获取
        for req in missing:
            logger.info(f"Fetching {req['symbol']} from {req['start']} to {req['end']}")

            try:
                df = self.client.get_ohlcv(
                    req['symbol'],
                    req['start'],
                    req['end']
                )

                if not df.empty:
                    self.cache.set(req['symbol'], df)
                    logger.info(f"Cached {len(df)} records for {req['symbol']}")

                # 限流：每次请求后等待
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to fetch {req['symbol']}: {e}")
                continue

    def _analyze_requirements(self, session):
        """分析数据库，确定需要获取的数据"""
        # 从 trades 表获取所有 symbols
        symbols_query = session.query(
            Trade.symbol,
            func.min(Trade.trade_date).label('min_date'),
            func.max(Trade.trade_date).label('max_date')
        ).group_by(Trade.symbol)

        requirements = []
        for row in symbols_query:
            # 为计算技术指标，往前多取200天
            start_date = row.min_date - timedelta(days=200)
            end_date = date.today()

            requirements.append({
                'symbol': row.symbol,
                'start': start_date,
                'end': end_date
            })

        return requirements
```

---

## 4. 数据流设计

```
┌─────────────────┐
│   调用方        │
│ (indicators,    │
│  analyzers)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CacheManager   │
│                 │
│  get_data()     │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    │          │          │         │
    ▼          ▼          ▼         ▼
┌─────┐   ┌──────┐   ┌──────┐   ┌─────────┐
│ L1  │   │  L2  │   │  L3  │   │ API     │
│内存 │   │ 数据库│   │ 磁盘  │   │yfinance │
└─────┘   └──────┘   └──────┘   └─────────┘
  hit?      hit?       hit?        fetch
   │         │          │            │
   └─────────┴──────────┴────────────┘
                │
                ▼
        ┌──────────────┐
        │  返回数据     │
        │  DataFrame   │
        └──────────────┘
```

**缓存查找流程**:
1. L1 (内存) → 命中则直接返回
2. L2 (数据库) → 命中则写入L1，返回
3. L3 (磁盘) → 命中则写入L2和L1，返回
4. API调用 → 获取数据，写入L1/L2/L3，返回

---

## 5. 开发任务清单

### Day 1: 基础架构 (2-3小时)

- [x] **Task 1.1**: 创建 `src/data_sources/` 目录结构
- [ ] **Task 1.2**: 实现 `BaseDataClient` 抽象类
  - 定义接口方法
  - 定义异常类 (RateLimitError, DataNotFoundError)
- [ ] **Task 1.3**: 实现 `YFinanceClient`
  - get_ohlcv() 方法
  - get_stock_info() 方法
  - 限流机制
  - 重试机制（3次，指数退避）
  - 列名标准化
- [ ] **Task 1.4**: 实现 `CacheManager` L1 缓存
  - 内存字典缓存
  - cache_key 生成逻辑
  - get/set 接口

### Day 2: 缓存系统 (1-2小时)

- [ ] **Task 2.1**: 实现 `CacheManager` L2 缓存（数据库）
  - _load_from_db() 方法
  - _save_to_db() 方法
  - DataFrame ↔ MarketData 模型转换
- [ ] **Task 2.2**: 实现 `CacheManager` L3 缓存（磁盘）
  - _load_from_disk() 方法（pickle）
  - _save_to_disk() 方法
  - 缓存文件命名规则
- [ ] **Task 2.3**: 实现缓存失效机制
  - 数据过期检查（> 1天的数据）
  - 手动清理缓存方法

### Day 3: 批量获取和测试 (1-2小时)

- [ ] **Task 3.1**: 实现 `BatchFetcher`
  - _analyze_requirements() - 分析数据库需求
  - _filter_missing() - 过滤已缓存数据
  - fetch_required_data() - 批量获取
  - 进度显示（tqdm）
- [ ] **Task 3.2**: 期权处理
  - parse_option_symbol() - 解析期权代码
  - get_underlying_symbol() - 获取标的代码
  - 同时获取期权和标的数据
- [ ] **Task 3.3**: 编写单元测试
  - YFinanceClient 测试（mock API）
  - CacheManager 测试（三级缓存）
  - BatchFetcher 测试
- [ ] **Task 3.4**: 集成测试
  - 使用真实 symbols 测试
  - 验证缓存命中率
  - 性能测试

---

## 6. 测试策略

### 6.1 单元测试

#### Test YFinanceClient
```python
def test_get_ohlcv_success(mock_yfinance):
    """测试成功获取OHLCV数据"""
    client = YFinanceClient()
    df = client.get_ohlcv('AAPL', date(2025, 1, 1), date(2025, 1, 31))

    assert not df.empty
    assert 'Open' in df.columns
    assert 'Close' in df.columns

def test_rate_limit_enforcement():
    """测试限流机制"""
    client = YFinanceClient(rate_limit=2)

    client.get_ohlcv('AAPL', ...)
    client.get_ohlcv('GOOGL', ...)

    with pytest.raises(RateLimitError):
        client.get_ohlcv('MSFT', ...)
```

#### Test CacheManager
```python
def test_cache_l1_hit():
    """测试L1缓存命中"""
    cache = CacheManager(session, cache_dir='/tmp/test_cache')

    # 写入
    df = pd.DataFrame(...)
    cache.set('AAPL', df)

    # L1 读取
    cached = cache.get('AAPL', start, end)
    assert cached is not None
    pd.testing.assert_frame_equal(df, cached)

def test_cache_hierarchy():
    """测试缓存层级"""
    cache = CacheManager(...)

    # 清空L1
    cache.memory_cache.clear()

    # 应该从L2或L3恢复
    df = cache.get('AAPL', ...)
    assert df is not None
```

### 6.2 集成测试

```python
def test_full_data_pipeline():
    """测试完整数据流"""
    client = YFinanceClient()
    cache = CacheManager(session)
    fetcher = BatchFetcher(client, cache)

    # 批量获取
    fetcher.fetch_required_data(session)

    # 验证缓存
    df = cache.get('AAPL', date(2025, 1, 1), date(2025, 1, 31))
    assert df is not None
    assert len(df) > 0
```

### 6.3 真实数据测试

使用数据库中的 Top 10 symbols：
- TSLL, AAPL, FIG, 09988, HIMS
- 测试期权 symbol 解析
- 测试港股数据获取（09988, 01810）

---

## 7. 配置和依赖

### 7.1 新增依赖

```txt
# 已有
yfinance>=0.2.28

# 新增（可选）
alpha-vantage>=2.3.0  # Alpha Vantage 备用数据源
tqdm>=4.65.0          # 进度条
```

### 7.2 配置项

在 `config.py` 中添加：

```python
# 数据源配置
DATA_SOURCE_PRIORITY = ['yfinance', 'alpha_vantage']

# 缓存配置
CACHE_DIR = 'cache/market_data'
CACHE_EXPIRY_DAYS = 1  # 数据过期天数

# API限流
YFINANCE_RATE_LIMIT = 2000  # 每小时
ALPHA_VANTAGE_API_KEY = ''  # 需要用户填写

# 批量获取配置
BATCH_SIZE = 50  # 每批次symbols数量
REQUEST_DELAY = 0.5  # 请求间隔（秒）
```

---

## 8. 期权特殊处理

### 8.1 期权 Symbol 解析

```python
def parse_option_symbol(symbol: str) -> dict:
    """
    解析期权代码

    格式: {UNDERLYING}{YYMMDD}[CP]{STRIKE}
    示例: AAPL250117C150000

    Returns:
        {
            'underlying': 'AAPL',
            'expiry': date(2025, 1, 17),
            'option_type': 'call',
            'strike': 150.0
        }
    """
    import re

    pattern = r'([A-Z]+)(\d{6})([CP])(\d{8})'
    match = re.match(pattern, symbol)

    if not match:
        return None

    underlying, date_str, opt_type, strike_str = match.groups()

    # 解析日期
    year = 2000 + int(date_str[:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])

    # 解析行权价
    strike = int(strike_str) / 1000.0

    return {
        'underlying': underlying,
        'expiry': date(year, month, day),
        'option_type': 'call' if opt_type == 'C' else 'put',
        'strike': strike
    }
```

### 8.2 同时获取期权和标的数据

```python
def fetch_option_with_underlying(self, option_symbol: str):
    """获取期权及其标的数据"""
    # 解析期权
    option_info = parse_option_symbol(option_symbol)

    if option_info:
        underlying = option_info['underlying']

        # 获取标的数据
        underlying_df = self.get_ohlcv(underlying, start, end)

        # 获取期权数据（如可用）
        option_df = self.get_ohlcv(option_symbol, start, end)

        return {
            'underlying': underlying_df,
            'option': option_df,
            'info': option_info
        }
```

---

## 9. 错误处理

### 9.1 异常定义

```python
class DataSourceError(Exception):
    """数据源基础异常"""
    pass

class RateLimitError(DataSourceError):
    """API限流异常"""
    pass

class DataNotFoundError(DataSourceError):
    """数据未找到异常"""
    pass

class CacheError(Exception):
    """缓存相关异常"""
    pass
```

### 9.2 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _fetch_with_retry(self, symbol, start, end):
    """带重试的数据获取"""
    try:
        return self._fetch_data(symbol, start, end)
    except Exception as e:
        logger.warning(f"Fetch failed for {symbol}: {e}, retrying...")
        raise
```

---

## 10. 性能优化

### 10.1 批量获取优化

- 将 symbols 分组，每批50个
- 使用多线程并发获取（注意限流）
- 优先获取高频交易的 symbols

### 10.2 缓存预热

```python
def warmup_cache(self, session):
    """缓存预热 - 预加载常用数据"""
    # 获取Top 20交易symbols
    top_symbols = session.query(
        Trade.symbol,
        func.count().label('count')
    ).group_by(Trade.symbol)\
     .order_by(func.count().desc())\
     .limit(20)

    for row in top_symbols:
        # 预加载数据
        self.fetch_data(row.symbol, ...)
```

### 10.3 内存管理

- L1 缓存大小限制（LRU淘汰）
- 定期清理过期磁盘缓存

---

## 11. 文档和脚本

### 11.1 创建数据预加载脚本

```bash
# scripts/preload_market_data.py
python3 scripts/preload_market_data.py --symbols all --days 365
```

### 11.2 缓存管理脚本

```bash
# scripts/manage_cache.py
python3 scripts/manage_cache.py --clear-all
python3 scripts/manage_cache.py --stats
```

---

## 12. 验收标准

Phase 5 完成的标准：

- ✅ YFinanceClient 实现并通过测试
- ✅ 三级缓存系统正常工作
- ✅ BatchFetcher 可以批量获取数据
- ✅ 缓存命中率 > 80%（第二次运行）
- ✅ 单元测试覆盖率 > 90%
- ✅ 真实数据测试通过（Top 10 symbols）
- ✅ 文档完善（README更新）

---

## 13. 下一步（Phase 6）

Phase 5 完成后，进入 Phase 6: 技术指标计算

- 使用 pandas-ta 计算 RSI, MACD, Bollinger Bands
- 将指标缓存到 market_data 表
- 为持仓分析提供技术指标支持

---

**文档结束**
