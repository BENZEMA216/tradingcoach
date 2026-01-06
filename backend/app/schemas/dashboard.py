"""
Dashboard API schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class DashboardKPIs(BaseModel):
    """KPI metrics for dashboard"""
    total_pnl: float
    win_rate: float
    avg_score: float
    trade_count: int
    total_fees: float = 0.0
    avg_holding_days: float = 0.0

    class Config:
        from_attributes = True


class EquityCurvePoint(BaseModel):
    """Single point on equity curve"""
    date: date
    cumulative_pnl: float
    trade_count: int


class EquityCurveResponse(BaseModel):
    """Equity curve data"""
    data: List[EquityCurvePoint]
    total_pnl: float
    max_drawdown: Optional[float] = None
    max_drawdown_pct: Optional[float] = None


class RecentTradeItem(BaseModel):
    """Recent trade item"""
    id: int
    symbol: str
    close_date: Optional[date]
    net_pnl: float
    net_pnl_pct: Optional[float]
    grade: Optional[str]
    direction: str


class NeedsReviewItem(BaseModel):
    """Trade needing review"""
    id: int
    symbol: str
    close_date: Optional[date]
    net_pnl: float
    grade: Optional[str]
    reason: str


class StrategyBreakdownItem(BaseModel):
    """Strategy distribution item"""
    strategy: str
    strategy_name: str
    count: int
    total_pnl: float
    win_rate: float


class DailyPnLItem(BaseModel):
    """Daily P&L item"""
    date: date
    pnl: float
    trade_count: int
