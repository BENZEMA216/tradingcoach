"""
MarketEnvironment model - 市场环境数据表
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, Date,
    Index, JSON
)
from datetime import datetime
from sqlalchemy import DateTime

from .base import Base


class MarketEnvironment(Base):
    """
    市场环境数据表

    记录每日的大盘指数、波动率、市场趋势等环境信息
    """
    __tablename__ = 'market_environment'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 日期 ====================
    date = Column(Date, nullable=False, unique=True, index=True, comment="日期")

    # ==================== 大盘指数 ====================
    # 美股指数
    spy_close = Column(Numeric(10, 2), comment="S&P 500 ETF收盘价")
    spy_change_pct = Column(Numeric(6, 2), comment="SPY涨跌幅%")

    qqq_close = Column(Numeric(10, 2), comment="纳斯达克100 ETF收盘价")
    qqq_change_pct = Column(Numeric(6, 2), comment="QQQ涨跌幅%")

    dia_close = Column(Numeric(10, 2), comment="道琼斯ETF收盘价")
    dia_change_pct = Column(Numeric(6, 2), comment="DIA涨跌幅%")

    # 港股指数
    hsi_close = Column(Numeric(10, 2), comment="恒生指数收盘点位")
    hsi_change_pct = Column(Numeric(6, 2), comment="恒指涨跌幅%")

    # 沪深指数
    sh_close = Column(Numeric(10, 2), comment="上证指数收盘点位")
    sh_change_pct = Column(Numeric(6, 2), comment="上证涨跌幅%")

    sz_close = Column(Numeric(10, 2), comment="深证成指收盘点位")
    sz_change_pct = Column(Numeric(6, 2), comment="深证涨跌幅%")

    # ==================== 波动率指标 ====================
    vix = Column(Numeric(6, 2), comment="VIX恐慌指数")
    vix_level = Column(
        String(20),
        comment="VIX水平（low/medium/high/extreme）"
    )

    # 历史波动率
    spy_hv_20 = Column(Numeric(6, 2), comment="SPY 20日历史波动率")
    spy_hv_60 = Column(Numeric(6, 2), comment="SPY 60日历史波动率")

    # ==================== 市场趋势判断 ====================
    market_trend = Column(
        String(50),
        comment="市场趋势（strong_bullish/bullish/neutral/bearish/strong_bearish）"
    )

    # 均线排列
    ma20_above_ma50 = Column(Integer, comment="MA20是否在MA50之上（1/0）")
    ma50_above_ma200 = Column(Integer, comment="MA50是否在MA200之上（1/0）")

    # 市场宽度指标
    advance_decline_ratio = Column(
        Numeric(6, 2),
        comment="涨跌家数比（上涨/下跌）"
    )

    # ==================== 行业强弱 ====================
    # JSON格式存储各行业ETF的涨跌幅
    sector_performance = Column(
        JSON,
        comment='行业表现 {"XLK": 1.5, "XLF": -0.3, ...}'
    )

    # 领涨板块
    leading_sectors = Column(String(200), comment="领涨板块（逗号分隔）")
    lagging_sectors = Column(String(200), comment="落后板块（逗号分隔）")

    # ==================== 资金流向 ====================
    # 资金净流入
    spy_money_flow = Column(Numeric(15, 2), comment="SPY资金流量")

    # 看涨看跌比
    put_call_ratio = Column(Numeric(6, 4), comment="Put/Call Ratio")

    # ==================== 经济数据（可选） ====================
    # 美债收益率
    us_10y_yield = Column(Numeric(6, 4), comment="美国10年期国债收益率%")
    us_2y_yield = Column(Numeric(6, 4), comment="美国2年期国债收益率%")

    # 美元指数
    dxy = Column(Numeric(8, 2), comment="美元指数")

    # 黄金价格
    gold_price = Column(Numeric(10, 2), comment="黄金价格（美元/盎司）")

    # ==================== 情绪指标 ====================
    market_sentiment = Column(
        String(20),
        comment="市场情绪（extreme_greed/greed/neutral/fear/extreme_fear）"
    )

    # Fear & Greed Index (0-100)
    fear_greed_index = Column(Integer, comment="恐惧贪婪指数(0-100)")

    # ==================== 重大事件标记 ====================
    has_major_event = Column(Integer, default=0, comment="是否有重大事件（1/0）")
    event_description = Column(String(500), comment="事件描述")

    # ==================== 元数据 ====================
    data_source = Column(
        String(50),
        default='yfinance',
        comment="数据来源"
    )

    data_completeness = Column(
        Numeric(5, 2),
        comment="数据完整度百分比"
    )

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

    # ==================== 索引 ====================
    __table_args__ = (
        # 按日期查询（已有unique index）
        Index('idx_me_date', 'date'),

        # 按趋势查询
        Index('idx_me_market_trend', 'market_trend'),

        # 按VIX水平查询
        Index('idx_me_vix_level', 'vix_level'),
    )

    def __repr__(self):
        return (
            f"<MarketEnvironment(date={self.date}, "
            f"spy_change={self.spy_change_pct}%, "
            f"vix={self.vix}, "
            f"trend={self.market_trend})>"
        )

    @property
    def is_bullish(self):
        """是否牛市"""
        return self.market_trend in ['bullish', 'strong_bullish']

    @property
    def is_bearish(self):
        """是否熊市"""
        return self.market_trend in ['bearish', 'strong_bearish']

    @property
    def is_high_volatility(self):
        """是否高波动"""
        return self.vix_level in ['high', 'extreme']

    def determine_vix_level(self):
        """判断VIX水平"""
        if self.vix is None:
            return

        vix_value = float(self.vix)
        if vix_value < 12:
            self.vix_level = 'low'
        elif vix_value < 20:
            self.vix_level = 'medium'
        elif vix_value < 30:
            self.vix_level = 'high'
        else:
            self.vix_level = 'extreme'

    def determine_market_trend(self):
        """判断市场趋势"""
        if self.spy_change_pct is None:
            return

        # 简化版本：基于SPY涨跌幅和MA排列
        spy_change = float(self.spy_change_pct)

        if spy_change > 1.5 and self.ma20_above_ma50:
            self.market_trend = 'strong_bullish'
        elif spy_change > 0.5:
            self.market_trend = 'bullish'
        elif spy_change < -1.5 and not self.ma20_above_ma50:
            self.market_trend = 'strong_bearish'
        elif spy_change < -0.5:
            self.market_trend = 'bearish'
        else:
            self.market_trend = 'neutral'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'spy_close': float(self.spy_close) if self.spy_close else None,
            'spy_change_pct': float(self.spy_change_pct) if self.spy_change_pct else None,
            'vix': float(self.vix) if self.vix else None,
            'vix_level': self.vix_level,
            'market_trend': self.market_trend,
            'sector_performance': self.sector_performance,
            'fear_greed_index': self.fear_greed_index,
        }
