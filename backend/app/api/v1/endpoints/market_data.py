"""
Market Data API endpoints
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date, timedelta

from ....database import get_db, MarketData, Position, PositionStatus
from ....schemas import (
    MarketDataResponse,
    OHLCVData,
    TechnicalIndicators,
    CandlestickChartData,
    SymbolInfo,
)

router = APIRouter()


@router.get("/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str = Path(..., description="Stock symbol"),
    interval: str = Query("1d", description="Data interval: 1d, 1h, 5m"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=500, description="Max candles to return"),
    include_indicators: bool = Query(True, description="Include technical indicators"),
    db: Session = Depends(get_db),
) -> MarketDataResponse:
    """
    Get market data (OHLCV + indicators) for a symbol.
    """
    # Build query
    query = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol.upper())
        .filter(MarketData.interval == interval)
    )

    if start_date:
        query = query.filter(MarketData.date >= start_date)
    if end_date:
        query = query.filter(MarketData.date <= end_date)

    # Order by date descending, then limit, then reverse for chronological order
    data = query.order_by(desc(MarketData.date)).limit(limit).all()
    data = list(reversed(data))  # Chronological order

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for symbol {symbol}"
        )

    # Build candles
    candles = [
        OHLCVData(
            timestamp=d.timestamp,
            date=d.date,
            open=float(d.open) if d.open else None,
            high=float(d.high) if d.high else None,
            low=float(d.low) if d.low else None,
            close=float(d.close) if d.close else 0.0,
            volume=d.volume,
        )
        for d in data
    ]

    # Get latest indicators
    latest_indicators = None
    if include_indicators and data:
        latest = data[-1]
        latest_indicators = TechnicalIndicators(
            rsi_14=float(latest.rsi_14) if latest.rsi_14 else None,
            macd=float(latest.macd) if latest.macd else None,
            macd_signal=float(latest.macd_signal) if latest.macd_signal else None,
            macd_hist=float(latest.macd_hist) if latest.macd_hist else None,
            bb_upper=float(latest.bb_upper) if latest.bb_upper else None,
            bb_middle=float(latest.bb_middle) if latest.bb_middle else None,
            bb_lower=float(latest.bb_lower) if latest.bb_lower else None,
            bb_width=float(latest.bb_width) if latest.bb_width else None,
            atr_14=float(latest.atr_14) if latest.atr_14 else None,
            ma_5=float(latest.ma_5) if latest.ma_5 else None,
            ma_10=float(latest.ma_10) if latest.ma_10 else None,
            ma_20=float(latest.ma_20) if latest.ma_20 else None,
            ma_50=float(latest.ma_50) if latest.ma_50 else None,
            ma_200=float(latest.ma_200) if latest.ma_200 else None,
            ema_12=float(latest.ema_12) if latest.ema_12 else None,
            ema_26=float(latest.ema_26) if latest.ema_26 else None,
            volume_sma_20=float(latest.volume_sma_20) if latest.volume_sma_20 else None,
            adx=float(latest.adx) if latest.adx else None,
            plus_di=float(latest.plus_di) if latest.plus_di else None,
            minus_di=float(latest.minus_di) if latest.minus_di else None,
            stoch_k=float(latest.stoch_k) if latest.stoch_k else None,
            stoch_d=float(latest.stoch_d) if latest.stoch_d else None,
        )

    return MarketDataResponse(
        symbol=symbol.upper(),
        interval=interval,
        data_source=data[0].data_source if data else "yfinance",
        candles=candles,
        latest_indicators=latest_indicators,
        start_date=data[0].date if data else None,
        end_date=data[-1].date if data else None,
        total_candles=len(candles),
    )


@router.get("/{symbol}/chart", response_model=CandlestickChartData)
async def get_chart_data(
    symbol: str = Path(..., description="Stock symbol"),
    days: int = Query(90, ge=7, le=365, description="Number of days"),
    include_trades: bool = Query(True, description="Include trade markers"),
    db: Session = Depends(get_db),
) -> CandlestickChartData:
    """
    Get candlestick chart data optimized for frontend rendering.

    Returns arrays of OHLCV data plus trade markers for the symbol.
    """
    start_date = date.today() - timedelta(days=days)

    # Get market data
    data = (
        db.query(MarketData)
        .filter(MarketData.symbol == symbol.upper())
        .filter(MarketData.interval == "1d")
        .filter(MarketData.date >= start_date)
        .order_by(MarketData.date)
        .all()
    )

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No chart data found for symbol {symbol}"
        )

    # Build arrays
    timestamps = [d.timestamp for d in data]
    opens = [float(d.open) if d.open else None for d in data]
    highs = [float(d.high) if d.high else None for d in data]
    lows = [float(d.low) if d.low else None for d in data]
    closes = [float(d.close) if d.close else 0.0 for d in data]
    volumes = [d.volume for d in data]

    # Indicator arrays
    ma_20 = [float(d.ma_20) if d.ma_20 else None for d in data]
    ma_50 = [float(d.ma_50) if d.ma_50 else None for d in data]
    bb_upper = [float(d.bb_upper) if d.bb_upper else None for d in data]
    bb_lower = [float(d.bb_lower) if d.bb_lower else None for d in data]

    # Get trade markers if requested
    buy_markers = []
    sell_markers = []

    if include_trades:
        positions = (
            db.query(Position)
            .filter(Position.symbol == symbol.upper())
            .filter(Position.open_date >= start_date)
            .all()
        )

        for p in positions:
            # Buy marker at open
            if p.open_date and p.open_price:
                buy_markers.append({
                    "date": p.open_time.isoformat() if p.open_time else p.open_date.isoformat(),
                    "price": float(p.open_price),
                    "position_id": p.id,
                })

            # Sell marker at close
            if p.close_date and p.close_price:
                sell_markers.append({
                    "date": p.close_time.isoformat() if p.close_time else p.close_date.isoformat(),
                    "price": float(p.close_price),
                    "position_id": p.id,
                })

    return CandlestickChartData(
        symbol=symbol.upper(),
        timestamps=timestamps,
        opens=opens,
        highs=highs,
        lows=lows,
        closes=closes,
        volumes=volumes,
        ma_20=ma_20,
        ma_50=ma_50,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        buy_markers=buy_markers,
        sell_markers=sell_markers,
    )


@router.get("/symbols/list", response_model=list[SymbolInfo])
async def list_symbols_with_data(
    db: Session = Depends(get_db),
) -> list[SymbolInfo]:
    """
    Get list of symbols that have market data available.
    """
    # Get unique symbols from market_data
    from sqlalchemy import func

    symbol_stats = (
        db.query(
            MarketData.symbol,
            func.min(MarketData.date).label("first_date"),
            func.max(MarketData.date).label("last_date"),
            func.count(MarketData.id).label("total_records"),
        )
        .filter(MarketData.interval == "1d")
        .group_by(MarketData.symbol)
        .order_by(MarketData.symbol)
        .all()
    )

    # Get symbol names from positions
    symbol_names = {}
    positions = db.query(Position.symbol, Position.symbol_name).distinct().all()
    for p in positions:
        if p.symbol and p.symbol_name:
            symbol_names[p.symbol] = p.symbol_name

    return [
        SymbolInfo(
            symbol=s.symbol,
            name=symbol_names.get(s.symbol),
            has_data=True,
            first_date=s.first_date,
            last_date=s.last_date,
            total_records=s.total_records,
        )
        for s in symbol_stats
    ]
