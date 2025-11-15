"""
MarketData model - 市场行情数据表
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    Index, UniqueConstraint
)
from datetime import datetime

from .base import Base


class MarketData(Base):
    """
    市场行情数据表

    存储OHLCV数据和预计算的技术指标，用于缓存减少API调用
    """
    __tablename__ = 'market_data'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 基本信息 ====================
    symbol = Column(String(50), nullable=False, index=True, comment="股票代码")
    timestamp = Column(DateTime, nullable=False, comment="时间戳（UTC）")
    date = Column(Date, nullable=False, index=True, comment="日期")

    # 时间粒度（'1d', '1h', '5m'等）
    interval = Column(String(10), default='1d', comment="时间粒度")

    # ==================== OHLCV数据 ====================
    open = Column(Numeric(15, 4), comment="开盘价")
    high = Column(Numeric(15, 4), comment="最高价")
    low = Column(Numeric(15, 4), comment="最低价")
    close = Column(Numeric(15, 4), nullable=False, comment="收盘价")
    volume = Column(Integer, comment="成交量")

    # 成交额
    turnover = Column(Numeric(20, 2), comment="成交额")

    # ==================== 技术指标（预计算缓存） ====================
    # RSI
    rsi_14 = Column(Numeric(6, 2), comment="RSI(14)")

    # MACD
    macd = Column(Numeric(10, 4), comment="MACD")
    macd_signal = Column(Numeric(10, 4), comment="MACD信号线")
    macd_hist = Column(Numeric(10, 4), comment="MACD柱状图")

    # Bollinger Bands
    bb_upper = Column(Numeric(15, 4), comment="布林带上轨")
    bb_middle = Column(Numeric(15, 4), comment="布林带中轨")
    bb_lower = Column(Numeric(15, 4), comment="布林带下轨")
    bb_width = Column(Numeric(10, 4), comment="布林带宽度")

    # ATR
    atr_14 = Column(Numeric(10, 4), comment="ATR(14)")

    # Moving Averages
    ma_5 = Column(Numeric(15, 4), comment="MA5")
    ma_10 = Column(Numeric(15, 4), comment="MA10")
    ma_20 = Column(Numeric(15, 4), comment="MA20")
    ma_50 = Column(Numeric(15, 4), comment="MA50")
    ma_200 = Column(Numeric(15, 4), comment="MA200")

    # EMA
    ema_12 = Column(Numeric(15, 4), comment="EMA12")
    ema_26 = Column(Numeric(15, 4), comment="EMA26")

    # Volume指标
    volume_sma_20 = Column(Numeric(20, 2), comment="成交量20日均线")

    # ADX (Average Directional Index)
    adx = Column(Numeric(6, 2), comment="ADX趋势强度指标")
    plus_di = Column(Numeric(6, 2), comment="+DI")
    minus_di = Column(Numeric(6, 2), comment="-DI")

    # Stochastic
    stoch_k = Column(Numeric(6, 2), comment="Stochastic %K")
    stoch_d = Column(Numeric(6, 2), comment="Stochastic %D")

    # ==================== 期权相关数据 ====================
    # Greeks (如果是期权)
    delta = Column(Numeric(8, 6), comment="Delta")
    gamma = Column(Numeric(8, 6), comment="Gamma")
    theta = Column(Numeric(8, 6), comment="Theta")
    vega = Column(Numeric(8, 6), comment="Vega")
    rho = Column(Numeric(8, 6), comment="Rho")

    # 隐含波动率
    implied_volatility = Column(Numeric(8, 4), comment="隐含波动率")

    # ==================== 元数据 ====================
    data_source = Column(
        String(50),
        default='yfinance',
        comment="数据来源（yfinance/alpha_vantage/polygon）"
    )

    # 数据质量标记
    is_adjusted = Column(Integer, default=1, comment="是否复权（1=是，0=否）")
    data_quality = Column(String(20), comment="数据质量（good/partial/bad）")

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

    # ==================== 约束和索引 ====================
    __table_args__ = (
        # 唯一约束：同一symbol在同一时间点只有一条记录
        UniqueConstraint('symbol', 'timestamp', 'interval', name='uq_symbol_timestamp_interval'),

        # 复合索引：常用查询优化
        Index('idx_md_symbol_date', 'symbol', 'date'),
        Index('idx_md_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_md_date', 'date'),

        # 数据源索引
        Index('idx_md_data_source', 'data_source'),
    )

    def __repr__(self):
        return (
            f"<MarketData(symbol={self.symbol}, "
            f"date={self.date}, "
            f"close={self.close}, "
            f"source={self.data_source})>"
        )

    @property
    def has_indicators(self):
        """是否已计算技术指标"""
        return self.rsi_14 is not None or self.macd is not None

    @property
    def price_change(self):
        """价格变动"""
        if self.open and self.close:
            return self.close - self.open
        return None

    @property
    def price_change_pct(self):
        """价格变动百分比"""
        if self.open and self.close and self.open > 0:
            return ((self.close - self.open) / self.open) * 100
        return None

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'date': self.date.isoformat() if self.date else None,
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': self.volume,
            'rsi_14': float(self.rsi_14) if self.rsi_14 else None,
            'macd': float(self.macd) if self.macd else None,
            'bb_upper': float(self.bb_upper) if self.bb_upper else None,
            'bb_middle': float(self.bb_middle) if self.bb_middle else None,
            'bb_lower': float(self.bb_lower) if self.bb_lower else None,
            'atr_14': float(self.atr_14) if self.atr_14 else None,
            'ma_20': float(self.ma_20) if self.ma_20 else None,
            'ma_50': float(self.ma_50) if self.ma_50 else None,
            'adx': float(self.adx) if self.adx else None,
            'data_source': self.data_source,
        }
