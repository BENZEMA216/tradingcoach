"""
Pydantic schemas for API
"""

from .common import (
    PaginatedResponse,
    PaginationParams,
    DateRangeParams,
    MessageResponse,
)

from .dashboard import (
    DashboardKPIs,
    EquityCurvePoint,
    EquityCurveResponse,
    RecentTradeItem,
    NeedsReviewItem,
    StrategyBreakdownItem,
    DailyPnLItem,
)

from .position import (
    PositionStatusEnum,
    DirectionEnum,
    PositionBase,
    PositionListItem,
    PositionScoreDetail,
    PositionRiskMetrics,
    PositionDetail,
    PositionFilterParams,
    PositionReviewUpdate,
    PositionSummary,
)

from .trade import (
    TradeDirectionEnum,
    TradeStatusEnum,
    MarketTypeEnum,
    TradeListItem,
    TradeDetail,
    TradeFilterParams,
    TradeSummary,
)

from .market_data import (
    OHLCVData,
    TechnicalIndicators,
    MarketDataPoint,
    MarketDataResponse,
    MarketDataQueryParams,
    CandlestickChartData,
    SymbolInfo,
)

from .statistics import (
    DailyPnLItem as StatsDailyPnLItem,
    WeeklyPnLItem,
    MonthlyPnLItem,
    StrategyBreakdownItem as StatsStrategyBreakdownItem,
    SymbolBreakdownItem,
    GradeBreakdownItem,
    DirectionBreakdownItem,
    HoldingPeriodBreakdownItem,
    PerformanceMetrics,
    StatisticsSummary,
    CalendarHeatmapItem,
    DrawdownItem,
    RiskMetrics,
    EquityCurvePoint as StatsEquityCurvePoint,
    # Advanced Visualization
    EquityDrawdownItem,
    PnLDistributionBin,
    RollingMetricsItem,
    DurationPnLItem,
    SymbolRiskItem,
    HourlyPerformanceItem,
    TradingHeatmapCell,
    AssetTypeBreakdownItem,
)

from .insights import (
    InsightType,
    InsightCategory,
    TradingInsight,
    InsightsResponse,
)

__all__ = [
    # Common
    "PaginatedResponse",
    "PaginationParams",
    "DateRangeParams",
    "MessageResponse",
    # Dashboard
    "DashboardKPIs",
    "EquityCurvePoint",
    "EquityCurveResponse",
    "RecentTradeItem",
    "NeedsReviewItem",
    "StrategyBreakdownItem",
    "DailyPnLItem",
    # Position
    "PositionStatusEnum",
    "DirectionEnum",
    "PositionBase",
    "PositionListItem",
    "PositionScoreDetail",
    "PositionRiskMetrics",
    "PositionDetail",
    "PositionFilterParams",
    "PositionReviewUpdate",
    "PositionSummary",
    # Trade
    "TradeDirectionEnum",
    "TradeStatusEnum",
    "MarketTypeEnum",
    "TradeListItem",
    "TradeDetail",
    "TradeFilterParams",
    "TradeSummary",
    # Market Data
    "OHLCVData",
    "TechnicalIndicators",
    "MarketDataPoint",
    "MarketDataResponse",
    "MarketDataQueryParams",
    "CandlestickChartData",
    "SymbolInfo",
    # Statistics
    "StatsDailyPnLItem",
    "WeeklyPnLItem",
    "MonthlyPnLItem",
    "StatsStrategyBreakdownItem",
    "SymbolBreakdownItem",
    "GradeBreakdownItem",
    "DirectionBreakdownItem",
    "HoldingPeriodBreakdownItem",
    "PerformanceMetrics",
    "StatisticsSummary",
    "CalendarHeatmapItem",
    "DrawdownItem",
    "RiskMetrics",
    "StatsEquityCurvePoint",
    # Advanced Visualization
    "EquityDrawdownItem",
    "PnLDistributionBin",
    "RollingMetricsItem",
    "DurationPnLItem",
    "SymbolRiskItem",
    "HourlyPerformanceItem",
    "TradingHeatmapCell",
    "AssetTypeBreakdownItem",
    # Insights
    "InsightType",
    "InsightCategory",
    "TradingInsight",
    "InsightsResponse",
]
