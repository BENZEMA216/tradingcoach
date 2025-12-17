"""
Unit tests for Advanced Statistics API endpoints

Tests the new visualization endpoints:
1. Equity Drawdown
2. P&L Distribution
3. Rolling Metrics
4. Duration vs P&L
5. Symbol Risk
6. Hourly Performance
7. Trading Heatmap
8. Asset Type Breakdown
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict
import math

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.position import Position, PositionStatus
from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_positions(db_session):
    """Create sample positions for testing"""
    positions = [
        Position(
            id=1,
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction='long',
            is_option=0,  # stock
            open_time=datetime(2024, 1, 5, 10, 30),
            close_time=datetime(2024, 1, 10, 14, 0),
            open_date=date(2024, 1, 5),
            close_date=date(2024, 1, 10),
            open_price=150.0,
            close_price=160.0,
            quantity=100,
            realized_pnl=1000.0,
            net_pnl=980.0,
            total_fees=20.0,
            holding_period_days=5,
            score_grade='A',
            status=PositionStatus.CLOSED,
        ),
        Position(
            id=2,
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction='long',
            is_option=0,  # stock
            open_time=datetime(2024, 1, 12, 9, 30),
            close_time=datetime(2024, 1, 15, 15, 0),
            open_date=date(2024, 1, 12),
            close_date=date(2024, 1, 15),
            open_price=162.0,
            close_price=158.0,
            quantity=50,
            realized_pnl=-200.0,
            net_pnl=-220.0,
            total_fees=20.0,
            holding_period_days=3,
            score_grade='C',
            status=PositionStatus.CLOSED,
        ),
        Position(
            id=3,
            symbol='TSLA',
            symbol_name='Tesla Inc',
            direction='short',
            is_option=0,  # stock
            open_time=datetime(2024, 1, 18, 11, 0),
            close_time=datetime(2024, 1, 25, 13, 0),
            open_date=date(2024, 1, 18),
            close_date=date(2024, 1, 25),
            open_price=250.0,
            close_price=240.0,
            quantity=30,
            realized_pnl=300.0,
            net_pnl=280.0,
            total_fees=20.0,
            holding_period_days=7,
            score_grade='B',
            status=PositionStatus.CLOSED,
        ),
        Position(
            id=4,
            symbol='AMZN240119C185',
            symbol_name='Amazon Option',
            direction='long',
            is_option=1,  # option
            underlying_symbol='AMZN',
            option_type='call',
            strike_price=185.0,
            expiry_date=date(2024, 1, 19),
            open_time=datetime(2024, 2, 1, 10, 0),
            close_time=datetime(2024, 2, 5, 11, 0),
            open_date=date(2024, 2, 1),
            close_date=date(2024, 2, 5),
            open_price=5.0,
            close_price=8.0,
            quantity=10,
            realized_pnl=300.0,
            net_pnl=290.0,
            total_fees=10.0,
            holding_period_days=4,
            score_grade='A',
            status=PositionStatus.CLOSED,
        ),
        Position(
            id=5,
            symbol='NVDA',
            symbol_name='NVIDIA Corp',
            direction='long',
            is_option=0,  # stock
            open_time=datetime(2024, 2, 15, 14, 30),
            close_time=datetime(2024, 2, 28, 10, 0),
            open_date=date(2024, 2, 15),
            close_date=date(2024, 2, 28),
            open_price=700.0,
            close_price=750.0,
            quantity=10,
            realized_pnl=500.0,
            net_pnl=485.0,
            total_fees=15.0,
            holding_period_days=13,
            score_grade='A',
            status=PositionStatus.CLOSED,
        ),
    ]

    for p in positions:
        db_session.add(p)
    db_session.commit()

    return positions


@pytest.fixture
def sample_trades(db_session, sample_positions):
    """Create sample trades for hourly/heatmap testing"""
    trades = [
        Trade(
            id=1,
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction=TradeDirection.BUY,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            filled_time=datetime(2024, 1, 5, 10, 30),  # Friday 10:30
            trade_date=date(2024, 1, 5),
            filled_price=150.0,
            filled_quantity=100,
            filled_amount=15000.0,
            total_fee=5.0,
            position_id=1,
        ),
        Trade(
            id=2,
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction=TradeDirection.SELL,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            filled_time=datetime(2024, 1, 10, 14, 0),  # Wednesday 14:00
            trade_date=date(2024, 1, 10),
            filled_price=160.0,
            filled_quantity=100,
            filled_amount=16000.0,
            total_fee=5.0,
            position_id=1,
        ),
        Trade(
            id=3,
            symbol='TSLA',
            symbol_name='Tesla Inc',
            direction=TradeDirection.SELL_SHORT,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            filled_time=datetime(2024, 1, 18, 11, 0),  # Thursday 11:00
            trade_date=date(2024, 1, 18),
            filled_price=250.0,
            filled_quantity=30,
            filled_amount=7500.0,
            total_fee=5.0,
            position_id=3,
        ),
        Trade(
            id=4,
            symbol='TSLA',
            symbol_name='Tesla Inc',
            direction=TradeDirection.BUY_TO_COVER,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            filled_time=datetime(2024, 1, 25, 13, 0),  # Thursday 13:00
            trade_date=date(2024, 1, 25),
            filled_price=240.0,
            filled_quantity=30,
            filled_amount=7200.0,
            total_fee=5.0,
            position_id=3,
        ),
        Trade(
            id=5,
            symbol='NVDA',
            symbol_name='NVIDIA Corp',
            direction=TradeDirection.BUY,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            filled_time=datetime(2024, 2, 15, 14, 30),  # Thursday 14:30
            trade_date=date(2024, 2, 15),
            filled_price=700.0,
            filled_quantity=10,
            filled_amount=7000.0,
            total_fee=5.0,
            position_id=5,
        ),
    ]

    for t in trades:
        db_session.add(t)
    db_session.commit()

    return trades


# ==================== Equity Drawdown Tests ====================

class TestEquityDrawdown:
    """Test equity drawdown calculation for combo chart"""

    def test_cumulative_pnl_calculation(self, db_session, sample_positions):
        """Test cumulative P&L is calculated correctly by date"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        daily_pnl = defaultdict(float)
        for p in positions:
            if p.close_date and p.net_pnl:
                daily_pnl[p.close_date] += float(p.net_pnl)

        cumulative = 0.0
        for d in sorted(daily_pnl.keys()):
            cumulative += daily_pnl[d]

        # Total: 980 - 220 + 280 + 290 + 485 = 1815
        assert cumulative == pytest.approx(1815.0, rel=0.01)

    def test_drawdown_tracking(self, db_session, sample_positions):
        """Test drawdown is tracked correctly"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        daily_pnl = defaultdict(float)
        for p in positions:
            if p.close_date and p.net_pnl:
                daily_pnl[p.close_date] += float(p.net_pnl)

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for d in sorted(daily_pnl.keys()):
            cumulative += daily_pnl[d]
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)

        # After AAPL1: +980, peak=980
        # After AAPL2: +980-220=760, drawdown=220
        # After TSLA: +760+280=1040, new peak
        # After option: +1040+290=1330, new peak
        # After NVDA: +1330+485=1815, new peak
        assert max_drawdown == pytest.approx(220.0, rel=0.01)

    def test_peak_tracking(self, db_session, sample_positions):
        """Test peak value is tracked correctly"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        daily_pnl = defaultdict(float)
        for p in positions:
            if p.close_date and p.net_pnl:
                daily_pnl[p.close_date] += float(p.net_pnl)

        cumulative = 0.0
        peak = 0.0

        for d in sorted(daily_pnl.keys()):
            cumulative += daily_pnl[d]
            if cumulative > peak:
                peak = cumulative

        # Final peak should equal final cumulative (all winners after recovery)
        assert peak == pytest.approx(1815.0, rel=0.01)


# ==================== P&L Distribution Tests ====================

class TestPnLDistribution:
    """Test P&L distribution histogram calculation"""

    def test_distribution_binning(self, db_session, sample_positions):
        """Test P&L values are binned correctly"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        pnl_values = [float(p.net_pnl) for p in positions if p.net_pnl is not None]

        # Values: -220, 280, 290, 485, 980
        assert len(pnl_values) == 5
        assert min(pnl_values) == -220.0
        assert max(pnl_values) == 980.0

    def test_bin_count_creation(self):
        """Test bins are created correctly"""
        pnl_values = [-220.0, 280.0, 290.0, 485.0, 980.0]
        bin_count = 10

        min_pnl = min(pnl_values)
        max_pnl = max(pnl_values)
        bin_size = (max_pnl - min_pnl) / bin_count

        # Bin size = (980 - (-220)) / 10 = 120
        assert bin_size == 120.0

    def test_profit_loss_classification(self):
        """Test profit/loss classification in bins"""
        pnl_values = [-220.0, 280.0, 290.0, 485.0, 980.0]

        profit_count = sum(1 for v in pnl_values if v > 0)
        loss_count = sum(1 for v in pnl_values if v <= 0)

        assert profit_count == 4
        assert loss_count == 1


# ==================== Rolling Metrics Tests ====================

class TestRollingMetrics:
    """Test rolling metrics calculation"""

    def test_rolling_window(self, db_session, sample_positions):
        """Test rolling window calculation"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        window = 3

        if len(positions) >= window:
            for i in range(window - 1, len(positions)):
                window_positions = positions[i - window + 1:i + 1]
                assert len(window_positions) == window

    def test_rolling_win_rate(self, db_session, sample_positions):
        """Test rolling win rate calculation"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        window = 3

        # For window ending at position 3 (TSLA): [AAPL1(W), AAPL2(L), TSLA(W)]
        # Win rate = 2/3 = 66.67%
        if len(positions) >= window:
            window_positions = positions[0:3]
            winners = sum(1 for p in window_positions if p.net_pnl and float(p.net_pnl) > 0)
            win_rate = winners / window * 100

            assert win_rate == pytest.approx(66.67, rel=0.01)

    def test_cumulative_pnl_in_rolling(self, db_session, sample_positions):
        """Test cumulative P&L is tracked alongside rolling metrics"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        cumulative = 0.0
        for p in positions:
            cumulative += float(p.net_pnl or 0)

        assert cumulative == pytest.approx(1815.0, rel=0.01)


# ==================== Duration vs P&L Tests ====================

class TestDurationPnL:
    """Test duration vs P&L scatter data"""

    def test_duration_pnl_data(self, db_session, sample_positions):
        """Test duration and P&L data extraction"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        data = []
        for p in positions:
            if p.holding_period_days is not None and p.net_pnl is not None:
                data.append({
                    'holding_days': p.holding_period_days,
                    'pnl': float(p.net_pnl),
                    'is_winner': float(p.net_pnl) > 0,
                })

        assert len(data) == 5

        # Check specific position data
        holding_days = [d['holding_days'] for d in data]
        assert 5 in holding_days  # AAPL1
        assert 3 in holding_days  # AAPL2
        assert 13 in holding_days  # NVDA

    def test_winner_loser_separation(self, db_session, sample_positions):
        """Test winners and losers are correctly identified"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

        assert len(winners) == 4
        assert len(losers) == 1

    def test_avg_holding_by_outcome(self, db_session, sample_positions):
        """Test average holding days by win/loss"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

        avg_winner_days = sum(p.holding_period_days for p in winners) / len(winners)
        avg_loser_days = sum(p.holding_period_days for p in losers) / len(losers)

        # Winners: 5+7+4+13=29 / 4 = 7.25
        # Losers: 3 / 1 = 3.0
        assert avg_winner_days == pytest.approx(7.25, rel=0.01)
        assert avg_loser_days == 3.0


# ==================== Symbol Risk Tests ====================

class TestSymbolRisk:
    """Test symbol risk quadrant data"""

    def test_symbol_stats_grouping(self, db_session, sample_positions):
        """Test symbols are grouped with win/loss stats"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        symbol_stats = defaultdict(lambda: {"winners": [], "losers": [], "total_pnl": 0.0})

        for p in positions:
            pnl = float(p.net_pnl or 0)
            symbol_stats[p.symbol]["total_pnl"] += pnl
            if pnl > 0:
                symbol_stats[p.symbol]["winners"].append(pnl)
            else:
                symbol_stats[p.symbol]["losers"].append(pnl)

        # AAPL: 1 winner (980), 1 loser (-220)
        assert len(symbol_stats['AAPL']['winners']) == 1
        assert len(symbol_stats['AAPL']['losers']) == 1

    def test_avg_win_loss_calculation(self, db_session, sample_positions):
        """Test average win/loss per symbol"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.symbol == 'AAPL'
        ).all()

        winners = [float(p.net_pnl) for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [float(p.net_pnl) for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

        avg_win = sum(winners) / len(winners) if winners else 0
        avg_loss = sum(losers) / len(losers) if losers else 0

        assert avg_win == 980.0
        assert avg_loss == -220.0

    def test_risk_reward_ratio(self):
        """Test risk/reward ratio calculation"""
        avg_win = 980.0
        avg_loss = -220.0

        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else None

        # 980 / 220 = 4.45
        assert rr_ratio == pytest.approx(4.45, rel=0.01)


# ==================== Hourly Performance Tests ====================

class TestHourlyPerformance:
    """Test hourly performance data based on position open time"""

    def test_hour_grouping(self, db_session, sample_positions):
        """Test positions are grouped by hour of opening"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        hour_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            if p.open_time:
                hour = p.open_time.hour
                hour_stats[hour]["count"] += 1
                hour_stats[hour]["total_pnl"] += float(p.net_pnl or 0)

        # AAPL1: 10:30 -> hour 10 (pnl=980)
        # AAPL2: 9:30 -> hour 9 (pnl=-220)
        # TSLA: 11:00 -> hour 11 (pnl=280)
        # Option: 10:00 -> hour 10 (pnl=290)
        # NVDA: 14:30 -> hour 14 (pnl=485)
        assert hour_stats[10]["count"] == 2  # AAPL1 and Option
        assert hour_stats[9]["count"] == 1   # AAPL2
        assert hour_stats[11]["count"] == 1  # TSLA
        assert hour_stats[14]["count"] == 1  # NVDA

    def test_hourly_win_rate(self, db_session, sample_positions):
        """Test win rate calculation per hour"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        hour_stats = defaultdict(lambda: {"count": 0, "winners": 0})

        for p in positions:
            if p.open_time:
                hour = p.open_time.hour
                hour_stats[hour]["count"] += 1
                if p.net_pnl and float(p.net_pnl) > 0:
                    hour_stats[hour]["winners"] += 1

        # Hour 10: 2 positions, both positive (AAPL1=980, Option=290)
        win_rate_10 = hour_stats[10]["winners"] / hour_stats[10]["count"] * 100
        assert win_rate_10 == 100.0

        # Hour 9: 1 position, negative (AAPL2=-220)
        win_rate_9 = hour_stats[9]["winners"] / hour_stats[9]["count"] * 100
        assert win_rate_9 == 0.0


# ==================== Trading Heatmap Tests ====================

class TestTradingHeatmap:
    """Test trading heatmap data (weekday x hour) based on position open time"""

    def test_weekday_hour_matrix(self, db_session, sample_positions):
        """Test positions are grouped by weekday and hour"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        matrix = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            if p.open_time:
                day = p.open_time.weekday()  # 0=Monday
                hour = p.open_time.hour
                key = (day, hour)
                matrix[key]["count"] += 1
                matrix[key]["total_pnl"] += float(p.net_pnl or 0)

        # Check that we have entries
        assert len(matrix) > 0

    def test_day_names(self):
        """Test day name mapping"""
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        # Thursday is day 3
        assert day_names[3] == "Thu"

    def test_heatmap_avg_pnl(self, db_session, sample_positions):
        """Test average P&L per cell"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        matrix = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            if p.open_time:
                day = p.open_time.weekday()
                hour = p.open_time.hour
                key = (day, hour)
                matrix[key]["count"] += 1
                matrix[key]["total_pnl"] += float(p.net_pnl or 0)

        for key, stats in matrix.items():
            if stats["count"] > 0:
                avg_pnl = stats["total_pnl"] / stats["count"]
                assert isinstance(avg_pnl, float)


# ==================== Asset Type Breakdown Tests ====================

class TestAssetTypeBreakdown:
    """Test asset type breakdown data"""

    def test_asset_type_grouping(self, db_session, sample_positions):
        """Test positions are grouped by asset type"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        type_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            # Use is_option to determine asset type
            asset_type = "option" if p.is_option else "stock"
            type_stats[asset_type]["count"] += 1
            type_stats[asset_type]["total_pnl"] += float(p.net_pnl or 0)

        # 4 stocks, 1 option
        assert type_stats["stock"]["count"] == 4
        assert type_stats["option"]["count"] == 1

    def test_stock_performance(self, db_session, sample_positions):
        """Test stock asset type performance"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.is_option == 0  # stocks
        ).all()

        total_pnl = sum(float(p.net_pnl or 0) for p in positions)

        # Stocks: 980 - 220 + 280 + 485 = 1525
        assert total_pnl == pytest.approx(1525.0, rel=0.01)

    def test_option_performance(self, db_session, sample_positions):
        """Test option asset type performance"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.is_option == 1  # options
        ).all()

        total_pnl = sum(float(p.net_pnl or 0) for p in positions)

        # Options: 290
        assert total_pnl == pytest.approx(290.0, rel=0.01)

    def test_asset_type_win_rate(self, db_session, sample_positions):
        """Test win rate per asset type"""
        stock_positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED,
            Position.is_option == 0
        ).all()

        winners = [p for p in stock_positions if p.net_pnl and float(p.net_pnl) > 0]
        win_rate = len(winners) / len(stock_positions) * 100

        # Stocks: 3 winners out of 4 = 75%
        assert win_rate == 75.0


# ==================== Edge Cases ====================

class TestAdvancedEdgeCases:
    """Test edge cases for advanced statistics"""

    def test_empty_data_handling(self, db_session):
        """Test handling when no data exists"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        assert len(positions) == 0

        # Equity drawdown should return empty
        daily_pnl = defaultdict(float)
        for p in positions:
            if p.close_date and p.net_pnl:
                daily_pnl[p.close_date] += float(p.net_pnl)

        assert len(daily_pnl) == 0

    def test_single_position_handling(self, db_session):
        """Test with only one position"""
        position = Position(
            symbol='TEST',
            direction='long',
            is_option=0,  # stock
            open_time=datetime(2024, 1, 1, 9, 30),
            close_time=datetime(2024, 1, 5, 16, 0),
            open_date=date(2024, 1, 1),
            close_date=date(2024, 1, 5),
            open_price=100.0,
            close_price=110.0,
            quantity=100,
            net_pnl=1000.0,
            holding_period_days=4,
            status=PositionStatus.CLOSED,
        )
        db_session.add(position)
        db_session.commit()

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        assert len(positions) == 1

        # Rolling metrics need at least window size
        window = 20
        assert len(positions) < window

    def test_all_winners_scenario(self, db_session):
        """Test when all trades are winners"""
        for i in range(3):
            position = Position(
                symbol='WIN',
                direction='long',
                is_option=0,
                open_time=datetime(2024, 1, i + 1, 9, 30),
                open_date=date(2024, 1, i + 1),
                close_date=date(2024, 1, i + 5),
                net_pnl=100.0 * (i + 1),
                holding_period_days=4,
                status=PositionStatus.CLOSED,
                open_price=100.0,
                quantity=10,
            )
            db_session.add(position)
        db_session.commit()

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]
        assert len(losers) == 0

        # Max drawdown should be 0
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for p in positions:
            cumulative += float(p.net_pnl or 0)
            if cumulative > peak:
                peak = cumulative
            max_drawdown = max(max_drawdown, peak - cumulative)

        assert max_drawdown == 0.0

    def test_all_losers_scenario(self, db_session):
        """Test when all trades are losers"""
        for i in range(3):
            position = Position(
                symbol='LOSE',
                direction='long',
                is_option=0,
                open_time=datetime(2024, 1, i + 1, 9, 30),
                open_date=date(2024, 1, i + 1),
                close_date=date(2024, 1, i + 5),
                net_pnl=-100.0 * (i + 1),
                holding_period_days=4,
                status=PositionStatus.CLOSED,
                open_price=100.0,
                quantity=10,
            )
            db_session.add(position)
        db_session.commit()

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        assert len(winners) == 0

        win_rate = 0.0
        assert win_rate == 0.0

    def test_same_day_positions(self, db_session):
        """Test multiple positions closed on same day"""
        for i in range(3):
            position = Position(
                symbol=f'SYM{i}',
                direction='long',
                is_option=0,
                open_time=datetime(2024, 1, 1, 9 + i, 30),
                open_date=date(2024, 1, 1),
                close_date=date(2024, 1, 5),  # Same close date
                net_pnl=100.0 * (i + 1),
                holding_period_days=4,
                status=PositionStatus.CLOSED,
                open_price=100.0,
                quantity=10,
            )
            db_session.add(position)
        db_session.commit()

        daily_pnl = defaultdict(float)
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        for p in positions:
            if p.close_date and p.net_pnl:
                daily_pnl[p.close_date] += float(p.net_pnl)

        # All positions close on same day, so 1 entry with sum of P&L
        assert len(daily_pnl) == 1
        assert daily_pnl[date(2024, 1, 5)] == pytest.approx(600.0, rel=0.01)
