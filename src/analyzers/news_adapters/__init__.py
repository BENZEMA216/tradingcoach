"""
news_adapters - 新闻搜索适配器模块

input: 配置参数、网络区域设置
output: 适合当前网络环境的新闻搜索适配器
pos: 分析器层 - 统一管理多个新闻搜索后端，自动选择最佳提供商

支持的适配器:
- DDGSAdapter: 默认首选，免费无需 API Key，多引擎支持
- TavilyAdapter: 国际网络备选，LLM友好（需 API Key）
- PolygonAdapter: 专业金融新闻，双网络可用（需 API Key）

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
import socket
from typing import Optional, List, Callable, Dict, Any

from .base import NewsAdapter, MockNewsAdapter
from .ddgs_adapter import DDGSAdapter
from .tavily_adapter import TavilyAdapter
from .polygon_adapter import PolygonAdapter

logger = logging.getLogger(__name__)

__all__ = [
    'NewsAdapter',
    'MockNewsAdapter',
    'DDGSAdapter',
    'TavilyAdapter',
    'PolygonAdapter',
    'get_news_adapter',
    'create_search_func',
    'detect_network_region',
]


def detect_network_region(timeout: float = 3.0) -> str:
    """
    自动检测网络区域

    尝试连接 google.com 来判断是否在国际网络环境

    Args:
        timeout: 连接超时时间（秒）

    Returns:
        "international" 或 "china"
    """
    try:
        # 尝试连接 google.com
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("www.google.com", 443))
        logger.info("Network region detected: international")
        return "international"
    except (socket.timeout, socket.error, OSError):
        logger.info("Network region detected: china")
        return "china"


def get_news_adapter(
    region: str = "auto",
    tavily_key: Optional[str] = None,
    polygon_key: Optional[str] = None,
    providers_international: Optional[List[str]] = None,
    providers_china: Optional[List[str]] = None,
) -> Optional[NewsAdapter]:
    """
    获取适合当前网络环境的新闻搜索适配器

    Args:
        region: 网络区域 ("international", "china", "auto")
        tavily_key: Tavily API Key
        polygon_key: Polygon.io API Key
        providers_international: 国际网络提供商优先级
        providers_china: 中国网络提供商优先级

    Returns:
        可用的新闻适配器，如果没有可用的返回 None
    """
    # 自动检测网络区域
    if region == "auto":
        region = detect_network_region()

    # 选择提供商优先级 (DDGS 为默认首选，免费无需配置)
    if region == "international":
        providers = providers_international or ["ddgs", "tavily", "polygon"]
    else:
        providers = providers_china or ["ddgs", "polygon"]

    # 适配器映射
    # DDGS 不需要 API Key，始终可尝试
    adapter_map = {
        "ddgs": lambda: DDGSAdapter(),
        "tavily": lambda: TavilyAdapter(tavily_key) if tavily_key else None,
        "polygon": lambda: PolygonAdapter(polygon_key) if polygon_key else None,
    }

    # 按优先级尝试获取可用的适配器
    for provider in providers:
        factory = adapter_map.get(provider)
        if factory:
            adapter = factory()
            if adapter and adapter.is_available():
                logger.info(f"Using news adapter: {adapter.name}")
                return adapter
            elif adapter:
                logger.debug(f"Adapter {provider} not available")

    logger.warning("No news adapter available")
    return None


def create_search_func(
    region: str = "auto",
    tavily_key: Optional[str] = None,
    polygon_key: Optional[str] = None,
) -> Optional[Callable[[str], List[Dict[str, Any]]]]:
    """
    创建搜索函数，用于注入到 NewsSearcher

    这个函数返回一个符合 NewsSearcher.search_func 签名的函数:
    search_func(query: str) -> List[Dict]

    Args:
        region: 网络区域
        tavily_key: Tavily API Key
        polygon_key: Polygon.io API Key

    Returns:
        搜索函数，如果没有可用适配器返回 None
    """
    adapter = get_news_adapter(
        region=region,
        tavily_key=tavily_key,
        polygon_key=polygon_key,
    )

    if not adapter:
        return None

    def search_func(query: str) -> List[Dict[str, Any]]:
        """封装的搜索函数"""
        return adapter.search(query)

    return search_func


def get_adapter_from_config() -> Optional[NewsAdapter]:
    """
    从 config.py 配置自动获取适配器

    读取 config.py 中的配置，自动选择合适的适配器
    """
    try:
        import sys
        import os

        # 确保能导入 config
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        import config

        return get_news_adapter(
            region=getattr(config, 'NEWS_NETWORK_REGION', 'auto'),
            tavily_key=getattr(config, 'TAVILY_API_KEY', None),
            polygon_key=getattr(config, 'POLYGON_API_KEY', None),
            providers_international=getattr(config, 'NEWS_PROVIDERS_INTERNATIONAL', None),
            providers_china=getattr(config, 'NEWS_PROVIDERS_CHINA', None),
        )
    except ImportError as e:
        logger.error(f"Failed to import config: {e}")
        return None


def create_search_func_from_config() -> Optional[Callable[[str], List[Dict[str, Any]]]]:
    """
    从 config.py 配置创建搜索函数

    这是最常用的方法，直接从配置文件读取 API Keys 和区域设置
    """
    adapter = get_adapter_from_config()
    if not adapter:
        return None

    def search_func(query: str) -> List[Dict[str, Any]]:
        return adapter.search(query)

    return search_func
