"""
Market Data API schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class OHLCVData(BaseModel):
    """OHLCV candle data"""
    timestamp: datetime
    date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: Optional[int] = None

    class Config:
        from_attributes = True


class TechnicalIndicators(BaseModel):
    """Technical indicators data"""
    # RSI
    rsi_14: Optional[float] = None

    # MACD
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None

    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None

    # ATR
    atr_14: Optional[float] = None

    # Moving Averages
    ma_5: Optional[float] = None
    ma_10: Optional[float] = None
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None

    # EMA
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

    # Volume indicator
    volume_sma_20: Optional[float] = None

    # ADX
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None

    # Stochastic
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None


class MarketDataPoint(OHLCVData):
    """Single market data point with indicators"""
    # Technical indicators
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    atr_14: Optional[float] = None
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    adx: Optional[float] = None


class MarketDataResponse(BaseModel):
    """Market data response for a symbol"""
    symbol: str
    interval: str = "1d"
    data_source: str = "yfinance"

    # OHLCV data
    candles: List[OHLCVData]

    # Latest indicators
    latest_indicators: Optional[TechnicalIndicators] = None

    # Metadata
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_candles: int


class MarketDataQueryParams(BaseModel):
    """Market data query parameters"""
    symbol: str = Field(..., description="Stock symbol")
    interval: str = Field(default="1d", description="Data interval: 1d, 1h, 5m, etc.")
    start_date: Optional[date] = Field(default=None, description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date")
    limit: int = Field(default=100, ge=1, le=500, description="Max candles to return")
    include_indicators: bool = Field(default=True, description="Include technical indicators")


class CandlestickChartData(BaseModel):
    """Candlestick chart data for frontend"""
    symbol: str

    # OHLCV arrays for Plotly
    timestamps: List[datetime]
    opens: List[Optional[float]]
    highs: List[Optional[float]]
    lows: List[Optional[float]]
    closes: List[float]
    volumes: List[Optional[int]]

    # Indicator arrays
    ma_20: List[Optional[float]] = []
    ma_50: List[Optional[float]] = []
    bb_upper: List[Optional[float]] = []
    bb_lower: List[Optional[float]] = []

    # Trade markers for this symbol
    buy_markers: List[dict] = []  # [{date, price, position_id}]
    sell_markers: List[dict] = []  # [{date, price, position_id}]


class SymbolInfo(BaseModel):
    """Symbol information"""
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    is_option: bool = False
    underlying_symbol: Optional[str] = None

    # Data availability
    has_data: bool = False
    first_date: Optional[date] = None
    last_date: Optional[date] = None
    total_records: int = 0
