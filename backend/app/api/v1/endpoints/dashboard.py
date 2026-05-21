"""
Dashboard API endpoints
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import date, timedelta

from ....database import get_db, Position, PositionStatus
from ....schemas import (
    DashboardKPIs,
    EquityCurveResponse,
    EquityCurvePoint,
    RecentTradeItem,
    NeedsReviewItem,
    StrategyBreakdownItem,
    DailyPnLItem,
)
from ....utils.currency import get_pnl_in_usd, get_fees_in_usd

router = APIRouter()


@router.get("/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    date_start: Optional[date] = Query(None, description="Start date filter"),
    date_end: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
) -> DashboardKPIs:
    """
    Get dashboard KPI metrics.

    Returns total P&L, win rate, average score, trade count, etc.
    """
    # Base query for closed positions
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    # Apply date filters
    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    if not positions:
        return DashboardKPIs(
            total_pnl=0.0,
            win_rate=0.0,
            avg_score=0.0,
            trade_count=0,
            total_fees=0.0,
            avg_holding_days=0.0,
        )

    # Calculate metrics — convert each position's P&L / fees to USD so HKD
    # and USD positions don't get summed naïvely as if they were the same unit.
    total_pnl = sum(get_pnl_in_usd(p) for p in positions)
    total_fees = sum(get_fees_in_usd(p) for p in positions)
    trade_count = len(positions)

    # Win rate (sign of P&L is currency-agnostic, no conversion needed here)
    winners = sum(1 for p in positions if p.net_pnl and float(p.net_pnl) > 0)
    win_rate = (winners / trade_count * 100) if trade_count > 0 else 0.0

    # Average score
    scored_positions = [p for p in positions if p.overall_score is not None]
    avg_score = (
        sum(float(p.overall_score) for p in scored_positions) / len(scored_positions)
        if scored_positions
        else 0.0
    )

    # Average holding days
    positions_with_holding = [p for p in positions if p.holding_period_days is not None]
    avg_holding_days = (
        sum(p.holding_period_days for p in positions_with_holding)
        / len(positions_with_holding)
        if positions_with_holding
        else 0.0
    )

    return DashboardKPIs(
        total_pnl=round(total_pnl, 2),
        win_rate=round(win_rate, 2),
        avg_score=round(avg_score, 2),
        trade_count=trade_count,
        total_fees=round(total_fees, 2),
        avg_holding_days=round(avg_holding_days, 1),
    )


@router.get("/equity-curve", response_model=EquityCurveResponse)
async def get_equity_curve(
    date_start: Optional[date] = Query(None, description="Start date filter"),
    date_end: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
) -> EquityCurveResponse:
    """
    Get equity curve data for chart.

    Returns cumulative P&L over time.
    """
    # Query closed positions ordered by close date
    query = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .filter(Position.close_date.isnot(None))
        .order_by(Position.close_date)
    )

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    if not positions:
        return EquityCurveResponse(data=[], total_pnl=0.0)

    # Group by date and calculate cumulative P&L (USD-equivalent)
    date_pnl = {}
    for p in positions:
        d = p.close_date
        pnl = get_pnl_in_usd(p)
        if d not in date_pnl:
            date_pnl[d] = {"pnl": 0, "count": 0}
        date_pnl[d]["pnl"] += pnl
        date_pnl[d]["count"] += 1

    # Build equity curve
    data = []
    cumulative = 0.0
    peak = 0.0
    max_drawdown = 0.0

    for d in sorted(date_pnl.keys()):
        cumulative += date_pnl[d]["pnl"]
        data.append(
            EquityCurvePoint(
                date=d,
                cumulative_pnl=round(cumulative, 2),
                trade_count=date_pnl[d]["count"],
            )
        )

        # Track max drawdown
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Calculate max drawdown percentage
    max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else None

    return EquityCurveResponse(
        data=data,
        total_pnl=round(cumulative, 2),
        max_drawdown=round(max_drawdown, 2) if max_drawdown > 0 else None,
        max_drawdown_pct=round(max_drawdown_pct, 2) if max_drawdown_pct else None,
    )


@router.get("/recent-trades", response_model=list[RecentTradeItem])
async def get_recent_trades(
    limit: int = Query(10, ge=1, le=50, description="Number of trades to return"),
    db: Session = Depends(get_db),
) -> list[RecentTradeItem]:
    """
    Get most recent closed trades.
    """
    positions = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .order_by(Position.close_date.desc())
        .limit(limit)
        .all()
    )

    return [
        RecentTradeItem(
            id=p.id,
            symbol=p.symbol,
            close_date=p.close_date,
            net_pnl=float(p.net_pnl) if p.net_pnl else 0.0,
            net_pnl_pct=float(p.net_pnl_pct) if p.net_pnl_pct else None,
            grade=p.score_grade,
            direction=p.direction,
            currency=p.currency,
        )
        for p in positions
    ]


@router.get("/needs-review", response_model=list[NeedsReviewItem])
async def get_needs_review(
    limit: int = Query(10, ge=1, le=50, description="Number of trades to return"),
    db: Session = Depends(get_db),
) -> list[NeedsReviewItem]:
    """
    Get trades that need review.

    Includes:
    - Large losses (net_pnl < -500)
    - Low scores (grade D or F)
    - Not yet reviewed
    """
    # Large losses
    large_losses = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .filter(Position.net_pnl < -500)
        .filter(Position.reviewed_at.is_(None))
        .order_by(Position.net_pnl)
        .limit(limit // 2)
        .all()
    )

    # Low scores
    low_scores = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .filter(
            or_(
                func.upper(Position.score_grade).like("D%"),
                func.upper(Position.score_grade).like("F%"),
            )
        )
        .filter(Position.reviewed_at.is_(None))
        .order_by(Position.overall_score)
        .limit(limit // 2)
        .all()
    )

    # Combine and dedupe
    seen_ids = set()
    items = []

    for p in large_losses:
        if p.id not in seen_ids:
            seen_ids.add(p.id)
            items.append(
                NeedsReviewItem(
                    id=p.id,
                    symbol=p.symbol,
                    close_date=p.close_date,
                    net_pnl=float(p.net_pnl) if p.net_pnl else 0.0,
                    grade=p.score_grade,
                    reason="Large loss",
                    currency=p.currency,
                )
            )

    for p in low_scores:
        if p.id not in seen_ids:
            seen_ids.add(p.id)
            items.append(
                NeedsReviewItem(
                    id=p.id,
                    symbol=p.symbol,
                    close_date=p.close_date,
                    net_pnl=float(p.net_pnl) if p.net_pnl else 0.0,
                    grade=p.score_grade,
                    reason=f"Low score ({p.score_grade})",
                    currency=p.currency,
                )
            )

    return items[:limit]


@router.get("/strategy-breakdown", response_model=list[StrategyBreakdownItem])
async def get_strategy_breakdown(
    date_start: Optional[date] = Query(None, description="Start date filter"),
    date_end: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
) -> list[StrategyBreakdownItem]:
    """
    Get P&L breakdown by strategy type.
    """
    query = db.query(Position).filter(Position.status == PositionStatus.CLOSED)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    # Group by strategy
    strategy_stats = {}
    strategy_names = {
        "trend": "Trend Following",
        "mean_reversion": "Mean Reversion",
        "breakout": "Breakout",
        "range": "Range Trading",
        "momentum": "Momentum",
        None: "Unclassified",
    }

    for p in positions:
        strategy = p.strategy_type or None
        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                "count": 0,
                "total_pnl": 0.0,
                "winners": 0,
            }
        strategy_stats[strategy]["count"] += 1
        strategy_stats[strategy]["total_pnl"] += get_pnl_in_usd(p)
        if p.net_pnl and float(p.net_pnl) > 0:
            strategy_stats[strategy]["winners"] += 1

    # Convert to response items
    items = []
    for strategy, stats in strategy_stats.items():
        win_rate = (
            stats["winners"] / stats["count"] * 100 if stats["count"] > 0 else 0.0
        )
        items.append(
            StrategyBreakdownItem(
                strategy=strategy or "unknown",
                strategy_name=strategy_names.get(strategy, strategy or "Unknown"),
                count=stats["count"],
                total_pnl=round(stats["total_pnl"], 2),
                win_rate=round(win_rate, 2),
            )
        )

    # Sort by count descending
    items.sort(key=lambda x: x.count, reverse=True)
    return items


@router.get("/daily-pnl", response_model=list[DailyPnLItem])
async def get_daily_pnl(
    days: int = Query(30, ge=7, le=365, description="Number of days"),
    db: Session = Depends(get_db),
) -> list[DailyPnLItem]:
    """
    Get daily P&L for the last N days.
    """
    start_date = date.today() - timedelta(days=days)

    positions = (
        db.query(Position)
        .filter(Position.status == PositionStatus.CLOSED)
        .filter(Position.close_date >= start_date)
        .order_by(Position.close_date)
        .all()
    )

    # Group by date (USD-equivalent)
    date_pnl = {}
    for p in positions:
        d = p.close_date
        if d not in date_pnl:
            date_pnl[d] = {"pnl": 0.0, "count": 0}
        date_pnl[d]["pnl"] += get_pnl_in_usd(p)
        date_pnl[d]["count"] += 1

    return [
        DailyPnLItem(
            date=d,
            pnl=round(stats["pnl"], 2),
            trade_count=stats["count"],
        )
        for d, stats in sorted(date_pnl.items())
    ]
