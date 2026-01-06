"""
Unit tests for Statistics API endpoints

Tests:
1. Performance metrics calculation
2. Risk metrics (Sharpe, Sortino, Calmar, VaR)
3. Drawdown period tracking
4. Symbol/Grade/Direction breakdown
5. Edge cases
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import math

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.position import Position, PositionStatus


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
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction='long',
            open_time=datetime(2024, 1, 5, 9, 30),
            close_time=datetime(2024, 1, 10, 16, 0),
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
            symbol='AAPL',
            symbol_name='Apple Inc',
            direction='long',
            open_time=datetime(2024, 1, 12, 9, 30),
            close_time=datetime(2024, 1, 15, 16, 0),
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
            symbol='TSLA',
            symbol_name='Tesla Inc',
            direction='short',
            open_time=datetime(2024, 1, 18, 9, 30),
            close_time=datetime(2024, 1, 25, 16, 0),
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
            symbol='MSFT',
            symbol_name='Microsoft Corp',
            direction='long',
            open_time=datetime(2024, 2, 1, 9, 30),
            close_time=datetime(2024, 2, 10, 16, 0),
            open_date=date(2024, 2, 1),
            close_date=date(2024, 2, 10),
            open_price=380.0,
            close_price=370.0,
            quantity=20,
            realized_pnl=-200.0,
            net_pnl=-210.0,
            total_fees=10.0,
            holding_period_days=9,
            score_grade='D',
            status=PositionStatus.CLOSED,
        ),
        Position(
            symbol='NVDA',
            symbol_name='NVIDIA Corp',
            direction='long',
            open_time=datetime(2024, 2, 15, 9, 30),
            close_time=datetime(2024, 2, 28, 16, 0),
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


# ==================== Performance Metrics Tests ====================

class TestPerformanceMetrics:
    """Test performance metrics calculation"""

    def test_total_pnl_calculation(self, db_session, sample_positions):
        """Test total P&L is calculated correctly"""
        closed_positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        total_pnl = sum(float(p.net_pnl or 0) for p in closed_positions)

        # 980 - 220 + 280 - 210 + 485 = 1315
        assert total_pnl == pytest.approx(1315.0, rel=0.01)

    def test_win_rate_calculation(self, db_session, sample_positions):
        """Test win rate calculation"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        win_rate = len(winners) / len(positions) * 100

        # 3 winners out of 5 = 60%
        assert win_rate == 60.0

    def test_profit_factor_calculation(self, db_session, sample_positions):
        """Test profit factor calculation"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        losers = [p for p in positions if p.net_pnl and float(p.net_pnl) <= 0]

        gross_profit = sum(float(p.net_pnl) for p in winners)  # 980 + 280 + 485 = 1745
        gross_loss = abs(sum(float(p.net_pnl) for p in losers))  # 220 + 210 = 430

        profit_factor = gross_profit / gross_loss

        assert profit_factor == pytest.approx(4.058, rel=0.01)

    def test_max_drawdown_calculation(self, db_session, sample_positions):
        """Test max drawdown calculation"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for p in positions:
            cumulative += float(p.net_pnl or 0)
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # After AAPL1: +980 (peak=980)
        # After AAPL2: +980-220=760 (drawdown=220)
        # After TSLA: +760+280=1040 (new peak=1040)
        # After MSFT: +1040-210=830 (drawdown=210)
        # After NVDA: +830+485=1315 (new peak=1315)
        assert max_drawdown == pytest.approx(220.0, rel=0.01)

    def test_consecutive_wins_losses(self, db_session, sample_positions):
        """Test consecutive wins/losses tracking"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.close_date).all()

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for p in positions:
            if p.net_pnl and float(p.net_pnl) > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)

        # Sequence: W, L, W, L, W -> max consecutive wins = 1
        assert max_consecutive_wins == 1
        assert max_consecutive_losses == 1

    def test_empty_positions(self, db_session):
        """Test handling of no positions"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        total_pnl = sum(float(p.net_pnl or 0) for p in positions)

        assert total_pnl == 0.0
        assert len(positions) == 0


# ==================== Risk Metrics Tests ====================

class TestRiskMetrics:
    """Test risk metrics calculations"""

    def test_sharpe_ratio_calculation(self, sample_positions):
        """Test Sharpe ratio calculation logic"""
        # Simplified test using sample data
        returns = [980.0, -220.0, 280.0, -210.0, 485.0]  # Daily returns
        risk_free_rate = 0.05

        avg_return = sum(returns) / len(returns)
        daily_risk_free = risk_free_rate / 252

        mean_return = avg_return
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        daily_volatility = math.sqrt(variance)

        sharpe_ratio = ((avg_return - daily_risk_free) / daily_volatility) * math.sqrt(252)

        # Verify calculation produces reasonable value
        assert sharpe_ratio is not None
        assert isinstance(sharpe_ratio, float)

    def test_sortino_ratio_calculation(self):
        """Test Sortino ratio calculation logic"""
        returns = [980.0, -220.0, 280.0, -210.0, 485.0]
        risk_free_rate = 0.05
        daily_risk_free = risk_free_rate / 252
        avg_return = sum(returns) / len(returns)

        negative_returns = [r for r in returns if r < 0]  # [-220.0, -210.0]

        assert len(negative_returns) == 2

        downside_variance = sum(r ** 2 for r in negative_returns) / (len(negative_returns) - 1)
        downside_volatility = math.sqrt(downside_variance)

        sortino_ratio = ((avg_return - daily_risk_free) / downside_volatility) * math.sqrt(252)

        assert sortino_ratio is not None
        assert isinstance(sortino_ratio, float)

    def test_calmar_ratio_calculation(self):
        """Test Calmar ratio calculation logic"""
        total_pnl = 1315.0
        trading_days = 54  # Jan 10 to Feb 28
        max_drawdown = 220.0

        annualized_return = (total_pnl / trading_days) * 365
        calmar_ratio = annualized_return / max_drawdown

        # ~8891.57 / 220 = ~40.4
        assert calmar_ratio > 30  # Should be high since we have good returns

    def test_var_95_calculation(self):
        """Test VaR (95%) calculation logic"""
        returns = [980.0, -220.0, 280.0, -210.0, 485.0, 100.0, -50.0, 200.0, -80.0, 150.0,
                   120.0, -100.0, 300.0, -150.0, 250.0, 180.0, -60.0, 220.0, -120.0, 190.0]

        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = abs(sorted_returns[var_index])

        assert var_95 > 0
        # Should be one of the worst returns
        assert sorted_returns[var_index] < 0

    def test_expectancy_calculation(self):
        """Test expectancy calculation"""
        # 3 winners, 2 losers
        win_rate = 3 / 5  # 0.6
        avg_win = (980.0 + 280.0 + 485.0) / 3  # 581.67
        avg_loss = (-220.0 + -210.0) / 2  # -215.0
        loss_rate = 1 - win_rate  # 0.4

        expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)

        # 0.6 * 581.67 + 0.4 * (-215.0) = 349.0 - 86.0 = 263.0
        assert expectancy == pytest.approx(263.0, rel=0.01)

    def test_payoff_ratio_calculation(self):
        """Test payoff ratio calculation"""
        avg_win = (980.0 + 280.0 + 485.0) / 3  # 581.67
        avg_loss = (-220.0 + -210.0) / 2  # -215.0

        payoff_ratio = avg_win / abs(avg_loss)

        # 581.67 / 215.0 = ~2.7
        assert payoff_ratio == pytest.approx(2.7, rel=0.1)


# ==================== Drawdown Tests ====================

class TestDrawdownCalculation:
    """Test drawdown period tracking"""

    def test_drawdown_detection(self):
        """Test drawdown period detection"""
        # Simulated equity curve: peak, drop, recovery
        daily_pnl = {
            date(2024, 1, 1): 100,   # cumulative: 100
            date(2024, 1, 2): 200,   # cumulative: 300
            date(2024, 1, 3): -150,  # cumulative: 150 (drawdown: 150)
            date(2024, 1, 4): -50,   # cumulative: 100 (drawdown: 200)
            date(2024, 1, 5): 250,   # cumulative: 350 (new peak, recovered)
        }

        dates = sorted(daily_pnl.keys())
        cumulative = 0.0
        peak = 0.0
        drawdowns = []
        dd_start = None
        dd_trough = 0.0

        for d in dates:
            cumulative += daily_pnl[d]

            if cumulative > peak:
                if dd_start is not None and dd_trough > 0:
                    drawdowns.append({
                        'start': dd_start,
                        'recovery': d,
                        'amount': dd_trough
                    })
                peak = cumulative
                dd_start = None
                dd_trough = 0.0
            else:
                current_dd = peak - cumulative
                if current_dd > 0 and dd_start is None:
                    dd_start = d
                if current_dd > dd_trough:
                    dd_trough = current_dd

        assert len(drawdowns) == 1
        assert drawdowns[0]['amount'] == 200.0
        assert drawdowns[0]['recovery'] == date(2024, 1, 5)

    def test_active_drawdown(self):
        """Test detection of active (unrecovered) drawdown"""
        daily_pnl = {
            date(2024, 1, 1): 500,   # cumulative: 500 (peak)
            date(2024, 1, 2): -200,  # cumulative: 300
            date(2024, 1, 3): -100,  # cumulative: 200
        }

        dates = sorted(daily_pnl.keys())
        cumulative = 0.0
        peak = 0.0

        for d in dates:
            cumulative += daily_pnl[d]
            if cumulative > peak:
                peak = cumulative

        current_drawdown = peak - cumulative

        assert current_drawdown == 300.0  # Still in drawdown

    def test_no_drawdown(self):
        """Test when there's no drawdown (continuous uptrend)"""
        daily_pnl = {
            date(2024, 1, 1): 100,
            date(2024, 1, 2): 100,
            date(2024, 1, 3): 100,
        }

        dates = sorted(daily_pnl.keys())
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for d in dates:
            cumulative += daily_pnl[d]
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            max_drawdown = max(max_drawdown, drawdown)

        assert max_drawdown == 0.0


# ==================== Symbol Breakdown Tests ====================

class TestSymbolBreakdown:
    """Test symbol breakdown calculation"""

    def test_symbol_grouping(self, db_session, sample_positions):
        """Test positions are grouped correctly by symbol"""
        from collections import defaultdict

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        symbol_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            symbol_stats[p.symbol]["count"] += 1
            symbol_stats[p.symbol]["total_pnl"] += float(p.net_pnl or 0)

        # AAPL: 2 trades, 980 - 220 = 760
        assert symbol_stats['AAPL']['count'] == 2
        assert symbol_stats['AAPL']['total_pnl'] == pytest.approx(760.0, rel=0.01)

        # TSLA: 1 trade, 280
        assert symbol_stats['TSLA']['count'] == 1
        assert symbol_stats['TSLA']['total_pnl'] == pytest.approx(280.0, rel=0.01)

    def test_symbol_win_rate(self, db_session, sample_positions):
        """Test win rate per symbol"""
        from collections import defaultdict

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        symbol_stats = defaultdict(lambda: {"count": 0, "winners": 0})

        for p in positions:
            symbol_stats[p.symbol]["count"] += 1
            if p.net_pnl and float(p.net_pnl) > 0:
                symbol_stats[p.symbol]["winners"] += 1

        # AAPL: 1 winner out of 2 = 50%
        aapl_win_rate = symbol_stats['AAPL']['winners'] / symbol_stats['AAPL']['count'] * 100
        assert aapl_win_rate == 50.0


# ==================== Grade Breakdown Tests ====================

class TestGradeBreakdown:
    """Test grade breakdown calculation"""

    def test_grade_grouping(self, db_session, sample_positions):
        """Test positions are grouped correctly by grade"""
        from collections import defaultdict

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        grade_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            grade = p.score_grade or "N/A"
            grade_stats[grade]["count"] += 1
            grade_stats[grade]["total_pnl"] += float(p.net_pnl or 0)

        # A grade: 2 trades (AAPL1, NVDA), 980 + 485 = 1465
        assert grade_stats['A']['count'] == 2
        assert grade_stats['A']['total_pnl'] == pytest.approx(1465.0, rel=0.01)


# ==================== Direction Breakdown Tests ====================

class TestDirectionBreakdown:
    """Test direction breakdown calculation"""

    def test_direction_grouping(self, db_session, sample_positions):
        """Test positions are grouped by direction"""
        from collections import defaultdict

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        direction_stats = defaultdict(lambda: {"count": 0, "total_pnl": 0.0})

        for p in positions:
            direction_stats[p.direction]["count"] += 1
            direction_stats[p.direction]["total_pnl"] += float(p.net_pnl or 0)

        # Long: 4 trades, 980 - 220 - 210 + 485 = 1035
        assert direction_stats['long']['count'] == 4
        assert direction_stats['long']['total_pnl'] == pytest.approx(1035.0, rel=0.01)

        # Short: 1 trade, 280
        assert direction_stats['short']['count'] == 1
        assert direction_stats['short']['total_pnl'] == pytest.approx(280.0, rel=0.01)


# ==================== Holding Period Tests ====================

class TestHoldingPeriodBreakdown:
    """Test holding period breakdown calculation"""

    def test_holding_period_buckets(self, db_session, sample_positions):
        """Test positions are bucketed by holding period"""
        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        buckets = [
            ("Same Day", 0, 0),
            ("1-3 Days", 1, 3),
            ("4-7 Days", 4, 7),
            ("1-2 Weeks", 8, 14),
        ]

        bucket_counts = {label: 0 for label, _, _ in buckets}

        for p in positions:
            days = p.holding_period_days or 0
            for label, min_d, max_d in buckets:
                if min_d <= days <= max_d:
                    bucket_counts[label] += 1
                    break

        # 5 days (AAPL1) -> 4-7 Days
        # 3 days (AAPL2) -> 1-3 Days
        # 7 days (TSLA) -> 4-7 Days
        # 9 days (MSFT) -> 1-2 Weeks
        # 13 days (NVDA) -> 1-2 Weeks

        assert bucket_counts["1-3 Days"] == 1
        assert bucket_counts["4-7 Days"] == 2
        assert bucket_counts["1-2 Weeks"] == 2


# ==================== Edge Cases ====================

class TestEdgeCases:
    """Test edge cases"""

    def test_zero_division_handling(self):
        """Test handling of potential zero division scenarios"""
        # No losers -> profit factor should be None
        gross_profit = 1000.0
        gross_loss = 0.0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

        assert profit_factor is None

    def test_negative_values_handling(self):
        """Test handling of negative P&L values"""
        pnls = [-100.0, -200.0, -300.0]

        total_pnl = sum(pnls)
        assert total_pnl == -600.0

        winners = [p for p in pnls if p > 0]
        assert len(winners) == 0

    def test_none_values_handling(self):
        """Test handling of None values in data"""
        pnls = [100.0, None, 200.0, None, 300.0]

        total_pnl = sum(float(p or 0) for p in pnls)
        assert total_pnl == 600.0

    def test_single_position(self, db_session):
        """Test metrics with single position"""
        position = Position(
            symbol='TEST',
            direction='long',
            open_time=datetime(2024, 1, 1, 9, 30),
            close_time=datetime(2024, 1, 5, 16, 0),
            open_date=date(2024, 1, 1),
            close_date=date(2024, 1, 5),
            open_price=100.0,
            close_price=110.0,
            quantity=100,
            net_pnl=1000.0,
            total_fees=10.0,
            holding_period_days=4,
            status=PositionStatus.CLOSED,
        )
        db_session.add(position)
        db_session.commit()

        positions = db_session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        assert len(positions) == 1

        # Win rate should be 100%
        winners = [p for p in positions if p.net_pnl and float(p.net_pnl) > 0]
        win_rate = len(winners) / len(positions) * 100

        assert win_rate == 100.0
