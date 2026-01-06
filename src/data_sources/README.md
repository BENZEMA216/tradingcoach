# data_sources/

一旦我所属的文件夹有所变化，请更新我

## 架构说明

市场数据获取和缓存层。采用三级缓存架构（内存→数据库→文件）减少API调用，
支持多数据源切换（YFinance/Polygon等），提供批量获取和限流控制。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出客户端类 |
| `base_client.py` | 抽象基类 | 定义数据源接口标准 |
| `yfinance_client.py` | YFinance客户端 | 免费数据源，支持美/港股 |
| `akshare_client.py` | AKShare客户端 | 免费A股数据源，国内更稳定 |
| `data_router.py` | 智能路由器 | 根据代码自动选择数据源 |
| `options_client.py` | 期权数据客户端 | 获取期权链和Greeks数据 |
| `cache_manager.py` | 缓存管理器 | 三级缓存：L1内存/L2数据库/L3文件 |
| `batch_fetcher.py` | 批量获取器 | 并发控制（ThreadPoolExecutor, max_workers=4）、进度显示、断点续传 |
| `market_env_fetcher.py` | 市场环境获取器 | 获取VIX、指数等市场环境数据 |

---

## 设计思路

### 核心问题
- 市场数据 API 有限流限制
- 重复获取相同数据浪费资源
- 需要支持多数据源切换

### 解决方案

**三级缓存架构**:
```
请求 → L1 内存缓存 → L2 数据库缓存 → L3 磁盘缓存 → API 请求
```

**抽象工厂模式**:
```
BaseDataClient (抽象接口)
    ├── YFinanceClient (免费，美股/港股)
    ├── AKShareClient (免费，A股专用)
    ├── PolygonClient (付费，期权数据) [计划中]
    └── AlphaVantageClient (备选)

DataRouter (智能路由器)
    ├── A股代码 → AKShareClient
    └── 其他代码 → YFinanceClient
```

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `base_client.py` | 抽象基类，定义接口 | ~150 |
| `yfinance_client.py` | yfinance 实现 | ~370 |
| `cache_manager.py` | 三级缓存管理 | ~300 |
| `batch_fetcher.py` | 批量数据获取器 | ~200 |

## BaseDataClient

定义数据源客户端的标准接口。

```python
class BaseDataClient(ABC):
    @abstractmethod
    def get_ohlcv(self, symbol, start_date, end_date, interval) -> DataFrame:
        """获取 OHLCV 数据"""

    @abstractmethod
    def get_source_name(self) -> str:
        """返回数据源名称"""

    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""

    def validate_symbol(self, symbol) -> bool:
        """验证股票代码格式"""

    def standardize_dataframe(self, df) -> DataFrame:
        """标准化列名"""
```

### 自定义异常

```python
DataSourceError      # 通用数据源错误
RateLimitError       # 超过限流
DataNotFoundError    # 数据未找到
InvalidSymbolError   # 无效股票代码
```

## YFinanceClient

基于 yfinance 库的免费数据客户端。

### 特性

| 特性 | 说明 |
|------|------|
| 免费 | 无需 API Key |
| 多市场 | 美股、港股、A股 |
| 限流 | ~2000 请求/小时 |
| 重试 | 指数退避重试机制 |

### 代码转换

```python
# 港股: 5位数字
'09988' → '9988.HK'
'00700' → '0700.HK'

# A股: 6位数字
'600000' → '600000.SS'  # 上交所
'000001' → '000001.SZ'  # 深交所

# 美股: 直接使用
'AAPL' → 'AAPL'
'BRK.B' → 'BRK-B'

# 指数
'VIX' → '^VIX'
'SPX' → '^GSPC'
```

### 使用示例

```python
from src.data_sources.yfinance_client import YFinanceClient
from datetime import date

client = YFinanceClient(rate_limit=2000)

# 获取单个标的
df = client.get_ohlcv(
    symbol='AAPL',
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    interval='1d'
)

# 获取股票信息
info = client.get_stock_info('AAPL')
print(info['name'], info['sector'])

# 批量获取
results = client.get_multiple_ohlcv(
    symbols=['AAPL', 'TSLA', 'NVDA'],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)
```

### 限流机制

```python
# 滑动窗口限流
client = YFinanceClient(
    rate_limit=2000,          # 最大请求数
    rate_window_seconds=3600  # 时间窗口（1小时）
)

# 超限时抛出 RateLimitError
try:
    df = client.get_ohlcv(...)
except RateLimitError as e:
    print(f"需要等待: {e}")
```

## AKShareClient

基于 AKShare 库的 A 股数据客户端。

### 特性

| 特性 | 说明 |
|------|------|
| 免费 | 无需 API Key |
| A股专用 | 上交所、深交所、北交所 |
| 国内稳定 | 无需翻墙 |
| 前复权 | 自动调整历史价格 |

### 支持的代码格式

```python
# 纯数字
'000001' → 平安银行 (深圳)
'600000' → 浦发银行 (上海)
'300750' → 宁德时代 (创业板)

# 带后缀
'000001.SZ' → 深交所
'600000.SH' → 上交所
```

### 使用示例

```python
from src.data_sources.akshare_client import AKShareClient
from datetime import date

client = AKShareClient()

# 获取 A 股数据
df = client.get_ohlcv(
    symbol='000001',
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 获取实时行情
quote = client.get_realtime_quote('000001')
print(f"当前价: {quote['price']}, 涨跌幅: {quote['change_pct']}%")
```

## DataRouter

智能数据源路由器，自动选择最佳数据源。

### 路由规则

| 代码类型 | 示例 | 数据源 |
|----------|------|--------|
| A股 | 000001, 600000.SH | AKShare |
| 港股 | 00700.HK, 09988.HK | YFinance |
| 美股 | AAPL, TSLA | YFinance |

### 使用示例

```python
from src.data_sources.data_router import get_data_router
from datetime import date

router = get_data_router()

# 自动路由 - A股使用 AKShare
df = router.get_ohlcv('000001', date(2024, 1, 1), date(2024, 12, 31))

# 自动路由 - 美股使用 YFinance
df = router.get_ohlcv('AAPL', date(2024, 1, 1), date(2024, 12, 31))

# 批量获取（自动分组）
results = router.get_multiple_ohlcv(
    symbols=['000001', 'AAPL', '00700.HK'],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)
```

## CacheManager

三级缓存管理器，减少重复 API 请求。

### 缓存层级

| 层级 | 存储 | 特点 | TTL |
|------|------|------|-----|
| L1 | 内存 (LRU) | 最快，100条目限制 | 会话内 |
| L2 | SQLite (market_data 表) | 持久化，可查询 | 永久 |
| L3 | Pickle 文件 | 备份，离线可用 | 永久 |

### 查询流程

```
get(symbol, start, end)
    │
    ├─→ L1 命中? → 返回
    │
    ├─→ L2 命中? → 更新 L1 → 返回
    │
    ├─→ L3 命中? → 更新 L1, L2 → 返回
    │
    └─→ API 请求 → 更新 L1, L2, L3 → 返回
```

### 使用示例

```python
from src.data_sources.cache_manager import CacheManager

cache = CacheManager(session, data_client=yfinance_client)

# 智能获取（自动使用缓存）
df = cache.get(
    symbol='AAPL',
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# 强制刷新
df = cache.get(..., force_refresh=True)

# 预热缓存
cache.warmup(['AAPL', 'TSLA', 'NVDA'])

# 清理过期缓存
cache.cleanup(older_than_days=30)
```

## BatchFetcher

批量数据获取器，优化大量标的的数据获取。

### 特性

- 并发控制（避免触发限流）
- 进度显示
- 错误跳过和重试
- 断点续传

### 使用示例

```python
from src.data_sources.batch_fetcher import BatchFetcher

fetcher = BatchFetcher(session, cache_manager)

# 批量预加载
results = fetcher.fetch_all(
    symbols=['AAPL', 'TSLA', ...],  # 50+ 标的
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    delay_seconds=0.5  # 请求间隔
)

print(f"成功: {results['success']}")
print(f"失败: {results['failed']}")
```

## 数据标准化

所有数据源返回的 DataFrame 统一格式：

```python
DataFrame columns:
- Open: float     # 开盘价
- High: float     # 最高价
- Low: float      # 最低价
- Close: float    # 收盘价
- Volume: int     # 成交量

index: DatetimeIndex  # UTC 时间戳
```

## 扩展新数据源

1. 继承 `BaseDataClient`
2. 实现抽象方法
3. 添加到 BatchFetcher 的数据源列表

```python
class MyDataClient(BaseDataClient):
    def get_source_name(self) -> str:
        return 'my_source'

    def is_available(self) -> bool:
        # 检查 API 可用性
        return True

    def get_ohlcv(self, symbol, start_date, end_date, interval) -> DataFrame:
        # 实现数据获取逻辑
        pass
```
