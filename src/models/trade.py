"""
Trade model - 交易记录表
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    ForeignKey, Index, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class TradeDirection(enum.Enum):
    """交易方向枚举"""
    BUY = "buy"  # 买入（做多开仓）
    SELL = "sell"  # 卖出（做多平仓）
    SELL_SHORT = "sell_short"  # 卖空（做空开仓）
    BUY_TO_COVER = "buy_to_cover"  # 买入回补（做空平仓）


class TradeStatus(enum.Enum):
    """交易状态枚举"""
    FILLED = "filled"  # 完全成交
    PARTIALLY_FILLED = "partially_filled"  # 部分成交
    CANCELLED = "cancelled"  # 已撤单
    PENDING = "pending"  # 待成交


class MarketType(enum.Enum):
    """市场类型枚举"""
    US_STOCK = "美股"
    HK_STOCK = "港股"
    CN_STOCK = "沪深"


class Trade(Base):
    """
    交易记录表

    记录每一笔交易的详细信息，包括订单信息、成交信息、费用等
    """
    __tablename__ = 'trades'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 基本信息 ====================
    symbol = Column(String(50), nullable=False, index=True, comment="股票代码")
    symbol_name = Column(String(200), comment="股票名称")

    # 交易方向和状态
    direction = Column(
        SQLEnum(TradeDirection),
        nullable=False,
        comment="交易方向"
    )
    status = Column(
        SQLEnum(TradeStatus),
        nullable=False,
        default=TradeStatus.FILLED,
        comment="交易状态"
    )

    # ==================== 订单信息 ====================
    order_price = Column(Numeric(15, 4), comment="订单价格")
    order_quantity = Column(Integer, comment="订单数量")
    order_amount = Column(Numeric(20, 2), comment="订单金额")
    order_time = Column(DateTime, comment="下单时间（UTC）")
    order_type = Column(String(50), comment="订单类型（限价/市价等）")

    # ==================== 成交信息 ====================
    filled_price = Column(Numeric(15, 4), comment="成交价格")
    filled_quantity = Column(Integer, nullable=False, comment="成交数量")
    filled_amount = Column(Numeric(20, 2), comment="成交金额")
    filled_time = Column(DateTime, nullable=False, index=True, comment="成交时间（UTC）")

    # 交易日期（生成列，用于快速查询）
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期（UTC）")

    # ==================== 市场信息 ====================
    market = Column(
        SQLEnum(MarketType),
        nullable=False,
        comment="市场类型"
    )
    currency = Column(String(10), default="USD", comment="币种")

    # ==================== 费用明细 ====================
    commission = Column(Numeric(10, 2), comment="佣金")
    platform_fee = Column(Numeric(10, 2), comment="平台使用费")
    clearing_fee = Column(Numeric(10, 2), comment="交收费/清算费")
    transaction_fee = Column(Numeric(10, 2), comment="交易费")
    stamp_duty = Column(Numeric(10, 2), comment="印花税（港股）")
    sec_fee = Column(Numeric(10, 2), comment="证监会征费")
    option_regulatory_fee = Column(Numeric(10, 2), comment="期权监管费")
    option_clearing_fee = Column(Numeric(10, 2), comment="期权清算费")
    total_fee = Column(Numeric(10, 2), nullable=False, comment="合计费用")

    # ==================== 期权/衍生品信息 ====================
    underlying_symbol = Column(String(50), index=True, comment="标的股票代码（期权/窝轮）")
    is_option = Column(Integer, default=0, comment="是否为期权/窝轮（0/1）")
    option_type = Column(String(10), comment="期权类型（CALL/PUT）")
    strike_price = Column(Numeric(15, 4), comment="行权价")
    expiration_date = Column(Date, comment="到期日")

    # ==================== 关联字段 ====================
    matched_trade_id = Column(
        Integer,
        ForeignKey('trades.id'),
        comment="配对的交易ID（开仓对应的平仓）"
    )
    position_id = Column(
        Integer,
        ForeignKey('positions.id'),
        comment="所属持仓ID"
    )
    market_data_id = Column(
        Integer,
        ForeignKey('market_data.id'),
        comment="关联的市场数据ID"
    )
    market_env_id = Column(
        Integer,
        ForeignKey('market_environment.id'),
        comment="关联的市场环境ID"
    )

    # ==================== 元数据和备注 ====================
    metadata_json = Column(
        JSON,
        comment="额外元数据（JSON格式）"
    )
    notes = Column(String(500), comment="备注")

    # 原始CSV数据（用于调试）
    raw_data = Column(JSON, comment="原始CSV行数据")

    # ==================== 时间戳 ====================
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        comment="记录创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="记录更新时间"
    )

    # ==================== 关系定义 ====================
    # 配对交易（自引用）
    matched_trade = relationship(
        "Trade",
        remote_side=[id],
        foreign_keys=[matched_trade_id],
        backref="matching_trades"
    )

    # 所属持仓
    position = relationship(
        "Position",
        foreign_keys=[position_id],
        back_populates="trades"
    )

    # 市场数据
    market_data = relationship(
        "MarketData",
        foreign_keys=[market_data_id]
    )

    # 市场环境
    market_environment = relationship(
        "MarketEnvironment",
        foreign_keys=[market_env_id]
    )

    # ==================== 索引 ====================
    __table_args__ = (
        # 复合索引：按symbol和时间查询
        Index('idx_symbol_filled_time', 'symbol', 'filled_time'),
        Index('idx_symbol_trade_date', 'symbol', 'trade_date'),

        # 期权查询索引
        Index('idx_underlying_symbol_time', 'underlying_symbol', 'filled_time'),

        # 状态查询索引
        Index('idx_direction_status', 'direction', 'status'),

        # 市场类型查询
        Index('idx_market_trade_date', 'market', 'trade_date'),
    )

    def __repr__(self):
        return (
            f"<Trade(id={self.id}, symbol={self.symbol}, "
            f"direction={self.direction.value if self.direction else None}, "
            f"quantity={self.filled_quantity}, "
            f"price={self.filled_price}, "
            f"time={self.filled_time})>"
        )

    @property
    def is_opening_trade(self):
        """是否为开仓交易"""
        return self.direction in [TradeDirection.BUY, TradeDirection.SELL_SHORT]

    @property
    def is_closing_trade(self):
        """是否为平仓交易"""
        return self.direction in [TradeDirection.SELL, TradeDirection.BUY_TO_COVER]

    @property
    def is_long(self):
        """是否为做多"""
        return self.direction in [TradeDirection.BUY, TradeDirection.SELL]

    @property
    def is_short(self):
        """是否为做空"""
        return self.direction in [TradeDirection.SELL_SHORT, TradeDirection.BUY_TO_COVER]

    @property
    def is_partial_fill(self):
        """是否为部分成交"""
        return (
            self.order_quantity is not None and
            self.filled_quantity is not None and
            self.filled_quantity < self.order_quantity
        )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'symbol_name': self.symbol_name,
            'direction': self.direction.value if self.direction else None,
            'status': self.status.value if self.status else None,
            'filled_price': float(self.filled_price) if self.filled_price else None,
            'filled_quantity': self.filled_quantity,
            'filled_amount': float(self.filled_amount) if self.filled_amount else None,
            'filled_time': self.filled_time.isoformat() if self.filled_time else None,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'market': self.market.value if self.market else None,
            'currency': self.currency,
            'total_fee': float(self.total_fee) if self.total_fee else None,
            'underlying_symbol': self.underlying_symbol,
            'is_option': bool(self.is_option),
            'position_id': self.position_id,
        }
