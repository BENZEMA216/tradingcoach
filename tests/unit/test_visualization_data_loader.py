"""
Unit tests for visualization data loader
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.base import init_database, get_session, Base
from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from visualization.utils.data_loader import DataLoader, get_data_loader


@pytest.fixture
def test_db():
    """Create a temporary in-memory database for testing"""
    # Use in-memory SQLite database
    init_database('sqlite:///:memory:', echo=False)
    session = get_session()

    # Create all tables
    Base.metadata.create_all(session.bind)

    yield session

    session.close()


@pytest.fixture
def sample_trades(test_db):
    """Create sample trades for testing"""
    trades = [
        Trade(
            symbol='AAPL',
            direction=TradeDirection.BUY,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            order_time=datetime(2024, 1, 1, 9, 30),
            filled_time=datetime(2024, 1, 1, 9, 31),
            order_quantity=100,
            filled_quantity=100,
            order_price=Decimal('150.00'),
            filled_price=Decimal('150.50'),
            filled_amount=Decimal('15050.00'),
            total_fee=Decimal('2.00'),
            trade_date=datetime(2024, 1, 1).date()
        ),
        Trade(
            symbol='AAPL',
            direction=TradeDirection.SELL,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            order_time=datetime(2024, 1, 10, 14, 30),
            filled_time=datetime(2024, 1, 10, 14, 31),
            order_quantity=100,
            filled_quantity=100,
            order_price=Decimal('155.00'),
            filled_price=Decimal('155.50'),
            filled_amount=Decimal('15550.00'),
            total_fee=Decimal('2.00'),
            trade_date=datetime(2024, 1, 10).date()
        ),
        Trade(
            symbol='TSLA',
            direction=TradeDirection.BUY,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            order_time=datetime(2024, 1, 5, 10, 0),
            filled_time=datetime(2024, 1, 5, 10, 1),
            order_quantity=50,
            filled_quantity=50,
            order_price=Decimal('200.00'),
            filled_price=Decimal('200.25'),
            filled_amount=Decimal('10012.50'),
            total_fee=Decimal('1.50'),
            trade_date=datetime(2024, 1, 5).date()
        )
    ]

    for trade in trades:
        test_db.add(trade)

    test_db.commit()

    return trades


@pytest.fixture
def sample_positions(test_db, sample_trades):
    """Create sample positions for testing"""
    positions = [
        Position(
            symbol='AAPL',
            direction='long',
            quantity=100,
            open_price=Decimal('150.50'),
            close_price=Decimal('155.50'),
            open_time=datetime(2024, 1, 1, 9, 31),
            close_time=datetime(2024, 1, 10, 14, 31),
            open_date=datetime(2024, 1, 1).date(),
            close_date=datetime(2024, 1, 10).date(),
            status=PositionStatus.CLOSED,
            realized_pnl=Decimal('500.00'),
            total_fees=Decimal('4.00'),
            net_pnl=Decimal('496.00'),
            net_pnl_pct=Decimal('3.29'),
            holding_period_days=9,
            overall_score=Decimal('75.5'),
            score_grade='B+',
            entry_quality_score=Decimal('70.0'),
            exit_quality_score=Decimal('80.0'),
            trend_quality_score=Decimal('75.0'),
            risk_mgmt_score=Decimal('78.0')
        ),
        Position(
            symbol='TSLA',
            direction='long',
            quantity=50,
            open_price=Decimal('200.25'),
            open_time=datetime(2024, 1, 5, 10, 1),
            open_date=datetime(2024, 1, 5).date(),
            status=PositionStatus.OPEN,
            total_fees=Decimal('1.50')
        )
    ]

    for pos in positions:
        test_db.add(pos)

    test_db.commit()

    return positions


@pytest.fixture
def sample_market_data(test_db):
    """Create sample market data for testing"""
    market_data = [
        MarketData(
            symbol='AAPL',
            timestamp=datetime(2024, 1, 1, 16, 0),  # Market close time
            date=datetime(2024, 1, 1).date(),
            open=Decimal('150.00'),
            high=Decimal('152.00'),
            low=Decimal('149.00'),
            close=Decimal('151.00'),
            volume=1000000,
            rsi_14=Decimal('55.5'),
            macd=Decimal('0.5'),
            macd_signal=Decimal('0.3'),
            macd_hist=Decimal('0.2'),
            ma_5=Decimal('150.5'),
            ma_20=Decimal('148.0'),
            ma_50=Decimal('145.0'),
            bb_upper=Decimal('153.0'),
            bb_middle=Decimal('150.0'),
            bb_lower=Decimal('147.0'),
            atr_14=Decimal('2.5')
        ),
        MarketData(
            symbol='AAPL',
            timestamp=datetime(2024, 1, 2, 16, 0),
            date=datetime(2024, 1, 2).date(),
            open=Decimal('151.00'),
            high=Decimal('153.00'),
            low=Decimal('150.00'),
            close=Decimal('152.00'),
            volume=1100000,
            rsi_14=Decimal('58.0'),
            macd=Decimal('0.6'),
            macd_signal=Decimal('0.4'),
            macd_hist=Decimal('0.2'),
            ma_5=Decimal('151.0'),
            ma_20=Decimal('148.5'),
            ma_50=Decimal('145.5'),
            bb_upper=Decimal('154.0'),
            bb_middle=Decimal('151.0'),
            bb_lower=Decimal('148.0'),
            atr_14=Decimal('2.6')
        ),
        MarketData(
            symbol='TSLA',
            timestamp=datetime(2024, 1, 5, 16, 0),
            date=datetime(2024, 1, 5).date(),
            open=Decimal('200.00'),
            high=Decimal('202.00'),
            low=Decimal('199.00'),
            close=Decimal('201.00'),
            volume=2000000,
            rsi_14=Decimal('60.0'),
            macd=Decimal('1.0'),
            macd_signal=Decimal('0.8'),
            macd_hist=Decimal('0.2'),
            ma_5=Decimal('200.5'),
            ma_20=Decimal('198.0'),
            ma_50=Decimal('195.0'),
            bb_upper=Decimal('203.0'),
            bb_middle=Decimal('200.0'),
            bb_lower=Decimal('197.0'),
            atr_14=Decimal('3.0')
        )
    ]

    for md in market_data:
        test_db.add(md)

    test_db.commit()

    return market_data


class TestDataLoader:
    """Test DataLoader class"""

    def test_init(self):
        """Test DataLoader initialization"""
        loader = DataLoader()
        assert loader.session is not None

    def test_get_overview_stats(self, test_db, sample_trades, sample_positions):
        """Test getting overview statistics"""
        loader = DataLoader()
        loader.session = test_db

        stats = loader.get_overview_stats()

        assert stats['total_trades'] == 3
        assert stats['total_positions'] == 2
        assert stats['closed_positions'] == 1
        assert stats['open_positions'] == 1
        assert stats['scored_positions'] == 1
        assert stats['total_net_pnl'] == 496.00
        assert stats['win_rate'] == 100.0  # 1 winning position out of 1 closed

    def test_get_data_coverage(self, test_db, sample_trades, sample_market_data):
        """Test getting data coverage"""
        loader = DataLoader()
        loader.session = test_db

        coverage_df = loader.get_data_coverage()

        assert len(coverage_df) == 2  # AAPL and TSLA
        assert 'symbol' in coverage_df.columns
        assert 'trade_count' in coverage_df.columns
        assert 'data_count' in coverage_df.columns
        assert 'has_data' in coverage_df.columns

        # Check AAPL data
        aapl_row = coverage_df[coverage_df['symbol'] == 'AAPL'].iloc[0]
        assert aapl_row['trade_count'] == 2
        assert aapl_row['data_count'] == 2
        assert aapl_row['has_data'] == True

        # Check TSLA data
        tsla_row = coverage_df[coverage_df['symbol'] == 'TSLA'].iloc[0]
        assert tsla_row['trade_count'] == 1
        assert tsla_row['data_count'] == 1
        assert tsla_row['has_data'] == True

    def test_get_quality_scores(self, test_db, sample_positions):
        """Test getting quality scores"""
        loader = DataLoader()
        loader.session = test_db

        scores_df = loader.get_quality_scores()

        assert len(scores_df) == 1  # Only 1 closed position with score
        assert 'symbol' in scores_df.columns
        assert 'overall_score' in scores_df.columns
        assert 'grade' in scores_df.columns
        assert 'entry_score' in scores_df.columns
        assert 'exit_score' in scores_df.columns
        assert 'trend_score' in scores_df.columns
        assert 'risk_score' in scores_df.columns

        # Check values
        row = scores_df.iloc[0]
        assert row['symbol'] == 'AAPL'
        assert row['overall_score'] == 75.5
        assert row['grade'] == 'B+'
        assert row['entry_score'] == 70.0

    def test_get_symbol_trades(self, test_db, sample_trades):
        """Test getting trades for a specific symbol"""
        loader = DataLoader()
        loader.session = test_db

        aapl_trades = loader.get_symbol_trades('AAPL')

        assert len(aapl_trades) == 2
        assert all(t.symbol == 'AAPL' for t in aapl_trades)
        # Check chronological order
        assert aapl_trades[0].filled_time < aapl_trades[1].filled_time

    def test_get_symbol_positions(self, test_db, sample_positions):
        """Test getting positions for a specific symbol"""
        loader = DataLoader()
        loader.session = test_db

        aapl_positions = loader.get_symbol_positions('AAPL')

        assert len(aapl_positions) == 1
        assert aapl_positions[0].symbol == 'AAPL'

    def test_get_market_data(self, test_db, sample_market_data):
        """Test getting market data"""
        loader = DataLoader()
        loader.session = test_db

        # Get all AAPL data
        df = loader.get_market_data('AAPL')

        assert len(df) == 2
        assert 'date' in df.columns
        assert 'open' in df.columns
        assert 'close' in df.columns
        assert 'rsi' in df.columns
        assert 'macd' in df.columns

        # Check values
        assert df['close'].iloc[0] == 151.00
        assert df['close'].iloc[1] == 152.00

    def test_get_market_data_with_date_range(self, test_db, sample_market_data):
        """Test getting market data with date range filter"""
        loader = DataLoader()
        loader.session = test_db

        # Get data for specific date range
        df = loader.get_market_data(
            'AAPL',
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1)
        )

        assert len(df) == 1
        assert df['date'].iloc[0].date() == datetime(2024, 1, 1).date()

    def test_get_all_symbols(self, test_db, sample_trades):
        """Test getting all symbols"""
        loader = DataLoader()
        loader.session = test_db

        symbols = loader.get_all_symbols()

        assert len(symbols) == 2
        assert 'AAPL' in symbols
        assert 'TSLA' in symbols
        assert symbols == sorted(symbols)  # Should be sorted

    def test_get_symbols_with_scores(self, test_db, sample_positions):
        """Test getting symbols with scores"""
        loader = DataLoader()
        loader.session = test_db

        symbols = loader.get_symbols_with_scores()

        assert len(symbols) == 1
        assert 'AAPL' in symbols

    def test_get_symbols_with_market_data(self, test_db, sample_market_data):
        """Test getting symbols with market data"""
        loader = DataLoader()
        loader.session = test_db

        symbols = loader.get_symbols_with_market_data()

        assert len(symbols) == 2
        assert 'AAPL' in symbols
        assert 'TSLA' in symbols

    def test_get_position_by_id(self, test_db, sample_positions):
        """Test getting position by ID"""
        loader = DataLoader()
        loader.session = test_db

        # Get first position
        pos = loader.get_position_by_id(sample_positions[0].id)

        assert pos is not None
        assert pos.symbol == 'AAPL'
        assert pos.quantity == 100

    def test_get_position_by_id_not_found(self, test_db):
        """Test getting non-existent position"""
        loader = DataLoader()
        loader.session = test_db

        pos = loader.get_position_by_id(99999)

        assert pos is None

    def test_empty_database(self, test_db):
        """Test with empty database"""
        loader = DataLoader()
        loader.session = test_db

        stats = loader.get_overview_stats()

        assert stats['total_trades'] == 0
        assert stats['total_positions'] == 0
        assert stats['total_net_pnl'] == 0.0
        assert stats['win_rate'] == 0.0


class TestGetDataLoader:
    """Test get_data_loader singleton function"""

    def test_singleton_pattern(self):
        """Test that get_data_loader returns the same instance"""
        loader1 = get_data_loader()
        loader2 = get_data_loader()

        # Should return the same instance
        assert loader1 is loader2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
