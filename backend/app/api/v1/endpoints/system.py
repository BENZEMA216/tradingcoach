"""
System API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from ....database import get_db, Position, Trade, MarketData
from ....schemas import MessageResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
):
    """
    Get system statistics (database counts, etc.).
    """
    # Count records in each table
    position_count = db.query(func.count(Position.id)).scalar()
    trade_count = db.query(func.count(Trade.id)).scalar()
    market_data_count = db.query(func.count(MarketData.id)).scalar()

    # Get date ranges
    position_dates = db.query(
        func.min(Position.open_date),
        func.max(Position.close_date),
    ).first()

    trade_dates = db.query(
        func.min(Trade.trade_date),
        func.max(Trade.trade_date),
    ).first()

    market_data_dates = db.query(
        func.min(MarketData.date),
        func.max(MarketData.date),
    ).first()

    # Get unique symbols
    position_symbols = db.query(func.count(func.distinct(Position.symbol))).scalar()
    market_data_symbols = db.query(func.count(func.distinct(MarketData.symbol))).scalar()

    return {
        "database": {
            "positions": {
                "count": position_count,
                "symbols": position_symbols,
                "date_range": {
                    "start": position_dates[0].isoformat() if position_dates[0] else None,
                    "end": position_dates[1].isoformat() if position_dates[1] else None,
                },
            },
            "trades": {
                "count": trade_count,
                "date_range": {
                    "start": trade_dates[0].isoformat() if trade_dates[0] else None,
                    "end": trade_dates[1].isoformat() if trade_dates[1] else None,
                },
            },
            "market_data": {
                "count": market_data_count,
                "symbols": market_data_symbols,
                "date_range": {
                    "start": market_data_dates[0].isoformat() if market_data_dates[0] else None,
                    "end": market_data_dates[1].isoformat() if market_data_dates[1] else None,
                },
            },
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/symbols")
async def list_all_symbols(
    db: Session = Depends(get_db),
):
    """
    Get list of all symbols in the system.
    """
    # Get symbols from positions
    position_symbols = (
        db.query(Position.symbol, Position.symbol_name)
        .distinct()
        .order_by(Position.symbol)
        .all()
    )

    # Get symbols from market data
    market_data_symbols = (
        db.query(MarketData.symbol)
        .distinct()
        .order_by(MarketData.symbol)
        .all()
    )

    # Combine and dedupe
    symbols = {}
    for symbol, name in position_symbols:
        symbols[symbol] = {
            "symbol": symbol,
            "name": name,
            "has_positions": True,
            "has_market_data": False,
        }

    for (symbol,) in market_data_symbols:
        if symbol in symbols:
            symbols[symbol]["has_market_data"] = True
        else:
            symbols[symbol] = {
                "symbol": symbol,
                "name": None,
                "has_positions": False,
                "has_market_data": True,
            }

    return {
        "symbols": list(symbols.values()),
        "total": len(symbols),
    }
