# 技术实现方案文档

## 1. 概述

本文档提供交易复盘系统的具体技术实现方案，包括数据源选型、技术栈、代码示例和最佳实践。

## 2. 技术栈选型

### 2.1 核心技术栈

| 技术组件 | 选型 | 版本要求 | 用途 |
|----------|------|----------|------|
| **语言** | Python | 3.10+ | 主开发语言 |
| **数据处理** | pandas | 2.0+ | 数据清洗和分析 |
| **数据库** | SQLite | 3.38+ | 数据存储 (MVP) |
| **ORM** | SQLAlchemy | 2.0+ | 数据库访问层 |
| **数值计算** | numpy | 1.24+ | 高性能计算 |
| **技术指标** | pandas-ta | 0.3+ | 技术指标计算 |
| **市场数据** | yfinance | 0.2+ | 免费行情数据 |
| **Web框架** | Streamlit | 1.28+ | 交互式UI |

### 2.2 依赖管理

**requirements.txt**:
```txt
# 核心依赖
pandas>=2.0.0
numpy>=1.24.0
sqlalchemy>=2.0.0

# 数据获取
yfinance>=0.2.30
alpha-vantage>=2.3.1  # 备用数据源

# 技术指标
pandas-ta>=0.3.14b
# TA-Lib>=0.4.28  # 可选，性能更好但安装复杂

# 工具库
python-dateutil>=2.8.2
pytz>=2023.3
requests>=2.31.0
tenacity>=8.2.3  # 重试机制

# 定时任务
apscheduler>=3.10.4

# Web UI
streamlit>=1.28.0

# 开发工具
pytest>=7.4.0
black>=23.0.0
flake8>=6.1.0
```

## 3. 数据源实现方案

### 3.1 市场行情数据获取

#### 方案对比

| 数据源 | 优势 | 劣势 | 成本 | API限流 | 推荐度 |
|--------|------|------|------|---------|--------|
| **yfinance** | 完全免费<br>数据全面<br>易于使用 | 非官方API<br>稳定性一般 | $0 | ~2000次/小时 | ⭐⭐⭐⭐⭐ |
| **Alpha Vantage** | 官方API<br>数据准确 | 限流严格 | $0-$50/月 | 5次/分钟(免费) | ⭐⭐⭐⭐ |
| **Polygon.io** | 数据质量高<br>实时数据 | 需付费 | $29-199/月 | 根据套餐 | ⭐⭐⭐ |
| **Tiingo** | 基本面+行情 | 免费额度少 | $0-30/月 | 根据套餐 | ⭐⭐ |

**推荐方案**: yfinance (主) + Alpha Vantage (备)

#### yfinance 实现

```python
# data_sources/yfinance_client.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class YFinanceClient:
    """yfinance数据获取客户端"""

    def __init__(self):
        self.session = None

    def get_ohlcv(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = '1d'
    ) -> Optional[pd.DataFrame]:
        """
        获取OHLCV数据

        Args:
            symbol: 股票代码 (e.g., 'AAPL', '1810.HK')
            start_date: 起始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            interval: 时间粒度 '1m','5m','1h','1d','1wk','1mo'

        Returns:
            DataFrame with: Open, High, Low, Close, Volume
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True  # 自动复权
            )

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # 重命名列为标准格式
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            logger.info(f"Fetched {len(df)} records for {symbol}")
            return df[['open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return None

    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        batch_size: int = 10
    ) -> dict:
        """
        批量获取多个symbol的数据

        Args:
            symbols: 股票代码列表
            start_date: 起始日期
            end_date: 结束日期
            batch_size: 每批处理的symbol数量

        Returns:
            dict: {symbol: DataFrame}
        """
        import time

        all_data = {}

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            logger.info(f"Fetching batch {i//batch_size + 1}: {batch}")

            try:
                # yfinance批量下载
                data = yf.download(
                    tickers=batch,
                    start=start_date,
                    end=end_date,
                    group_by='ticker',
                    auto_adjust=True,
                    threads=True  # 多线程
                )

                # 解析结果
                if len(batch) == 1:
                    # 单个symbol的数据格式不同
                    all_data[batch[0]] = data
                else:
                    for symbol in batch:
                        if symbol in data.columns.levels[0]:
                            all_data[symbol] = data[symbol]

            except Exception as e:
                logger.error(f"Error in batch {i//batch_size + 1}: {e}")
                # 失败的批次逐个获取
                for symbol in batch:
                    df = self.get_ohlcv(symbol, start_date, end_date)
                    if df is not None:
                        all_data[symbol] = df

            # 避免触发限流
            time.sleep(1)

        return all_data

    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票基本信息

        Returns:
            dict: sector, industry, market_cap, pe_ratio等
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'country': info.get('country', ''),
                'currency': info.get('currency', 'USD')
            }

        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return {}

    def get_market_indices(self, date: str) -> dict:
        """
        获取市场指数数据

        Args:
            date: 日期 'YYYY-MM-DD'

        Returns:
            dict: SPY, VIX, QQQ等指数数据
        """
        indices = {
            'SPY': '^GSPC',  # S&P 500
            'VIX': '^VIX',   # 波动率指数
            'QQQ': '^IXIC',  # 纳斯达克
            'DIA': '^DJI',   # 道琼斯
        }

        result = {}
        start = datetime.strptime(date, '%Y-%m-%d') - timedelta(days=5)
        end = datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)

        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start, end=end)

                if not df.empty:
                    # 找到最接近目标日期的数据
                    target_date = pd.Timestamp(date)
                    closest_idx = df.index.get_indexer([target_date], method='nearest')[0]
                    row = df.iloc[closest_idx]

                    result[name] = {
                        'close': row['Close'],
                        'change_pct': ((row['Close'] - row['Open']) / row['Open'] * 100)
                    }

            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")

        return result
```

#### Alpha Vantage 备用实现

```python
# data_sources/alpha_vantage_client.py
from alpha_vantage.timeseries import TimeSeries
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Alpha Vantage备用数据源"""

    def __init__(self, api_key: str):
        self.ts = TimeSeries(key=api_key, output_format='pandas')

    def get_ohlcv(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取日线数据 (全量历史)

        Note: 免费版每分钟5次调用限制
        """
        try:
            data, meta_data = self.ts.get_daily_adjusted(
                symbol=symbol,
                outputsize='full'
            )

            # 重命名列
            data = data.rename(columns={
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '6. volume': 'volume'
            })

            return data[['open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            return None
```

### 3.2 技术指标计算库

#### 库对比

| 库名 | 优势 | 劣势 | 性能 | 安装难度 | 推荐度 |
|------|------|------|------|----------|--------|
| **TA-Lib** | C实现，极快<br>150+指标<br>行业标准 | 安装复杂<br>Windows兼容性差 | ⚡⚡⚡ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **pandas-ta** | 纯Python<br>易安装<br>130+指标 | 性能较慢 | ⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **ta** | 轻量级 | 指标少 | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

**推荐方案**: pandas-ta (MVP) → TA-Lib (优化)

#### pandas-ta 实现

```python
# indicators/calculator.py
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class IndicatorCalculator:
    """技术指标计算器"""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 包含OHLCV的DataFrame

        Returns:
            添加了技术指标列的DataFrame
        """
        try:
            # 确保索引是DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # RSI
            df['rsi_14'] = ta.rsi(df['close'], length=14)

            # MACD
            macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df['macd'] = macd['MACD_12_26_9']
            df['macd_signal'] = macd['MACDs_12_26_9']
            df['macd_hist'] = macd['MACDh_12_26_9']

            # Bollinger Bands
            bbands = ta.bbands(df['close'], length=20, std=2)
            df['bb_upper'] = bbands['BBU_20_2.0']
            df['bb_middle'] = bbands['BBM_20_2.0']
            df['bb_lower'] = bbands['BBL_20_2.0']

            # ATR
            df['atr_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)

            # Moving Averages
            df['ma_5'] = ta.sma(df['close'], length=5)
            df['ma_10'] = ta.sma(df['close'], length=10)
            df['ma_20'] = ta.sma(df['close'], length=20)
            df['ma_50'] = ta.sma(df['close'], length=50)
            df['ma_200'] = ta.sma(df['close'], length=200)

            # Volume SMA
            df['volume_sma_20'] = ta.sma(df['volume'], length=20)

            # ADX (趋势强度)
            adx = ta.adx(df['high'], df['low'], df['close'], length=14)
            df['adx'] = adx['ADX_14']

            logger.info(f"Calculated indicators for {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df

    @staticmethod
    def calculate_for_single_point(
        df: pd.DataFrame,
        target_date: str
    ) -> Optional[Dict]:
        """
        计算特定日期的技术指标

        Args:
            df: 历史OHLCV数据 (需包含足够历史数据用于计算)
            target_date: 目标日期

        Returns:
            dict: 该日期的所有指标值
        """
        df_with_indicators = IndicatorCalculator.calculate_all(df)

        target_ts = pd.Timestamp(target_date)
        if target_ts not in df_with_indicators.index:
            logger.warning(f"Date {target_date} not in data")
            return None

        row = df_with_indicators.loc[target_ts]

        return {
            'date': target_date,
            'close': row['close'],
            'rsi_14': row.get('rsi_14'),
            'macd': row.get('macd'),
            'macd_signal': row.get('macd_signal'),
            'macd_hist': row.get('macd_hist'),
            'bb_upper': row.get('bb_upper'),
            'bb_middle': row.get('bb_middle'),
            'bb_lower': row.get('bb_lower'),
            'atr_14': row.get('atr_14'),
            'ma_20': row.get('ma_20'),
            'ma_50': row.get('ma_50'),
            'ma_200': row.get('ma_200'),
            'adx': row.get('adx')
        }

    @staticmethod
    def get_required_lookback(indicator: str) -> int:
        """
        获取计算指标所需的历史数据天数

        Returns:
            int: 需要的历史天数
        """
        lookback_periods = {
            'rsi_14': 14 + 20,  # RSI + 平滑期
            'macd': 26 + 9 + 20,  # 慢线 + 信号线 + 平滑
            'bbands': 20 + 10,
            'atr_14': 14 + 10,
            'ma_200': 200 + 10,
            'adx': 14 + 10
        }

        return max(lookback_periods.values())  # 返回最大值
```

#### TA-Lib 实现 (可选优化)

```python
# indicators/talib_calculator.py
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    logger.warning("TA-Lib not available, falling back to pandas-ta")

class TALibCalculator:
    """使用TA-Lib的高性能计算器"""

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """使用TA-Lib计算指标 (速度提升3-5倍)"""
        if not TALIB_AVAILABLE:
            raise ImportError("TA-Lib not installed")

        try:
            # 转换为numpy数组 (TA-Lib要求)
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            volume = df['volume'].values

            # RSI
            df['rsi_14'] = talib.RSI(close, timeperiod=14)

            # MACD
            macd, signal, hist = talib.MACD(
                close,
                fastperiod=12,
                slowperiod=26,
                signalperiod=9
            )
            df['macd'] = macd
            df['macd_signal'] = signal
            df['macd_hist'] = hist

            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(
                close,
                timeperiod=20,
                nbdevup=2,
                nbdevdn=2
            )
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower

            # ATR
            df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)

            # Moving Averages
            df['ma_5'] = talib.SMA(close, timeperiod=5)
            df['ma_20'] = talib.SMA(close, timeperiod=20)
            df['ma_50'] = talib.SMA(close, timeperiod=50)
            df['ma_200'] = talib.SMA(close, timeperiod=200)

            # ADX
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)

            return df

        except Exception as e:
            logger.error(f"TA-Lib calculation error: {e}")
            return df
```

## 4. 缓存机制实现

### 4.1 三级缓存架构

```python
# cache/cache_manager.py
import hashlib
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """三级缓存管理器"""

    def __init__(self, db_session, cache_dir: str = './cache'):
        self.memory_cache = {}  # L1: 内存缓存
        self.db_session = db_session  # L2: 数据库缓存
        self.cache_dir = Path(cache_dir)  # L3: 磁盘缓存
        self.cache_dir.mkdir(exist_ok=True)

        # 缓存配置
        self.memory_max_size = 100  # MB
        self.disk_ttl = 7  # 天

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get_market_data(
        self,
        symbol: str,
        date: str
    ) -> Optional[dict]:
        """
        获取市场数据 (三级缓存查询)

        返回顺序: L1 -> L2 -> L3 -> API
        """
        cache_key = f"{symbol}_{date}"

        # L1: 内存缓存
        if cache_key in self.memory_cache:
            logger.debug(f"[L1 Hit] {cache_key}")
            return self.memory_cache[cache_key]

        # L2: 数据库缓存
        db_data = self._query_from_db(symbol, date)
        if db_data:
            logger.debug(f"[L2 Hit] {cache_key}")
            # 写入L1
            self.memory_cache[cache_key] = db_data
            return db_data

        # L3: 磁盘缓存
        disk_data = self._load_from_disk(cache_key)
        if disk_data:
            logger.debug(f"[L3 Hit] {cache_key}")
            # 写入L2和L1
            self._save_to_db(symbol, date, disk_data)
            self.memory_cache[cache_key] = disk_data
            return disk_data

        # Cache Miss - 需要从API获取
        logger.info(f"[Cache Miss] {cache_key}")
        return None

    def _query_from_db(self, symbol: str, date: str) -> Optional[dict]:
        """从数据库查询"""
        from models import MarketData

        record = self.db_session.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date == date
        ).first()

        if record:
            return {
                'open': record.open,
                'high': record.high,
                'low': record.low,
                'close': record.close,
                'volume': record.volume,
                'rsi_14': record.rsi_14,
                'macd': record.macd,
                # ... 其他指标
            }
        return None

    def _save_to_db(self, symbol: str, date: str, data: dict):
        """保存到数据库"""
        from models import MarketData

        record = MarketData(
            symbol=symbol,
            date=date,
            timestamp=datetime.strptime(date, '%Y-%m-%d'),
            **data
        )
        self.db_session.merge(record)  # 如果存在则更新
        self.db_session.commit()

    def _load_from_disk(self, key: str) -> Optional[dict]:
        """从磁盘加载缓存"""
        cache_file = self.cache_dir / f"{key}.pkl"

        if not cache_file.exists():
            return None

        # 检查是否过期
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=self.disk_ttl):
            cache_file.unlink()  # 删除过期缓存
            return None

        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading cache {key}: {e}")
            return None

    def _save_to_disk(self, key: str, data: dict):
        """保存到磁盘"""
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving cache {key}: {e}")

    def clear_expired(self):
        """清理过期的磁盘缓存"""
        count = 0
        for cache_file in self.cache_dir.glob('*.pkl'):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > timedelta(days=self.disk_ttl):
                cache_file.unlink()
                count += 1

        logger.info(f"Cleared {count} expired cache files")
```

### 4.2 批量预加载

```python
# cache/preloader.py
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataPreloader:
    """数据批量预加载器"""

    def __init__(self, yf_client, calculator, cache_manager):
        self.yf_client = yf_client
        self.calculator = calculator
        self.cache = cache_manager

    def preload_for_trades(self, trades_df: pd.DataFrame):
        """
        为所有交易批量预加载市场数据

        策略: 按symbol分组，批量获取整个日期范围的数据
        """
        # 提取唯一的 (symbol, date) 组合
        unique_symbols = trades_df['symbol'].unique()

        for symbol in unique_symbols:
            symbol_trades = trades_df[trades_df['symbol'] == symbol]

            # 计算日期范围 (预留200天用于MA200计算)
            min_date = symbol_trades['trade_date'].min()
            max_date = symbol_trades['trade_date'].max()

            lookback = self.calculator.get_required_lookback('ma_200')
            start_date = min_date - timedelta(days=lookback)

            logger.info(f"Preloading {symbol}: {start_date} to {max_date}")

            # 一次性获取整个时间段的数据
            df = self.yf_client.get_ohlcv(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                max_date.strftime('%Y-%m-%d')
            )

            if df is not None and not df.empty:
                # 计算所有技术指标
                df = self.calculator.calculate_all(df)

                # 批量保存到数据库
                self._batch_save(symbol, df)

        logger.info("Preload completed!")

    def _batch_save(self, symbol: str, df: pd.DataFrame):
        """批量保存到数据库"""
        from models import MarketData

        records = []
        for timestamp, row in df.iterrows():
            record = {
                'symbol': symbol,
                'timestamp': timestamp,
                'date': timestamp.date(),
                'open': row.get('open'),
                'high': row.get('high'),
                'low': row.get('low'),
                'close': row.get('close'),
                'volume': row.get('volume'),
                'rsi_14': row.get('rsi_14'),
                'macd': row.get('macd'),
                'macd_signal': row.get('macd_signal'),
                'macd_hist': row.get('macd_hist'),
                'bb_upper': row.get('bb_upper'),
                'bb_middle': row.get('bb_middle'),
                'bb_lower': row.get('bb_lower'),
                'atr_14': row.get('atr_14'),
                'ma_5': row.get('ma_5'),
                'ma_20': row.get('ma_20'),
                'ma_50': row.get('ma_50'),
                'ma_200': row.get('ma_200'),
                'adx': row.get('adx'),
                'data_source': 'yfinance'
            }
            records.append(record)

        # 批量插入
        self.cache.db_session.bulk_insert_mappings(
            MarketData,
            records
        )
        self.cache.db_session.commit()

        logger.info(f"Saved {len(records)} records for {symbol}")
```

## 5. API调用优化

### 5.1 限流控制

```python
# utils/rate_limiter.py
from ratelimit import limits, sleep_and_retry
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """API限流控制器"""

    @staticmethod
    def yfinance_limit(calls: int = 2000, period: int = 3600):
        """yfinance限流装饰器: 2000次/小时"""
        def decorator(func):
            @sleep_and_retry
            @limits(calls=calls, period=period)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def alpha_vantage_limit(calls: int = 5, period: int = 60):
        """Alpha Vantage限流: 5次/分钟"""
        def decorator(func):
            @sleep_and_retry
            @limits(calls=calls, period=period)
            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

# 使用示例
@RateLimiter.yfinance_limit()
def fetch_data_with_limit(symbol):
    return yf.Ticker(symbol).history(period='1mo')
```

### 5.2 错误重试机制

```python
# utils/retry.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests
import logging

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError)),
    reraise=True
)
def robust_api_call(func, *args, **kwargs):
    """
    带重试的API调用

    重试策略:
    - 最多重试3次
    - 指数退避: 2s, 4s, 8s
    - 仅对网络错误重试
    """
    try:
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        logger.warning(f"API call failed: {e}, retrying...")
        raise

# 使用示例
def fetch_with_retry(symbol):
    return robust_api_call(yf.Ticker(symbol).history, period='1mo')
```

## 6. 定时任务实现

```python
# scheduler/update_scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

class DataUpdateScheduler:
    """数据自动更新调度器"""

    def __init__(self, update_service):
        self.scheduler = BackgroundScheduler()
        self.update_service = update_service

    def setup(self):
        """配置定时任务"""

        # 美股数据更新: 每天UTC 21:00 (美东17:00收盘后)
        self.scheduler.add_job(
            func=self.update_service.update_us_stocks,
            trigger=CronTrigger(hour=21, minute=0, timezone='UTC'),
            id='us_stock_update',
            name='Update US stock data',
            replace_existing=True
        )

        # 港股数据更新: 每天UTC 09:00 (香港17:00收盘后)
        self.scheduler.add_job(
            func=self.update_service.update_hk_stocks,
            trigger=CronTrigger(hour=9, minute=0, timezone='UTC'),
            id='hk_stock_update',
            name='Update HK stock data',
            replace_existing=True
        )

        # 市场环境更新: 每天UTC 22:00
        self.scheduler.add_job(
            func=self.update_service.update_market_environment,
            trigger=CronTrigger(hour=22, minute=0, timezone='UTC'),
            id='market_env_update',
            name='Update market environment'
        )

        # 基本面数据: 每周一00:00
        self.scheduler.add_job(
            func=self.update_service.update_fundamentals,
            trigger=CronTrigger(day_of_week='mon', hour=0, minute=0),
            id='fundamental_update',
            name='Update fundamental data'
        )

        logger.info("Scheduled jobs configured")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
```

## 7. 性能优化建议

### 7.1 数据库查询优化

```python
# 使用批量查询替代循环查询
# 差的做法 ❌
for trade_id in trade_ids:
    trade = session.query(Trade).get(trade_id)
    market_data = session.query(MarketData).filter(...).first()

# 好的做法 ✅
trades = session.query(Trade).filter(Trade.id.in_(trade_ids)).all()
market_data = session.query(MarketData).filter(...).all()

# 使用JOIN减少查询次数
# 差的做法 ❌
trades = session.query(Trade).all()
for trade in trades:
    env = session.query(MarketEnvironment).filter(
        MarketEnvironment.date == trade.trade_date
    ).first()

# 好的做法 ✅
from sqlalchemy.orm import joinedload

trades = session.query(Trade).options(
    joinedload(Trade.market_environment)
).all()
```

### 7.2 pandas性能优化

```python
# 向量化操作替代循环
# 差的做法 ❌
for i in range(len(df)):
    df.loc[i, 'pnl'] = (df.loc[i, 'sell_price'] - df.loc[i, 'buy_price']) * df.loc[i, 'quantity']

# 好的做法 ✅
df['pnl'] = (df['sell_price'] - df['buy_price']) * df['quantity']

# 使用category类型节省内存
df['sector'] = df['sector'].astype('category')
df['industry'] = df['industry'].astype('category')

# 批量计算技术指标
# 好：一次计算所有日期
df_all = calculator.calculate_all(df)

# 差：逐行计算
for date in dates:
    indicators = calculator.calculate_for_single_point(df, date)
```

## 8. 成本估算

### 8.1 MVP阶段 (免费方案)

| 项目 | 选型 | 月成本 |
|------|------|--------|
| 市场数据API | yfinance | $0 |
| 技术指标计算 | pandas-ta | $0 |
| 数据库 | SQLite | $0 |
| Web框架 | Streamlit | $0 |
| 服务器 | 本地运行 | $0 |
| **总计** | | **$0** |

**限制**:
- API调用限流: ~2000次/小时
- 单机部署: 不支持多用户
- 数据量限制: < 1GB

### 8.2 扩展阶段 (付费优化)

| 项目 | 选型 | 月成本 | 收益 |
|------|------|--------|------|
| 高级API | Alpha Vantage Premium | $50 | 500次/分钟 |
| 实时数据 | Polygon.io Starter | $29 | WebSocket实时流 |
| 云数据库 | DigitalOcean PostgreSQL | $15 | 托管服务 |
| 服务器 | DigitalOcean Droplet | $12 | 多用户部署 |
| **总计** | | **$106** | 稳定+实时+云端 |

## 9. 部署建议

### 9.1 开发环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -m scripts.init_db

# 运行数据导入
python -m scripts.import_trades

# 启动Web UI
streamlit run app.py
```

### 9.2 生产环境 (未来)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/tradingcoach
    depends_on:
      - db

  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=tradingcoach
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 10. 总结

### 10.1 技术选型总结

| 场景 | 推荐方案 | 备选方案 |
|------|----------|----------|
| **市场数据** | yfinance | Alpha Vantage |
| **技术指标** | pandas-ta (MVP)<br>TA-Lib (优化) | ta库 |
| **数据库** | SQLite (MVP)<br>PostgreSQL (扩展) | TimescaleDB |
| **缓存** | 内存+DB+磁盘三级 | Redis |
| **任务调度** | APScheduler | Celery |
| **Web UI** | Streamlit | Flask + React |

### 10.2 实现优先级

| 优先级 | 组件 | 工作量 |
|--------|------|--------|
| P0 | yfinance客户端 | 2小时 |
| P0 | pandas-ta计算器 | 2小时 |
| P0 | 数据库缓存 | 3小时 |
| P1 | 批量预加载 | 2小时 |
| P1 | 限流和重试 | 1小时 |
| P2 | 定时任务 | 2小时 |
| P3 | TA-Lib优化 | 4小时 |

---

**文档版本**: v1.0
**创建日期**: 2025-11-16
**相关文档**:
- `data_extensibility_design.md` - 数据扩展性设计
- `technical_indicators_research.md` - 技术指标研究
