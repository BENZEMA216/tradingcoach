"""
Positions API endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional
from datetime import date, datetime

from ....database import get_db, Position, PositionStatus, Trade
from ....schemas import (
    PaginatedResponse,
    PositionListItem,
    PositionDetail,
    PositionScoreDetail,
    PositionRiskMetrics,
    PositionFilterParams,
    PositionReviewUpdate,
    PositionSummary,
    MessageResponse,
)

router = APIRouter()


def position_to_list_item(p: Position) -> PositionListItem:
    """Convert Position model to PositionListItem schema."""
    return PositionListItem(
        id=p.id,
        symbol=p.symbol,
        symbol_name=p.symbol_name,
        direction=p.direction,
        status=p.status.value if p.status else "unknown",
        open_date=p.open_date,
        close_date=p.close_date,
        holding_period_days=p.holding_period_days,
        open_price=float(p.open_price) if p.open_price else 0.0,
        close_price=float(p.close_price) if p.close_price else None,
        quantity=p.quantity,
        net_pnl=float(p.net_pnl) if p.net_pnl else None,
        net_pnl_pct=float(p.net_pnl_pct) if p.net_pnl_pct else None,
        overall_score=float(p.overall_score) if p.overall_score else None,
        score_grade=p.score_grade,
        strategy_type=p.strategy_type,
        reviewed_at=p.reviewed_at,
    )


@router.get("", response_model=PaginatedResponse[PositionListItem])
async def list_positions(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filters
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    direction: Optional[str] = Query(None, description="Filter by direction: long/short"),
    status: Optional[str] = Query(None, description="Filter by status: open/closed"),
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    pnl_min: Optional[float] = Query(None, description="Minimum P&L"),
    pnl_max: Optional[float] = Query(None, description="Maximum P&L"),
    is_winner: Optional[bool] = Query(None, description="Filter winners/losers"),
    score_min: Optional[float] = Query(None, description="Minimum score"),
    score_max: Optional[float] = Query(None, description="Maximum score"),
    score_grade: Optional[str] = Query(None, description="Filter by grade: A/B/C/D/F"),
    strategy_type: Optional[str] = Query(None, description="Filter by strategy type"),
    is_reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    # Sorting
    sort_by: str = Query("close_date", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[PositionListItem]:
    """
    List positions with pagination and filtering.
    """
    # Base query
    query = db.query(Position)

    # Apply filters
    if symbol:
        query = query.filter(Position.symbol.ilike(f"%{symbol}%"))
    if direction:
        query = query.filter(Position.direction == direction)
    if status:
        status_enum = PositionStatus(status)
        query = query.filter(Position.status == status_enum)
    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)
    if pnl_min is not None:
        query = query.filter(Position.net_pnl >= pnl_min)
    if pnl_max is not None:
        query = query.filter(Position.net_pnl <= pnl_max)
    if is_winner is not None:
        if is_winner:
            query = query.filter(Position.net_pnl > 0)
        else:
            query = query.filter(Position.net_pnl <= 0)
    if score_min is not None:
        query = query.filter(Position.overall_score >= score_min)
    if score_max is not None:
        query = query.filter(Position.overall_score <= score_max)
    if score_grade:
        query = query.filter(Position.score_grade == score_grade.upper())
    if strategy_type:
        query = query.filter(Position.strategy_type == strategy_type)
    if is_reviewed is not None:
        if is_reviewed:
            query = query.filter(Position.reviewed_at.isnot(None))
        else:
            query = query.filter(Position.reviewed_at.is_(None))

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(Position, sort_by, Position.close_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * page_size
    positions = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse[PositionListItem](
        items=[position_to_list_item(p) for p in positions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=PositionSummary)
async def get_position_summary(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> PositionSummary:
    """
    Get position summary statistics.
    """
    # Query all positions
    query = db.query(Position)

    if date_start:
        query = query.filter(Position.close_date >= date_start)
    if date_end:
        query = query.filter(Position.close_date <= date_end)

    positions = query.all()

    closed_positions = [p for p in positions if p.status == PositionStatus.CLOSED]
    open_positions = [p for p in positions if p.status == PositionStatus.OPEN]

    # Calculate metrics
    total_pnl = sum(float(p.net_pnl or 0) for p in closed_positions)
    total_realized_pnl = sum(float(p.realized_pnl or 0) for p in closed_positions)
    total_fees = sum(float(p.total_fees or 0) for p in closed_positions)

    winners = [p for p in closed_positions if p.net_pnl and float(p.net_pnl) > 0]
    losers = [p for p in closed_positions if p.net_pnl and float(p.net_pnl) <= 0]

    win_rate = len(winners) / len(closed_positions) * 100 if closed_positions else 0.0
    avg_pnl = total_pnl / len(closed_positions) if closed_positions else 0.0
    avg_winner = (
        sum(float(p.net_pnl) for p in winners) / len(winners) if winners else 0.0
    )
    avg_loser = (
        sum(float(p.net_pnl) for p in losers) / len(losers) if losers else 0.0
    )

    # Profit factor
    gross_profit = sum(float(p.net_pnl) for p in winners)
    gross_loss = abs(sum(float(p.net_pnl) for p in losers))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    # Average score
    scored = [p for p in closed_positions if p.overall_score is not None]
    avg_score = (
        sum(float(p.overall_score) for p in scored) / len(scored) if scored else None
    )

    # Average holding days
    with_holding = [p for p in closed_positions if p.holding_period_days is not None]
    avg_holding_days = (
        sum(p.holding_period_days for p in with_holding) / len(with_holding)
        if with_holding
        else 0.0
    )

    return PositionSummary(
        total_positions=len(positions),
        closed_positions=len(closed_positions),
        open_positions=len(open_positions),
        total_pnl=round(total_pnl, 2),
        total_realized_pnl=round(total_realized_pnl, 2),
        total_fees=round(total_fees, 2),
        winners=len(winners),
        losers=len(losers),
        win_rate=round(win_rate, 2),
        avg_pnl=round(avg_pnl, 2),
        avg_winner=round(avg_winner, 2),
        avg_loser=round(avg_loser, 2),
        profit_factor=round(profit_factor, 2) if profit_factor else None,
        avg_score=round(avg_score, 2) if avg_score else None,
        avg_holding_days=round(avg_holding_days, 1),
    )


@router.get("/{position_id}", response_model=PositionDetail)
async def get_position_detail(
    position_id: int = Path(..., description="Position ID"),
    db: Session = Depends(get_db),
) -> PositionDetail:
    """
    Get detailed information about a specific position.
    """
    position = db.query(Position).filter(Position.id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Get associated trade IDs
    trade_ids = [t.id for t in position.trades] if position.trades else []

    return PositionDetail(
        id=position.id,
        symbol=position.symbol,
        symbol_name=position.symbol_name,
        direction=position.direction,
        status=position.status.value if position.status else "unknown",
        open_time=position.open_time,
        close_time=position.close_time,
        open_date=position.open_date,
        close_date=position.close_date,
        holding_period_days=position.holding_period_days,
        holding_period_hours=float(position.holding_period_hours) if position.holding_period_hours else None,
        open_price=float(position.open_price) if position.open_price else 0.0,
        close_price=float(position.close_price) if position.close_price else None,
        quantity=position.quantity,
        realized_pnl=float(position.realized_pnl) if position.realized_pnl else None,
        realized_pnl_pct=float(position.realized_pnl_pct) if position.realized_pnl_pct else None,
        total_fees=float(position.total_fees) if position.total_fees else None,
        open_fee=float(position.open_fee) if position.open_fee else None,
        close_fee=float(position.close_fee) if position.close_fee else None,
        net_pnl=float(position.net_pnl) if position.net_pnl else None,
        net_pnl_pct=float(position.net_pnl_pct) if position.net_pnl_pct else None,
        market=position.market,
        currency=position.currency,
        is_option=bool(position.is_option),
        underlying_symbol=position.underlying_symbol,
        scores=PositionScoreDetail(
            entry_quality_score=float(position.entry_quality_score) if position.entry_quality_score else None,
            exit_quality_score=float(position.exit_quality_score) if position.exit_quality_score else None,
            trend_quality_score=float(position.trend_quality_score) if position.trend_quality_score else None,
            risk_mgmt_score=float(position.risk_mgmt_score) if position.risk_mgmt_score else None,
            overall_score=float(position.overall_score) if position.overall_score else None,
            score_grade=position.score_grade,
        ),
        risk_metrics=PositionRiskMetrics(
            mae=float(position.mae) if position.mae else None,
            mae_pct=float(position.mae_pct) if position.mae_pct else None,
            mae_time=position.mae_time,
            mfe=float(position.mfe) if position.mfe else None,
            mfe_pct=float(position.mfe_pct) if position.mfe_pct else None,
            mfe_time=position.mfe_time,
            risk_reward_ratio=float(position.risk_reward_ratio) if position.risk_reward_ratio else None,
        ),
        strategy_type=position.strategy_type,
        strategy_confidence=float(position.strategy_confidence) if position.strategy_confidence else None,
        entry_indicators=position.entry_indicators,
        exit_indicators=position.exit_indicators,
        post_exit_5d_pct=float(position.post_exit_5d_pct) if position.post_exit_5d_pct else None,
        post_exit_10d_pct=float(position.post_exit_10d_pct) if position.post_exit_10d_pct else None,
        post_exit_20d_pct=float(position.post_exit_20d_pct) if position.post_exit_20d_pct else None,
        review_notes=position.review_notes,
        emotion_tag=position.emotion_tag,
        discipline_score=position.discipline_score,
        reviewed_at=position.reviewed_at,
        analysis_notes=position.analysis_notes,
        trade_ids=trade_ids,
        created_at=position.created_at,
        updated_at=position.updated_at,
    )


@router.patch("/{position_id}/review", response_model=MessageResponse)
async def update_position_review(
    position_id: int = Path(..., description="Position ID"),
    review: PositionReviewUpdate = ...,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Update position review notes.
    """
    position = db.query(Position).filter(Position.id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    # Update review fields
    if review.review_notes is not None:
        position.review_notes = review.review_notes
    if review.emotion_tag is not None:
        position.emotion_tag = review.emotion_tag
    if review.discipline_score is not None:
        position.discipline_score = review.discipline_score

    # Mark as reviewed
    position.reviewed_at = datetime.utcnow()

    db.commit()

    return MessageResponse(
        message=f"Position {position_id} review updated successfully",
        success=True,
    )


@router.get("/symbols/list", response_model=list[str])
async def list_symbols(
    db: Session = Depends(get_db),
) -> list[str]:
    """
    Get list of unique symbols from positions.
    """
    symbols = (
        db.query(Position.symbol)
        .distinct()
        .order_by(Position.symbol)
        .all()
    )
    return [s[0] for s in symbols]
