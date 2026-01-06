"""
NewsSearcher - 新闻搜索引擎

input: 股票代码、交易日期、搜索范围
output: 新闻列表、情感分析结果、类别标记
pos: 分析器层 - 通过 Web Search 获取交易相关新闻背景

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import re
import time
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    source: str
    date: Optional[date] = None
    url: Optional[str] = None
    snippet: Optional[str] = None
    category: str = "other"  # earnings, product, analyst, sector, macro, geopolitical, other
    sentiment: str = "neutral"  # bullish, bearish, neutral
    relevance: float = 0.5  # 0-1


@dataclass
class NewsSearchResult:
    """新闻搜索结果"""
    symbol: str
    search_date: date
    search_range_days: int = 3

    # 新闻列表
    news_items: List[NewsItem] = field(default_factory=list)
    news_count: int = 0

    # 类别标记
    has_earnings: bool = False
    has_product_news: bool = False
    has_analyst_rating: bool = False
    has_sector_news: bool = False
    has_macro_news: bool = False
    has_geopolitical: bool = False

    # 情感分析
    overall_sentiment: str = "neutral"  # bullish, bearish, neutral, mixed
    sentiment_score: float = 0.0  # -100 to +100
    news_impact_level: str = "none"  # high, medium, low, none

    # 搜索元数据
    search_queries: List[str] = field(default_factory=list)
    search_source: str = "web_search"
    search_error: Optional[str] = None


class NewsSearcher:
    """
    新闻搜索引擎

    通过 Web Search 搜索股票相关新闻，进行分类和情感分析。
    内置缓存和速率限制。
    """

    # 速率限制: 10次/分钟
    RATE_LIMIT = 10
    RATE_WINDOW = 60  # 秒

    # 缓存 TTL: 7天
    CACHE_TTL_DAYS = 7

    # 情感关键词
    BULLISH_KEYWORDS = [
        'surge', 'soar', 'rally', 'jump', 'gain', 'rise', 'up',
        'beat', 'exceed', 'outperform', 'upgrade', 'buy',
        'bullish', 'optimistic', 'growth', 'record', 'high',
        'breakthrough', 'strong', 'positive', 'boom',
        '上涨', '大涨', '飙升', '突破', '创新高', '利好', '超预期'
    ]

    BEARISH_KEYWORDS = [
        'fall', 'drop', 'plunge', 'crash', 'decline', 'down',
        'miss', 'disappoint', 'underperform', 'downgrade', 'sell',
        'bearish', 'pessimistic', 'weak', 'low', 'concern', 'risk',
        'warning', 'cut', 'layoff', 'lawsuit', 'investigation',
        '下跌', '大跌', '暴跌', '利空', '不及预期', '裁员', '调查'
    ]

    # 类别关键词
    EARNINGS_KEYWORDS = [
        'earnings', 'revenue', 'profit', 'EPS', 'quarterly',
        'guidance', 'forecast', 'results', 'beat', 'miss',
        '财报', '季报', '业绩', '营收', '利润'
    ]

    ANALYST_KEYWORDS = [
        'analyst', 'upgrade', 'downgrade', 'price target',
        'rating', 'buy', 'sell', 'hold', 'overweight', 'underweight',
        '分析师', '评级', '目标价'
    ]

    PRODUCT_KEYWORDS = [
        'launch', 'release', 'announce', 'product', 'new',
        'innovation', 'feature', 'update', 'AI', 'chip',
        '发布', '新品', '产品', '创新'
    ]

    SECTOR_KEYWORDS = [
        'sector', 'industry', 'market', 'competitors',
        'tech', 'semiconductor', 'EV', 'energy',
        '行业', '板块', '市场'
    ]

    MACRO_KEYWORDS = [
        'Fed', 'interest rate', 'inflation', 'GDP', 'employment',
        'economic', 'policy', 'tariff', 'trade',
        '美联储', '利率', '通胀', '经济', '政策'
    ]

    GEOPOLITICAL_KEYWORDS = [
        'China', 'Taiwan', 'sanction', 'ban', 'war', 'conflict',
        'geopolitical', 'regulation', 'antitrust',
        '中国', '台湾', '制裁', '禁令', '监管'
    ]

    def __init__(self, search_func=None):
        """
        初始化新闻搜索器

        Args:
            search_func: 可选的自定义搜索函数，用于测试或替换搜索实现
                        签名: search_func(query: str) -> List[Dict]
        """
        self._search_func = search_func
        self._request_times: List[float] = []
        self._cache: Dict[str, NewsSearchResult] = {}

    def search(
        self,
        symbol: str,
        trade_date: date,
        range_days: int = 3,
        underlying_symbol: Optional[str] = None
    ) -> NewsSearchResult:
        """
        搜索股票相关新闻

        Args:
            symbol: 股票代码 (如 NVDA, AAPL)
            trade_date: 交易日期
            range_days: 搜索范围 (交易日前后 ±N 天)
            underlying_symbol: 期权的底层标的代码

        Returns:
            NewsSearchResult: 搜索结果
        """
        # 期权使用底层标的搜索
        search_symbol = underlying_symbol or symbol

        # 检查缓存
        cache_key = f"{search_symbol}_{trade_date}_{range_days}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            logger.debug(f"Cache hit for {cache_key}")
            return cached

        logger.info(f"Searching news for {search_symbol} around {trade_date}")

        result = NewsSearchResult(
            symbol=search_symbol,
            search_date=trade_date,
            search_range_days=range_days,
        )

        # 构建搜索查询
        queries = self._build_search_queries(search_symbol, trade_date, range_days)
        result.search_queries = queries

        # 执行搜索（带速率限制）
        all_news: List[NewsItem] = []
        for query in queries:
            if not self._check_rate_limit():
                logger.warning("Rate limit reached, waiting...")
                time.sleep(self.RATE_WINDOW / self.RATE_LIMIT)

            try:
                news_items = self._execute_search(query, trade_date, range_days)
                all_news.extend(news_items)
                self._record_request()
            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                result.search_error = str(e)

        # 去重和排序
        all_news = self._deduplicate_news(all_news)
        all_news.sort(key=lambda x: (x.relevance, x.date or date.min), reverse=True)

        # 限制数量
        result.news_items = all_news[:20]
        result.news_count = len(result.news_items)

        # 分析类别
        self._analyze_categories(result)

        # 分析情感
        self._analyze_sentiment(result)

        # 确定影响级别
        self._determine_impact_level(result)

        # 缓存结果
        self._cache[cache_key] = result

        logger.info(
            f"News search completed: {result.news_count} items, "
            f"sentiment={result.overall_sentiment}, impact={result.news_impact_level}"
        )

        return result

    def _build_search_queries(
        self,
        symbol: str,
        trade_date: date,
        range_days: int
    ) -> List[str]:
        """构建搜索查询列表"""
        date_str = trade_date.strftime("%Y-%m")

        # 获取公司名称映射
        company_names = {
            'NVDA': 'NVIDIA',
            'AAPL': 'Apple',
            'TSLA': 'Tesla',
            'MSFT': 'Microsoft',
            'GOOGL': 'Google Alphabet',
            'AMZN': 'Amazon',
            'META': 'Meta Facebook',
            'AMD': 'AMD',
            'INTC': 'Intel',
            'NFLX': 'Netflix',
        }
        company = company_names.get(symbol, symbol)

        queries = [
            # 公司新闻
            f"{company} {symbol} stock news {date_str}",
            # 财报
            f"{company} earnings report {date_str}",
            # 分析师评级
            f"{symbol} analyst rating upgrade downgrade {date_str}",
            # 产品/业务新闻
            f"{company} product launch announcement {date_str}",
        ]

        return queries

    def _execute_search(
        self,
        query: str,
        trade_date: date,
        range_days: int
    ) -> List[NewsItem]:
        """
        执行搜索查询

        实际项目中需要对接真实的搜索 API (如 Google Custom Search, Bing Search API)
        当前实现为占位符，返回模拟数据用于开发测试
        """
        if self._search_func:
            # 使用自定义搜索函数
            results = self._search_func(query)
            return [self._parse_search_result(r, trade_date) for r in results]

        # 默认返回空结果（需要对接真实搜索 API）
        logger.debug(f"No search function configured, returning empty results for: {query}")
        return []

    def _parse_search_result(self, result: Dict, trade_date: date) -> NewsItem:
        """解析搜索结果为 NewsItem"""
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        full_text = f"{title} {snippet}".lower()

        # 分类
        category = self._categorize_news(full_text)

        # 情感
        sentiment = self._analyze_single_sentiment(full_text)

        # 解析日期
        news_date = None
        if 'date' in result:
            try:
                if isinstance(result['date'], str):
                    news_date = datetime.strptime(result['date'], '%Y-%m-%d').date()
                else:
                    news_date = result['date']
            except:
                pass

        # 计算相关性
        relevance = self._calculate_relevance(result, trade_date)

        return NewsItem(
            title=title,
            source=result.get('source', 'unknown'),
            date=news_date,
            url=result.get('url'),
            snippet=snippet,
            category=category,
            sentiment=sentiment,
            relevance=relevance,
        )

    def _categorize_news(self, text: str) -> str:
        """对新闻进行分类"""
        text_lower = text.lower()

        # 按优先级检查类别
        if any(kw.lower() in text_lower for kw in self.EARNINGS_KEYWORDS):
            return "earnings"
        if any(kw.lower() in text_lower for kw in self.ANALYST_KEYWORDS):
            return "analyst"
        if any(kw.lower() in text_lower for kw in self.PRODUCT_KEYWORDS):
            return "product"
        if any(kw.lower() in text_lower for kw in self.GEOPOLITICAL_KEYWORDS):
            return "geopolitical"
        if any(kw.lower() in text_lower for kw in self.MACRO_KEYWORDS):
            return "macro"
        if any(kw.lower() in text_lower for kw in self.SECTOR_KEYWORDS):
            return "sector"

        return "other"

    def _analyze_single_sentiment(self, text: str) -> str:
        """分析单条新闻的情感"""
        text_lower = text.lower()

        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw.lower() in text_lower)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw.lower() in text_lower)

        if bullish_count > bearish_count + 1:
            return "bullish"
        elif bearish_count > bullish_count + 1:
            return "bearish"
        return "neutral"

    def _calculate_relevance(self, result: Dict, trade_date: date) -> float:
        """计算新闻相关性得分 (0-1)"""
        relevance = 0.5

        # 日期越接近交易日，相关性越高
        if 'date' in result:
            try:
                if isinstance(result['date'], str):
                    news_date = datetime.strptime(result['date'], '%Y-%m-%d').date()
                else:
                    news_date = result['date']
                days_diff = abs((news_date - trade_date).days)
                if days_diff == 0:
                    relevance += 0.3
                elif days_diff <= 1:
                    relevance += 0.2
                elif days_diff <= 3:
                    relevance += 0.1
            except:
                pass

        # 来源权重
        high_quality_sources = ['reuters', 'bloomberg', 'wsj', 'cnbc', 'yahoo finance']
        source = result.get('source', '').lower()
        if any(src in source for src in high_quality_sources):
            relevance += 0.2

        return min(relevance, 1.0)

    def _deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """去除重复新闻"""
        seen_titles = set()
        unique_news = []

        for item in news_items:
            # 简化标题用于去重
            simplified = re.sub(r'[^\w\s]', '', item.title.lower())[:50]
            if simplified not in seen_titles:
                seen_titles.add(simplified)
                unique_news.append(item)

        return unique_news

    def _analyze_categories(self, result: NewsSearchResult):
        """分析新闻类别标记"""
        for item in result.news_items:
            if item.category == "earnings":
                result.has_earnings = True
            elif item.category == "product":
                result.has_product_news = True
            elif item.category == "analyst":
                result.has_analyst_rating = True
            elif item.category == "sector":
                result.has_sector_news = True
            elif item.category == "macro":
                result.has_macro_news = True
            elif item.category == "geopolitical":
                result.has_geopolitical = True

    def _analyze_sentiment(self, result: NewsSearchResult):
        """分析整体情感"""
        if not result.news_items:
            result.overall_sentiment = "neutral"
            result.sentiment_score = 0.0
            return

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for item in result.news_items:
            weight = item.relevance  # 按相关性加权
            if item.sentiment == "bullish":
                bullish_count += weight
            elif item.sentiment == "bearish":
                bearish_count += weight
            else:
                neutral_count += weight

        total = bullish_count + bearish_count + neutral_count
        if total == 0:
            result.overall_sentiment = "neutral"
            result.sentiment_score = 0.0
            return

        # 计算情感分数 (-100 to +100)
        result.sentiment_score = ((bullish_count - bearish_count) / total) * 100

        # 确定整体情感
        if bullish_count > bearish_count * 1.5 and bullish_count > neutral_count:
            result.overall_sentiment = "bullish"
        elif bearish_count > bullish_count * 1.5 and bearish_count > neutral_count:
            result.overall_sentiment = "bearish"
        elif abs(bullish_count - bearish_count) < total * 0.1:
            result.overall_sentiment = "neutral"
        else:
            result.overall_sentiment = "mixed"

    def _determine_impact_level(self, result: NewsSearchResult):
        """确定新闻影响级别"""
        if not result.news_items:
            result.news_impact_level = "none"
            return

        # 高影响: 财报或地缘政治 + 新闻数量多
        if result.has_earnings or result.has_geopolitical:
            if result.news_count >= 3:
                result.news_impact_level = "high"
                return

        # 中等影响: 分析师评级或产品新闻
        if result.has_analyst_rating or result.has_product_news:
            result.news_impact_level = "medium"
            return

        # 低影响: 一般新闻
        if result.news_count >= 2:
            result.news_impact_level = "low"
            return

        result.news_impact_level = "none"

    def _check_rate_limit(self) -> bool:
        """检查是否超过速率限制"""
        now = time.time()
        # 清理过期记录
        self._request_times = [t for t in self._request_times if now - t < self.RATE_WINDOW]
        return len(self._request_times) < self.RATE_LIMIT

    def _record_request(self):
        """记录请求时间"""
        self._request_times.append(time.time())

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("News search cache cleared")

    def to_news_context_dict(self, result: NewsSearchResult) -> Dict[str, Any]:
        """将搜索结果转换为 NewsContext 可用的字典"""
        return {
            'symbol': result.symbol,
            'search_date': result.search_date,
            'search_range_days': result.search_range_days,
            'search_source': result.search_source,

            'has_earnings': result.has_earnings,
            'has_product_news': result.has_product_news,
            'has_analyst_rating': result.has_analyst_rating,
            'has_sector_news': result.has_sector_news,
            'has_macro_news': result.has_macro_news,
            'has_geopolitical': result.has_geopolitical,

            'overall_sentiment': result.overall_sentiment,
            'sentiment_score': result.sentiment_score,
            'news_impact_level': result.news_impact_level,

            'news_items': [
                {
                    'title': item.title,
                    'source': item.source,
                    'date': str(item.date) if item.date else None,
                    'url': item.url,
                    'snippet': item.snippet,
                    'category': item.category,
                    'sentiment': item.sentiment,
                    'relevance': item.relevance,
                }
                for item in result.news_items
            ],
            'search_queries': result.search_queries,
            'news_count': result.news_count,
        }
