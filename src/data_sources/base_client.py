"""
BaseDataClient - 数据源客户端抽象基类

定义所有数据源客户端的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import date, datetime
import pandas as pd


# ==================== 异常定义 ====================

class DataSourceError(Exception):
    """数据源基础异常"""
    pass


class RateLimitError(DataSourceError):
    """API限流异常"""
    pass


class DataNotFoundError(DataSourceError):
    """数据未找到异常"""
    pass


class InvalidSymbolError(DataSourceError):
    """无效的股票代码"""
    pass


# ==================== 抽象基类 ====================

class BaseDataClient(ABC):
    """
    数据源客户端抽象基类

    所有数据源客户端（yfinance, Alpha Vantage等）都应继承此类
    并实现抽象方法
    """

    @abstractmethod
    def get_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = '1d'
    ) -> pd.DataFrame:
        """
        获取OHLCV数据

        Args:
            symbol: 股票代码（如 'AAPL', '09988.HK'）
            start_date: 开始日期
            end_date: 结束日期
            interval: 时间粒度（'1d', '1h', '5m'等）

        Returns:
            DataFrame with columns: ['Open', 'High', 'Low', 'Close', 'Volume']
            Index: DatetimeIndex

        Raises:
            DataNotFoundError: 数据不存在
            RateLimitError: 超过请求限制
            DataSourceError: 其他错误
        """
        pass

    @abstractmethod
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict with keys:
                - name: 公司名称
                - sector: 行业
                - market_cap: 市值
                - currency: 币种
                - ...

        Raises:
            DataNotFoundError: 信息不存在
            DataSourceError: 其他错误
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            bool: True表示可用，False表示不可用
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        获取数据源名称

        Returns:
            str: 数据源名称（如 'yfinance', 'alpha_vantage'）
        """
        pass

    def standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名和格式

        不同数据源返回的列名可能不同，统一标准化为：
        ['Open', 'High', 'Low', 'Close', 'Volume']

        Args:
            df: 原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        if df.empty:
            return df

        # 列名映射（小写 → 标题格式）
        column_mapping = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'adj close': 'Adj Close',
            'adj_close': 'Adj Close'
        }

        # 重命名列
        df.columns = [column_mapping.get(col.lower(), col) for col in df.columns]

        # 确保有必需的列
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")

        # 按标准列顺序排序
        standard_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        other_columns = [col for col in df.columns if col not in standard_columns]
        df = df[standard_columns + other_columns]

        # 确保索引是DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                df.index = pd.to_datetime(df.index)
            except Exception as e:
                raise ValueError(f"无法将索引转换为DatetimeIndex: {e}")

        # 移除NaN行
        df = df.dropna(subset=['Close'])

        return df

    def validate_symbol(self, symbol: str) -> bool:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码

        Returns:
            bool: True表示格式有效
        """
        if not symbol or not isinstance(symbol, str):
            return False

        # 移除空格
        symbol = symbol.strip()

        # 基本长度检查
        if len(symbol) < 1 or len(symbol) > 50:
            return False

        return True

    def validate_date_range(self, start_date: date, end_date: date) -> bool:
        """
        验证日期范围

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            bool: True表示日期范围有效
        """
        if not isinstance(start_date, date) or not isinstance(end_date, date):
            return False

        # 开始日期不能晚于结束日期
        if start_date > end_date:
            return False

        # 结束日期不能晚于今天
        if end_date > date.today():
            return False

        return True
