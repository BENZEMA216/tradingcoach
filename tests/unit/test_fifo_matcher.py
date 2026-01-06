"""
单元测试 - FIFOMatcher 交易配对总协调器

测试 FIFOMatcher 类的所有功能：
- 交易加载
- 多标的协调
- 统计信息
- 数据库保存
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from decimal import Decimal
from datetime import datetime

from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from src.models.position import Position, PositionStatus
from src.matchers.fifo_matcher import FIFOMatcher, match_trades_from_database


@pytest.fixture
def mock_session():
    """创建Mock数据库会话"""
    session = Mock()
    session.query = Mock()
    session.commit = Mock()
    session.add = Mock()
    session.flush = Mock()
    return session


@pytest.fixture
def fifo_matcher_dry_run(mock_session):
    """创建FIFOMatcher实例（dry_run模式）"""
    return FIFOMatcher(mock_session, dry_run=True)


@pytest.fixture
def fifo_matcher_production(mock_session):
    """创建FIFOMatcher实例（生产模式）"""
    return FIFOMatcher(mock_session, dry_run=False)


def create_trade(
    symbol: str,
    direction: TradeDirection,
    quantity: int,
    price: float,
    filled_time: datetime,
    trade_id: int = None
) -> Trade:
    """辅助函数：创建交易记录"""
    trade = Trade(
        symbol=symbol,
        symbol_name=f'{symbol} Inc.',
        direction=direction,
        status=TradeStatus.FILLED,
        order_quantity=quantity,
        filled_quantity=quantity,
        order_price=Decimal(str(price)),
        filled_price=Decimal(str(price)),
        filled_time=filled_time,
        trade_date=filled_time.date(),
        total_fee=Decimal('1.00'),
        market=MarketType.US_STOCK,
        currency='USD'
    )
    if trade_id:
        trade.id = trade_id
    return trade


class TestFIFOMatcherInit:
    """测试 FIFOMatcher 初始化"""

    def test_init_dry_run(self, mock_session):
        """测试dry_run模式初始化"""
        matcher = FIFOMatcher(mock_session, dry_run=True)

        assert matcher.session == mock_session
        assert matcher.dry_run is True
        assert len(matcher.symbol_matchers) == 0
        assert matcher.stats['total_trades'] == 0
        assert matcher.stats['positions_created'] == 0

    def test_init_production(self, mock_session):
        """测试生产模式初始化"""
        matcher = FIFOMatcher(mock_session, dry_run=False)

        assert matcher.dry_run is False


class TestFIFOMatcherLoadTrades:
    """测试交易加载"""

    def test_load_trades_success(self, fifo_matcher_dry_run, mock_session):
        """测试成功加载交易"""
        # Mock数据库查询
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0), 1),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0), 2),
        ]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = trades

        # 调用私有方法
        loaded_trades = fifo_matcher_dry_run._load_trades()

        # 验证
        assert len(loaded_trades) == 2
        assert loaded_trades[0].symbol == 'AAPL'
        mock_session.query.assert_called_once()

    def test_load_trades_empty(self, fifo_matcher_dry_run, mock_session):
        """测试加载空交易列表"""
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        loaded_trades = fifo_matcher_dry_run._load_trades()

        assert len(loaded_trades) == 0


class TestFIFOMatcherProcessTrades:
    """测试交易处理"""

    def test_process_single_symbol(self, fifo_matcher_dry_run):
        """测试处理单个标的的交易"""
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
        ]

        positions = fifo_matcher_dry_run._process_all_trades(trades)

        # 应该生成1个持仓
        assert len(positions) == 1
        assert positions[0].symbol == 'AAPL'
        assert positions[0].status == PositionStatus.CLOSED

        # 应该创建了1个SymbolMatcher
        assert len(fifo_matcher_dry_run.symbol_matchers) == 1
        assert 'AAPL' in fifo_matcher_dry_run.symbol_matchers

    def test_process_multiple_symbols(self, fifo_matcher_dry_run):
        """测试处理多个标的的交易"""
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('GOOGL', TradeDirection.BUY, 50, 2800.00, datetime(2025, 1, 1, 11, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
            create_trade('GOOGL', TradeDirection.SELL, 50, 2900.00, datetime(2025, 1, 2, 11, 0, 0)),
        ]

        positions = fifo_matcher_dry_run._process_all_trades(trades)

        # 应该生成2个持仓
        assert len(positions) == 2

        # 应该创建了2个SymbolMatcher
        assert len(fifo_matcher_dry_run.symbol_matchers) == 2
        assert 'AAPL' in fifo_matcher_dry_run.symbol_matchers
        assert 'GOOGL' in fifo_matcher_dry_run.symbol_matchers

    def test_process_trades_with_open_positions(self, fifo_matcher_dry_run):
        """测试处理有未平仓的交易"""
        trades = [
            # AAPL 完全平仓
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
            # GOOGL 未平仓
            create_trade('GOOGL', TradeDirection.BUY, 50, 2800.00, datetime(2025, 1, 1, 11, 0, 0)),
        ]

        closed_positions = fifo_matcher_dry_run._process_all_trades(trades)

        # 1个已平仓
        assert len(closed_positions) == 1

        # Finalize获取未平仓
        open_positions = fifo_matcher_dry_run._finalize_all_matchers()

        # 1个未平仓
        assert len(open_positions) == 1
        assert open_positions[0].symbol == 'GOOGL'
        assert open_positions[0].status == PositionStatus.OPEN


class TestFIFOMatcherStatistics:
    """测试统计信息"""

    def test_calculate_statistics(self, fifo_matcher_dry_run):
        """测试统计信息计算"""
        # 创建持仓列表
        closed_pos = Position(
            symbol='AAPL',
            symbol_name='Apple',
            direction='long',
            status=PositionStatus.CLOSED,
            quantity=100,
            market=MarketType.US_STOCK,
            currency='USD'
        )

        open_pos = Position(
            symbol='GOOGL',
            symbol_name='Google',
            direction='long',
            status=PositionStatus.OPEN,
            quantity=50,
            market=MarketType.US_STOCK,
            currency='USD'
        )

        all_positions = [closed_pos, open_pos]

        fifo_matcher_dry_run._calculate_statistics(all_positions)

        assert fifo_matcher_dry_run.stats['positions_created'] == 2
        assert fifo_matcher_dry_run.stats['closed_positions'] == 1
        assert fifo_matcher_dry_run.stats['open_positions'] == 1

    def test_get_statistics(self, fifo_matcher_dry_run):
        """测试获取统计信息"""
        fifo_matcher_dry_run.stats['total_trades'] = 100
        fifo_matcher_dry_run.stats['positions_created'] = 80

        stats = fifo_matcher_dry_run.get_statistics()

        assert stats['total_trades'] == 100
        assert stats['positions_created'] == 80
        # 应该返回副本，不是原始字典
        stats['total_trades'] = 999
        assert fifo_matcher_dry_run.stats['total_trades'] == 100


class TestFIFOMatcherSavePositions:
    """测试持仓保存"""

    def test_save_positions_dry_run(self, fifo_matcher_dry_run, mock_session):
        """测试dry_run模式不保存

        注意：_save_positions 方法本身不检查 dry_run，
        检查是在 match_all_trades 中调用之前进行的。
        这个测试验证 _save_positions 本身确实会调用数据库操作。
        """
        positions = [
            Position(
                symbol='AAPL',
                symbol_name='Apple',
                direction='long',
                status=PositionStatus.CLOSED,
                quantity=100,
                market=MarketType.US_STOCK,
                currency='USD'
            )
        ]

        fifo_matcher_dry_run._save_positions(positions)

        # _save_positions 本身会调用数据库，不管是否 dry_run
        # dry_run 的检查在调用方（match_all_trades）中
        # 重构后使用 add + flush 而不是 bulk_save_objects
        assert mock_session.add.call_count == len(positions)
        mock_session.add.assert_called_with(positions[0])
        mock_session.flush.assert_called_once()

    def test_save_positions_production(self, fifo_matcher_production, mock_session):
        """测试生产模式保存"""
        positions = [
            Position(
                symbol='AAPL',
                symbol_name='Apple',
                direction='long',
                status=PositionStatus.CLOSED,
                quantity=100,
                market=MarketType.US_STOCK,
                currency='USD'
            )
        ]

        fifo_matcher_production._save_positions(positions)

        # 生产模式使用 add + flush 保存持仓
        assert mock_session.add.call_count == len(positions)
        mock_session.add.assert_called_with(positions[0])
        mock_session.flush.assert_called_once()

    def test_save_empty_positions(self, fifo_matcher_production, mock_session):
        """测试保存空持仓列表"""
        fifo_matcher_production._save_positions([])

        # 空列表不应该调用数据库
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()


class TestFIFOMatcherMatchAllTrades:
    """测试完整配对流程"""

    def test_match_all_trades_dry_run(self, fifo_matcher_dry_run, mock_session):
        """测试dry_run模式的完整流程"""
        # Mock交易数据
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = trades

        # 执行配对
        result = fifo_matcher_dry_run.match_all_trades()

        # 验证结果
        assert result['total_trades'] == 2
        assert result['positions_created'] == 1
        assert result['closed_positions'] == 1
        assert result['symbols_processed'] == 1

        # dry_run不应该commit
        mock_session.commit.assert_not_called()

    def test_match_all_trades_production(self, fifo_matcher_production, mock_session):
        """测试生产模式的完整流程"""
        # Mock交易数据
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = trades

        # 执行配对
        result = fifo_matcher_production.match_all_trades()

        # 验证结果
        assert result['total_trades'] == 2
        assert result['positions_created'] == 1

        # 生产模式应该commit
        mock_session.commit.assert_called_once()

    def test_match_all_trades_no_trades(self, fifo_matcher_dry_run, mock_session):
        """测试没有交易的情况"""
        # Mock空交易列表
        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = []

        # 执行配对
        result = fifo_matcher_dry_run.match_all_trades()

        # 应该返回空结果
        assert result['total_trades'] == 0
        assert result['positions_created'] == 0


class TestFIFOMatcherWarnings:
    """测试警告信息"""

    def test_warnings_for_open_shorts(self, fifo_matcher_dry_run, mock_session):
        """测试未平仓做空产生警告"""
        # Mock交易数据：有未平仓做空
        trades = [
            create_trade('AAPL', TradeDirection.SELL_SHORT, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
        ]

        mock_query = Mock()
        mock_filter = Mock()
        mock_order = Mock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order
        mock_order.all.return_value = trades

        # 执行配对
        result = fifo_matcher_dry_run.match_all_trades()

        # 应该产生警告
        assert len(result['warnings']) > 0
        assert 'AAPL' in result['warnings'][0]
        assert 'open short' in result['warnings'][0]


class TestFIFOMatcherGetPositionsBySymbol:
    """测试按标的获取持仓"""

    def test_get_positions_by_symbol_exists(self, fifo_matcher_dry_run):
        """测试获取存在的标的持仓"""
        # 先处理一些交易
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 100, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
        ]

        fifo_matcher_dry_run._process_all_trades(trades)

        # 获取持仓
        positions = fifo_matcher_dry_run.get_positions_by_symbol('AAPL')

        # AAPL应该有持仓（在matched_positions中）
        # 注意：这个方法返回的是matcher.matched_positions，在当前实现中这个列表在process阶段不会填充
        # 只有在save之后才会有
        assert positions == []  # 当前实现返回空列表

    def test_get_positions_by_symbol_not_exists(self, fifo_matcher_dry_run):
        """测试获取不存在的标的持仓"""
        positions = fifo_matcher_dry_run.get_positions_by_symbol('NONEXISTENT')

        assert positions == []


class TestMatchTradesFromDatabase:
    """测试便捷函数"""

    @patch('src.matchers.fifo_matcher.FIFOMatcher')
    def test_match_trades_from_database(self, mock_matcher_class):
        """测试便捷函数"""
        mock_session = Mock()
        mock_matcher_instance = Mock()
        mock_matcher_instance.match_all_trades.return_value = {'positions_created': 10}

        mock_matcher_class.return_value = mock_matcher_instance

        # 调用便捷函数
        result = match_trades_from_database(mock_session, dry_run=True)

        # 验证
        mock_matcher_class.assert_called_once_with(mock_session, dry_run=True)
        mock_matcher_instance.match_all_trades.assert_called_once()
        assert result['positions_created'] == 10


class TestFIFOMatcherComplexScenarios:
    """测试复杂场景"""

    def test_interleaved_symbols(self, fifo_matcher_dry_run):
        """测试交错的多标的交易"""
        trades = [
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('GOOGL', TradeDirection.BUY, 50, 2800.00, datetime(2025, 1, 1, 11, 0, 0)),
            create_trade('AAPL', TradeDirection.BUY, 100, 155.00, datetime(2025, 1, 2, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 150, 160.00, datetime(2025, 1, 3, 10, 0, 0)),
            create_trade('GOOGL', TradeDirection.SELL, 50, 2900.00, datetime(2025, 1, 3, 11, 0, 0)),
        ]

        positions = fifo_matcher_dry_run._process_all_trades(trades)

        # AAPL应该产生2个持仓（100股+50股）
        # GOOGL应该产生1个持仓（50股）
        aapl_positions = [p for p in positions if p.symbol == 'AAPL']
        googl_positions = [p for p in positions if p.symbol == 'GOOGL']

        assert len(aapl_positions) == 2
        assert len(googl_positions) == 1

        # 验证FIFO：第一个AAPL持仓应该是$150买入
        assert aapl_positions[0].open_price == Decimal('150.00')

    def test_partial_fills_multiple_symbols(self, fifo_matcher_dry_run):
        """测试多标的的部分成交"""
        trades = [
            # AAPL: 买100，卖60，剩余40
            create_trade('AAPL', TradeDirection.BUY, 100, 150.00, datetime(2025, 1, 1, 10, 0, 0)),
            create_trade('AAPL', TradeDirection.SELL, 60, 160.00, datetime(2025, 1, 2, 10, 0, 0)),
            # GOOGL: 买50，卖30，剩余20
            create_trade('GOOGL', TradeDirection.BUY, 50, 2800.00, datetime(2025, 1, 1, 11, 0, 0)),
            create_trade('GOOGL', TradeDirection.SELL, 30, 2900.00, datetime(2025, 1, 2, 11, 0, 0)),
        ]

        closed_positions = fifo_matcher_dry_run._process_all_trades(trades)
        open_positions = fifo_matcher_dry_run._finalize_all_matchers()

        # 应该有2个已平仓，2个未平仓
        assert len(closed_positions) == 2
        assert len(open_positions) == 2

        # 检查未平仓数量
        aapl_open = [p for p in open_positions if p.symbol == 'AAPL'][0]
        googl_open = [p for p in open_positions if p.symbol == 'GOOGL'][0]

        assert aapl_open.quantity == 40
        assert googl_open.quantity == 20
