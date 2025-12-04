"""
YFinanceClient - yfinance 数据源客户端

使用 yfinance 库获取股票市场数据
"""

import yfinance as yf
import pandas as pd
import time
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.data_sources.base_client import (
    BaseDataClient,
    DataSourceError,
    RateLimitError,
    DataNotFoundError,
    InvalidSymbolError
)

logger = logging.getLogger(__name__)


class YFinanceClient(BaseDataClient):
    """
    yfinance 数据客户端

    特点：
    - 免费，无需API key
    - 支持美股、港股、A股等多市场
    - 限流：约2000请求/小时
    - 数据质量较好，更新及时
    """

    def __init__(self, rate_limit: int = 2000, rate_window_seconds: int = 3600):
        """
        初始化 yfinance 客户端

        Args:
            rate_limit: 限流数量（默认2000）
            rate_window_seconds: 限流时间窗口（秒，默认3600=1小时）
        """
        self.rate_limit = rate_limit
        self.rate_window_seconds = rate_window_seconds

        # 限流追踪
        self.request_times = []  # 记录请求时间戳

        logger.info(f"YFinanceClient initialized with rate_limit={rate_limit}/{rate_window_seconds}s")

    def get_source_name(self) -> str:
        """获取数据源名称"""
        return 'yfinance'

    def is_available(self) -> bool:
        """
        检查 yfinance 是否可用

        通过尝试获取 SPY 的数据来测试
        """
        try:
            spy = yf.Ticker('SPY')
            info = spy.info
            return info is not None and len(info) > 0
        except Exception as e:
            logger.error(f"yfinance availability check failed: {e}")
            return False

    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        获取 OHLCV 数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度（'1d', '1h', '5m'等）

        Returns:
            DataFrame with OHLCV data

        Raises:
            InvalidSymbolError: 无效的股票代码
            DataNotFoundError: 数据未找到
            RateLimitError: 超过限流
            DataSourceError: 其他错误
        """
        # 参数验证
        if not self.validate_symbol(symbol):
            raise InvalidSymbolError(f"Invalid symbol: {symbol}")

        if not self.validate_date_range(start_date, end_date):
            raise ValueError(f"Invalid date range: {start_date} to {end_date}")

        # 限流检查
        self._check_rate_limit()

        # 获取数据（带重试）
        try:
            df = self._fetch_with_retry(symbol, start_date, end_date, interval)

            if df is None or df.empty:
                raise DataNotFoundError(f"No data found for {symbol} from {start_date} to {end_date}")

            # 标准化
            df = self.standardize_dataframe(df)

            logger.info(f"Fetched {len(df)} records for {symbol} ({start_date} to {end_date})")

            return df

        except (DataNotFoundError, InvalidSymbolError, RateLimitError):
            raise
        except Exception as e:
            raise DataSourceError(f"Failed to fetch data for {symbol}: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    def _fetch_with_retry(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str
    ) -> pd.DataFrame:
        """
        带重试机制的数据获取

        使用 tenacity 库实现指数退避重试
        """
        logger.debug(f"Fetching {symbol} from {start_date} to {end_date}, interval={interval}")

        # 记录请求时间
        self._record_request()

        # 创建 Ticker 对象
        ticker = yf.Ticker(symbol)

        # 下载历史数据
        df = ticker.history(
            start=start_date,
            end=end_date + timedelta(days=1),  # yfinance end是不包含的，所以+1天
            interval=interval,
            auto_adjust=False,  # 不自动调整，保留原始价格
            actions=False  # 不包含分红、拆股等事件
        )

        return df

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict with stock information
        """
        if not self.validate_symbol(symbol):
            raise InvalidSymbolError(f"Invalid symbol: {symbol}")

        # 限流检查
        self._check_rate_limit()

        try:
            self._record_request()

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise DataNotFoundError(f"No info found for {symbol}")

            # 提取关键信息
            stock_info = {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'currency': info.get('currency'),
                'exchange': info.get('exchange'),
                'country': info.get('country'),
                'website': info.get('website'),
                'description': info.get('longBusinessSummary'),
                'employees': info.get('fullTimeEmployees'),
                # 价格信息
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose'),
                'open': info.get('open'),
                'day_high': info.get('dayHigh'),
                'day_low': info.get('dayLow'),
                'volume': info.get('volume'),
                'average_volume': info.get('averageVolume'),
                # 估值指标
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_book': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                # 52周高低
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                # 其他
                'beta': info.get('beta'),
                'shares_outstanding': info.get('sharesOutstanding'),
            }

            logger.info(f"Fetched info for {symbol}: {stock_info.get('name')}")

            return stock_info

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"Failed to fetch info for {symbol}: {e}")

    def get_multiple_ohlcv(
        self,
        symbols: list,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个标的的 OHLCV 数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度

        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}

        for symbol in symbols:
            try:
                df = self.get_ohlcv(symbol, start_date, end_date, interval)
                results[symbol] = df

                # 避免请求过快
                time.sleep(0.1)

            except (DataNotFoundError, InvalidSymbolError) as e:
                logger.warning(f"Skipped {symbol}: {e}")
                continue
            except RateLimitError:
                logger.error(f"Rate limit reached at {symbol}")
                break
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue

        logger.info(f"Batch fetched {len(results)}/{len(symbols)} symbols")

        return results

    def _check_rate_limit(self):
        """
        检查是否超过限流

        使用滑动窗口算法
        """
        current_time = time.time()

        # 清理过期的请求记录（超出时间窗口）
        cutoff_time = current_time - self.rate_window_seconds
        self.request_times = [t for t in self.request_times if t > cutoff_time]

        # 检查是否超限
        if len(self.request_times) >= self.rate_limit:
            oldest_request = self.request_times[0]
            wait_time = self.rate_window_seconds - (current_time - oldest_request)

            logger.warning(
                f"Rate limit reached: {len(self.request_times)}/{self.rate_limit}. "
                f"Need to wait {wait_time:.0f}s"
            )

            raise RateLimitError(
                f"Rate limit exceeded. Please wait {wait_time:.0f} seconds."
            )

    def _record_request(self):
        """记录请求时间"""
        self.request_times.append(time.time())

    # 特殊代码映射（指数、ETF等）
    SPECIAL_SYMBOL_MAPPINGS = {
        'VIX': '^VIX',      # CBOE波动率指数
        'DJI': '^DJI',      # 道琼斯指数
        'SPX': '^GSPC',     # 标普500指数
        'NDX': '^NDX',      # 纳斯达克100指数
        'IXIC': '^IXIC',    # 纳斯达克综合指数
    }

    def convert_symbol_for_yfinance(self, symbol: str, market: str = None) -> str:
        """
        转换股票代码为 yfinance 格式

        Args:
            symbol: 原始代码
            market: 市场类型（'HK_STOCK', 'CN_STOCK', 'US_STOCK'）

        Returns:
            yfinance 格式的代码

        Examples:
            '09988' (港股) → '9988.HK'
            '01810' (港股) → '1810.HK'
            '00700' (港股) → '0700.HK' (保留至少4位)
            '600000' (A股) → '600000.SS' (上交所)
            'AAPL' (美股) → 'AAPL'
            'BRK.B' (美股) → 'BRK-B'
            'VIX' (指数) → '^VIX'
        """
        symbol = symbol.strip()

        # 特殊代码映射（指数等）
        if symbol.upper() in self.SPECIAL_SYMBOL_MAPPINGS:
            return self.SPECIAL_SYMBOL_MAPPINGS[symbol.upper()]

        # 美股特殊格式：BRK.B → BRK-B (yfinance uses dash not dot)
        if '.' in symbol and not symbol.endswith(('.HK', '.SS', '.SZ', '.TW')):
            # Check if it's a US stock with class suffix (like BRK.B)
            if len(symbol.split('.')) == 2 and len(symbol.split('.')[1]) == 1:
                return symbol.replace('.', '-')
            # Otherwise already in yfinance format
            return symbol

        # 港股：5位数字代码
        if len(symbol) == 5 and symbol.isdigit():
            # 保留至少4位数字(去掉多余前导0，但保留至少4位)
            # 00700 → 0700, 09988 → 9988, 01810 → 1810
            code = str(int(symbol)).zfill(4)
            return f"{code}.HK"

        # A股：6位数字代码
        if len(symbol) == 6 and symbol.isdigit():
            # 上交所：600xxx, 601xxx, 603xxx
            if symbol.startswith(('600', '601', '603', '688')):
                return f"{symbol}.SS"
            # 深交所：000xxx, 001xxx, 002xxx, 003xxx, 300xxx
            else:
                return f"{symbol}.SZ"

        # 美股：直接返回
        return symbol

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"YFinanceClient(rate_limit={self.rate_limit}/{self.rate_window_seconds}s, "
            f"requests={len(self.request_times)})"
        )
