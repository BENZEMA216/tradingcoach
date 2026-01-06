"""
单元测试 - SymbolMatcher 单标的FIFO配对器

测试 SymbolMatcher 类的所有功能：
- FIFO配对逻辑
- 做多/做空持仓
- 部分成交处理
- 未平仓持仓创建
- 盈亏计算
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from src.models.position import Position, PositionStatus
from src.matchers.symbol_matcher import SymbolMatcher


@pytest.fixture
def symbol_matcher():
    """创建 SymbolMatcher 实例"""
    return SymbolMatcher('AAPL')


def create_trade(
    direction: TradeDirection,
    quantity: int,
    price: float,
    filled_time: datetime,
    fee: float = 1.0,
    symbol: str = 'AAPL'
) -> Trade:
    """辅助函数：创建交易记录"""
    return Trade(
        symbol=symbol,
        symbol_name='Apple Inc.',
        direction=direction,
        status=TradeStatus.FILLED,
        order_quantity=quantity,
        filled_quantity=quantity,
        order_price=Decimal(str(price)),
        filled_price=Decimal(str(price)),
        filled_time=filled_time,
        trade_date=filled_time.date(),
        total_fee=Decimal(str(fee)),
        market=MarketType.US_STOCK,
        currency='USD'
    )


class TestSymbolMatcherInit:
    """测试 SymbolMatcher 初始化"""

    def test_init_success(self):
        """测试正常初始化"""
        matcher = SymbolMatcher('AAPL')

        assert matcher.symbol == 'AAPL'
        assert len(matcher.open_long_queue) == 0
        assert len(matcher.open_short_queue) == 0
        assert len(matcher.matched_positions) == 0

    def test_init_empty_symbol(self):
        """测试空标的代码"""
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            SymbolMatcher('')


class TestSymbolMatcherLongPositions:
    """测试做多持仓配对（买入->卖出）"""

    def test_simple_long_match(self, symbol_matcher):
        """测试简单的买卖配对"""
        # 买入100股
        buy_trade = create_trade(
            TradeDirection.BUY,
            100,
            150.00,
            datetime(2025, 1, 1, 10, 0, 0),
            fee=2.0
        )

        # 卖出100股
        sell_trade = create_trade(
            TradeDirection.SELL,
            100,
            160.00,
            datetime(2025, 1, 5, 15, 0, 0),
            fee=2.0
        )

        # 处理交易
        positions1 = symbol_matcher.process_trade(buy_trade)
        positions2 = symbol_matcher.process_trade(sell_trade)

        # 买入不产生持仓
        assert len(positions1) == 0

        # 卖出产生1个持仓
        assert len(positions2) == 1

        position = positions2[0]
        assert position.symbol == 'AAPL'
        assert position.direction == 'long'
        assert position.status == PositionStatus.CLOSED
        assert position.quantity == 100
        assert position.open_price == Decimal('150.00')
        assert position.close_price == Decimal('160.00')

        # 盈亏检查：(160-150) * 100 - 4 = 996
        assert position.realized_pnl == 1000.00
        assert position.total_fees == 4.0
        assert position.net_pnl == 996.00

    def test_fifo_order(self, symbol_matcher):
        """测试FIFO顺序：先买先卖"""
        # 第一次买入：$100
        buy1 = create_trade(TradeDirection.BUY, 50, 100.00, datetime(2025, 1, 1, 10, 0, 0))
        # 第二次买入：$110
        buy2 = create_trade(TradeDirection.BUY, 50, 110.00, datetime(2025, 1, 2, 10, 0, 0))
        # 第三次买入：$120
        buy3 = create_trade(TradeDirection.BUY, 50, 120.00, datetime(2025, 1, 3, 10, 0, 0))

        # 卖出100股 @ $130
        sell = create_trade(TradeDirection.SELL, 100, 130.00, datetime(2025, 1, 4, 10, 0, 0))

        symbol_matcher.process_trade(buy1)
        symbol_matcher.process_trade(buy2)
        symbol_matcher.process_trade(buy3)
        positions = symbol_matcher.process_trade(sell)

        # 应该产生2个持仓
        assert len(positions) == 2

        # 第一个持仓：50股 @ $100 -> $130
        pos1 = positions[0]
        assert pos1.quantity == 50
        assert pos1.open_price == Decimal('100.00')
        assert pos1.close_price == Decimal('130.00')

        # 第二个持仓：50股 @ $110 -> $130
        pos2 = positions[1]
        assert pos2.quantity == 50
        assert pos2.open_price == Decimal('110.00')
        assert pos2.close_price == Decimal('130.00')

        # 队列中应该还剩一个买入
        assert len(symbol_matcher.open_long_queue) == 1

    def test_partial_fill_matching(self, symbol_matcher):
        """测试部分成交配对"""
        # 买入100股
        buy = create_trade(TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        # 卖出60股（部分平仓）
        sell1 = create_trade(TradeDirection.SELL, 60, 160.00, datetime(2025, 1, 2, 10, 0, 0))

        # 卖出40股（完全平仓）
        sell2 = create_trade(TradeDirection.SELL, 40, 165.00, datetime(2025, 1, 3, 10, 0, 0))

        symbol_matcher.process_trade(buy)
        positions1 = symbol_matcher.process_trade(sell1)
        positions2 = symbol_matcher.process_trade(sell2)

        # 第一次卖出产生1个持仓
        assert len(positions1) == 1
        assert positions1[0].quantity == 60

        # 第二次卖出产生1个持仓
        assert len(positions2) == 1
        assert positions2[0].quantity == 40

        # 队列应该清空
        assert len(symbol_matcher.open_long_queue) == 0

    def test_multiple_buys_single_sell(self, symbol_matcher):
        """测试多次买入，一次卖出"""
        # 多次买入
        buy1 = create_trade(TradeDirection.BUY, 30, 100.00, datetime(2025, 1, 1, 10, 0, 0))
        buy2 = create_trade(TradeDirection.BUY, 40, 105.00, datetime(2025, 1, 2, 10, 0, 0))
        buy3 = create_trade(TradeDirection.BUY, 30, 110.00, datetime(2025, 1, 3, 10, 0, 0))

        # 一次性卖出所有
        sell = create_trade(TradeDirection.SELL, 100, 120.00, datetime(2025, 1, 4, 10, 0, 0))

        symbol_matcher.process_trade(buy1)
        symbol_matcher.process_trade(buy2)
        symbol_matcher.process_trade(buy3)
        positions = symbol_matcher.process_trade(sell)

        # 应该产生3个持仓
        assert len(positions) == 3

        # 验证数量
        assert positions[0].quantity == 30
        assert positions[1].quantity == 40
        assert positions[2].quantity == 30

        # 验证FIFO顺序
        assert positions[0].open_price == Decimal('100.00')
        assert positions[1].open_price == Decimal('105.00')
        assert positions[2].open_price == Decimal('110.00')


class TestSymbolMatcherShortPositions:
    """测试做空持仓配对（卖空->买券还券）"""

    def test_simple_short_match(self, symbol_matcher):
        """测试简单的做空配对"""
        # 卖空100股 @ $150
        sell_short = create_trade(
            TradeDirection.SELL_SHORT,
            100,
            150.00,
            datetime(2025, 1, 1, 10, 0, 0),
            fee=2.0
        )

        # 买券还券100股 @ $140
        buy_cover = create_trade(
            TradeDirection.BUY_TO_COVER,
            100,
            140.00,
            datetime(2025, 1, 5, 15, 0, 0),
            fee=2.0
        )

        # 处理交易
        positions1 = symbol_matcher.process_trade(sell_short)
        positions2 = symbol_matcher.process_trade(buy_cover)

        # 卖空不产生持仓
        assert len(positions1) == 0

        # 买券还券产生1个持仓
        assert len(positions2) == 1

        position = positions2[0]
        assert position.direction == 'short'
        assert position.status == PositionStatus.CLOSED
        assert position.quantity == 100
        assert position.open_price == Decimal('150.00')
        assert position.close_price == Decimal('140.00')

        # 做空盈亏：(150-140) * 100 - 4 = 996
        assert position.realized_pnl == 1000.00
        assert position.net_pnl == 996.00

    def test_short_fifo_order(self, symbol_matcher):
        """测试做空FIFO顺序"""
        # 三次卖空
        short1 = create_trade(TradeDirection.SELL_SHORT, 50, 150.00, datetime(2025, 1, 1, 10, 0, 0))
        short2 = create_trade(TradeDirection.SELL_SHORT, 50, 155.00, datetime(2025, 1, 2, 10, 0, 0))
        short3 = create_trade(TradeDirection.SELL_SHORT, 50, 160.00, datetime(2025, 1, 3, 10, 0, 0))

        # 买券还券100股 @ $140
        cover = create_trade(TradeDirection.BUY_TO_COVER, 100, 140.00, datetime(2025, 1, 4, 10, 0, 0))

        symbol_matcher.process_trade(short1)
        symbol_matcher.process_trade(short2)
        symbol_matcher.process_trade(short3)
        positions = symbol_matcher.process_trade(cover)

        # 应该产生2个持仓
        assert len(positions) == 2

        # FIFO：先卖空的先平仓
        assert positions[0].open_price == Decimal('150.00')
        assert positions[1].open_price == Decimal('155.00')

        # 还剩一个未平仓
        assert len(symbol_matcher.open_short_queue) == 1


class TestSymbolMatcherOrphanedTrades:
    """测试孤立交易（没有对应开仓的平仓）"""

    def test_orphaned_sell(self, symbol_matcher):
        """测试没有买入的卖出"""
        # 直接卖出，没有对应的买入
        sell = create_trade(TradeDirection.SELL, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        positions = symbol_matcher.process_trade(sell)

        # 不会产生持仓
        assert len(positions) == 0

    def test_orphaned_buy_to_cover(self, symbol_matcher):
        """测试没有卖空的买券还券"""
        # 直接买券还券，没有对应的卖空
        cover = create_trade(TradeDirection.BUY_TO_COVER, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        positions = symbol_matcher.process_trade(cover)

        # 不会产生持仓
        assert len(positions) == 0

    def test_partial_orphaned_sell(self, symbol_matcher):
        """测试部分孤立的卖出"""
        # 买入50股
        buy = create_trade(TradeDirection.BUY, 50, 100.00, datetime(2025, 1, 1, 10, 0, 0))

        # 卖出100股（其中50股是孤立的）
        sell = create_trade(TradeDirection.SELL, 100, 110.00, datetime(2025, 1, 2, 10, 0, 0))

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        # 只产生1个50股的持仓
        assert len(positions) == 1
        assert positions[0].quantity == 50

        # 队列清空
        assert len(symbol_matcher.open_long_queue) == 0


class TestSymbolMatcherOpenPositions:
    """测试未平仓持仓"""

    def test_finalize_open_long(self, symbol_matcher):
        """测试创建未平仓做多持仓"""
        # 买入100股，未卖出
        buy = create_trade(TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        symbol_matcher.process_trade(buy)

        # Finalize
        open_positions = symbol_matcher.finalize_open_positions()

        assert len(open_positions) == 1

        position = open_positions[0]
        assert position.status == PositionStatus.OPEN
        assert position.direction == 'long'
        assert position.quantity == 100
        assert position.open_price == Decimal('150.00')
        assert position.close_price is None
        assert position.close_time is None

    def test_finalize_open_short(self, symbol_matcher):
        """测试创建未平仓做空持仓"""
        # 卖空100股，未买券还券
        short = create_trade(TradeDirection.SELL_SHORT, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        symbol_matcher.process_trade(short)

        # Finalize
        open_positions = symbol_matcher.finalize_open_positions()

        assert len(open_positions) == 1

        position = open_positions[0]
        assert position.status == PositionStatus.OPEN
        assert position.direction == 'short'
        assert position.quantity == 100

    def test_finalize_partial_open(self, symbol_matcher):
        """测试部分平仓后的未平仓持仓"""
        # 买入100股
        buy = create_trade(TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))

        # 卖出60股
        sell = create_trade(TradeDirection.SELL, 60, 160.00, datetime(2025, 1, 2, 10, 0, 0))

        symbol_matcher.process_trade(buy)
        symbol_matcher.process_trade(sell)

        # Finalize
        open_positions = symbol_matcher.finalize_open_positions()

        assert len(open_positions) == 1

        # 剩余40股未平仓
        position = open_positions[0]
        assert position.quantity == 40

    def test_finalize_no_open_positions(self, symbol_matcher):
        """测试完全平仓后无未平仓持仓"""
        # 买入卖出配对
        buy = create_trade(TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0))
        sell = create_trade(TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0))

        symbol_matcher.process_trade(buy)
        symbol_matcher.process_trade(sell)

        # Finalize
        open_positions = symbol_matcher.finalize_open_positions()

        assert len(open_positions) == 0


class TestSymbolMatcherPnLCalculation:
    """测试盈亏计算"""

    def test_long_profit(self, symbol_matcher):
        """测试做多盈利"""
        buy = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0), fee=5.0)
        sell = create_trade(TradeDirection.SELL, 100, 120.00, datetime(2025, 1, 2, 10, 0, 0), fee=5.0)

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        position = positions[0]
        # 盈利：(120-100) * 100 = 2000
        assert position.realized_pnl == 2000.00
        # 费用：5 + 5 = 10
        assert position.total_fees == 10.0
        # 净盈利：2000 - 10 = 1990
        assert position.net_pnl == 1990.00

    def test_long_loss(self, symbol_matcher):
        """测试做多亏损"""
        buy = create_trade(TradeDirection.BUY, 100, 120.00, datetime(2025, 1, 1, 10, 0, 0), fee=5.0)
        sell = create_trade(TradeDirection.SELL, 100, 100.00, datetime(2025, 1, 2, 10, 0, 0), fee=5.0)

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        position = positions[0]
        # 亏损：(100-120) * 100 = -2000
        assert position.realized_pnl == -2000.00
        # 净亏损：-2000 - 10 = -2010
        assert position.net_pnl == -2010.00

    def test_short_profit(self, symbol_matcher):
        """测试做空盈利"""
        short = create_trade(TradeDirection.SELL_SHORT, 100, 120.00, datetime(2025, 1, 1, 10, 0, 0), fee=5.0)
        cover = create_trade(TradeDirection.BUY_TO_COVER, 100, 100.00, datetime(2025, 1, 2, 10, 0, 0), fee=5.0)

        symbol_matcher.process_trade(short)
        positions = symbol_matcher.process_trade(cover)

        position = positions[0]
        # 做空盈利：(120-100) * 100 = 2000
        assert position.realized_pnl == 2000.00
        assert position.net_pnl == 1990.00

    def test_short_loss(self, symbol_matcher):
        """测试做空亏损"""
        short = create_trade(TradeDirection.SELL_SHORT, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0), fee=5.0)
        cover = create_trade(TradeDirection.BUY_TO_COVER, 100, 120.00, datetime(2025, 1, 2, 10, 0, 0), fee=5.0)

        symbol_matcher.process_trade(short)
        positions = symbol_matcher.process_trade(cover)

        position = positions[0]
        # 做空亏损：(100-120) * 100 = -2000
        assert position.realized_pnl == -2000.00
        assert position.net_pnl == -2010.00

    def test_pnl_percentage(self, symbol_matcher):
        """测试盈亏百分比"""
        buy = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0), fee=0)
        sell = create_trade(TradeDirection.SELL, 100, 110.00, datetime(2025, 1, 2, 10, 0, 0), fee=0)

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        position = positions[0]
        # 价格涨幅：10%
        assert position.realized_pnl_pct == 10.00


class TestSymbolMatcherHoldingPeriod:
    """测试持仓时间计算"""

    def test_holding_period_days(self, symbol_matcher):
        """测试持仓天数"""
        buy = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0))
        sell = create_trade(TradeDirection.SELL, 100, 110.00, datetime(2025, 1, 11, 15, 0, 0))

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        position = positions[0]
        assert position.holding_period_days == 10

    def test_holding_period_hours(self, symbol_matcher):
        """测试持仓小时数"""
        buy = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0))
        sell = create_trade(TradeDirection.SELL, 100, 110.00, datetime(2025, 1, 1, 16, 0, 0))

        symbol_matcher.process_trade(buy)
        positions = symbol_matcher.process_trade(sell)

        position = positions[0]
        assert position.holding_period_days == 0
        assert position.holding_period_hours == 6.0


class TestSymbolMatcherWrongSymbol:
    """测试错误的标的代码"""

    def test_process_trade_wrong_symbol(self, symbol_matcher):
        """测试处理错误标的的交易"""
        wrong_trade = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0), symbol='GOOGL')

        with pytest.raises(ValueError, match="Trade symbol GOOGL does not match matcher symbol AAPL"):
            symbol_matcher.process_trade(wrong_trade)


class TestSymbolMatcherStatistics:
    """测试统计信息"""

    def test_get_statistics(self, symbol_matcher):
        """测试获取统计信息"""
        # 做多：买入100，卖出60，剩余40
        buy = create_trade(TradeDirection.BUY, 100, 100.00, datetime(2025, 1, 1, 10, 0, 0))
        sell = create_trade(TradeDirection.SELL, 60, 110.00, datetime(2025, 1, 2, 10, 0, 0))

        # 做空：卖空50，未平仓
        short = create_trade(TradeDirection.SELL_SHORT, 50, 120.00, datetime(2025, 1, 3, 10, 0, 0))

        symbol_matcher.process_trade(buy)
        symbol_matcher.process_trade(sell)
        symbol_matcher.process_trade(short)

        stats = symbol_matcher.get_statistics()

        assert stats['symbol'] == 'AAPL'
        assert stats['open_long_trades'] == 1  # 剩余40股的买入
        assert stats['open_short_trades'] == 1  # 50股的卖空
        assert stats['total_open_quantity'] == 90  # 40 + 50


class TestSymbolMatcherRepr:
    """测试字符串表示"""

    def test_repr(self, symbol_matcher):
        """测试__repr__"""
        repr_str = repr(symbol_matcher)

        assert 'SymbolMatcher' in repr_str
        assert 'AAPL' in repr_str
        assert 'long_queue' in repr_str
        assert 'short_queue' in repr_str
