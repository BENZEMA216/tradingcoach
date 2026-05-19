"""
市场快照模型

input: SQLAlchemy Base
output: MarketSnapshot 模型
pos: 数据层 - 缓存每日大盘指标（VIX/SPY/QQQ + 行情状态），供 QualityScorer
     的市场环境维度使用。原本是 scripts/migrate_add_score_fields.py 临时
     建出来的，没纳入 ORM 导致 create_all 不会创建，scorer 每次都报
     "no such table: market_snapshots"。
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float, Index, Text, Boolean,
    UniqueConstraint,
)

from src.models.base import Base


class MarketSnapshot(Base):
    """每日市场快照（VIX + SPY + QQQ + 板块表现 + 特殊日期）"""

    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)

    # VIX
    vix_close = Column(Float)
    vix_ma5 = Column(Float)
    vix_ma20 = Column(Float)

    # SPY
    spy_close = Column(Float)
    spy_ma5 = Column(Float)
    spy_ma20 = Column(Float)
    spy_ma50 = Column(Float)
    spy_rsi_14 = Column(Float)
    spy_change_pct = Column(Float)

    # QQQ
    qqq_close = Column(Float)
    qqq_change_pct = Column(Float)

    # 市场状态
    market_trend = Column(String(20))  # bullish/bearish/neutral
    volatility_regime = Column(String(20))  # low/medium/high/extreme

    # 板块表现 (JSON string)
    sector_performance = Column(Text)

    # 特殊日期标记
    is_fomc_day = Column(Boolean, default=False)
    is_opex_day = Column(Boolean, default=False)
    is_earnings_season = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("date", name="uq_market_snapshots_date"),
        Index("idx_market_snapshots_date", "date"),
    )
