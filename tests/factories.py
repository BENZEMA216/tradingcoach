"""
Test Data Factories - 使用 factory_boy 创建测试数据

input: src/models (Trade, Position 等模型)
output: TradeFactory, PositionFactory 等工厂类
pos: 测试基础设施 - 提供统一的测试数据生成

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import factory
from factory import fuzzy
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Trade, Position, MarketData
from src.models.trade import TradeDirection, TradeStatus, MarketType
from src.models.position import PositionStatus


class TradeFactory(factory.Factory):
    """交易记录工厂"""

    class Meta:
        model = Trade

    # 基本信息
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA', 'META', 'AMZN'])
    symbol_name = factory.LazyAttribute(lambda o: f"{o.symbol} Inc.")

    # 交易方向和状态
    direction = fuzzy.FuzzyChoice([
        TradeDirection.BUY,
        TradeDirection.SELL,
        TradeDirection.SELL_SHORT,
        TradeDirection.BUY_TO_COVER
    ])
    status = TradeStatus.FILLED

    # 成交信息
    filled_price = fuzzy.FuzzyDecimal(10.0, 500.0, precision=4)
    filled_quantity = fuzzy.FuzzyInteger(1, 1000)
    filled_amount = factory.LazyAttribute(
        lambda o: Decimal(str(o.filled_price)) * o.filled_quantity
    )
    filled_time = fuzzy.FuzzyDateTime(
        start_dt=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_dt=datetime(2024, 12, 31, tzinfo=timezone.utc)
    )
    trade_date = factory.LazyAttribute(lambda o: o.filled_time.date())

    # 市场信息
    market = MarketType.US_STOCK
    currency = "USD"

    # 费用
    commission = fuzzy.FuzzyDecimal(0.5, 10.0, precision=2)
    total_fee = factory.LazyAttribute(lambda o: o.commission)

    # 期权相关 - 默认非期权
    is_option = 0
    underlying_symbol = None
    option_type = None
    strike_price = None
    expiration_date = None

    # 导入追踪
    broker_id = "futu_cn"
    trade_fingerprint = factory.LazyAttribute(
        lambda o: f"{o.symbol}_{o.direction.value}_{o.filled_time.isoformat()}_{o.filled_quantity}"
    )


class OptionTradeFactory(TradeFactory):
    """期权交易工厂"""

    is_option = 1
    underlying_symbol = factory.LazyAttribute(lambda o: o.symbol.split('_')[0] if '_' in o.symbol else o.symbol[:4])
    option_type = fuzzy.FuzzyChoice(['CALL', 'PUT'])
    strike_price = fuzzy.FuzzyDecimal(50.0, 300.0, precision=2)
    expiration_date = factory.LazyAttribute(
        lambda o: (o.filled_time + timedelta(days=random.randint(7, 90))).date()
    )
    symbol = factory.LazyAttribute(
        lambda o: f"{o.underlying_symbol}{o.expiration_date.strftime('%y%m%d')}C{int(o.strike_price)}"
    )


class PositionFactory(factory.Factory):
    """持仓记录工厂"""

    class Meta:
        model = Position

    # 基本信息
    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'])
    symbol_name = factory.LazyAttribute(lambda o: f"{o.symbol} Inc.")
    status = PositionStatus.CLOSED
    direction = fuzzy.FuzzyChoice(['long', 'short'])

    # 时间信息
    open_time = fuzzy.FuzzyDateTime(
        start_dt=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_dt=datetime(2024, 6, 30, tzinfo=timezone.utc)
    )
    close_time = factory.LazyAttribute(
        lambda o: o.open_time + timedelta(days=random.randint(1, 30))
    )
    open_date = factory.LazyAttribute(lambda o: o.open_time.date())
    close_date = factory.LazyAttribute(lambda o: o.close_time.date() if o.close_time else None)
    holding_period_days = factory.LazyAttribute(
        lambda o: (o.close_time - o.open_time).days if o.close_time else None
    )

    # 价格和数量
    open_price = fuzzy.FuzzyDecimal(50.0, 500.0, precision=4)
    close_price = factory.LazyAttribute(
        lambda o: o.open_price * Decimal(str(random.uniform(0.8, 1.3)))
    )
    quantity = fuzzy.FuzzyInteger(10, 500)

    # 盈亏指标 - 根据方向自动计算
    @factory.lazy_attribute
    def realized_pnl(self):
        if self.direction == 'long':
            return (self.close_price - self.open_price) * self.quantity
        else:
            return (self.open_price - self.close_price) * self.quantity

    @factory.lazy_attribute
    def realized_pnl_pct(self):
        cost = self.open_price * self.quantity
        return (self.realized_pnl / cost) * 100 if cost else Decimal('0')

    # 费用
    total_fees = fuzzy.FuzzyDecimal(1.0, 50.0, precision=2)
    open_fee = factory.LazyAttribute(lambda o: o.total_fees / 2)
    close_fee = factory.LazyAttribute(lambda o: o.total_fees / 2)

    # 净盈亏
    net_pnl = factory.LazyAttribute(lambda o: o.realized_pnl - o.total_fees)
    net_pnl_pct = factory.LazyAttribute(
        lambda o: (o.net_pnl / (o.open_price * o.quantity)) * 100
    )

    # 市场信息
    market = "美股"
    currency = "USD"

    # 期权信息 - 默认非期权
    is_option = 0
    underlying_symbol = None
    option_type = None
    strike_price = None
    expiry_date = None

    # 质量评分
    entry_quality_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    exit_quality_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    trend_quality_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    risk_mgmt_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)

    @factory.lazy_attribute
    def overall_score(self):
        return (
            self.entry_quality_score * Decimal('0.25') +
            self.exit_quality_score * Decimal('0.25') +
            self.trend_quality_score * Decimal('0.25') +
            self.risk_mgmt_score * Decimal('0.25')
        )

    @factory.lazy_attribute
    def score_grade(self):
        score = float(self.overall_score)
        if score >= 93:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 87:
            return 'A-'
        elif score >= 83:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 77:
            return 'B-'
        elif score >= 73:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 67:
            return 'C-'
        elif score >= 60:
            return 'D'
        else:
            return 'F'


class OpenPositionFactory(PositionFactory):
    """未平仓持仓工厂"""

    status = PositionStatus.OPEN
    close_time = None
    close_date = None
    close_price = None
    realized_pnl = None
    realized_pnl_pct = None
    net_pnl = None
    net_pnl_pct = None
    holding_period_days = None


class OptionPositionFactory(PositionFactory):
    """期权持仓工厂"""

    is_option = 1
    underlying_symbol = factory.LazyAttribute(lambda o: o.symbol[:4])
    option_type = fuzzy.FuzzyChoice(['call', 'put'])
    strike_price = fuzzy.FuzzyDecimal(50.0, 300.0, precision=2)
    expiry_date = factory.LazyAttribute(
        lambda o: (o.open_time + timedelta(days=random.randint(30, 120))).date()
    )

    # 期权评分
    option_entry_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    option_exit_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    option_strategy_score = fuzzy.FuzzyDecimal(40.0, 95.0, precision=2)
    entry_moneyness = fuzzy.FuzzyDecimal(-0.2, 0.2, precision=4)
    entry_dte = fuzzy.FuzzyInteger(7, 90)
    exit_dte = factory.LazyAttribute(lambda o: max(0, o.entry_dte - random.randint(1, 30)))


class MarketDataFactory(factory.Factory):
    """市场数据工厂"""

    class Meta:
        model = MarketData

    symbol = factory.Iterator(['AAPL', 'GOOGL', 'MSFT', 'NVDA', 'TSLA'])
    trade_date = fuzzy.FuzzyDate(date(2024, 1, 1), date(2024, 12, 31))

    # OHLC 数据
    open_price = fuzzy.FuzzyDecimal(100.0, 200.0, precision=2)
    high_price = factory.LazyAttribute(
        lambda o: o.open_price * Decimal(str(random.uniform(1.0, 1.05)))
    )
    low_price = factory.LazyAttribute(
        lambda o: o.open_price * Decimal(str(random.uniform(0.95, 1.0)))
    )
    close_price = factory.LazyAttribute(
        lambda o: Decimal(str(random.uniform(float(o.low_price), float(o.high_price))))
    )
    volume = fuzzy.FuzzyInteger(1000000, 50000000)

    # 技术指标
    rsi_14 = fuzzy.FuzzyDecimal(20.0, 80.0, precision=2)
    macd = fuzzy.FuzzyDecimal(-5.0, 5.0, precision=4)
    macd_signal = fuzzy.FuzzyDecimal(-5.0, 5.0, precision=4)
    macd_histogram = factory.LazyAttribute(lambda o: o.macd - o.macd_signal)

    sma_20 = factory.LazyAttribute(lambda o: o.close_price * Decimal(str(random.uniform(0.95, 1.05))))
    sma_50 = factory.LazyAttribute(lambda o: o.close_price * Decimal(str(random.uniform(0.90, 1.10))))
    sma_200 = factory.LazyAttribute(lambda o: o.close_price * Decimal(str(random.uniform(0.85, 1.15))))

    bb_upper = factory.LazyAttribute(lambda o: o.sma_20 * Decimal('1.04'))
    bb_lower = factory.LazyAttribute(lambda o: o.sma_20 * Decimal('0.96'))
    bb_middle = factory.LazyAttribute(lambda o: o.sma_20)

    atr_14 = fuzzy.FuzzyDecimal(1.0, 10.0, precision=4)


# 批量创建辅助函数
def create_trade_batch(count: int = 10, **kwargs) -> list:
    """批量创建交易记录"""
    return TradeFactory.create_batch(count, **kwargs)


def create_position_batch(count: int = 10, **kwargs) -> list:
    """批量创建持仓记录"""
    return PositionFactory.create_batch(count, **kwargs)


def create_winning_positions(count: int = 5) -> list:
    """创建盈利持仓"""
    positions = []
    for _ in range(count):
        pos = PositionFactory.build()
        # 确保盈利
        if pos.direction == 'long':
            pos.close_price = pos.open_price * Decimal('1.1')
        else:
            pos.close_price = pos.open_price * Decimal('0.9')
        pos.realized_pnl = abs((pos.close_price - pos.open_price) * pos.quantity)
        pos.net_pnl = pos.realized_pnl - pos.total_fees
        positions.append(pos)
    return positions


def create_losing_positions(count: int = 5) -> list:
    """创建亏损持仓"""
    positions = []
    for _ in range(count):
        pos = PositionFactory.build()
        # 确保亏损
        if pos.direction == 'long':
            pos.close_price = pos.open_price * Decimal('0.9')
        else:
            pos.close_price = pos.open_price * Decimal('1.1')
        pos.realized_pnl = -abs((pos.close_price - pos.open_price) * pos.quantity)
        pos.net_pnl = pos.realized_pnl - pos.total_fees
        positions.append(pos)
    return positions


def create_mixed_portfolio(winners: int = 6, losers: int = 4) -> list:
    """创建混合盈亏的投资组合"""
    return create_winning_positions(winners) + create_losing_positions(losers)
