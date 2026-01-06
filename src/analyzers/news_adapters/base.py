"""
NewsAdapter Base - 新闻搜索适配器基类

input: 搜索查询、日期范围
output: 标准化的新闻搜索结果
pos: 分析器层 - 提供统一的新闻搜索接口，支持多个后端提供商

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class NewsAdapter(ABC):
    """
    新闻搜索适配器基类

    所有新闻搜索提供商都需要实现此接口，返回标准化的搜索结果。
    """

    # 适配器名称
    name: str = "base"

    # 是否需要 API Key
    requires_api_key: bool = True

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化适配器

        Args:
            api_key: API密钥（如果需要）
        """
        self.api_key = api_key
        self._initialized = False

    def is_available(self) -> bool:
        """检查适配器是否可用（API Key已配置且有效）"""
        if self.requires_api_key and not self.api_key:
            return False
        return self._check_availability()

    def _check_availability(self) -> bool:
        """子类可重写以添加额外的可用性检查"""
        return True

    @abstractmethod
    def search(
        self,
        query: str,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        执行新闻搜索

        Args:
            query: 搜索查询字符串
            search_date: 目标日期（搜索该日期前后的新闻）
            days_range: 日期范围（±N天）

        Returns:
            标准化的新闻列表，每条新闻包含:
            - title: str - 新闻标题
            - snippet: str - 新闻摘要
            - source: str - 新闻来源
            - url: str - 新闻链接
            - date: str - 发布日期 (YYYY-MM-DD 格式)
        """
        pass

    def search_symbol(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        搜索股票相关新闻（便捷方法）

        Args:
            symbol: 股票代码 (如 NVDA)
            company_name: 公司名称 (如 NVIDIA)
            search_date: 目标日期
            days_range: 日期范围

        Returns:
            标准化的新闻列表
        """
        # 构建查询
        if company_name:
            query = f"{company_name} {symbol} stock news"
        else:
            query = f"{symbol} stock news"

        return self.search(query, search_date, days_range)

    def _normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将原始搜索结果标准化为统一格式

        子类应该在 search() 中调用此方法来标准化结果
        """
        return {
            'title': raw_result.get('title', ''),
            'snippet': raw_result.get('snippet', raw_result.get('description', '')),
            'source': raw_result.get('source', raw_result.get('domain', 'unknown')),
            'url': raw_result.get('url', raw_result.get('link', '')),
            'date': raw_result.get('date', raw_result.get('published_date', '')),
        }


class MockNewsAdapter(NewsAdapter):
    """
    模拟新闻适配器（用于测试）
    """

    name = "mock"
    requires_api_key = False

    def __init__(self, mock_results: Optional[List[Dict]] = None):
        super().__init__()
        self.mock_results = mock_results or []

    def search(
        self,
        query: str,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """返回模拟结果"""
        logger.debug(f"MockNewsAdapter.search: {query}")
        return self.mock_results
