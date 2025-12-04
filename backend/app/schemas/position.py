"""
Position API schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime, date
from enum import Enum


class PositionStatusEnum(str, Enum):
    """Position status enum"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


class DirectionEnum(str, Enum):
    """Position direction enum"""
    LONG = "long"
    SHORT = "short"


class PositionBase(BaseModel):
    """Base position fields"""
    symbol: str
    symbol_name: Optional[str] = None
    direction: DirectionEnum
    status: PositionStatusEnum


class PositionListItem(BaseModel):
    """Position item for list view"""
    id: int
    symbol: str
    symbol_name: Optional[str] = None
    direction: str
    status: str

    # Time info
    open_date: date
    close_date: Optional[date] = None
    holding_period_days: Optional[int] = None

    # Price and quantity
    open_price: float
    close_price: Optional[float] = None
    quantity: int

    # P&L
    net_pnl: Optional[float] = None
    net_pnl_pct: Optional[float] = None

    # Quality score
    overall_score: Optional[float] = None
    score_grade: Optional[str] = None

    # Strategy
    strategy_type: Optional[str] = None

    # Review status
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PositionScoreDetail(BaseModel):
    """Position score breakdown"""
    entry_quality_score: Optional[float] = None
    exit_quality_score: Optional[float] = None
    trend_quality_score: Optional[float] = None
    risk_mgmt_score: Optional[float] = None
    overall_score: Optional[float] = None
    score_grade: Optional[str] = None


class PositionRiskMetrics(BaseModel):
    """Position risk metrics"""
    mae: Optional[float] = None
    mae_pct: Optional[float] = None
    mae_time: Optional[datetime] = None
    mfe: Optional[float] = None
    mfe_pct: Optional[float] = None
    mfe_time: Optional[datetime] = None
    risk_reward_ratio: Optional[float] = None


class PositionDetail(BaseModel):
    """Full position detail"""
    id: int
    symbol: str
    symbol_name: Optional[str] = None
    direction: str
    status: str

    # Time info
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    open_date: date
    close_date: Optional[date] = None
    holding_period_days: Optional[int] = None
    holding_period_hours: Optional[float] = None

    # Price and quantity
    open_price: float
    close_price: Optional[float] = None
    quantity: int

    # P&L
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    total_fees: Optional[float] = None
    open_fee: Optional[float] = None
    close_fee: Optional[float] = None
    net_pnl: Optional[float] = None
    net_pnl_pct: Optional[float] = None

    # Market info
    market: Optional[str] = None
    currency: Optional[str] = None
    is_option: bool = False
    underlying_symbol: Optional[str] = None

    # Quality scores
    scores: PositionScoreDetail

    # Risk metrics
    risk_metrics: PositionRiskMetrics

    # Strategy classification
    strategy_type: Optional[str] = None
    strategy_confidence: Optional[float] = None

    # Technical indicators snapshot
    entry_indicators: Optional[dict] = None
    exit_indicators: Optional[dict] = None

    # Post-exit performance
    post_exit_5d_pct: Optional[float] = None
    post_exit_10d_pct: Optional[float] = None
    post_exit_20d_pct: Optional[float] = None

    # Review fields
    review_notes: Optional[dict] = None
    emotion_tag: Optional[str] = None
    discipline_score: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    # Analysis notes
    analysis_notes: Optional[dict] = None

    # Associated trades
    trade_ids: List[int] = []

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PositionFilterParams(BaseModel):
    """Position filter parameters"""
    symbol: Optional[str] = None
    direction: Optional[DirectionEnum] = None
    status: Optional[PositionStatusEnum] = None

    # Date range
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    # P&L filter
    pnl_min: Optional[float] = None
    pnl_max: Optional[float] = None
    is_winner: Optional[bool] = None

    # Score filter
    score_min: Optional[float] = None
    score_max: Optional[float] = None
    score_grade: Optional[str] = None

    # Strategy filter
    strategy_type: Optional[str] = None

    # Review filter
    is_reviewed: Optional[bool] = None

    # Sort
    sort_by: str = Field(default="close_date", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class PositionReviewUpdate(BaseModel):
    """Position review update payload"""
    review_notes: Optional[dict] = None
    emotion_tag: Optional[str] = Field(
        default=None,
        description="Emotion tag: greedy, fearful, calm, impulsive"
    )
    discipline_score: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Discipline score 1-5"
    )


class PositionSummary(BaseModel):
    """Position summary statistics"""
    total_positions: int
    closed_positions: int
    open_positions: int

    # P&L summary
    total_pnl: float
    total_realized_pnl: float
    total_fees: float

    # Win/loss stats
    winners: int
    losers: int
    win_rate: float

    # Average metrics
    avg_pnl: float
    avg_winner: float
    avg_loser: float
    profit_factor: Optional[float] = None

    # Score metrics
    avg_score: Optional[float] = None

    # Holding period
    avg_holding_days: float
