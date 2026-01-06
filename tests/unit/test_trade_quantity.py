"""
单元测试 - TradeQuantity 部分成交追踪器

测试 TradeQuantity 类的所有功能：
- 初始化
- 数量消耗
- 费用分摊
- 边界条件
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from src.matchers.trade_quantity import TradeQuantity


@pytest.fixture
def sample_trade():
    """创建示例交易"""
    trade = Trade(
        symbol='AAPL',
        symbol_name='Apple Inc.',
        direction=TradeDirection.BUY,
        status=TradeStatus.FILLED,
        order_quantity=100,
        filled_quantity=100,
        order_price=Decimal('150.00'),
        filled_price=Decimal('150.50'),
        filled_time=datetime(2025, 1, 15, 10, 30, 0),
        trade_date=datetime(2025, 1, 15).date(),
        total_fee=Decimal('10.00'),
        market=MarketType.US_STOCK,
        currency='USD'
    )
    return trade


class TestTradeQuantityInit:
    """测试 TradeQuantity 初始化"""

    def test_init_success(self, sample_trade):
        """测试正常初始化"""
        tq = TradeQuantity(sample_trade)

        assert tq.trade == sample_trade
        assert tq.original_quantity == 100
        assert tq.remaining_quantity == 100
        assert tq.matched_positions == []

    def test_init_with_none_trade(self):
        """测试传入None交易"""
        with pytest.raises(ValueError, match="Trade cannot be None"):
            TradeQuantity(None)

    def test_init_with_zero_quantity(self, sample_trade):
        """测试零数量交易"""
        sample_trade.filled_quantity = 0

        with pytest.raises(ValueError, match="Invalid filled_quantity"):
            TradeQuantity(sample_trade)

    def test_init_with_negative_quantity(self, sample_trade):
        """测试负数量交易"""
        sample_trade.filled_quantity = -50

        with pytest.raises(ValueError, match="Invalid filled_quantity"):
            TradeQuantity(sample_trade)


class TestTradeQuantityConsume:
    """测试 TradeQuantity 数量消耗"""

    def test_consume_partial(self, sample_trade):
        """测试部分消耗"""
        tq = TradeQuantity(sample_trade)

        result = tq.consume(60)

        assert result is False  # 未完全消耗
        assert tq.remaining_quantity == 40
        assert tq.get_consumed_quantity() == 60

    def test_consume_full(self, sample_trade):
        """测试完全消耗"""
        tq = TradeQuantity(sample_trade)

        result = tq.consume(100)

        assert result is True  # 完全消耗
        assert tq.remaining_quantity == 0
        assert tq.get_consumed_quantity() == 100
        assert tq.is_fully_consumed() is True

    def test_consume_multiple_times(self, sample_trade):
        """测试多次消耗"""
        tq = TradeQuantity(sample_trade)

        # 第一次消耗
        result1 = tq.consume(30)
        assert result1 is False
        assert tq.remaining_quantity == 70

        # 第二次消耗
        result2 = tq.consume(40)
        assert result2 is False
        assert tq.remaining_quantity == 30

        # 第三次消耗完
        result3 = tq.consume(30)
        assert result3 is True
        assert tq.remaining_quantity == 0

    def test_consume_zero(self, sample_trade):
        """测试消耗零数量"""
        tq = TradeQuantity(sample_trade)

        with pytest.raises(ValueError, match="Consume quantity must be positive"):
            tq.consume(0)

    def test_consume_negative(self, sample_trade):
        """测试消耗负数"""
        tq = TradeQuantity(sample_trade)

        with pytest.raises(ValueError, match="Consume quantity must be positive"):
            tq.consume(-10)

    def test_consume_more_than_remaining(self, sample_trade):
        """测试消耗超过剩余数量"""
        tq = TradeQuantity(sample_trade)
        tq.consume(60)  # 剩余40

        with pytest.raises(ValueError, match="Cannot consume 50, only 40 remaining"):
            tq.consume(50)


class TestTradeQuantityFeeAllocation:
    """测试 TradeQuantity 费用分摊"""

    def test_fee_allocation_full(self, sample_trade):
        """测试完整配对的费用分摊"""
        tq = TradeQuantity(sample_trade)

        fee = tq.calculate_fee_allocation(100)

        assert fee == 10.00  # 全部费用

    def test_fee_allocation_partial(self, sample_trade):
        """测试部分配对的费用分摊"""
        tq = TradeQuantity(sample_trade)

        # 配对60股，费用应该是 60/100 * 10 = 6.00
        fee = tq.calculate_fee_allocation(60)

        assert fee == 6.00

    def test_fee_allocation_multiple(self, sample_trade):
        """测试多次配对的费用分摊总和"""
        tq = TradeQuantity(sample_trade)

        fee1 = tq.calculate_fee_allocation(30)  # 3.00
        fee2 = tq.calculate_fee_allocation(40)  # 4.00
        fee3 = tq.calculate_fee_allocation(30)  # 3.00

        assert fee1 == 3.00
        assert fee2 == 4.00
        assert fee3 == 3.00
        assert fee1 + fee2 + fee3 == 10.00  # 总和等于原始费用

    def test_fee_allocation_zero_fee(self, sample_trade):
        """测试零费用"""
        sample_trade.total_fee = Decimal('0.00')
        tq = TradeQuantity(sample_trade)

        fee = tq.calculate_fee_allocation(50)

        assert fee == 0.00

    def test_fee_allocation_none_fee(self, sample_trade):
        """测试费用为None"""
        sample_trade.total_fee = None
        tq = TradeQuantity(sample_trade)

        fee = tq.calculate_fee_allocation(50)

        assert fee == 0.00

    def test_fee_allocation_rounding(self, sample_trade):
        """测试费用四舍五入"""
        sample_trade.total_fee = Decimal('10.01')
        tq = TradeQuantity(sample_trade)

        # 配对33股：33/100 * 10.01 = 3.3033 -> 3.30
        fee = tq.calculate_fee_allocation(33)

        assert fee == 3.30


class TestTradeQuantityMatchedPositions:
    """测试 TradeQuantity 持仓记录"""

    def test_add_matched_position(self, sample_trade):
        """测试添加匹配的持仓ID"""
        tq = TradeQuantity(sample_trade)

        tq.add_matched_position(101)
        tq.add_matched_position(102)
        tq.add_matched_position(103)

        assert len(tq.matched_positions) == 3
        assert tq.matched_positions == [101, 102, 103]


class TestTradeQuantityIsFullyConsumed:
    """测试 TradeQuantity 完全消耗检查"""

    def test_is_fully_consumed_false_initial(self, sample_trade):
        """测试初始状态未完全消耗"""
        tq = TradeQuantity(sample_trade)

        assert tq.is_fully_consumed() is False

    def test_is_fully_consumed_false_partial(self, sample_trade):
        """测试部分消耗后未完全消耗"""
        tq = TradeQuantity(sample_trade)
        tq.consume(50)

        assert tq.is_fully_consumed() is False

    def test_is_fully_consumed_true(self, sample_trade):
        """测试完全消耗"""
        tq = TradeQuantity(sample_trade)
        tq.consume(100)

        assert tq.is_fully_consumed() is True


class TestTradeQuantityGetConsumedQuantity:
    """测试 TradeQuantity 已消耗数量"""

    def test_get_consumed_quantity_initial(self, sample_trade):
        """测试初始已消耗数量"""
        tq = TradeQuantity(sample_trade)

        assert tq.get_consumed_quantity() == 0

    def test_get_consumed_quantity_partial(self, sample_trade):
        """测试部分消耗后已消耗数量"""
        tq = TradeQuantity(sample_trade)
        tq.consume(30)

        assert tq.get_consumed_quantity() == 30

    def test_get_consumed_quantity_multiple(self, sample_trade):
        """测试多次消耗后已消耗数量"""
        tq = TradeQuantity(sample_trade)
        tq.consume(30)
        tq.consume(40)

        assert tq.get_consumed_quantity() == 70


class TestTradeQuantityRepr:
    """测试 TradeQuantity 字符串表示"""

    def test_repr_initial(self, sample_trade):
        """测试初始状态字符串表示"""
        tq = TradeQuantity(sample_trade)

        repr_str = repr(tq)

        assert 'AAPL' in repr_str
        assert 'buy' in repr_str.lower()
        assert '100/100' in repr_str
        assert 'PARTIAL' in repr_str

    def test_repr_fully_consumed(self, sample_trade):
        """测试完全消耗状态字符串表示"""
        tq = TradeQuantity(sample_trade)
        tq.consume(100)

        repr_str = repr(tq)

        assert 'AAPL' in repr_str
        assert '0/100' in repr_str
        assert 'FULLY_CONSUMED' in repr_str

    def test_str_equals_repr(self, sample_trade):
        """测试 str() 等于 repr()"""
        tq = TradeQuantity(sample_trade)

        assert str(tq) == repr(tq)


class TestTradeQuantityEdgeCases:
    """测试 TradeQuantity 边界情况"""

    def test_single_share_trade(self, sample_trade):
        """测试单股交易"""
        sample_trade.filled_quantity = 1
        sample_trade.total_fee = Decimal('1.00')

        tq = TradeQuantity(sample_trade)

        assert tq.original_quantity == 1
        assert tq.remaining_quantity == 1

        fee = tq.calculate_fee_allocation(1)
        assert fee == 1.00

        tq.consume(1)
        assert tq.is_fully_consumed() is True

    def test_large_quantity_trade(self, sample_trade):
        """测试大数量交易"""
        sample_trade.filled_quantity = 10000
        sample_trade.total_fee = Decimal('1000.00')

        tq = TradeQuantity(sample_trade)

        assert tq.original_quantity == 10000

        # 消耗一半
        tq.consume(5000)
        assert tq.remaining_quantity == 5000

        fee = tq.calculate_fee_allocation(5000)
        assert fee == 500.00

    def test_decimal_fee_precision(self, sample_trade):
        """测试Decimal费用精度"""
        sample_trade.total_fee = Decimal('12.345')
        tq = TradeQuantity(sample_trade)

        # 50股的费用：50/100 * 12.345 = 6.1725 -> 6.17
        fee = tq.calculate_fee_allocation(50)

        assert fee == 6.17
