"""
Data Sources - 市场数据获取模块

提供多数据源支持和智能三级缓存机制
"""

from src.data_sources.base_client import (
    BaseDataClient,
    DataSourceError,
    RateLimitError,
    DataNotFoundError
)
from src.data_sources.yfinance_client import YFinanceClient
from src.data_sources.akshare_client import AKShareClient
from src.data_sources.options_client import OptionsClient, get_options_client
from src.data_sources.cache_manager import CacheManager
from src.data_sources.batch_fetcher import BatchFetcher
from src.data_sources.market_env_fetcher import MarketEnvironmentFetcher
from src.data_sources.data_router import DataRouter, get_data_router

__all__ = [
    # Base
    'BaseDataClient',
    'DataSourceError',
    'RateLimitError',
    'DataNotFoundError',

    # Clients
    'YFinanceClient',
    'AKShareClient',
    'OptionsClient',
    'get_options_client',

    # Cache
    'CacheManager',

    # Batch
    'BatchFetcher',

    # Market Environment
    'MarketEnvironmentFetcher',

    # Router
    'DataRouter',
    'get_data_router',
]
