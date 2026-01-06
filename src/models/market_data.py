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

    # ==================== 成交量分析指标 ====================
    # OBV (On Balance Volume)
    obv = Column(Numeric(20, 2), comment="OBV能量潮")

    # VWAP (Volume Weighted Average Price)
    vwap = Column(Numeric(15, 4), comment="成交量加权平均价")

    # MFI (Money Flow Index)
    mfi_14 = Column(Numeric(6, 2), comment="MFI资金流量指标(14)")

    # A/D Line (Accumulation/Distribution)
    ad_line = Column(Numeric(20, 2), comment="A/D累积分布线")

    # CMF (Chaikin Money Flow)
    cmf_20 = Column(Numeric(8, 4), comment="CMF蔡金资金流(20)")

    # Volume Ratio
    volume_ratio = Column(Numeric(8, 2), comment="成交量比率")

    # ==================== 动量指标补充 ====================
    # CCI (Commodity Channel Index)
    cci_20 = Column(Numeric(8, 2), comment="CCI商品通道指数(20)")

    # Williams %R
    willr_14 = Column(Numeric(8, 2), comment="威廉指标(14)")

    # ROC (Rate of Change)
    roc_12 = Column(Numeric(10, 4), comment="变动率(12)")

    # Momentum
    mom_10 = Column(Numeric(10, 4), comment="动量指标(10)")

    # Ultimate Oscillator
    uo = Column(Numeric(6, 2), comment="终极震荡指标")

    # RSI Divergence Signal (-1, 0, 1)
    rsi_div = Column(Integer, comment="RSI背离信号(-1熊/0无/1牛)")

    # ==================== 波动率指标补充 ====================
    # Keltner Channel
    kc_upper = Column(Numeric(15, 4), comment="肯特纳通道上轨")
    kc_middle = Column(Numeric(15, 4), comment="肯特纳通道中轨")
    kc_lower = Column(Numeric(15, 4), comment="肯特纳通道下轨")

    # Donchian Channel
    dc_upper = Column(Numeric(15, 4), comment="唐奇安通道上轨(20)")
    dc_lower = Column(Numeric(15, 4), comment="唐奇安通道下轨(20)")

    # Historical Volatility
    hvol_20 = Column(Numeric(8, 4), comment="20日历史波动率")

    # ATR Percentage
    atr_pct = Column(Numeric(8, 4), comment="ATR百分比")

    # Bollinger Squeeze
    bb_squeeze = Column(Integer, comment="布林挤压信号(1=挤压中/0=释放)")

    # Volatility Rank (0-100)
    vol_rank = Column(Numeric(6, 2), comment="波动率排名(0-100)")

    # ==================== 趋势指标补充 ====================
    # Ichimoku Cloud (一目均衡图)
    ichi_tenkan = Column(Numeric(15, 4), comment="转换线(9)")
    ichi_kijun = Column(Numeric(15, 4), comment="基准线(26)")
    ichi_senkou_a = Column(Numeric(15, 4), comment="先行带A")
    ichi_senkou_b = Column(Numeric(15, 4), comment="先行带B")
    ichi_chikou = Column(Numeric(15, 4), comment="迟行线")

    # Parabolic SAR
    psar = Column(Numeric(15, 4), comment="抛物线SAR")
    psar_dir = Column(Integer, comment="SAR方向(1多/-1空)")

    # SuperTrend
    supertrend = Column(Numeric(15, 4), comment="超级趋势")
    supertrend_dir = Column(Integer, comment="SuperTrend方向(1多/-1空)")

    # TRIX
    trix = Column(Numeric(10, 4), comment="TRIX三重指数平滑")

    # DPO (Detrended Price Oscillator)
    dpo = Column(Numeric(10, 4), comment="去趋势价格振荡器")

    # ==================== 期权相关数据 ====================
    # Greeks (如果是期权)
    delta = Column(Numeric(8, 6), comment="Delta")
    gamma = Column(Numeric(8, 6), comment="Gamma")
    theta = Column(Numeric(8, 6), comment="Theta")
    vega = Column(Numeric(8, 6), comment="Vega")
    rho = Column(Numeric(8, 6), comment="Rho")

    # 隐含波动率
    implied_volatility = Column(Numeric(8, 4), comment="隐含波动率")

    # IV Rank / IV Percentile
    iv_rank = Column(Numeric(6, 2), comment="IV排名(0-100)")
    iv_percentile = Column(Numeric(6, 2), comment="IV百分位(0-100)")

    # Put/Call Ratio
    pcr = Column(Numeric(8, 4), comment="看跌/看涨比率")

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
        def safe_float(val):
            return float(val) if val is not None else None

        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'date': self.date.isoformat() if self.date else None,
            # OHLCV
            'open': safe_float(self.open),
            'high': safe_float(self.high),
            'low': safe_float(self.low),
            'close': safe_float(self.close),
            'volume': self.volume,
            # 原有指标
            'rsi_14': safe_float(self.rsi_14),
            'macd': safe_float(self.macd),
            'macd_signal': safe_float(self.macd_signal),
            'macd_hist': safe_float(self.macd_hist),
            'bb_upper': safe_float(self.bb_upper),
            'bb_middle': safe_float(self.bb_middle),
            'bb_lower': safe_float(self.bb_lower),
            'bb_width': safe_float(self.bb_width),
            'atr_14': safe_float(self.atr_14),
            'ma_5': safe_float(self.ma_5),
            'ma_10': safe_float(self.ma_10),
            'ma_20': safe_float(self.ma_20),
            'ma_50': safe_float(self.ma_50),
            'ma_200': safe_float(self.ma_200),
            'ema_12': safe_float(self.ema_12),
            'ema_26': safe_float(self.ema_26),
            'adx': safe_float(self.adx),
            'plus_di': safe_float(self.plus_di),
            'minus_di': safe_float(self.minus_di),
            'stoch_k': safe_float(self.stoch_k),
            'stoch_d': safe_float(self.stoch_d),
            'volume_sma_20': safe_float(self.volume_sma_20),
            # 成交量指标
            'obv': safe_float(self.obv),
            'vwap': safe_float(self.vwap),
            'mfi_14': safe_float(self.mfi_14),
            'ad_line': safe_float(self.ad_line),
            'cmf_20': safe_float(self.cmf_20),
            'volume_ratio': safe_float(self.volume_ratio),
            # 动量指标
            'cci_20': safe_float(self.cci_20),
            'willr_14': safe_float(self.willr_14),
            'roc_12': safe_float(self.roc_12),
            'mom_10': safe_float(self.mom_10),
            'uo': safe_float(self.uo),
            'rsi_div': self.rsi_div,
            # 波动率指标
            'kc_upper': safe_float(self.kc_upper),
            'kc_middle': safe_float(self.kc_middle),
            'kc_lower': safe_float(self.kc_lower),
            'dc_upper': safe_float(self.dc_upper),
            'dc_lower': safe_float(self.dc_lower),
            'hvol_20': safe_float(self.hvol_20),
            'atr_pct': safe_float(self.atr_pct),
            'bb_squeeze': self.bb_squeeze,
            'vol_rank': safe_float(self.vol_rank),
            # 趋势指标
            'ichi_tenkan': safe_float(self.ichi_tenkan),
            'ichi_kijun': safe_float(self.ichi_kijun),
            'ichi_senkou_a': safe_float(self.ichi_senkou_a),
            'ichi_senkou_b': safe_float(self.ichi_senkou_b),
            'ichi_chikou': safe_float(self.ichi_chikou),
            'psar': safe_float(self.psar),
            'psar_dir': self.psar_dir,
            'supertrend': safe_float(self.supertrend),
            'supertrend_dir': self.supertrend_dir,
            'trix': safe_float(self.trix),
            'dpo': safe_float(self.dpo),
            # 期权指标
            'delta': safe_float(self.delta),
            'gamma': safe_float(self.gamma),
            'theta': safe_float(self.theta),
            'vega': safe_float(self.vega),
            'implied_volatility': safe_float(self.implied_volatility),
            'iv_rank': safe_float(self.iv_rank),
            'iv_percentile': safe_float(self.iv_percentile),
            'pcr': safe_float(self.pcr),
            # 元数据
            'data_source': self.data_source,
        }
