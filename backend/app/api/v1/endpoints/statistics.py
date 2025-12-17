"""
Statistics API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from collections import defaultdict

from ....database import get_db, Position, PositionStatus
from ....schemas import (
    PerformanceMetrics,
    SymbolBreakdownItem,
    GradeBreakdownItem,
    DirectionBreakdownItem,
    HoldingPeriodBreakdownItem,
    CalendarHeatmapItem,
    WeeklyPnLItem,
    MonthlyPnLItem,
    RiskMetrics,
    DrawdownItem,
    TradingInsight,
    InsightsResponse,
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
from ....services.insight_engine import InsightEngine

router = APIRouter()

# Currency exchange rates (to USD)
EXCHANGE_RATES = {
    "USD": 1.0,
    "HKD": 0.128,  # 1 HKD ≈ 0.128 USD (1 USD ≈ 7.8 HKD)
    "CNY": 0.14,   # 1 CNY ≈ 0.14 USD
}


def convert_to_usd(amount: float, currency: str) -> float:
    """Convert amount to USD based on currency."""
    if amount is None:
        return 0.0
    rate = EXCHANGE_RATES.get(currency, 1.0)
    return float(amount) * rate


def get_pnl_in_usd(position) -> float:
    """Get position PnL converted to USD."""
    pnl = float(position.net_pnl or 0)
    currency = position.currency or "USD"
    return convert_to_usd(pnl, currency)


@router.get("/date-range")
async def get_data_date_range(
    db: Session = Depends(get_db),
):
    """
    Get the date range of available trading data.
    Returns the earliest and latest close dates for closed positions.
    """
    from sqlalchemy import func

    result = db.query(
        func.min(Position.close_date).label("min_date"),
        func.max(Position.close_date).label("max_date"),
        func.count(Position.id).label("total_count")
    ).filter(Position.status == PositionStatus.CLOSED).first()

    return {
        "min_date": result.min_date.isoformat() if result.min_date else None,
        "max_date": result.max_date.isoformat() if result.max_date else None,
        "total_positions": result.total_count or 0,
    }


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> PerformanceMetrics:
    """
    Get comprehensive performance metrics.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.order_by(Position.close_date).all()

    if not positions:
        return PerformanceMetrics(
            total_pnl=0.0,
            total_trades=0,
            winners=0,
            losers=0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            avg_pnl=0.0,
            total_fees=0.0,
            avg_holding_days=0.0,
        )

    # Basic metrics (with currency conversion to USD)
    total_pnl = sum(get_pnl_in_usd(p) for p in positions)
    total_fees = sum(convert_to_usd(float(p.total_fees or 0), p.currency or "USD") for p in positions)
    total_trades = len(positions)

    # Winners and losers (based on original currency PnL sign)
    winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
    losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

    win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0.0

    # Average metrics (converted to USD)
    avg_win = sum(get_pnl_in_usd(p) for p in winners) / len(winners) if winners else 0.0
    avg_loss = sum(get_pnl_in_usd(p) for p in losers) / len(losers) if losers else 0.0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0.0

    # Profit factor (converted to USD)
    gross_profit = sum(get_pnl_in_usd(p) for p in winners)
    gross_loss = abs(sum(get_pnl_in_usd(p) for p in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    # Max drawdown (using USD-converted PnL)
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for p in positions:
        cumulative += get_pnl_in_usd(p)
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else None

    # Consecutive wins/losses
    max_consecutive_wins = 0
    max_consecutive_losses = 0
    current_wins = 0
    current_losses = 0

    for p in positions:
        if p.net_pnl and float(p.net_pnl) > 0:
            current_wins += 1
            current_losses = 0
            max_consecutive_wins = max(max_consecutive_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_consecutive_losses = max(max_consecutive_losses, current_losses)

    # Holding period
    with_holding = [p for p in positions if p.holding_period_days is not None]
    avg_holding_days = (
        sum(p.holding_period_days for p in with_holding) / len(with_holding)
        if with_holding
        else 0.0
    )

    winners_with_holding = [p for p in winners if p.holding_period_days is not None]
    losers_with_holding = [p for p in losers if p.holding_period_days is not None]

    avg_winner_holding = (
        sum(p.holding_period_days for p in winners_with_holding) / len(winners_with_holding)
        if winners_with_holding
        else None
    )
    avg_loser_holding = (
        sum(p.holding_period_days for p in losers_with_holding) / len(losers_with_holding)
        if losers_with_holding
        else None
    )

    # Fees percentage
    fees_pct = (total_fees / abs(total_pnl) * 100) if total_pnl != 0 else None

    return PerformanceMetrics(
        total_pnl=round(total_pnl, 2),
        total_trades=total_trades,
        winners=len(winners),
        losers=len(losers),
        win_rate=round(win_rate, 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        avg_pnl=round(avg_pnl, 2),
        profit_factor=round(profit_factor, 2) if profit_factor else None,
        max_drawdown=round(max_drawdown, 2) if max_drawdown > 0 else None,
        max_drawdown_pct=round(max_drawdown_pct, 2) if max_drawdown_pct else None,
        max_consecutive_wins=max_consecutive_wins,
        max_consecutive_losses=max_consecutive_losses,
        total_fees=round(total_fees, 2),
        fees_pct_of_pnl=round(fees_pct, 2) if fees_pct else None,
        avg_holding_days=round(avg_holding_days, 1),
        avg_winner_holding_days=round(avg_winner_holding, 1) if avg_winner_holding else None,
        avg_loser_holding_days=round(avg_loser_holding, 1) if avg_loser_holding else None,
    )


@router.get("/by-symbol", response_model=list[SymbolBreakdownItem])
async def get_symbol_breakdown(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    limit: int = Query(20, ge=1, le=100, description="Number of symbols"),
    db: Session = Depends(get_db),
) -> list[SymbolBreakdownItem]:
    """
    Get P&L breakdown by symbol.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by symbol
    symbol_stats = defaultdict(lambda: {
        "name": None,
        "count": 0,
        "total_pnl": 0.0,
        "winners": 0,
        "total_holding_days": 0,
        "holding_count": 0,
    })

    for p in positions:
        stats = symbol_stats[p.symbol]
        if p.symbol_name and not stats["name"]:
            stats["name"] = p.symbol_name
        stats["count"] += 1
        stats["total_pnl"] += get_pnl_in_usd(p)  # Convert to USD
        if p.net_pnl and float(p.net_pnl) > 0:
            stats["winners"] += 1
        if p.holding_period_days:
            stats["total_holding_days"] += p.holding_period_days
            stats["holding_count"] += 1

    # Convert to response items
    items = []
    for symbol, stats in symbol_stats.items():
        win_rate = stats["winners"] / stats["count"] * 100 if stats["count"] > 0 else 0.0
        avg_pnl = stats["total_pnl"] / stats["count"] if stats["count"] > 0 else 0.0
        avg_holding = (
            stats["total_holding_days"] / stats["holding_count"]
            if stats["holding_count"] > 0
            else 0.0
        )

        items.append(
            SymbolBreakdownItem(
                symbol=symbol,
                symbol_name=stats["name"],
                count=stats["count"],
                total_pnl=round(stats["total_pnl"], 2),
                win_rate=round(win_rate, 2),
                avg_pnl=round(avg_pnl, 2),
                avg_holding_days=round(avg_holding, 1),
            )
        )

    # Sort by trade count descending
    items.sort(key=lambda x: x.count, reverse=True)
    return items[:limit]


@router.get("/by-grade", response_model=list[GradeBreakdownItem])
async def get_grade_breakdown(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[GradeBreakdownItem]:
    """
    Get P&L breakdown by score grade.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by grade
    grade_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0, "winners": 0})

    for p in positions:
        grade = p.score_grade or "N/A"
        grade_stats[grade]["count"] += 1
        grade_stats[grade]["total_pnl"] += get_pnl_in_usd(p)  # Convert to USD
        if p.net_pnl and float(p.net_pnl) > 0:
            grade_stats[grade]["winners"] += 1

    # Convert to response items with proper grade order
    grade_order = ["A", "B", "C", "D", "F", "N/A"]
    items = []

    for grade in grade_order:
        if grade in grade_stats:
            stats = grade_stats[grade]
            win_rate = stats["winners"] / stats["count"] * 100 if stats["count"] > 0 else 0.0
            avg_pnl = stats["total_pnl"] / stats["count"] if stats["count"] > 0 else 0.0

            items.append(
                GradeBreakdownItem(
                    grade=grade,
                    count=stats["count"],
                    total_pnl=round(stats["total_pnl"], 2),
                    win_rate=round(win_rate, 2),
                    avg_pnl=round(avg_pnl, 2),
                )
            )

    return items


@router.get("/by-direction", response_model=list[DirectionBreakdownItem])
async def get_direction_breakdown(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[DirectionBreakdownItem]:
    """
    Get P&L breakdown by direction (long/short).
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by direction
    direction_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0, "winners": 0})

    for p in positions:
        direction = p.direction or "unknown"
        direction_stats[direction]["count"] += 1
        direction_stats[direction]["total_pnl"] += get_pnl_in_usd(p)  # Convert to USD
        if p.net_pnl and float(p.net_pnl) > 0:
            direction_stats[direction]["winners"] += 1

    # Convert to response items
    items = []
    for direction, stats in direction_stats.items():
        win_rate = stats["winners"] / stats["count"] * 100 if stats["count"] > 0 else 0.0
        avg_pnl = stats["total_pnl"] / stats["count"] if stats["count"] > 0 else 0.0

        items.append(
            DirectionBreakdownItem(
                direction=direction,
                count=stats["count"],
                total_pnl=round(stats["total_pnl"], 2),
                win_rate=round(win_rate, 2),
                avg_pnl=round(avg_pnl, 2),
            )
        )

    return items


@router.get("/by-holding-period", response_model=list[HoldingPeriodBreakdownItem])
async def get_holding_period_breakdown(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[HoldingPeriodBreakdownItem]:
    """
    Get P&L breakdown by holding period.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Define holding period buckets
    buckets = [
        ("Same Day", 0, 0),
        ("1-3 Days", 1, 3),
        ("4-7 Days", 4, 7),
        ("1-2 Weeks", 8, 14),
        ("2-4 Weeks", 15, 28),
        ("1-3 Months", 29, 90),
        ("3+ Months", 91, 9999),
    ]

    # Group by bucket
    bucket_stats = {
        label: {"count": 0, "total_pnl": 0.0, "winners": 0}
        for label, _, _ in buckets
    }

    for p in positions:
        days = p.holding_period_days or 0
        for label, min_d, max_d in buckets:
            if min_d <= days <= max_d:
                bucket_stats[label]["count"] += 1
                bucket_stats[label]["total_pnl"] += get_pnl_in_usd(p)  # Convert to USD
                if p.net_pnl and float(p.net_pnl) > 0:
                    bucket_stats[label]["winners"] += 1
                break

    # Convert to response items
    items = []
    for label, min_d, max_d in buckets:
        stats = bucket_stats[label]
        if stats["count"] > 0:
            win_rate = stats["winners"] / stats["count"] * 100
            avg_pnl = stats["total_pnl"] / stats["count"]

            items.append(
                HoldingPeriodBreakdownItem(
                    period_label=label,
                    min_days=min_d,
                    max_days=max_d,
                    count=stats["count"],
                    total_pnl=round(stats["total_pnl"], 2),
                    win_rate=round(win_rate, 2),
                    avg_pnl=round(avg_pnl, 2),
                )
            )

    return items


@router.get("/calendar-heatmap", response_model=list[CalendarHeatmapItem])
async def get_calendar_heatmap(
    year: int = Query(..., description="Year to display"),
    db: Session = Depends(get_db),
) -> list[CalendarHeatmapItem]:
    """
    Get calendar heatmap data for a specific year.
    """
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    positions = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .filter(Position.close_date >= start_date)
        .filter(Position.close_date <= end_date)
        .all()
    )

    # Group by date
    date_stats = defaultdict(lambda: {"pnl": 0.0, "count": 0})

    for p in positions:
        d = p.close_date
        date_stats[d]["pnl"] += get_pnl_in_usd(p)  # Convert to USD
        date_stats[d]["count"] += 1

    return [
        CalendarHeatmapItem(
            date=d,
            pnl=round(stats["pnl"], 2),
            trade_count=stats["count"],
            is_winner=stats["pnl"] > 0,
        )
        for d, stats in sorted(date_stats.items())
    ]


@router.get("/monthly-pnl", response_model=list[MonthlyPnLItem])
async def get_monthly_pnl(
    year: Optional[int] = Query(None, description="Filter by year"),
    db: Session = Depends(get_db),
) -> list[MonthlyPnLItem]:
    """
    Get monthly P&L summary.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if year:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        query = query.filter(Position.close_date >= start_date)
        query = query.filter(Position.close_date <= end_date)

    positions = query.all()

    # Group by year-month
    month_stats = defaultdict(lambda: {"pnl": 0.0, "count": 0, "winners": 0})

    for p in positions:
        if p.close_date:
            key = (p.close_date.year, p.close_date.month)
            month_stats[key]["pnl"] += get_pnl_in_usd(p)  # Convert to USD
            month_stats[key]["count"] += 1
            if p.net_pnl and float(p.net_pnl) > 0:
                month_stats[key]["winners"] += 1

    # Convert to response items
    items = []
    for (y, m), stats in sorted(month_stats.items()):
        win_rate = stats["winners"] / stats["count"] * 100 if stats["count"] > 0 else 0.0

        items.append(
            MonthlyPnLItem(
                year=y,
                month=m,
                pnl=round(stats["pnl"], 2),
                trade_count=stats["count"],
                win_rate=round(win_rate, 2),
            )
        )

    return items


@router.get("/risk-metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    risk_free_rate: float = Query(0.05, description="Annual risk-free rate (default 5%)"),
    db: Session = Depends(get_db),
) -> RiskMetrics:
    """
    Get comprehensive risk metrics including Sharpe ratio, Sortino ratio, and drawdown analysis.
    """
    import math

    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.order_by(Position.close_date).all()

    if not positions:
        return RiskMetrics(
            max_drawdown=0.0,
            max_drawdown_pct=None,
            sharpe_ratio=None,
            sortino_ratio=None,
        )

    # Calculate daily returns (converted to USD)
    daily_pnl = defaultdict(float)
    for p in positions:
        if p.close_date and p.net_pnl:
            daily_pnl[p.close_date] += get_pnl_in_usd(p)

    returns = list(daily_pnl.values())
    dates = sorted(daily_pnl.keys())

    # Basic metrics
    total_pnl = sum(returns)
    avg_return = sum(returns) / len(returns) if returns else 0

    # Winners and losers
    winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
    losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]
    win_rate = len(winners) / len(positions) if positions else 0

    avg_win = sum(get_pnl_in_usd(p) for p in winners) / len(winners) if winners else 0
    avg_loss = sum(get_pnl_in_usd(p) for p in losers) / len(losers) if losers else 0

    # Profit factor (converted to USD)
    gross_profit = sum(get_pnl_in_usd(p) for p in winners)
    gross_loss = abs(sum(get_pnl_in_usd(p) for p in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    # Payoff ratio
    payoff_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else None

    # Expectancy
    loss_rate = 1 - win_rate
    expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)

    # Volatility
    if len(returns) > 1:
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        daily_volatility = math.sqrt(variance)
        annualized_volatility = daily_volatility * math.sqrt(252)
    else:
        daily_volatility = None
        annualized_volatility = None

    # Sharpe Ratio (annualized)
    daily_risk_free = risk_free_rate / 252
    if daily_volatility and daily_volatility > 0:
        sharpe_ratio = ((avg_return - daily_risk_free) / daily_volatility) * math.sqrt(252)
    else:
        sharpe_ratio = None

    # Sortino Ratio (only considers downside volatility)
    negative_returns = [r for r in returns if r < 0]
    if len(negative_returns) > 1:
        downside_variance = sum(r ** 2 for r in negative_returns) / (len(negative_returns) - 1)
        downside_volatility = math.sqrt(downside_variance)
        if downside_volatility > 0:
            sortino_ratio = ((avg_return - daily_risk_free) / downside_volatility) * math.sqrt(252)
        else:
            sortino_ratio = None
    else:
        sortino_ratio = None

    # Drawdown analysis
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0
    drawdowns = []
    dd_start = None
    current_dd = 0.0

    for d in dates:
        cumulative += daily_pnl[d]
        if cumulative > peak:
            peak = cumulative
            if dd_start is not None:
                drawdowns.append(current_dd)
                dd_start = None
        else:
            current_dd = peak - cumulative
            if current_dd > 0 and dd_start is None:
                dd_start = d
            if current_dd > max_drawdown:
                max_drawdown = current_dd

    # Current drawdown
    current_drawdown = current_dd if cumulative < peak else 0.0

    # Max drawdown percentage
    max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else None

    # Average drawdown
    all_drawdowns = drawdowns + [current_dd] if current_dd > 0 else drawdowns
    avg_drawdown = sum(all_drawdowns) / len(all_drawdowns) if all_drawdowns else None

    # Calmar Ratio
    if len(dates) >= 2:
        trading_days = (dates[-1] - dates[0]).days
        if trading_days > 0 and max_drawdown > 0:
            annualized_return = (total_pnl / trading_days) * 365
            calmar_ratio = annualized_return / max_drawdown
        else:
            calmar_ratio = None
    else:
        calmar_ratio = None

    # Value at Risk (95%)
    if len(returns) >= 20:
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = abs(sorted_returns[var_index])
        tail_returns = sorted_returns[:var_index + 1]
        expected_shortfall = abs(sum(tail_returns) / len(tail_returns)) if tail_returns else None
    else:
        var_95 = None
        expected_shortfall = None

    return RiskMetrics(
        max_drawdown=round(max_drawdown, 2),
        max_drawdown_pct=round(max_drawdown_pct, 2) if max_drawdown_pct else None,
        avg_drawdown=round(avg_drawdown, 2) if avg_drawdown else None,
        current_drawdown=round(current_drawdown, 2) if current_drawdown > 0 else None,
        sharpe_ratio=round(sharpe_ratio, 2) if sharpe_ratio else None,
        sortino_ratio=round(sortino_ratio, 2) if sortino_ratio else None,
        calmar_ratio=round(calmar_ratio, 2) if calmar_ratio else None,
        var_95=round(var_95, 2) if var_95 else None,
        expected_shortfall=round(expected_shortfall, 2) if expected_shortfall else None,
        profit_factor=round(profit_factor, 2) if profit_factor else None,
        payoff_ratio=round(payoff_ratio, 2) if payoff_ratio else None,
        expectancy=round(expectancy, 2),
        daily_volatility=round(daily_volatility, 2) if daily_volatility else None,
        annualized_volatility=round(annualized_volatility, 2) if annualized_volatility else None,
    )


@router.get("/drawdowns", response_model=list[DrawdownItem])
async def get_drawdown_periods(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    min_drawdown: float = Query(0, description="Minimum drawdown to include"),
    db: Session = Depends(get_db),
) -> list[DrawdownItem]:
    """
    Get list of drawdown periods with details.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.order_by(Position.close_date).all()

    if not positions:
        return []

    # Calculate daily P&L
    daily_pnl = defaultdict(float)
    for p in positions:
        if p.close_date and p.net_pnl:
            daily_pnl[p.close_date] += get_pnl_in_usd(p)

    dates = sorted(daily_pnl.keys())
    if not dates:
        return []

    # Track drawdown periods
    drawdown_periods = []
    cumulative = 0.0
    peak = 0.0
    peak_date = dates[0]

    dd_start = None
    dd_trough = 0.0
    dd_trough_date = None

    for d in dates:
        cumulative += daily_pnl[d]

        if cumulative > peak:
            if dd_start is not None and dd_trough > min_drawdown:
                duration = (d - dd_start).days
                drawdown_periods.append(DrawdownItem(
                    start_date=dd_start,
                    end_date=dd_trough_date,
                    peak_value=peak,
                    trough_value=peak - dd_trough,
                    drawdown=round(dd_trough, 2),
                    drawdown_pct=round(dd_trough / peak * 100, 2) if peak > 0 else 0,
                    recovery_date=d,
                    duration_days=duration,
                ))

            peak = cumulative
            peak_date = d
            dd_start = None
            dd_trough = 0.0
        else:
            current_dd = peak - cumulative
            if current_dd > 0:
                if dd_start is None:
                    dd_start = peak_date
                if current_dd > dd_trough:
                    dd_trough = current_dd
                    dd_trough_date = d

    # Add current drawdown if still in one
    if dd_start is not None and dd_trough > min_drawdown:
        duration = (dates[-1] - dd_start).days
        drawdown_periods.append(DrawdownItem(
            start_date=dd_start,
            end_date=dd_trough_date,
            peak_value=peak,
            trough_value=peak - dd_trough,
            drawdown=round(dd_trough, 2),
            drawdown_pct=round(dd_trough / peak * 100, 2) if peak > 0 else 0,
            recovery_date=None,
            duration_days=duration,
        ))

    drawdown_periods.sort(key=lambda x: x.drawdown, reverse=True)
    return drawdown_periods


@router.get("/insights", response_model=list[TradingInsight])
async def get_trading_insights(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of insights"),
    db: Session = Depends(get_db),
) -> list[TradingInsight]:
    """
    Get AI Coach trading insights based on rule-based analysis.

    Returns prioritized insights across multiple dimensions:
    - Time patterns (weekday effect)
    - Holding period analysis
    - Symbol performance
    - Direction effectiveness
    - Risk management
    - Behavior patterns
    - Fee impact
    - Options analysis
    - Performance trends
    """
    engine = InsightEngine(db)
    insights = engine.generate_insights(
        date_start=date_start,
        date_end=date_end,
        limit=limit,
    )
    return insights


# ============================================================
# Advanced Visualization Endpoints
# ============================================================


@router.get("/equity-drawdown", response_model=list[EquityDrawdownItem])
async def get_equity_drawdown(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[EquityDrawdownItem]:
    """
    Get equity curve with drawdown data for combo chart visualization.
    Returns daily cumulative P&L and corresponding drawdown values.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.order_by(Position.close_date).all()

    if not positions:
        return []

    # Aggregate daily P&L
    daily_pnl = defaultdict(float)
    for p in positions:
        if p.close_date and p.net_pnl:
            daily_pnl[p.close_date] += get_pnl_in_usd(p)

    # Calculate cumulative P&L and drawdown
    items = []
    cumulative = 0.0
    peak = 0.0

    for d in sorted(daily_pnl.keys()):
        cumulative += daily_pnl[d]
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        drawdown_pct = (drawdown / peak * 100) if peak > 0 else None

        items.append(EquityDrawdownItem(
            date=d,
            cumulative_pnl=round(cumulative, 2),
            drawdown=round(drawdown, 2),
            drawdown_pct=round(drawdown_pct, 2) if drawdown_pct else None,
            peak=round(peak, 2),
        ))

    return items


@router.get("/pnl-distribution", response_model=list[PnLDistributionBin])
async def get_pnl_distribution(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    bin_count: int = Query(20, ge=5, le=50, description="Number of bins"),
    db: Session = Depends(get_db),
) -> list[PnLDistributionBin]:
    """
    Get P&L distribution for histogram visualization.
    Returns binned P&L values showing the distribution of trade outcomes.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    if not positions:
        return []

    # Get all P&L values
    pnl_values = [get_pnl_in_usd(p) for p in positions if p.net_pnl is not None]

    if not pnl_values:
        return []

    min_pnl = min(pnl_values)
    max_pnl = max(pnl_values)

    # Create bins
    bin_size = (max_pnl - min_pnl) / bin_count if max_pnl != min_pnl else 1
    bins = []

    for i in range(bin_count):
        bin_min = min_pnl + (i * bin_size)
        bin_max = min_pnl + ((i + 1) * bin_size)
        count = sum(1 for v in pnl_values if bin_min <= v < bin_max)

        # Include max value in last bin
        if i == bin_count - 1:
            count = sum(1 for v in pnl_values if bin_min <= v <= bin_max)

        if count > 0:
            bins.append(PnLDistributionBin(
                min_value=round(bin_min, 2),
                max_value=round(bin_max, 2),
                count=count,
                is_profit=(bin_min + bin_max) / 2 > 0,
            ))

    return bins


@router.get("/rolling-metrics", response_model=list[RollingMetricsItem])
async def get_rolling_metrics(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    window: int = Query(20, ge=5, le=100, description="Rolling window size"),
    db: Session = Depends(get_db),
) -> list[RollingMetricsItem]:
    """
    Get rolling metrics (win rate, avg P&L) for trend analysis.
    Shows how trading performance changes over time using a moving window.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.order_by(Position.close_date).all()

    if len(positions) < window:
        return []

    items = []
    cumulative_pnl = 0.0

    for i in range(window - 1, len(positions)):
        window_positions = positions[i - window + 1:i + 1]
        winners = sum(1 for p in window_positions if p.net_pnl and float(p.net_pnl) > 0)
        total_pnl = sum(get_pnl_in_usd(p) for p in window_positions)
        cumulative_pnl += get_pnl_in_usd(positions[i])

        items.append(RollingMetricsItem(
            trade_index=i + 1,
            close_date=positions[i].close_date,
            rolling_win_rate=round(winners / window * 100, 2),
            rolling_avg_pnl=round(total_pnl / window, 2),
            cumulative_pnl=round(cumulative_pnl, 2),
        ))

    return items


@router.get("/duration-pnl", response_model=list[DurationPnLItem])
async def get_duration_pnl(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[DurationPnLItem]:
    """
    Get holding duration vs P&L data for scatter plot visualization.
    Helps identify if longer holding periods correlate with better/worse outcomes.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    items = []
    for p in positions:
        if p.holding_period_days is not None and p.net_pnl is not None:
            pnl = get_pnl_in_usd(p)  # Convert to USD
            items.append(DurationPnLItem(
                position_id=p.id,
                holding_days=float(p.holding_period_days),
                pnl=round(pnl, 2),
                pnl_pct=round(float(p.net_pnl_pct), 2) if p.net_pnl_pct else None,
                symbol=p.symbol,
                direction=p.direction or "unknown",
                is_winner=float(p.net_pnl) > 0,  # Use original PnL for winner determination
            ))

    return items


@router.get("/symbol-risk", response_model=list[SymbolRiskItem])
async def get_symbol_risk(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    min_trades: int = Query(2, ge=1, description="Minimum trades per symbol"),
    db: Session = Depends(get_db),
) -> list[SymbolRiskItem]:
    """
    Get symbol-level risk metrics for risk quadrant visualization.
    Returns avg win, avg loss, and trade count for each symbol.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by symbol
    symbol_stats = defaultdict(lambda: {
        "winners": [],
        "losers": [],
        "total_pnl": 0.0,
    })

    for p in positions:
        pnl = get_pnl_in_usd(p)  # Convert to USD
        symbol_stats[p.symbol]["total_pnl"] += pnl
        if float(p.net_pnl or 0) > 0:  # Use original PnL for winner/loser classification
            symbol_stats[p.symbol]["winners"].append(pnl)
        else:
            symbol_stats[p.symbol]["losers"].append(pnl)

    items = []
    for symbol, stats in symbol_stats.items():
        total_trades = len(stats["winners"]) + len(stats["losers"])
        if total_trades < min_trades:
            continue

        avg_win = sum(stats["winners"]) / len(stats["winners"]) if stats["winners"] else 0
        avg_loss = sum(stats["losers"]) / len(stats["losers"]) if stats["losers"] else 0
        win_rate = len(stats["winners"]) / total_trades * 100

        # Risk/reward ratio
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else None

        items.append(SymbolRiskItem(
            symbol=symbol,
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            trade_count=total_trades,
            win_rate=round(win_rate, 2),
            total_pnl=round(stats["total_pnl"], 2),
            risk_reward_ratio=round(rr_ratio, 2) if rr_ratio else None,
        ))

    return items


@router.get("/hourly-performance", response_model=list[HourlyPerformanceItem])
async def get_hourly_performance(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[HourlyPerformanceItem]:
    """
    Get trading performance by hour of day.
    Helps identify the best/worst trading hours.
    Uses Position close_time for hour analysis.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by hour of close time
    hour_stats = defaultdict(lambda: {"count": 0, "winners": 0, "total_pnl": 0.0})

    for p in positions:
        if p.close_time:
            hour = p.close_time.hour
            hour_stats[hour]["count"] += 1
            pnl = get_pnl_in_usd(p)  # Convert to USD
            hour_stats[hour]["total_pnl"] += pnl
            if float(p.realized_pnl or p.net_pnl or 0) > 0:
                hour_stats[hour]["winners"] += 1

    items = []
    for hour in range(24):
        stats = hour_stats[hour]
        if stats["count"] > 0:
            items.append(HourlyPerformanceItem(
                hour=hour,
                trade_count=stats["count"],
                win_rate=round(stats["winners"] / stats["count"] * 100, 2),
                total_pnl=round(stats["total_pnl"], 2),
                avg_pnl=round(stats["total_pnl"] / stats["count"], 2),
            ))

    return items


@router.get("/trading-heatmap", response_model=list[TradingHeatmapCell])
async def get_trading_heatmap(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[TradingHeatmapCell]:
    """
    Get trading heatmap data (weekday x hour matrix).
    Shows trading patterns and performance across different time slots.
    Uses Position close_time for analysis.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by weekday and hour
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    matrix = defaultdict(lambda: {"count": 0, "winners": 0, "total_pnl": 0.0})

    for p in positions:
        if p.close_time:
            day = p.close_time.weekday()
            hour = p.close_time.hour
            key = (day, hour)
            matrix[key]["count"] += 1
            pnl = get_pnl_in_usd(p)  # Convert to USD
            matrix[key]["total_pnl"] += pnl
            if float(p.realized_pnl or p.net_pnl or 0) > 0:
                matrix[key]["winners"] += 1

    items = []
    for (day, hour), stats in matrix.items():
        if stats["count"] > 0:
            items.append(TradingHeatmapCell(
                day_of_week=day,
                day_name=day_names[day],
                hour=hour,
                trade_count=stats["count"],
                win_rate=round(stats["winners"] / stats["count"] * 100, 2),
                avg_pnl=round(stats["total_pnl"] / stats["count"], 2),
                total_pnl=round(stats["total_pnl"], 2),
            ))

    # Sort by day then hour
    items.sort(key=lambda x: (x.day_of_week, x.hour))
    return items


@router.get("/by-asset-type", response_model=list[AssetTypeBreakdownItem])
async def get_by_asset_type(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> list[AssetTypeBreakdownItem]:
    """
    Get performance breakdown by asset type (stock vs option).
    Compares performance across different asset classes.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by asset type (using is_option field)
    type_stats = defaultdict(lambda: {
        "count": 0,
        "winners": 0,
        "total_pnl": 0.0,
        "total_holding_days": 0,
        "holding_count": 0,
    })

    for p in positions:
        # Determine asset type based on is_option field
        asset_type = "option" if p.is_option else "stock"
        type_stats[asset_type]["count"] += 1
        pnl = get_pnl_in_usd(p)  # Convert to USD
        type_stats[asset_type]["total_pnl"] += pnl
        if float(p.net_pnl or 0) > 0:
            type_stats[asset_type]["winners"] += 1
        if p.holding_period_days:
            type_stats[asset_type]["total_holding_days"] += p.holding_period_days
            type_stats[asset_type]["holding_count"] += 1

    items = []
    for asset_type, stats in type_stats.items():
        if stats["count"] > 0:
            avg_holding = (
                stats["total_holding_days"] / stats["holding_count"]
                if stats["holding_count"] > 0
                else 0
            )
            items.append(AssetTypeBreakdownItem(
                asset_type=asset_type,
                count=stats["count"],
                total_pnl=round(stats["total_pnl"], 2),
                win_rate=round(stats["winners"] / stats["count"] * 100, 2),
                avg_pnl=round(stats["total_pnl"] / stats["count"], 2),
                avg_holding_days=round(avg_holding, 1),
            ))

    return items
