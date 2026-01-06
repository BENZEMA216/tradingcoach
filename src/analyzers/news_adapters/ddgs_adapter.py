"""
DDGSAdapter - DDGS 多引擎新闻搜索适配器

input: 搜索查询
output: 标准化的新闻搜索结果
pos: 分析器层 - 使用 DDGS 库聚合多个搜索引擎，免费无需 API Key

DDGS 特点:
- 免费，无需 API Key
- 多引擎支持: DuckDuckGo, Bing, Yahoo
- 专门的 news() 方法搜索新闻
- GitHub: https://github.com/deedy5/duckduckgo_search

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from .base import NewsAdapter

logger = logging.getLogger(__name__)

# 延迟导入 DDGS，避免未安装时报错
DDGS = None


def _get_ddgs():
    """延迟导入 DDGS"""
    global DDGS
    if DDGS is None:
        try:
            from ddgs import DDGS as _DDGS
            DDGS = _DDGS
        except ImportError:
            logger.warning("ddgs package not installed. Run: pip install -U ddgs")
            return None
    return DDGS


class DDGSAdapter(NewsAdapter):
    """
    DDGS 多引擎新闻搜索适配器

    使用 DDGS 库聚合 DuckDuckGo、Bing、Yahoo 等多个搜索引擎，
    免费且无需 API Key。
    """

    name = "ddgs"
    requires_api_key = False  # 无需 API Key

    # 支持的新闻后端
    NEWS_BACKENDS = ["duckduckgo", "bing", "yahoo"]

    # 区域映射
    REGION_MAP = {
        "us": "us-en",
        "uk": "uk-en",
        "cn": "cn-zh",
        "hk": "hk-tzh",
        "tw": "tw-tzh",
    }

    def __init__(self, backend: str = "duckduckgo", region: str = "us-en"):
        """
        初始化 DDGS 适配器

        Args:
            backend: 新闻搜索后端 (duckduckgo, bing, yahoo)
            region: 搜索区域 (us-en, cn-zh, etc.)
        """
        super().__init__()
        self.backend = backend if backend in self.NEWS_BACKENDS else "duckduckgo"
        self.region = region

    def is_available(self) -> bool:
        """检查 DDGS 是否可用"""
        return _get_ddgs() is not None

    def search(
        self,
        query: str,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        使用 DDGS 搜索新闻

        Args:
            query: 搜索查询
            search_date: 目标日期（用于过滤结果）
            days_range: 日期范围

        Returns:
            标准化的新闻列表
        """
        ddgs_class = _get_ddgs()
        if not ddgs_class:
            logger.warning("DDGS not available")
            return []

        try:
            # 确定时间限制
            # DDGS timelimit: d=day, w=week, m=month, y=year
            if days_range <= 1:
                timelimit = "d"
            elif days_range <= 7:
                timelimit = "w"
            elif days_range <= 30:
                timelimit = "m"
            else:
                timelimit = "y"

            # 执行新闻搜索
            with ddgs_class() as ddgs:
                raw_results = list(ddgs.news(
                    query,  # 第一个位置参数
                    region=self.region,
                    safesearch="off",
                    timelimit=timelimit,
                    max_results=10,
                ))

            # 解析结果
            results = []
            for item in raw_results:
                # DDGS news() 返回格式:
                # {
                #   'date': '2024-01-15T10:30:00',
                #   'title': 'News Title',
                #   'body': 'News snippet...',
                #   'url': 'https://...',
                #   'source': 'Reuters'
                # }
                date_str = ""
                if "date" in item:
                    try:
                        # 提取日期部分
                        date_str = item["date"][:10] if item["date"] else ""
                    except:
                        pass

                results.append(self._normalize_result({
                    'title': item.get('title', ''),
                    'snippet': item.get('body', ''),
                    'source': item.get('source', 'unknown'),
                    'url': item.get('url', ''),
                    'date': date_str,
                }))

            logger.info(f"DDGS search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.error(f"DDGS search error: {e}")
            return []

    def search_text(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        使用 DDGS 进行通用文本搜索（非新闻专用）

        Args:
            query: 搜索查询
            max_results: 最大结果数

        Returns:
            标准化的搜索结果列表
        """
        ddgs_class = _get_ddgs()
        if not ddgs_class:
            return []

        try:
            with ddgs_class() as ddgs:
                raw_results = list(ddgs.text(
                    query,  # 第一个位置参数
                    region=self.region,
                    safesearch="off",
                    max_results=max_results,
                ))

            results = []
            for item in raw_results:
                # text() 返回格式:
                # {
                #   'title': 'Title',
                #   'href': 'https://...',
                #   'body': 'Snippet...'
                # }
                results.append(self._normalize_result({
                    'title': item.get('title', ''),
                    'snippet': item.get('body', ''),
                    'source': self._extract_domain(item.get('href', '')),
                    'url': item.get('href', ''),
                    'date': '',
                }))

            return results

        except Exception as e:
            logger.error(f"DDGS text search error: {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"

    def _check_availability(self) -> bool:
        """检查 DDGS 是否可用（只检查库是否安装）"""
        return _get_ddgs() is not None
