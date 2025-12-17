"""
Statistics API schemas
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class DailyPnLItem(BaseModel):
    """Daily P&L item"""
    date: date
    pnl: float
    trade_count: int
    cumulative_pnl: float


class WeeklyPnLItem(BaseModel):
    """Weekly P&L item"""
    week_start: date
    week_end: date
    pnl: float
    trade_count: int


class MonthlyPnLItem(BaseModel):
    """Monthly P&L item"""
    year: int
    month: int
    pnl: float
    trade_count: int
    win_rate: float


class StrategyBreakdownItem(BaseModel):
    """Strategy distribution item"""
    strategy: str
    strategy_name: str
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float
    avg_score: Optional[float] = None


class SymbolBreakdownItem(BaseModel):
    """Symbol distribution item"""
    symbol: str
    symbol_name: Optional[str] = None
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float
    avg_holding_days: float


class GradeBreakdownItem(BaseModel):
    """Grade distribution item"""
    grade: str
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float


class DirectionBreakdownItem(BaseModel):
    """Direction distribution item"""
    direction: str
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float


class HoldingPeriodBreakdownItem(BaseModel):
    """Holding period distribution item"""
    period_label: str  # "Same Day", "1-3 Days", "1 Week", etc.
    min_days: int
    max_days: int
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float


class PerformanceMetrics(BaseModel):
    """Overall performance metrics"""
    # Return metrics
    total_pnl: float
    total_pnl_pct: Optional[float] = None

    # Win/Loss metrics
    total_trades: int
    winners: int
    losers: int
    win_rate: float

    # Average metrics
    avg_win: float
    avg_loss: float
    avg_pnl: float

    # Risk metrics
    profit_factor: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Consecutive metrics
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    # Fee impact
    total_fees: float
    fees_pct_of_pnl: Optional[float] = None

    # Holding period
    avg_holding_days: float
    avg_winner_holding_days: Optional[float] = None
    avg_loser_holding_days: Optional[float] = None


class StatisticsSummary(BaseModel):
    """Complete statistics summary"""
    performance: PerformanceMetrics

    # Breakdowns
    by_strategy: List[StrategyBreakdownItem]
    by_symbol: List[SymbolBreakdownItem]
    by_grade: List[GradeBreakdownItem]
    by_direction: List[DirectionBreakdownItem]
    by_holding_period: List[HoldingPeriodBreakdownItem]

    # Time series
    daily_pnl: List[DailyPnLItem]
    monthly_pnl: List[MonthlyPnLItem]


class CalendarHeatmapItem(BaseModel):
    """Calendar heatmap item"""
    date: date
    pnl: float
    trade_count: int
    is_winner: bool


class DrawdownItem(BaseModel):
    """Drawdown period item"""
    start_date: date
    end_date: Optional[date] = None
    peak_value: float
    trough_value: float
    drawdown: float
    drawdown_pct: float
    recovery_date: Optional[date] = None
    duration_days: int


class RiskMetrics(BaseModel):
    """Comprehensive risk metrics"""
    # Drawdown metrics
    max_drawdown: float
    max_drawdown_pct: Optional[float] = None
    avg_drawdown: Optional[float] = None
    max_drawdown_duration_days: Optional[int] = None
    current_drawdown: Optional[float] = None

    # Risk-adjusted returns
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None

    # Value at Risk (simplified)
    var_95: Optional[float] = None  # 95% VaR
    expected_shortfall: Optional[float] = None  # CVaR

    # Other metrics
    profit_factor: Optional[float] = None
    payoff_ratio: Optional[float] = None  # avg_win / abs(avg_loss)
    expectancy: Optional[float] = None  # (win_rate * avg_win) - (loss_rate * avg_loss)

    # Volatility
    daily_volatility: Optional[float] = None
    annualized_volatility: Optional[float] = None


class EquityCurvePoint(BaseModel):
    """Equity curve data point"""
    date: date
    cumulative_pnl: float
    drawdown: float
    drawdown_pct: Optional[float] = None


# ============================================================
# Advanced Visualization Schemas
# ============================================================


class EquityDrawdownItem(BaseModel):
    """Equity and drawdown data point for combo chart"""
    date: date
    cumulative_pnl: float
    drawdown: float
    drawdown_pct: Optional[float] = None
    peak: float


class PnLDistributionBin(BaseModel):
    """P&L distribution histogram bin"""
    min_value: float
    max_value: float
    count: int
    is_profit: bool


class RollingMetricsItem(BaseModel):
    """Rolling metrics data point"""
    trade_index: int
    close_date: date
    rolling_win_rate: float
    rolling_avg_pnl: float
    cumulative_pnl: float


class DurationPnLItem(BaseModel):
    """Duration vs P&L scatter plot data point"""
    position_id: int
    holding_days: float
    pnl: float
    pnl_pct: Optional[float] = None
    symbol: str
    direction: str
    is_winner: bool


class SymbolRiskItem(BaseModel):
    """Symbol risk quadrant data point"""
    symbol: str
    avg_win: float
    avg_loss: float
    trade_count: int
    win_rate: float
    total_pnl: float
    risk_reward_ratio: Optional[float] = None


class HourlyPerformanceItem(BaseModel):
    """Hourly performance data point"""
    hour: int
    trade_count: int
    win_rate: float
    total_pnl: float
    avg_pnl: float


class TradingHeatmapCell(BaseModel):
    """Trading heatmap cell (weekday x hour)"""
    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str
    hour: int
    trade_count: int
    win_rate: float
    avg_pnl: float
    total_pnl: float


class AssetTypeBreakdownItem(BaseModel):
    """Asset type breakdown data point"""
    asset_type: str  # "stock", "option"
    count: int
    total_pnl: float
    win_rate: float
    avg_pnl: float
    avg_holding_days: float
