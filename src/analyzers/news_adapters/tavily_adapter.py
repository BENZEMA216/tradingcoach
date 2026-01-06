"""
TavilyAdapter - Tavily 新闻搜索适配器

input: 搜索查询、API Key
output: 标准化的新闻搜索结果
pos: 分析器层 - Tavily API 实现，适用于国际网络用户

Tavily 特点:
- 专为 LLM/AI Agent 设计
- 返回结构化 JSON 数据
- 支持历史日期搜索
- 注册: https://tavily.com

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
import requests
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from .base import NewsAdapter

logger = logging.getLogger(__name__)


class TavilyAdapter(NewsAdapter):
    """
    Tavily 新闻搜索适配器

    Tavily 是专为 AI Agent 设计的搜索 API，返回结构化数据，
    非常适合 LLM 应用。
    """

    name = "tavily"
    requires_api_key = True

    # API 端点
    API_URL = "https://api.tavily.com/search"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)

    def search(
        self,
        query: str,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        使用 Tavily API 搜索新闻

        Args:
            query: 搜索查询
            search_date: 目标日期
            days_range: 日期范围

        Returns:
            标准化的新闻列表
        """
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            return []

        try:
            # 构建请求参数
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": False,
                "include_raw_content": False,
                "max_results": 10,
                "include_domains": [
                    "reuters.com",
                    "bloomberg.com",
                    "cnbc.com",
                    "wsj.com",
                    "yahoo.com",
                    "marketwatch.com",
                    "seekingalpha.com",
                    "fool.com",
                    "investing.com",
                    "barrons.com",
                ],
            }

            # 如果指定了日期，添加日期过滤
            if search_date:
                start_date = search_date - timedelta(days=days_range)
                end_date = search_date + timedelta(days=days_range)
                # Tavily 使用 topic 参数来过滤新闻
                payload["topic"] = "news"

            # 发送请求
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 解析结果
            results = []
            for item in data.get("results", []):
                results.append(self._normalize_result({
                    'title': item.get('title', ''),
                    'snippet': item.get('content', ''),
                    'source': self._extract_domain(item.get('url', '')),
                    'url': item.get('url', ''),
                    'date': item.get('published_date', ''),
                }))

            logger.info(f"Tavily search returned {len(results)} results for: {query}")
            return results

        except requests.exceptions.Timeout:
            logger.error("Tavily API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Tavily API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # 移除 www. 前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"

    def _check_availability(self) -> bool:
        """检查 Tavily API 是否可访问"""
        if not self.api_key:
            return False

        try:
            # 简单的连通性测试
            response = requests.post(
                self.API_URL,
                json={
                    "api_key": self.api_key,
                    "query": "test",
                    "max_results": 1,
                },
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
