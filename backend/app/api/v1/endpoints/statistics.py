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
)

router = APIRouter()


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

    # Basic metrics
    total_pnl = sum(float(p.net_pnl or 0) for p in positions)
    total_fees = sum(float(p.total_fees or 0) for p in positions)
    total_trades = len(positions)

    # Winners and losers
    winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
    losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

    win_rate = len(winners) / total_trades * 100 if total_trades > 0 else 0.0

    # Average metrics
    avg_win = sum(float(p.net_pnl) for p in winners) / len(winners) if winners else 0.0
    avg_loss = sum(float(p.net_pnl) for p in losers) / len(losers) if losers else 0.0
    avg_pnl = total_pnl / total_trades if total_trades > 0 else 0.0

    # Profit factor
    gross_profit = sum(float(p.net_pnl) for p in winners)
    gross_loss = abs(sum(float(p.net_pnl) for p in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    # Max drawdown
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for p in positions:
        cumulative += float(p.net_pnl or 0)
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
        stats["total_pnl"] += float(p.net_pnl or 0)
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
        grade_stats[grade]["total_pnl"] += float(p.net_pnl or 0)
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
        direction_stats[direction]["total_pnl"] += float(p.net_pnl or 0)
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
                bucket_stats[label]["total_pnl"] += float(p.net_pnl or 0)
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
        date_stats[d]["pnl"] += float(p.net_pnl or 0)
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
            month_stats[key]["pnl"] += float(p.net_pnl or 0)
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
