"""
Events API endpoints - 事件复盘相关接口

提供事件查询、统计、与持仓关联等功能
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func, and_
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field

from ....database import get_db

# Import models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
from src.models.event_context import EventContext
from src.models.position import Position

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class EventListItem(BaseModel):
    """事件列表项"""
    id: int
    symbol: str
    event_type: str
    event_date: date
    event_title: str
    event_impact: Optional[str] = None
    event_importance: Optional[int] = None
    price_change_pct: Optional[float] = None
    volume_spike: Optional[float] = None
    position_id: Optional[int] = None
    position_pnl_on_event: Optional[float] = None
    is_key_event: bool = False

    class Config:
        from_attributes = True


class EventDetail(BaseModel):
    """事件详情"""
    id: int
    position_id: Optional[int] = None
    symbol: str
    underlying_symbol: Optional[str] = None

    # 事件信息
    event_type: str
    event_date: date
    event_time: Optional[datetime] = None
    event_title: str
    event_description: Optional[str] = None
    event_impact: Optional[str] = None
    event_importance: Optional[int] = None

    # 超预期信息
    is_surprise: bool = False
    surprise_direction: Optional[str] = None
    surprise_magnitude: Optional[float] = None

    # 市场反应
    price_before: Optional[float] = None
    price_after: Optional[float] = None
    price_change: Optional[float] = None
    price_change_pct: Optional[float] = None
    event_day_high: Optional[float] = None
    event_day_low: Optional[float] = None
    event_day_range_pct: Optional[float] = None
    gap_pct: Optional[float] = None

    # 成交量
    volume_on_event: Optional[float] = None
    volume_avg_20d: Optional[float] = None
    volume_spike: Optional[float] = None

    # 持仓影响
    position_pnl_on_event: Optional[float] = None
    position_pnl_pct_on_event: Optional[float] = None

    # 元数据
    source: Optional[str] = None
    confidence: Optional[float] = None
    is_key_event: bool = False
    user_notes: Optional[str] = None

    class Config:
        from_attributes = True


class EventStatistics(BaseModel):
    """事件统计"""
    total_events: int
    by_type: dict
    by_impact: dict
    high_impact_count: int
    avg_price_change: Optional[float] = None


class PositionEventsResponse(BaseModel):
    """持仓事件响应"""
    position_id: int
    symbol: str
    events: List[EventListItem]
    total_events: int
    key_events_count: int


class EventPerformanceByType(BaseModel):
    """按事件类型的绩效统计"""
    event_type: str
    event_count: int
    total_pnl: float
    avg_pnl: float
    win_rate: float
    avg_price_change: Optional[float] = None


class PaginatedEvents(BaseModel):
    """分页事件响应"""
    items: List[EventListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Helper Functions
# ============================================================================

def event_to_list_item(e: EventContext) -> EventListItem:
    """Convert EventContext to EventListItem"""
    return EventListItem(
        id=e.id,
        symbol=e.symbol,
        event_type=e.event_type,
        event_date=e.event_date,
        event_title=e.event_title,
        event_impact=e.event_impact,
        event_importance=e.event_importance,
        price_change_pct=float(e.price_change_pct) if e.price_change_pct else None,
        volume_spike=float(e.volume_spike) if e.volume_spike else None,
        position_id=e.position_id,
        position_pnl_on_event=float(e.position_pnl_on_event) if e.position_pnl_on_event else None,
        is_key_event=e.is_key_event or False,
    )


def event_to_detail(e: EventContext) -> EventDetail:
    """Convert EventContext to EventDetail"""
    return EventDetail(
        id=e.id,
        position_id=e.position_id,
        symbol=e.symbol,
        underlying_symbol=e.underlying_symbol,
        event_type=e.event_type,
        event_date=e.event_date,
        event_time=e.event_time,
        event_title=e.event_title,
        event_description=e.event_description,
        event_impact=e.event_impact,
        event_importance=e.event_importance,
        is_surprise=e.is_surprise or False,
        surprise_direction=e.surprise_direction,
        surprise_magnitude=float(e.surprise_magnitude) if e.surprise_magnitude else None,
        price_before=float(e.price_before) if e.price_before else None,
        price_after=float(e.price_after) if e.price_after else None,
        price_change=float(e.price_change) if e.price_change else None,
        price_change_pct=float(e.price_change_pct) if e.price_change_pct else None,
        event_day_high=float(e.event_day_high) if e.event_day_high else None,
        event_day_low=float(e.event_day_low) if e.event_day_low else None,
        event_day_range_pct=float(e.event_day_range_pct) if e.event_day_range_pct else None,
        gap_pct=float(e.gap_pct) if e.gap_pct else None,
        volume_on_event=float(e.volume_on_event) if e.volume_on_event else None,
        volume_avg_20d=float(e.volume_avg_20d) if e.volume_avg_20d else None,
        volume_spike=float(e.volume_spike) if e.volume_spike else None,
        position_pnl_on_event=float(e.position_pnl_on_event) if e.position_pnl_on_event else None,
        position_pnl_pct_on_event=float(e.position_pnl_pct_on_event) if e.position_pnl_pct_on_event else None,
        source=e.source,
        confidence=float(e.confidence) if e.confidence else None,
        is_key_event=e.is_key_event or False,
        user_notes=e.user_notes,
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=PaginatedEvents)
async def list_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_impact: Optional[str] = Query(None, description="Filter by impact: positive/negative/neutral"),
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    min_importance: Optional[int] = Query(None, ge=1, le=10, description="Minimum importance"),
    is_key_event: Optional[bool] = Query(None, description="Filter key events"),
    sort_by: str = Query("event_date", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc/desc"),
    db: Session = Depends(get_db),
) -> PaginatedEvents:
    """
    List events with pagination and filtering.
    """
    query = db.query(EventContext)

    # Apply filters
    if symbol:
        query = query.filter(EventContext.symbol.ilike(f"%{symbol}%"))
    if event_type:
        query = query.filter(EventContext.event_type == event_type)
    if event_impact:
        query = query.filter(EventContext.event_impact == event_impact)
    if date_start:
        query = query.filter(EventContext.event_date >= date_start)
    if date_end:
        query = query.filter(EventContext.event_date <= date_end)
    if min_importance:
        query = query.filter(EventContext.event_importance >= min_importance)
    if is_key_event is not None:
        query = query.filter(EventContext.is_key_event == is_key_event)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_column = getattr(EventContext, sort_by, EventContext.event_date)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # Apply pagination
    offset = (page - 1) * page_size
    events = query.offset(offset).limit(page_size).all()

    return PaginatedEvents(
        items=[event_to_list_item(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/statistics", response_model=EventStatistics)
async def get_event_statistics(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    date_start: Optional[date] = Query(None, description="Start date"),
    date_end: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
) -> EventStatistics:
    """
    Get event statistics.
    """
    query = db.query(EventContext)

    if symbol:
        query = query.filter(EventContext.symbol.ilike(f"%{symbol}%"))
    if date_start:
        query = query.filter(EventContext.event_date >= date_start)
    if date_end:
        query = query.filter(EventContext.event_date <= date_end)

    total = query.count()

    # By type
    by_type = db.query(
        EventContext.event_type,
        func.count(EventContext.id)
    ).group_by(EventContext.event_type).all()

    # By impact
    by_impact = db.query(
        EventContext.event_impact,
        func.count(EventContext.id)
    ).filter(EventContext.event_impact.isnot(None)).group_by(EventContext.event_impact).all()

    # High impact count
    high_impact = query.filter(EventContext.event_importance >= 7).count()

    # Average price change
    avg_change = db.query(func.avg(EventContext.price_change_pct)).filter(
        EventContext.price_change_pct.isnot(None)
    ).scalar()

    return EventStatistics(
        total_events=total,
        by_type={t: c for t, c in by_type},
        by_impact={i: c for i, c in by_impact if i},
        high_impact_count=high_impact,
        avg_price_change=float(avg_change) if avg_change else None,
    )


@router.get("/by-type-performance", response_model=List[EventPerformanceByType])
async def get_performance_by_event_type(
    db: Session = Depends(get_db),
) -> List[EventPerformanceByType]:
    """
    Get trading performance grouped by event type.
    """
    results = db.query(
        EventContext.event_type,
        func.count(EventContext.id).label('count'),
        func.sum(EventContext.position_pnl_on_event).label('total_pnl'),
        func.avg(EventContext.position_pnl_on_event).label('avg_pnl'),
        func.avg(EventContext.price_change_pct).label('avg_price_change'),
    ).filter(
        EventContext.position_pnl_on_event.isnot(None)
    ).group_by(EventContext.event_type).all()

    performance = []
    for r in results:
        # Calculate win rate
        win_count = db.query(func.count(EventContext.id)).filter(
            and_(
                EventContext.event_type == r.event_type,
                EventContext.position_pnl_on_event > 0
            )
        ).scalar() or 0

        win_rate = (win_count / r.count * 100) if r.count > 0 else 0

        performance.append(EventPerformanceByType(
            event_type=r.event_type,
            event_count=r.count,
            total_pnl=float(r.total_pnl or 0),
            avg_pnl=float(r.avg_pnl or 0),
            win_rate=win_rate,
            avg_price_change=float(r.avg_price_change) if r.avg_price_change else None,
        ))

    return performance


@router.get("/{event_id}", response_model=EventDetail)
async def get_event_detail(
    event_id: int = Path(..., description="Event ID"),
    db: Session = Depends(get_db),
) -> EventDetail:
    """
    Get event detail by ID.
    """
    event = db.query(EventContext).filter(EventContext.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event_to_detail(event)


@router.get("/position/{position_id}", response_model=PositionEventsResponse)
async def get_events_for_position(
    position_id: int = Path(..., description="Position ID"),
    db: Session = Depends(get_db),
) -> PositionEventsResponse:
    """
    Get all events associated with a position.
    """
    position = db.query(Position).filter(Position.id == position_id).first()

    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    events = db.query(EventContext).filter(
        EventContext.position_id == position_id
    ).order_by(EventContext.event_date).all()

    key_events_count = sum(1 for e in events if e.is_key_event)

    return PositionEventsResponse(
        position_id=position_id,
        symbol=position.symbol,
        events=[event_to_list_item(e) for e in events],
        total_events=len(events),
        key_events_count=key_events_count,
    )


@router.put("/{event_id}/mark-key", response_model=EventDetail)
async def mark_event_as_key(
    event_id: int = Path(..., description="Event ID"),
    is_key: bool = Query(True, description="Mark as key event"),
    db: Session = Depends(get_db),
) -> EventDetail:
    """
    Mark or unmark an event as a key event.
    """
    event = db.query(EventContext).filter(EventContext.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.is_key_event = is_key
    db.commit()
    db.refresh(event)

    return event_to_detail(event)


@router.put("/{event_id}/notes", response_model=EventDetail)
async def update_event_notes(
    event_id: int = Path(..., description="Event ID"),
    notes: str = Query(..., description="User notes"),
    db: Session = Depends(get_db),
) -> EventDetail:
    """
    Update user notes for an event.
    """
    event = db.query(EventContext).filter(EventContext.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.user_notes = notes
    db.commit()
    db.refresh(event)

    return event_to_detail(event)


@router.get("/symbol/{symbol}/timeline", response_model=List[EventListItem])
async def get_symbol_event_timeline(
    symbol: str = Path(..., description="Symbol"),
    days: int = Query(90, ge=7, le=365, description="Days to look back"),
    db: Session = Depends(get_db),
) -> List[EventListItem]:
    """
    Get event timeline for a symbol.
    """
    from datetime import timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    events = db.query(EventContext).filter(
        and_(
            EventContext.symbol.ilike(f"%{symbol}%"),
            EventContext.event_date >= start_date,
            EventContext.event_date <= end_date
        )
    ).order_by(EventContext.event_date).all()

    return [event_to_list_item(e) for e in events]
