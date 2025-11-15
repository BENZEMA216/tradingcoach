"""
StockClassification model - 股票分类表
"""

from sqlalchemy import (
    Column, Integer, String, BigInteger, Numeric, Date,
    Index, DateTime
)
from datetime import datetime

from .base import Base


class StockClassification(Base):
    """
    股票分类表

    存储股票的基本信息、行业分类、市值等数据
    """
    __tablename__ = 'stock_classifications'

    # ==================== 主键 ====================
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ==================== 基本信息 ====================
    symbol = Column(String(50), nullable=False, unique=True, index=True, comment="股票代码")
    company_name = Column(String(200), comment="公司全称")
    short_name = Column(String(100), comment="公司简称")

    # ==================== 行业分类 ====================
    # GICS分类（Global Industry Classification Standard）
    sector = Column(String(100), index=True, comment="行业板块（一级）")
    industry_group = Column(String(100), comment="行业组（二级）")
    industry = Column(String(100), index=True, comment="行业（三级）")
    sub_industry = Column(String(100), comment="子行业（四级）")

    # ==================== 地理信息 ====================
    country = Column(String(50), comment="所属国家/地区")
    exchange = Column(String(50), comment="交易所（NYSE/NASDAQ/HKEX）")
    market_type = Column(String(20), comment="市场类型（美股/港股/沪深）")

    # ==================== 市值信息 ====================
    market_cap = Column(BigInteger, comment="市值（单位：美元或港币）")
    market_cap_usd = Column(BigInteger, comment="市值（统一为美元）")

    # 市值分类
    cap_category = Column(
        String(20),
        comment="市值分类（mega/large/mid/small/micro）"
    )

    # ==================== 估值指标 ====================
    pe_ratio = Column(Numeric(10, 2), comment="市盈率（TTM）")
    forward_pe = Column(Numeric(10, 2), comment="远期市盈率")
    pb_ratio = Column(Numeric(10, 2), comment="市净率")
    ps_ratio = Column(Numeric(10, 2), comment="市销率")

    # ==================== 财务指标 ====================
    revenue = Column(BigInteger, comment="营收（TTM）")
    revenue_growth = Column(Numeric(8, 2), comment="营收增长率%")

    net_income = Column(BigInteger, comment="净利润（TTM）")
    profit_margin = Column(Numeric(8, 2), comment="净利润率%")

    eps = Column(Numeric(10, 4), comment="每股收益（EPS）")
    book_value_per_share = Column(Numeric(10, 4), comment="每股账面价值")

    # ROE & ROA
    roe = Column(Numeric(8, 2), comment="净资产收益率%")
    roa = Column(Numeric(8, 2), comment="总资产收益率%")

    # ==================== 分红信息 ====================
    dividend_yield = Column(Numeric(6, 2), comment="股息率%")
    dividend_rate = Column(Numeric(10, 4), comment="每股分红")
    payout_ratio = Column(Numeric(6, 2), comment="派息比率%")

    # ==================== 财报日历 ====================
    next_earnings_date = Column(Date, comment="下次财报日期")
    last_earnings_date = Column(Date, comment="上次财报日期")
    fiscal_year_end = Column(String(10), comment="财年结束月份")

    # ==================== 股票特征 ====================
    # 流动性
    avg_volume_3m = Column(BigInteger, comment="3个月平均成交量")
    avg_volume_10d = Column(BigInteger, comment="10日平均成交量")

    # 波动性
    beta = Column(Numeric(6, 2), comment="Beta系数（相对大盘）")
    volatility_52w = Column(Numeric(6, 2), comment="52周波动率%")

    # 价格范围
    week_52_high = Column(Numeric(15, 4), comment="52周最高价")
    week_52_low = Column(Numeric(15, 4), comment="52周最低价")

    # ==================== 公司描述 ====================
    business_summary = Column(String(2000), comment="业务简介")
    website = Column(String(200), comment="公司网站")

    # ==================== 元数据 ====================
    data_source = Column(
        String(50),
        default='yfinance',
        comment="数据来源"
    )

    # 币种
    currency = Column(String(10), comment="报价币种")

    # ==================== 时间戳 ====================
    last_updated = Column(Date, comment="数据最后更新日期")

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
        # 按行业查询
        Index('idx_sc_sector', 'sector'),
        Index('idx_sc_industry', 'industry'),

        # 按市值查询
        Index('idx_sc_market_cap', 'market_cap_usd'),
        Index('idx_sc_cap_category', 'cap_category'),

        # 按国家查询
        Index('idx_sc_country', 'country'),

        # 按交易所查询
        Index('idx_sc_exchange', 'exchange'),
    )

    def __repr__(self):
        return (
            f"<StockClassification(symbol={self.symbol}, "
            f"company={self.company_name}, "
            f"sector={self.sector}, "
            f"cap_category={self.cap_category})>"
        )

    def determine_cap_category(self):
        """判断市值分类"""
        if self.market_cap_usd is None:
            return

        cap = self.market_cap_usd / 1_000_000_000  # 转换为十亿美元

        if cap >= 200:
            self.cap_category = 'mega'  # 超大盘（≥2000亿）
        elif cap >= 10:
            self.cap_category = 'large'  # 大盘（100亿-2000亿）
        elif cap >= 2:
            self.cap_category = 'mid'  # 中盘（20亿-100亿）
        elif cap >= 0.3:
            self.cap_category = 'small'  # 小盘（3亿-20亿）
        else:
            self.cap_category = 'micro'  # 微盘（<3亿）

    @property
    def is_mega_cap(self):
        """是否超大盘股"""
        return self.cap_category == 'mega'

    @property
    def is_large_cap(self):
        """是否大盘股"""
        return self.cap_category in ['mega', 'large']

    @property
    def is_growth_stock(self):
        """是否成长股（简单判断）"""
        return (
            self.revenue_growth is not None and
            self.revenue_growth > 15 and
            self.pe_ratio is not None and
            self.pe_ratio > 25
        )

    @property
    def is_value_stock(self):
        """是否价值股（简单判断）"""
        return (
            self.pe_ratio is not None and
            self.pe_ratio < 15 and
            self.dividend_yield is not None and
            self.dividend_yield > 2
        )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'company_name': self.company_name,
            'sector': self.sector,
            'industry': self.industry,
            'country': self.country,
            'market_cap_usd': self.market_cap_usd,
            'cap_category': self.cap_category,
            'pe_ratio': float(self.pe_ratio) if self.pe_ratio else None,
            'dividend_yield': float(self.dividend_yield) if self.dividend_yield else None,
            'beta': float(self.beta) if self.beta else None,
        }
