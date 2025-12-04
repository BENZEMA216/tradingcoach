"""
Trade API schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from enum import Enum


class TradeDirectionEnum(str, Enum):
    """Trade direction enum"""
    BUY = "buy"
    SELL = "sell"
    SELL_SHORT = "sell_short"
    BUY_TO_COVER = "buy_to_cover"


class TradeStatusEnum(str, Enum):
    """Trade status enum"""
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    PENDING = "pending"


class MarketTypeEnum(str, Enum):
    """Market type enum"""
    US_STOCK = "美股"
    HK_STOCK = "港股"
    CN_STOCK = "沪深"


class TradeListItem(BaseModel):
    """Trade item for list view"""
    id: int
    symbol: str
    symbol_name: Optional[str] = None
    direction: str
    status: str

    # Execution info
    filled_price: Optional[float] = None
    filled_quantity: int
    filled_amount: Optional[float] = None
    filled_time: datetime
    trade_date: date

    # Market info
    market: str
    currency: str = "USD"

    # Fees
    total_fee: float

    # Option info
    is_option: bool = False
    underlying_symbol: Optional[str] = None

    # Position link
    position_id: Optional[int] = None

    class Config:
        from_attributes = True


class TradeDetail(BaseModel):
    """Full trade detail"""
    id: int
    symbol: str
    symbol_name: Optional[str] = None
    direction: str
    status: str

    # Order info
    order_price: Optional[float] = None
    order_quantity: Optional[int] = None
    order_amount: Optional[float] = None
    order_time: Optional[datetime] = None
    order_type: Optional[str] = None

    # Execution info
    filled_price: Optional[float] = None
    filled_quantity: int
    filled_amount: Optional[float] = None
    filled_time: datetime
    trade_date: date

    # Market info
    market: str
    currency: str = "USD"

    # Fee breakdown
    commission: Optional[float] = None
    platform_fee: Optional[float] = None
    clearing_fee: Optional[float] = None
    transaction_fee: Optional[float] = None
    stamp_duty: Optional[float] = None
    sec_fee: Optional[float] = None
    option_regulatory_fee: Optional[float] = None
    option_clearing_fee: Optional[float] = None
    total_fee: float

    # Option info
    is_option: bool = False
    underlying_symbol: Optional[str] = None
    option_type: Optional[str] = None
    strike_price: Optional[float] = None
    expiration_date: Optional[date] = None

    # Position link
    position_id: Optional[int] = None
    matched_trade_id: Optional[int] = None

    # Notes
    notes: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TradeFilterParams(BaseModel):
    """Trade filter parameters"""
    symbol: Optional[str] = None
    direction: Optional[TradeDirectionEnum] = None
    status: Optional[TradeStatusEnum] = None
    market: Optional[MarketTypeEnum] = None

    # Date range
    date_start: Optional[date] = None
    date_end: Optional[date] = None

    # Option filter
    is_option: Optional[bool] = None
    underlying_symbol: Optional[str] = None

    # Position filter
    position_id: Optional[int] = None
    has_position: Optional[bool] = None


class TradeSummary(BaseModel):
    """Trade summary statistics"""
    total_trades: int
    buy_trades: int
    sell_trades: int

    # Volume
    total_volume: int
    total_amount: float

    # Fees
    total_fees: float
    avg_fee_per_trade: float

    # Options vs stocks
    stock_trades: int
    option_trades: int
