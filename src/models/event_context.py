"""
EventContext - 事件上下文数据模型

input: 财报日历、价格异常检测、新闻事件
output: 持仓期间发生的重大事件记录及市场反应
pos: 数据模型层 - 存储与持仓关联的市场事件，用于事件复盘和归因分析

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    ForeignKey, Index, JSON, Boolean, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class EventType(enum.Enum):
    """事件类型枚举"""
    EARNINGS = "earnings"               # 财报发布
    EARNINGS_PRE = "earnings_pre"       # 财报前（盘前发布）
    EARNINGS_POST = "earnings_post"     # 财报后（盘后发布）
    DIVIDEND = "dividend"               # 分红公告
    SPLIT = "split"                     # 股票拆分
    PRODUCT = "product"                 # 产品发布
    GUIDANCE = "guidance"               # 业绩指引更新
    ANALYST = "analyst"                 # 分析师评级变动
    INSIDER = "insider"                 # 内部人交易
    BUYBACK = "buyback"                 # 回购公告
    OFFERING = "offering"               # 增发
    FDA = "fda"                         # FDA审批（医药股）
    CONTRACT = "contract"               # 重大合同
    MANAGEMENT = "management"           # 管理层变动
    MACRO = "macro"                     # 宏观经济事件
    FED = "fed"                         # 美联储会议/决议
    CPI = "cpi"                         # CPI/通胀数据
    NFP = "nfp"                         # 非农就业
    GEOPOLITICAL = "geopolitical"       # 地缘政治
    SECTOR = "sector"                   # 行业事件
    PRICE_ANOMALY = "price_anomaly"     # 价格异常（检测到的）
    VOLUME_ANOMALY = "volume_anomaly"   # 成交量异常
    OTHER = "other"                     # 其他


class EventImpact(enum.Enum):
    """事件影响方向"""
    POSITIVE = "positive"       # 利好
    NEGATIVE = "negative"       # 利空
    NEUTRAL = "neutral"         # 中性
    MIXED = "mixed"             # 混合
    UNKNOWN = "unknown"         # 未知


class EventContext(Base):
    """
    事件上下文表

    记录持仓期间发生的重大市场事件，包括财报、宏观数据、
    政策变动等，以及事件对股价和持仓的影响。
    用于事件驱动的交易复盘和归因分析。
    """
    __tablename__ = 'event_context'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 关联信息 ====================
    position_id = Column(
        Integer,
        ForeignKey('positions.id'),
        nullable=True,  # 可以是独立事件记录
        index=True,
        comment="关联的持仓ID"
    )

    # ==================== 事件基本信息 ====================
    symbol = Column(String(50), nullable=False, index=True, comment="股票代码")
    underlying_symbol = Column(String(50), index=True, comment="期权底层标的")

    event_type = Column(
        String(30),
        nullable=False,
        index=True,
        comment="事件类型"
    )
    event_date = Column(Date, nullable=False, index=True, comment="事件日期")
    event_time = Column(DateTime, comment="事件时间（精确到分钟）")

    event_title = Column(String(500), nullable=False, comment="事件标题")
    event_description = Column(Text, comment="事件详细描述")

    # ==================== 事件影响评估 ====================
    event_impact = Column(
        String(20),
        default='unknown',
        comment="事件影响方向: positive/negative/neutral/mixed"
    )
    event_importance = Column(
        Integer,
        default=5,
        comment="事件重要性(1-10): 10=最重要"
    )

    # 是否为惊喜/超预期
    is_surprise = Column(Boolean, default=False, comment="是否超出预期")
    surprise_direction = Column(String(20), comment="超预期方向: beat/miss")
    surprise_magnitude = Column(Numeric(10, 4), comment="超预期幅度(%)")

    # ==================== 市场反应指标 ====================
    # 事件日价格变动
    price_before = Column(Numeric(15, 4), comment="事件前收盘价")
    price_after = Column(Numeric(15, 4), comment="事件后收盘价")
    price_change = Column(Numeric(15, 4), comment="价格变动")
    price_change_pct = Column(Numeric(10, 4), comment="价格变动百分比")

    # 事件日盘中极值
    event_day_high = Column(Numeric(15, 4), comment="事件日最高价")
    event_day_low = Column(Numeric(15, 4), comment="事件日最低价")
    event_day_range_pct = Column(Numeric(10, 4), comment="事件日振幅(%)")

    # 成交量异常
    volume_on_event = Column(Numeric(20, 0), comment="事件日成交量")
    volume_avg_20d = Column(Numeric(20, 0), comment="20日均量")
    volume_spike = Column(Numeric(10, 2), comment="成交量倍数(相对20日均量)")

    # 波动率变化
    volatility_before = Column(Numeric(10, 4), comment="事件前波动率")
    volatility_after = Column(Numeric(10, 4), comment="事件后波动率")
    volatility_spike = Column(Numeric(10, 4), comment="波动率变化幅度")

    # 跳空幅度
    gap_pct = Column(Numeric(10, 4), comment="跳空百分比")

    # ==================== 持仓影响 ====================
    position_pnl_on_event = Column(Numeric(20, 2), comment="事件日持仓盈亏")
    position_pnl_pct_on_event = Column(Numeric(10, 4), comment="事件日盈亏百分比")

    # 事件前后5日累计影响
    pnl_5d_before = Column(Numeric(20, 2), comment="事件前5日累计盈亏")
    pnl_5d_after = Column(Numeric(20, 2), comment="事件后5日累计盈亏")

    # ==================== 数据来源 ====================
    source = Column(String(50), comment="数据来源: polygon/yfinance/manual/detected")
    source_url = Column(String(500), comment="来源链接")
    source_data = Column(JSON, comment="原始数据(JSON)")

    # 置信度（检测事件的可信度）
    confidence = Column(Numeric(5, 2), default=100, comment="置信度(0-100)")

    # ==================== 关联事件 ====================
    # 同一事件可能影响多个持仓，用 event_group_id 关联
    event_group_id = Column(String(50), index=True, comment="事件组ID(关联同一事件)")

    # 关联的市场环境
    market_env_id = Column(
        Integer,
        ForeignKey('market_environment.id'),
        comment="事件日市场环境ID"
    )

    # ==================== 用户标记 ====================
    user_notes = Column(Text, comment="用户备注")
    is_key_event = Column(Boolean, default=False, index=True, comment="用户标记为关键事件")

    # ==================== 时间戳 ====================
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    # ==================== 关系 ====================
    position = relationship(
        "Position",
        foreign_keys=[position_id],
        backref="events"
    )

    market_environment = relationship(
        "MarketEnvironment",
        foreign_keys=[market_env_id],
        backref="events"
    )

    # ==================== 索引 ====================
    __table_args__ = (
        Index('ix_event_symbol_date', 'symbol', 'event_date'),
        Index('ix_event_type_date', 'event_type', 'event_date'),
        Index('ix_event_position_date', 'position_id', 'event_date'),
        Index('ix_event_importance', 'event_importance', 'event_date'),
    )

    def __repr__(self) -> str:
        return (
            f"<EventContext(id={self.id}, symbol='{self.symbol}', "
            f"type={self.event_type}, date={self.event_date}, "
            f"impact={self.event_impact})>"
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'position_id': self.position_id,
            'symbol': self.symbol,
            'underlying_symbol': self.underlying_symbol,
            'event_type': self.event_type,
            'event_date': str(self.event_date) if self.event_date else None,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'event_title': self.event_title,
            'event_description': self.event_description,
            'event_impact': self.event_impact,
            'event_importance': self.event_importance,
            'is_surprise': self.is_surprise,
            'surprise_direction': self.surprise_direction,
            'surprise_magnitude': float(self.surprise_magnitude) if self.surprise_magnitude else None,
            # 价格反应
            'price_before': float(self.price_before) if self.price_before else None,
            'price_after': float(self.price_after) if self.price_after else None,
            'price_change': float(self.price_change) if self.price_change else None,
            'price_change_pct': float(self.price_change_pct) if self.price_change_pct else None,
            'gap_pct': float(self.gap_pct) if self.gap_pct else None,
            # 成交量
            'volume_spike': float(self.volume_spike) if self.volume_spike else None,
            # 持仓影响
            'position_pnl_on_event': float(self.position_pnl_on_event) if self.position_pnl_on_event else None,
            'position_pnl_pct_on_event': float(self.position_pnl_pct_on_event) if self.position_pnl_pct_on_event else None,
            # 元数据
            'source': self.source,
            'confidence': float(self.confidence) if self.confidence else None,
            'is_key_event': self.is_key_event,
            'user_notes': self.user_notes,
        }

    @property
    def impact_emoji(self) -> str:
        """返回影响方向的 emoji"""
        emoji_map = {
            'positive': '🟢',
            'negative': '🔴',
            'neutral': '⚪',
            'mixed': '🟡',
            'unknown': '❓'
        }
        return emoji_map.get(self.event_impact, '❓')

    @property
    def type_emoji(self) -> str:
        """返回事件类型的 emoji"""
        emoji_map = {
            'earnings': '📊',
            'earnings_pre': '📊',
            'earnings_post': '📊',
            'dividend': '💰',
            'split': '✂️',
            'product': '📦',
            'guidance': '🎯',
            'analyst': '📝',
            'insider': '👔',
            'buyback': '🔄',
            'offering': '📈',
            'fda': '💊',
            'contract': '📑',
            'management': '👥',
            'macro': '🌍',
            'fed': '🏛️',
            'cpi': '📈',
            'nfp': '👷',
            'geopolitical': '🌐',
            'sector': '🏭',
            'price_anomaly': '⚡',
            'volume_anomaly': '📢',
            'other': '📌'
        }
        return emoji_map.get(self.event_type, '📌')

    @property
    def summary(self) -> str:
        """生成简短摘要"""
        pct_str = ""
        if self.price_change_pct:
            sign = "+" if self.price_change_pct > 0 else ""
            pct_str = f" ({sign}{self.price_change_pct:.1f}%)"

        return f"{self.type_emoji} {self.event_title}{pct_str}"

    @property
    def is_high_impact(self) -> bool:
        """是否为高影响事件"""
        # 事件重要性>=7 或 价格变动超过5%
        if self.event_importance and self.event_importance >= 7:
            return True
        if self.price_change_pct and abs(self.price_change_pct) >= 5:
            return True
        return False

    @property
    def is_volume_surge(self) -> bool:
        """是否有成交量激增"""
        return self.volume_spike is not None and self.volume_spike >= 2.0

    def calculate_market_reaction(self) -> dict:
        """计算市场反应指标"""
        return {
            'price_move': float(self.price_change_pct) if self.price_change_pct else 0,
            'volume_multiple': float(self.volume_spike) if self.volume_spike else 1,
            'gap': float(self.gap_pct) if self.gap_pct else 0,
            'volatility_change': float(self.volatility_spike) if self.volatility_spike else 0,
            'is_high_impact': self.is_high_impact,
            'is_volume_surge': self.is_volume_surge,
        }
