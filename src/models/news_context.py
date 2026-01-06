"""
NewsContext - 新闻上下文数据模型

input: 新闻搜索结果、情感分析
output: 持仓相关的新闻背景和评分
pos: 数据模型层 - 存储交易相关的新闻上下文用于评分和复盘

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    ForeignKey, Index, JSON, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class NewsSentiment(enum.Enum):
    """新闻情感枚举"""
    BULLISH = "bullish"      # 看涨
    BEARISH = "bearish"      # 看跌
    NEUTRAL = "neutral"      # 中性
    MIXED = "mixed"          # 混合


class NewsImpactLevel(enum.Enum):
    """新闻影响级别"""
    HIGH = "high"            # 高影响（财报、重大公告）
    MEDIUM = "medium"        # 中等影响
    LOW = "low"              # 低影响
    NONE = "none"            # 无显著新闻


class NewsCategory(enum.Enum):
    """新闻类别"""
    EARNINGS = "earnings"           # 财报相关
    PRODUCT = "product"             # 产品发布
    ANALYST = "analyst"             # 分析师评级
    SECTOR = "sector"               # 行业新闻
    MACRO = "macro"                 # 宏观经济
    GEOPOLITICAL = "geopolitical"   # 地缘政治
    MANAGEMENT = "management"       # 管理层变动
    REGULATORY = "regulatory"       # 监管相关
    OTHER = "other"                 # 其他


class NewsContext(Base):
    """
    新闻上下文表

    存储与持仓相关的新闻搜索结果和情感分析
    用于评分系统中的"新闻契合度"维度
    """
    __tablename__ = 'news_context'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 关联信息 ====================
    position_id = Column(
        Integer,
        ForeignKey('positions.id'),
        nullable=False,
        index=True,
        comment="关联的持仓ID"
    )

    # ==================== 搜索元数据 ====================
    symbol = Column(String(50), nullable=False, index=True, comment="股票代码")
    underlying_symbol = Column(String(50), index=True, comment="期权底层标的")
    search_date = Column(Date, nullable=False, index=True, comment="搜索中心日期（交易日）")
    search_range_days = Column(Integer, default=3, comment="搜索范围（±天数）")
    search_source = Column(String(50), default='web_search', comment="搜索来源")

    # ==================== 新闻类别标记 ====================
    has_earnings = Column(Boolean, default=False, comment="是否有财报新闻")
    has_product_news = Column(Boolean, default=False, comment="是否有产品新闻")
    has_analyst_rating = Column(Boolean, default=False, comment="是否有分析师评级")
    has_sector_news = Column(Boolean, default=False, comment="是否有行业新闻")
    has_macro_news = Column(Boolean, default=False, comment="是否有宏观新闻")
    has_geopolitical = Column(Boolean, default=False, comment="是否有地缘政治新闻")

    # ==================== 情感分析 ====================
    overall_sentiment = Column(
        String(20),
        comment="整体情感: bullish/bearish/neutral/mixed"
    )
    sentiment_score = Column(
        Numeric(6, 2),
        comment="情感评分: -100 到 +100"
    )
    news_impact_level = Column(
        String(20),
        default='none',
        comment="新闻影响级别: high/medium/low/none"
    )

    # ==================== 新闻数据存储 ====================
    news_items = Column(
        JSON,
        comment="新闻列表: [{title, source, date, url, category, sentiment, relevance}]"
    )
    search_queries = Column(
        JSON,
        comment="使用的搜索查询"
    )
    news_count = Column(Integer, default=0, comment="新闻数量")

    # ==================== 评分结果 ====================
    news_alignment_score = Column(
        Numeric(5, 2),
        comment="新闻契合度评分: 0-100"
    )
    score_breakdown = Column(
        JSON,
        comment="评分细节: {direction, timing, completeness, risk}"
    )
    scoring_warnings = Column(
        JSON,
        comment="评分警告信息"
    )

    # ==================== 缓存管理 ====================
    cached_at = Column(
        DateTime,
        default=datetime.utcnow,
        comment="缓存时间"
    )
    cache_valid_until = Column(
        DateTime,
        comment="缓存有效期"
    )
    is_stale = Column(Boolean, default=False, comment="缓存是否过期")

    # ==================== 时间戳 ====================
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # ==================== 关系 ====================
    # 通过 position_id 关联到 Position (多对一，但实际是一对一)
    position = relationship(
        "Position",
        foreign_keys=[position_id],
        backref="news_context_ref"  # 使用不同名称避免冲突
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('ix_news_context_symbol_date', 'symbol', 'search_date'),
        Index('ix_news_context_cache', 'symbol', 'search_date', 'is_stale'),
    )

    def __repr__(self) -> str:
        return (
            f"<NewsContext(id={self.id}, symbol='{self.symbol}', "
            f"date={self.search_date}, sentiment={self.overall_sentiment}, "
            f"score={self.news_alignment_score})>"
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'position_id': self.position_id,
            'symbol': self.symbol,
            'search_date': str(self.search_date) if self.search_date else None,
            'overall_sentiment': self.overall_sentiment,
            'sentiment_score': float(self.sentiment_score) if self.sentiment_score else None,
            'news_impact_level': self.news_impact_level,
            'news_count': self.news_count,
            'has_earnings': self.has_earnings,
            'has_analyst_rating': self.has_analyst_rating,
            'has_macro_news': self.has_macro_news,
            'news_items': self.news_items,
            'news_alignment_score': float(self.news_alignment_score) if self.news_alignment_score else None,
            'score_breakdown': self.score_breakdown,
        }

    @property
    def is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self.is_stale:
            return False
        if not self.cache_valid_until:
            return False
        return datetime.utcnow() < self.cache_valid_until

    @property
    def summary(self) -> str:
        """生成简短摘要"""
        if not self.news_items:
            return "No significant news found"

        sentiment_emoji = {
            'bullish': '📈',
            'bearish': '📉',
            'neutral': '➡️',
            'mixed': '↔️'
        }
        emoji = sentiment_emoji.get(self.overall_sentiment, '❓')

        categories = []
        if self.has_earnings:
            categories.append('Earnings')
        if self.has_analyst_rating:
            categories.append('Analyst')
        if self.has_macro_news:
            categories.append('Macro')

        cat_str = ', '.join(categories) if categories else 'General'

        return f"{emoji} {self.overall_sentiment} ({self.news_count} news) - {cat_str}"
