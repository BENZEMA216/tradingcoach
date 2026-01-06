"""
DataRouter - 智能数据源路由器

input: 股票代码
output: 根据代码自动选择正确的数据源获取数据
pos: 作为数据获取的统一入口，自动路由到 AKShare(A股) 或 YFinance(其他)

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import re
import logging
from datetime import date
from typing import Optional, Dict, Any, List
import pandas as pd

from .base_client import (
    BaseDataClient,
    DataSourceError,
    DataNotFoundError
)
from .yfinance_client import YFinanceClient
from .akshare_client import AKShareClient, AKSHARE_AVAILABLE

logger = logging.getLogger(__name__)


class DataRouter:
    """
    智能数据源路由器

    根据股票代码自动选择合适的数据源:
    - A股 (000xxx, 600xxx, 300xxx 等) -> AKShare
    - 港股 (xxx.HK) -> YFinance
    - 美股 (AAPL, TSLA 等) -> YFinance
    """

    # A股代码模式
    A_STOCK_PATTERNS = [
        r'^[036]\d{5}$',           # 纯6位数字: 000001, 600000, 300750
        r'^[036]\d{5}\.(SZ|SH|BJ|SS)$',  # 带后缀: 000001.SZ
        r'^(SZ|SH|BJ)\d{6}$',      # 前缀格式: SZ000001
    ]

    # 港股代码模式
    HK_STOCK_PATTERNS = [
        r'^\d{4,5}\.HK$',          # 00700.HK, 9988.HK
        r'^\d{4,5}$',              # 纯数字4-5位可能是港股
    ]

    def __init__(
        self,
        prefer_akshare: bool = True,
        yfinance_client: Optional[YFinanceClient] = None,
        akshare_client: Optional[AKShareClient] = None
    ):
        """
        初始化数据路由器

        Args:
            prefer_akshare: 对于 A 股优先使用 AKShare
            yfinance_client: 可选的 YFinance 客户端实例
            akshare_client: 可选的 AKShare 客户端实例
        """
        self._prefer_akshare = prefer_akshare

        # 延迟初始化客户端
        self._yfinance_client = yfinance_client
        self._akshare_client = akshare_client

        logger.info(f"DataRouter 初始化: prefer_akshare={prefer_akshare}, "
                    f"akshare_available={AKSHARE_AVAILABLE}")

    @property
    def yfinance_client(self) -> YFinanceClient:
        """获取 YFinance 客户端（延迟初始化）"""
        if self._yfinance_client is None:
            self._yfinance_client = YFinanceClient()
        return self._yfinance_client

    @property
    def akshare_client(self) -> Optional[AKShareClient]:
        """获取 AKShare 客户端（延迟初始化）"""
        if self._akshare_client is None and AKSHARE_AVAILABLE:
            self._akshare_client = AKShareClient()
        return self._akshare_client

    def detect_market(self, symbol: str) -> str:
        """
        检测股票代码所属市场

        Args:
            symbol: 股票代码

        Returns:
            str: 市场类型 ('A_STOCK', 'HK_STOCK', 'US_STOCK', 'UNKNOWN')
        """
        symbol = symbol.strip().upper()

        # 检查 A 股模式
        for pattern in self.A_STOCK_PATTERNS:
            if re.match(pattern, symbol, re.IGNORECASE):
                return 'A_STOCK'

        # 检查港股模式
        for pattern in self.HK_STOCK_PATTERNS:
            if re.match(pattern, symbol, re.IGNORECASE):
                # 4-5位纯数字需要进一步判断
                if symbol.isdigit():
                    # 如果是4-5位数字，先假设是港股
                    return 'HK_STOCK'
                return 'HK_STOCK'

        # 美股通常是纯字母或字母+数字
        if re.match(r'^[A-Z]{1,5}$', symbol):
            return 'US_STOCK'

        # 检查特殊后缀
        if '.HK' in symbol:
            return 'HK_STOCK'
        elif any(suffix in symbol for suffix in ['.SZ', '.SH', '.BJ', '.SS']):
            return 'A_STOCK'

        return 'UNKNOWN'

    def select_client(self, symbol: str) -> BaseDataClient:
        """
        根据股票代码选择合适的客户端

        Args:
            symbol: 股票代码

        Returns:
            BaseDataClient: 选定的数据客户端
        """
        market = self.detect_market(symbol)

        if market == 'A_STOCK' and self._prefer_akshare:
            if self.akshare_client is not None:
                logger.debug(f"使用 AKShare 获取 A 股 {symbol}")
                return self.akshare_client
            else:
                logger.warning(f"AKShare 不可用，回退到 YFinance 获取 {symbol}")
                return self.yfinance_client
        else:
            logger.debug(f"使用 YFinance 获取 {market} {symbol}")
            return self.yfinance_client

    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        获取 OHLCV 数据（自动路由）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度

        Returns:
            DataFrame: OHLCV 数据
        """
        client = self.select_client(symbol)

        try:
            df = client.get_ohlcv(symbol, start_date, end_date, interval)
            logger.info(f"通过 {client.get_source_name()} 成功获取 {symbol} 数据")
            return df
        except DataNotFoundError:
            # 如果主数据源失败，尝试备用数据源
            if client.get_source_name() == 'akshare':
                logger.info(f"AKShare 未找到 {symbol}，尝试 YFinance")
                return self.yfinance_client.get_ohlcv(
                    symbol, start_date, end_date, interval
                )
            else:
                raise

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票信息（自动路由）

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票信息
        """
        client = self.select_client(symbol)

        try:
            info = client.get_stock_info(symbol)
            return info
        except DataNotFoundError:
            # 回退到备用数据源
            if client.get_source_name() == 'akshare':
                logger.info(f"AKShare 未找到 {symbol} 信息，尝试 YFinance")
                return self.yfinance_client.get_stock_info(symbol)
            else:
                raise

    def get_multiple_ohlcv(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据

        根据代码类型自动分组，使用相应的数据源批量获取

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度

        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}
        errors = {}

        # 按市场分组
        a_stocks = []
        other_stocks = []

        for symbol in symbols:
            market = self.detect_market(symbol)
            if market == 'A_STOCK':
                a_stocks.append(symbol)
            else:
                other_stocks.append(symbol)

        logger.info(f"批量获取: A股 {len(a_stocks)} 只, 其他 {len(other_stocks)} 只")

        # 获取 A 股数据
        if a_stocks and self._prefer_akshare and self.akshare_client:
            a_results = self.akshare_client.get_multiple_ohlcv(
                a_stocks, start_date, end_date, interval
            )
            results.update(a_results)

            # 记录失败的
            for symbol in a_stocks:
                if symbol not in a_results:
                    errors[symbol] = "AKShare 获取失败"
        elif a_stocks:
            # AKShare 不可用，使用 YFinance
            for symbol in a_stocks:
                other_stocks.append(symbol)

        # 获取其他股票数据
        for symbol in other_stocks:
            try:
                df = self.yfinance_client.get_ohlcv(
                    symbol, start_date, end_date, interval
                )
                results[symbol] = df
            except Exception as e:
                logger.warning(f"获取 {symbol} 失败: {e}")
                errors[symbol] = str(e)

        if errors:
            logger.warning(f"部分股票获取失败: {list(errors.keys())}")

        return results

    def is_available(self) -> Dict[str, bool]:
        """
        检查各数据源可用性

        Returns:
            dict: {source_name: is_available}
        """
        status = {
            'yfinance': self.yfinance_client.is_available(),
            'akshare': False
        }

        if self.akshare_client:
            status['akshare'] = self.akshare_client.is_available()

        return status


# 全局单例
_router_instance: Optional[DataRouter] = None


def get_data_router(prefer_akshare: bool = True) -> DataRouter:
    """
    获取数据路由器单例

    Args:
        prefer_akshare: 对于 A 股优先使用 AKShare

    Returns:
        DataRouter: 数据路由器实例
    """
    global _router_instance

    if _router_instance is None:
        _router_instance = DataRouter(prefer_akshare=prefer_akshare)

    return _router_instance
