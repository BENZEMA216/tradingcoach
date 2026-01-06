"""
PolygonAdapter - Polygon.io 新闻搜索适配器

input: 股票代码、API Key
output: 标准化的新闻搜索结果
pos: 分析器层 - Polygon.io News API 实现，专业金融新闻

Polygon.io 特点:
- 专业金融新闻 API
- 按股票代码搜索
- 数据质量高
- 用户已有 API Key

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import logging
import requests
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from .base import NewsAdapter

logger = logging.getLogger(__name__)


class PolygonAdapter(NewsAdapter):
    """
    Polygon.io 新闻搜索适配器

    使用 Polygon.io 的金融新闻 API，专业的股票新闻数据。
    """

    name = "polygon"
    requires_api_key = True

    # API 端点
    API_URL = "https://api.polygon.io/v2/reference/news"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)

    def search(
        self,
        query: str,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        使用 Polygon.io News API 搜索新闻

        注意: Polygon 按 ticker 搜索，需要从 query 中提取股票代码

        Args:
            query: 搜索查询（应包含股票代码）
            search_date: 目标日期
            days_range: 日期范围

        Returns:
            标准化的新闻列表
        """
        if not self.api_key:
            logger.warning("Polygon API key not configured")
            return []

        # 从查询中提取可能的股票代码
        ticker = self._extract_ticker(query)
        if not ticker:
            logger.debug(f"No ticker found in query: {query}")
            return []

        try:
            params = {
                "ticker": ticker,
                "limit": 10,
                "apiKey": self.api_key,
            }

            # 添加日期过滤
            if search_date:
                start_date = search_date - timedelta(days=days_range)
                end_date = search_date + timedelta(days=days_range)
                params["published_utc.gte"] = start_date.isoformat()
                params["published_utc.lte"] = end_date.isoformat()

            response = requests.get(
                self.API_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 解析结果
            results = []
            for item in data.get("results", []):
                # 解析日期
                date_str = ""
                if "published_utc" in item:
                    try:
                        date_str = item["published_utc"][:10]
                    except:
                        pass

                results.append(self._normalize_result({
                    'title': item.get('title', ''),
                    'snippet': item.get('description', ''),
                    'source': item.get('publisher', {}).get('name', 'unknown'),
                    'url': item.get('article_url', ''),
                    'date': date_str,
                }))

            logger.info(f"Polygon search returned {len(results)} results for ticker: {ticker}")
            return results

        except requests.exceptions.Timeout:
            logger.error("Polygon API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Polygon API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Polygon search error: {e}")
            return []

    def search_symbol(
        self,
        symbol: str,
        company_name: Optional[str] = None,
        search_date: Optional[date] = None,
        days_range: int = 3
    ) -> List[Dict[str, Any]]:
        """
        直接按股票代码搜索（更高效）
        """
        return self.search(symbol, search_date, days_range)

    def _extract_ticker(self, query: str) -> Optional[str]:
        """从查询字符串中提取股票代码"""
        # 常见股票代码列表
        known_tickers = [
            'NVDA', 'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'GOOG', 'AMZN',
            'META', 'AMD', 'INTC', 'NFLX', 'BABA', 'JD', 'NIO',
            'SPY', 'QQQ', 'IWM', 'VIX',
        ]

        query_upper = query.upper()
        for ticker in known_tickers:
            if ticker in query_upper:
                return ticker

        # 尝试匹配 1-5 个大写字母的模式
        import re
        matches = re.findall(r'\b([A-Z]{1,5})\b', query_upper)
        for match in matches:
            if match not in ['THE', 'AND', 'FOR', 'WITH', 'NEWS', 'STOCK']:
                return match

        return None

    def _check_availability(self) -> bool:
        """检查 Polygon API 是否可访问"""
        if not self.api_key:
            return False

        try:
            response = requests.get(
                self.API_URL,
                params={"ticker": "AAPL", "limit": 1, "apiKey": self.api_key},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
