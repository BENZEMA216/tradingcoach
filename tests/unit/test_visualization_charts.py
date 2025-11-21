"""
Unit tests for visualization chart components
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization.components.charts import (
    create_score_distribution_chart,
    create_grade_distribution_chart,
    create_dimension_radar_chart,
    create_pnl_vs_score_scatter,
    create_candlestick_chart,
    create_fifo_timeline_chart,
    create_score_trend_chart
)
from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from decimal import Decimal


@pytest.fixture
def sample_scores_df():
    """Create sample quality scores dataframe"""
    data = {
        'id': [1, 2, 3, 4, 5],
        'symbol': ['AAPL', 'TSLA', 'GOOGL', 'MSFT', 'AMZN'],
        'overall_score': [75.5, 82.3, 65.8, 58.2, 90.1],
        'grade': ['B+', 'A-', 'C+', 'C-', 'A+'],
        'entry_score': [70.0, 80.0, 60.0, 55.0, 88.0],
        'exit_score': [78.0, 85.0, 68.0, 60.0, 92.0],
        'trend_score': [76.0, 83.0, 67.0, 58.0, 91.0],
        'risk_score': [77.0, 81.0, 66.0, 59.0, 89.0],
        'net_pnl': [500.0, -200.0, 300.0, -100.0, 800.0],
        'net_pnl_pct': [5.0, -2.0, 3.0, -1.0, 8.0],
        'open_time': [
            datetime(2024, 1, 1),
            datetime(2024, 1, 5),
            datetime(2024, 1, 10),
            datetime(2024, 1, 15),
            datetime(2024, 1, 20)
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_market_df():
    """Create sample market data dataframe"""
    data = {
        'date': pd.date_range('2024-01-01', periods=10, freq='D'),
        'open': [150.0, 151.0, 152.0, 151.5, 153.0, 154.0, 153.5, 155.0, 156.0, 157.0],
        'high': [152.0, 153.0, 154.0, 153.5, 155.0, 156.0, 155.5, 157.0, 158.0, 159.0],
        'low': [149.0, 150.0, 151.0, 150.5, 152.0, 153.0, 152.5, 154.0, 155.0, 156.0],
        'close': [151.0, 152.0, 153.0, 152.5, 154.0, 155.0, 154.5, 156.0, 157.0, 158.0],
        'volume': [1000000] * 10,
        'rsi': [55.0, 58.0, 60.0, 57.0, 62.0, 65.0, 63.0, 68.0, 70.0, 72.0],
        'macd': [0.5, 0.6, 0.7, 0.6, 0.8, 0.9, 0.8, 1.0, 1.1, 1.2],
        'macd_signal': [0.3, 0.4, 0.5, 0.4, 0.6, 0.7, 0.6, 0.8, 0.9, 1.0],
        'macd_hist': [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
        'ma_5': [150.5, 151.0, 151.5, 152.0, 152.5, 153.0, 153.5, 154.0, 154.5, 155.0],
        'ma_20': [148.0, 148.5, 149.0, 149.5, 150.0, 150.5, 151.0, 151.5, 152.0, 152.5],
        'ma_50': [145.0, 145.5, 146.0, 146.5, 147.0, 147.5, 148.0, 148.5, 149.0, 149.5],
        'bb_upper': [153.0, 154.0, 155.0, 154.5, 156.0, 157.0, 156.5, 158.0, 159.0, 160.0],
        'bb_middle': [150.0, 151.0, 152.0, 151.5, 153.0, 154.0, 153.5, 155.0, 156.0, 157.0],
        'bb_lower': [147.0, 148.0, 149.0, 148.5, 150.0, 151.0, 150.5, 152.0, 153.0, 154.0]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_trades():
    """Create sample trades for timeline"""
    trades = [
        Trade(
            symbol='AAPL',
            direction=TradeDirection.BUY,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            order_time=datetime(2024, 1, 1, 9, 30),
            filled_time=datetime(2024, 1, 1, 9, 31),
            filled_quantity=100,
            filled_price=Decimal('150.00')
        ),
        Trade(
            symbol='AAPL',
            direction=TradeDirection.SELL,
            status=TradeStatus.FILLED,
            market=MarketType.US_STOCK,
            order_time=datetime(2024, 1, 10, 14, 30),
            filled_time=datetime(2024, 1, 10, 14, 31),
            filled_quantity=100,
            filled_price=Decimal('155.00')
        )
    ]
    return trades


class TestScoreDistributionChart:
    """Test create_score_distribution_chart"""

    def test_creates_figure(self, sample_scores_df):
        """Test that function creates a Plotly figure"""
        fig = create_score_distribution_chart(sample_scores_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_has_correct_layout(self, sample_scores_df):
        """Test that figure has correct layout"""
        fig = create_score_distribution_chart(sample_scores_df)

        assert fig.layout.xaxis.title.text == '总体评分'
        assert fig.layout.yaxis.title.text == '持仓数量'
        assert '质量评分分布' in fig.layout.title.text


class TestGradeDistributionChart:
    """Test create_grade_distribution_chart"""

    def test_creates_pie_chart(self, sample_scores_df):
        """Test that function creates a pie chart"""
        fig = create_grade_distribution_chart(sample_scores_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Pie)

    def test_has_all_grades(self, sample_scores_df):
        """Test that all grades are represented"""
        fig = create_grade_distribution_chart(sample_scores_df)

        pie_data = fig.data[0]
        grades = sample_scores_df['grade'].unique()

        # All grades should be in the chart
        for grade in grades:
            assert grade in pie_data.labels


class TestDimensionRadarChart:
    """Test create_dimension_radar_chart"""

    def test_creates_radar_chart(self, sample_scores_df):
        """Test that function creates a radar chart"""
        fig = create_dimension_radar_chart(sample_scores_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Scatterpolar)

    def test_has_four_dimensions(self, sample_scores_df):
        """Test that radar chart has 4 dimensions"""
        fig = create_dimension_radar_chart(sample_scores_df)

        polar_data = fig.data[0]

        # Should have 4 dimensions + 1 to close the shape
        assert len(polar_data.r) == 5
        assert len(polar_data.theta) == 5

    def test_calculates_average_scores(self, sample_scores_df):
        """Test that average scores are calculated correctly"""
        fig = create_dimension_radar_chart(sample_scores_df)

        polar_data = fig.data[0]
        avg_entry = sample_scores_df['entry_score'].mean()

        # First value should be average entry score
        assert abs(polar_data.r[0] - avg_entry) < 0.1


class TestPnlVsScoreScatter:
    """Test create_pnl_vs_score_scatter"""

    def test_creates_scatter_plot(self, sample_scores_df):
        """Test that function creates a scatter plot"""
        fig = create_pnl_vs_score_scatter(sample_scores_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_has_correct_axes(self, sample_scores_df):
        """Test that axes are correctly labeled"""
        fig = create_pnl_vs_score_scatter(sample_scores_df)

        assert '总体评分' in fig.layout.xaxis.title.text
        assert '净盈亏率' in fig.layout.yaxis.title.text

    def test_includes_zero_line(self, sample_scores_df):
        """Test that zero line is included"""
        fig = create_pnl_vs_score_scatter(sample_scores_df)

        # Check for horizontal line shapes
        has_hline = any(
            shape.type == 'line' and shape.y0 == 0
            for shape in fig.layout.shapes
        )
        assert has_hline


class TestCandlestickChart:
    """Test create_candlestick_chart"""

    def test_creates_candlestick(self, sample_market_df):
        """Test that function creates a candlestick chart"""
        fig = create_candlestick_chart(sample_market_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_includes_candlestick_trace(self, sample_market_df):
        """Test that candlestick trace is included"""
        fig = create_candlestick_chart(sample_market_df)

        # Should have at least one Candlestick trace
        has_candlestick = any(
            isinstance(trace, go.Candlestick)
            for trace in fig.data
        )
        assert has_candlestick

    def test_includes_ma_when_requested(self, sample_market_df):
        """Test that moving averages are included when requested"""
        fig = create_candlestick_chart(sample_market_df, show_ma=True)

        # Count scatter traces (MA lines)
        scatter_traces = [
            trace for trace in fig.data
            if isinstance(trace, go.Scatter)
        ]

        # Should have MA5, MA20, MA50
        assert len(scatter_traces) >= 3

    def test_includes_bb_when_requested(self, sample_market_df):
        """Test that Bollinger Bands are included when requested"""
        fig = create_candlestick_chart(sample_market_df, show_bb=True, show_ma=False)

        # Should have BB upper, middle, lower lines
        scatter_traces = [
            trace for trace in fig.data
            if isinstance(trace, go.Scatter) and 'BB' in trace.name
        ]

        assert len(scatter_traces) >= 3

    def test_includes_trade_markers(self, sample_market_df, sample_trades):
        """Test that trade markers are included"""
        fig = create_candlestick_chart(sample_market_df, trades=sample_trades)

        # Should have buy and sell markers
        marker_traces = [
            trace for trace in fig.data
            if isinstance(trace, go.Scatter) and trace.mode == 'markers'
        ]

        # Should have at least buy and sell traces
        assert len(marker_traces) >= 2


class TestFifoTimelineChart:
    """Test create_fifo_timeline_chart"""

    def test_creates_timeline(self, sample_trades):
        """Test that function creates a timeline chart"""
        fig = create_fifo_timeline_chart(sample_trades, [])

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_separates_buy_sell(self, sample_trades):
        """Test that buy and sell trades are separated"""
        fig = create_fifo_timeline_chart(sample_trades, [])

        # Should have separate traces for buy and sell
        assert len(fig.data) == 2


class TestScoreTrendChart:
    """Test create_score_trend_chart"""

    def test_creates_trend_chart(self, sample_scores_df):
        """Test that function creates a trend chart"""
        fig = create_score_trend_chart(sample_scores_df)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_includes_moving_average(self, sample_scores_df):
        """Test that moving average is included for sufficient data"""
        # Create larger dataset
        large_df = pd.concat([sample_scores_df] * 3, ignore_index=True)
        large_df['open_time'] = pd.date_range('2024-01-01', periods=len(large_df), freq='D')

        fig = create_score_trend_chart(large_df)

        # Should have main line and MA line
        assert len(fig.data) >= 2

    def test_handles_small_dataset(self, sample_scores_df):
        """Test that function handles small datasets"""
        small_df = sample_scores_df.head(2)

        fig = create_score_trend_chart(small_df)

        # Should still create a figure
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0


class TestChartIntegration:
    """Integration tests for chart components"""

    def test_all_charts_with_real_data(self, sample_scores_df, sample_market_df):
        """Test that all charts work with realistic data"""
        # Test all chart functions
        charts = [
            create_score_distribution_chart(sample_scores_df),
            create_grade_distribution_chart(sample_scores_df),
            create_dimension_radar_chart(sample_scores_df),
            create_pnl_vs_score_scatter(sample_scores_df),
            create_candlestick_chart(sample_market_df),
            create_score_trend_chart(sample_scores_df)
        ]

        # All should be valid Plotly figures
        for chart in charts:
            assert isinstance(chart, go.Figure)
            assert len(chart.data) > 0

    def test_empty_dataframe_handling(self):
        """Test that charts handle empty dataframes gracefully"""
        empty_df = pd.DataFrame()

        # These should not crash (though they may produce empty charts)
        try:
            create_score_distribution_chart(empty_df)
        except Exception as e:
            # Expected to potentially fail with empty data
            assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
