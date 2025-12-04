"""
Trades API endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import Optional
from datetime import date

from ....database import get_db, Trade
from ....schemas import (
    PaginatedResponse,
    TradeListItem,
    TradeDetail,
    TradeSummary,
)

router = APIRouter()


def trade_to_list_item(t: Trade) -> TradeListItem:
    """Convert Trade model to TradeListItem schema."""
    return TradeListItem(
        id=t.id,
        symbol=t.symbol,
        symbol_name=t.symbol_name,
        direction=t.direction.value if t.direction else "unknown",
        status=t.status.value if t.status else "unknown",
        filled_price=float(t.filled_price) if t.filled_price else None,
        filled_quantity=t.filled_quantity,
        filled_amount=float(t.filled_amount) if t.filled_amount else None,
        filled_time=t.filled_time,
        trade_date=t.trade_date,
        market=t.market.value if t.market else "unknown",
        currency=t.currency or "USD",
        total_fee=float(t.total_fee) if t.total_fee else 0.0,
        is_option=bool(t.is_option),
        underlying_symbol=t.underlying_symbol,
        position_id=t.position_id,
    )


@router.get("", response_model=PaginatedResponse[TradeListItem])
async def list_trades(
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Filters
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    direction: Optional[str] = Query(None, description="Filter by direction"),
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    is_option: Optional[bool] = Query(None, description="Filter options only"),
    position_id: Optional[int] = Query(None, description="Filter by position ID"),
    # Sorting
    sort_by: str = Query("filled_time", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TradeListItem]:
    """
    List trades with pagination and filtering.
    """
    query = db.query(Trade)

    # Apply filters
    if symbol:
        query = query.filter(Trade.symbol.ilike(f"%{symbol}%"))
    if direction:
        query = query.filter(Trade.direction == direction)
    if date_start:
        query = query.filter(Trade.trade_date >= date_start)
    if date_end:
        query = query.filter(Trade.trade_date <= date_end)
    if is_option is not None:
        query = query.filter(Trade.is_option == (1 if is_option else 0))
    if position_id is not None:
        query = query.filter(Trade.position_id == position_id)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(Trade, sort_by, Trade.filled_time)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * page_size
    trades = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse[TradeListItem](
        items=[trade_to_list_item(t) for t in trades],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/summary", response_model=TradeSummary)
async def get_trade_summary(
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> TradeSummary:
    """
    Get trade summary statistics.
    """
    query = db.query(Trade)

    if date_start:
        query = query.filter(Trade.trade_date >= date_start)
    if date_end:
        query = query.filter(Trade.trade_date <= date_end)

    trades = query.all()

    # Calculate metrics
    total_trades = len(trades)
    buy_trades = sum(1 for t in trades if t.direction and t.direction.value in ["buy", "buy_to_cover"])
    sell_trades = sum(1 for t in trades if t.direction and t.direction.value in ["sell", "sell_short"])

    total_volume = sum(t.filled_quantity or 0 for t in trades)
    total_amount = sum(float(t.filled_amount or 0) for t in trades)
    total_fees = sum(float(t.total_fee or 0) for t in trades)
    avg_fee = total_fees / total_trades if total_trades > 0 else 0.0

    stock_trades = sum(1 for t in trades if not t.is_option)
    option_trades = sum(1 for t in trades if t.is_option)

    return TradeSummary(
        total_trades=total_trades,
        buy_trades=buy_trades,
        sell_trades=sell_trades,
        total_volume=total_volume,
        total_amount=round(total_amount, 2),
        total_fees=round(total_fees, 2),
        avg_fee_per_trade=round(avg_fee, 2),
        stock_trades=stock_trades,
        option_trades=option_trades,
    )


@router.get("/{trade_id}", response_model=TradeDetail)
async def get_trade_detail(
    trade_id: int = Path(..., description="Trade ID"),
    db: Session = Depends(get_db),
) -> TradeDetail:
    """
    Get detailed information about a specific trade.
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return TradeDetail(
        id=trade.id,
        symbol=trade.symbol,
        symbol_name=trade.symbol_name,
        direction=trade.direction.value if trade.direction else "unknown",
        status=trade.status.value if trade.status else "unknown",
        order_price=float(trade.order_price) if trade.order_price else None,
        order_quantity=trade.order_quantity,
        order_amount=float(trade.order_amount) if trade.order_amount else None,
        order_time=trade.order_time,
        order_type=trade.order_type,
        filled_price=float(trade.filled_price) if trade.filled_price else None,
        filled_quantity=trade.filled_quantity,
        filled_amount=float(trade.filled_amount) if trade.filled_amount else None,
        filled_time=trade.filled_time,
        trade_date=trade.trade_date,
        market=trade.market.value if trade.market else "unknown",
        currency=trade.currency or "USD",
        commission=float(trade.commission) if trade.commission else None,
        platform_fee=float(trade.platform_fee) if trade.platform_fee else None,
        clearing_fee=float(trade.clearing_fee) if trade.clearing_fee else None,
        transaction_fee=float(trade.transaction_fee) if trade.transaction_fee else None,
        stamp_duty=float(trade.stamp_duty) if trade.stamp_duty else None,
        sec_fee=float(trade.sec_fee) if trade.sec_fee else None,
        option_regulatory_fee=float(trade.option_regulatory_fee) if trade.option_regulatory_fee else None,
        option_clearing_fee=float(trade.option_clearing_fee) if trade.option_clearing_fee else None,
        total_fee=float(trade.total_fee) if trade.total_fee else 0.0,
        is_option=bool(trade.is_option),
        underlying_symbol=trade.underlying_symbol,
        option_type=trade.option_type,
        strike_price=float(trade.strike_price) if trade.strike_price else None,
        expiration_date=trade.expiration_date,
        position_id=trade.position_id,
        matched_trade_id=trade.matched_trade_id,
        notes=trade.notes,
        created_at=trade.created_at,
        updated_at=trade.updated_at,
    )
