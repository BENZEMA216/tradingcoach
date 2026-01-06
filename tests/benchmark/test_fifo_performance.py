"""
FIFO Matcher Performance Benchmark Tests

input: src/matchers/symbol_matcher.py, src/matchers/fifo_matcher.py
output: 性能基准数据，验证大批量数据处理性能
pos: 性能测试 - 防止 FIFO 配对算法性能退化

使用 pytest-benchmark 插件运行:
    pytest tests/benchmark/ -v --benchmark-only

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""
import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType
from src.matchers.symbol_matcher import SymbolMatcher


def generate_trade_objects(count: int, symbol: str = "AAPL") -> list:
    """生成模拟 Trade 对象用于基准测试"""
    trades = []
    base_time = datetime(2024, 1, 1, 9, 30, tzinfo=timezone.utc)
    price = 150.0

    for i in range(count):
        # 交替生成买入和卖出
        is_buy = i % 2 == 0
        direction = TradeDirection.BUY if is_buy else TradeDirection.SELL
        qty = random.randint(10, 100)
        trade_price = Decimal(str(price + random.uniform(-5, 5)))

        trade = Trade(
            id=i + 1,
            symbol=symbol,
            symbol_name=f"{symbol} Inc.",
            direction=direction,
            status=TradeStatus.FILLED,
            filled_quantity=qty,
            filled_price=trade_price,
            filled_amount=trade_price * qty,
            filled_time=base_time + timedelta(minutes=i * 5),
            trade_date=(base_time + timedelta(minutes=i * 5)).date(),
            market=MarketType.US_STOCK,
            currency="USD",
            commission=Decimal("1.50"),
            total_fee=Decimal("1.50"),
            trade_fingerprint=f"{symbol}_{direction.value}_{i}",
        )
        trades.append(trade)

    return trades


class TestFIFOMatcherPerformance:
    """FIFO 配对算法性能基准测试"""

    @pytest.mark.benchmark(group="fifo-small")
    def test_fifo_100_trades(self, benchmark):
        """基准测试：100笔交易配对"""
        trades = generate_trade_objects(100)
        matcher = SymbolMatcher("AAPL")

        def run_matching():
            m = SymbolMatcher("AAPL")
            for trade in trades:
                m.process_trade(trade)
            return m.matched_positions

        result = benchmark(run_matching)
        assert result is not None

    @pytest.mark.benchmark(group="fifo-medium")
    def test_fifo_1000_trades(self, benchmark):
        """基准测试：1000笔交易配对"""
        trades = generate_trade_objects(1000)

        def run_matching():
            m = SymbolMatcher("AAPL")
            for trade in trades:
                m.process_trade(trade)
            return m.matched_positions

        result = benchmark(run_matching)
        assert result is not None

    @pytest.mark.benchmark(group="fifo-large")
    def test_fifo_5000_trades(self, benchmark):
        """基准测试：5000笔交易配对"""
        trades = generate_trade_objects(5000)

        def run_matching():
            m = SymbolMatcher("AAPL")
            for trade in trades:
                m.process_trade(trade)
            return m.matched_positions

        result = benchmark(run_matching)
        assert result is not None


class TestIndicatorCalculationPerformance:
    """技术指标计算性能基准测试"""

    @pytest.fixture
    def sample_market_data(self):
        """生成示例市场数据"""
        import pandas as pd
        import numpy as np

        dates = pd.date_range(start='2024-01-01', periods=500, freq='D')
        return pd.DataFrame({
            'date': dates,
            'open': np.random.uniform(100, 200, 500),
            'high': np.random.uniform(105, 210, 500),
            'low': np.random.uniform(95, 195, 500),
            'close': np.random.uniform(100, 200, 500),
            'volume': np.random.randint(1000000, 10000000, 500),
        })

    @pytest.mark.benchmark(group="indicators")
    def test_calculate_rsi(self, benchmark, sample_market_data):
        """基准测试：RSI 计算"""
        from src.indicators.calculator import IndicatorCalculator

        calc = IndicatorCalculator()
        df = sample_market_data.rename(columns={'close': 'Close'})

        def run_calc():
            return calc.calculate_rsi(df, period=14)

        result = benchmark(run_calc)
        assert result is not None

    @pytest.mark.benchmark(group="indicators")
    def test_calculate_macd(self, benchmark, sample_market_data):
        """基准测试：MACD 计算"""
        from src.indicators.calculator import IndicatorCalculator

        calc = IndicatorCalculator()
        df = sample_market_data.rename(columns={'close': 'Close'})

        def run_calc():
            return calc.calculate_macd(df)

        result = benchmark(run_calc)
        assert result is not None

    @pytest.mark.benchmark(group="indicators")
    def test_calculate_bollinger_bands(self, benchmark, sample_market_data):
        """基准测试：布林带计算"""
        from src.indicators.calculator import IndicatorCalculator

        calc = IndicatorCalculator()
        df = sample_market_data.rename(columns={'close': 'Close'})

        def run_calc():
            return calc.calculate_bollinger_bands(df)

        result = benchmark(run_calc)
        assert result is not None


# 性能基准阈值（可选）
class TestPerformanceThresholds:
    """性能阈值测试 - 确保性能不退化"""

    @pytest.mark.slow
    def test_fifo_under_2_seconds(self):
        """FIFO 配对 5000 笔交易应在 2 秒内完成"""
        import time

        trades = generate_trade_objects(5000)

        start = time.time()
        matcher = SymbolMatcher("AAPL")
        for trade in trades:
            matcher.process_trade(trade)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"FIFO matching took {elapsed:.2f}s, expected < 2s"

    @pytest.mark.slow
    def test_indicator_batch_under_1_second(self):
        """指标计算 500 天数据应在 1 秒内完成"""
        import time
        import pandas as pd
        import numpy as np
        from src.indicators.calculator import IndicatorCalculator

        # 生成测试数据
        dates = pd.date_range(start='2024-01-01', periods=500, freq='D')
        df = pd.DataFrame({
            'date': dates,
            'Open': np.random.uniform(100, 200, 500),
            'High': np.random.uniform(105, 210, 500),
            'Low': np.random.uniform(95, 195, 500),
            'Close': np.random.uniform(100, 200, 500),
            'Volume': np.random.randint(1000000, 10000000, 500),
        })

        calc = IndicatorCalculator()

        start = time.time()
        calc.calculate_rsi(df, period=14)
        calc.calculate_macd(df)
        calc.calculate_bollinger_bands(df)
        calc.calculate_atr(df, period=14)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Indicator calculations took {elapsed:.2f}s, expected < 1s"
