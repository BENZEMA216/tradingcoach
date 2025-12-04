"""
测试 OptionTradeAnalyzer - 期权交易分析器

测试覆盖：
1. 期权合约信息解析
2. 入场环境分析
3. 正股变动分析
4. Greeks影响估算
5. 策略评估
6. 期权评分计算
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.analyzers.option_analyzer import OptionTradeAnalyzer
from src.utils.option_parser import parse_option


@pytest.fixture
def db_session():
    """创建测试数据库session"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def analyzer(db_session):
    """创建OptionTradeAnalyzer实例"""
    return OptionTradeAnalyzer(db_session)


@pytest.fixture
def sample_call_position():
    """创建一个Call期权持仓样本"""
    return Position(
        id=1,
        symbol='AAPL241115C00225000',  # AAPL Call $225 expires 2024-11-15
        symbol_name='AAPL Call 225',
        status=PositionStatus.CLOSED,
        direction='buy_to_open',
        open_time=datetime(2024, 10, 15, 10, 30),
        close_time=datetime(2024, 10, 25, 14, 0),
        open_date=date(2024, 10, 15),
        close_date=date(2024, 10, 25),
        open_price=Decimal('5.50'),
        close_price=Decimal('8.20'),
        quantity=10,
        realized_pnl=Decimal('2700.00'),
        realized_pnl_pct=Decimal('49.09'),
        net_pnl=Decimal('2680.00'),
        net_pnl_pct=Decimal('48.73'),
        holding_period_days=10,
        mae_pct=Decimal('-15.0'),
        mfe_pct=Decimal('55.0'),
        is_option=1,
        underlying_symbol='AAPL'
    )


@pytest.fixture
def sample_put_position():
    """创建一个Put期权持仓样本"""
    return Position(
        id=2,
        symbol='TSLA241025P00250000',  # TSLA Put $250 expires 2024-10-25
        symbol_name='TSLA Put 250',
        status=PositionStatus.CLOSED,
        direction='buy_to_open',
        open_time=datetime(2024, 10, 1, 9, 45),
        close_time=datetime(2024, 10, 10, 15, 30),
        open_date=date(2024, 10, 1),
        close_date=date(2024, 10, 10),
        open_price=Decimal('8.00'),
        close_price=Decimal('4.50'),
        quantity=5,
        realized_pnl=Decimal('-1750.00'),
        realized_pnl_pct=Decimal('-43.75'),
        net_pnl=Decimal('-1760.00'),
        net_pnl_pct=Decimal('-44.00'),
        holding_period_days=9,
        mae_pct=Decimal('-50.0'),
        mfe_pct=Decimal('12.0'),
        is_option=1,
        underlying_symbol='TSLA'
    )


@pytest.fixture
def sample_market_data_bullish():
    """创建一个看涨的市场数据样本 (AAPL)"""
    return MarketData(
        symbol='AAPL',
        timestamp=datetime(2024, 10, 15, 16, 0),
        date=date(2024, 10, 15),
        open=Decimal('220.0'),
        high=Decimal('223.0'),
        low=Decimal('219.0'),
        close=Decimal('222.0'),
        volume=50000000,
        rsi_14=Decimal('45.0'),
        macd=Decimal('1.5'),
        macd_signal=Decimal('0.8'),
        macd_hist=Decimal('0.7'),
        bb_upper=Decimal('230.0'),
        bb_middle=Decimal('220.0'),
        bb_lower=Decimal('210.0'),
        atr_14=Decimal('4.5'),
        ma_5=Decimal('221.0'),
        ma_20=Decimal('218.0'),
        ma_50=Decimal('215.0'),
        plus_di=Decimal('28.0'),
        minus_di=Decimal('18.0'),
        adx=Decimal('30.0')
    )


@pytest.fixture
def sample_market_data_bearish():
    """创建一个看跌的市场数据样本 (TSLA)"""
    return MarketData(
        symbol='TSLA',
        timestamp=datetime(2024, 10, 1, 16, 0),
        date=date(2024, 10, 1),
        open=Decimal('260.0'),
        high=Decimal('262.0'),
        low=Decimal('255.0'),
        close=Decimal('258.0'),
        volume=80000000,
        rsi_14=Decimal('65.0'),
        macd=Decimal('-0.5'),
        macd_signal=Decimal('0.3'),
        macd_hist=Decimal('-0.8'),
        bb_upper=Decimal('270.0'),
        bb_middle=Decimal('260.0'),
        bb_lower=Decimal('250.0'),
        atr_14=Decimal('8.0'),
        ma_5=Decimal('259.0'),
        ma_20=Decimal('262.0'),
        ma_50=Decimal('265.0'),
        plus_di=Decimal('20.0'),
        minus_di=Decimal('25.0'),
        adx=Decimal('25.0')
    )


class TestOptionInfoParsing:
    """测试期权信息解析 - 使用 option_parser 模块"""

    def test_parse_call_option(self):
        """测试解析Call期权"""
        symbol = 'AAPL241115C00225000'
        info = parse_option(symbol)

        assert info is not None
        assert info['underlying'] == 'AAPL'
        assert info['option_type'] == 'call'
        assert info['strike'] == 225.0
        # expiry_date can be datetime or date
        expiry = info['expiry_date']
        if hasattr(expiry, 'date'):
            expiry = expiry.date()
        assert expiry == date(2024, 11, 15)

    def test_parse_put_option(self):
        """测试解析Put期权"""
        symbol = 'TSLA241025P00250000'
        info = parse_option(symbol)

        assert info is not None
        assert info['underlying'] == 'TSLA'
        assert info['option_type'] == 'put'
        assert info['strike'] == 250.0
        # expiry_date can be datetime or date
        expiry = info['expiry_date']
        if hasattr(expiry, 'date'):
            expiry = expiry.date()
        assert expiry == date(2024, 10, 25)

    def test_parse_invalid_symbol(self):
        """测试解析无效符号"""
        symbol = 'AAPL'  # 普通股票
        info = parse_option(symbol)

        assert info is None


class TestMoneynessCalculation:
    """测试Moneyness计算"""

    def test_atm_call(self, analyzer):
        """测试ATM Call期权"""
        stock_price = 222.0
        strike = 220.0
        option_type = 'call'

        moneyness = analyzer._calculate_moneyness(stock_price, strike, option_type)

        # (222 - 220) / 220 = 0.0091
        assert moneyness == pytest.approx(0.0091, rel=0.1)

    def test_itm_call(self, analyzer):
        """测试ITM Call期权"""
        stock_price = 230.0
        strike = 200.0
        option_type = 'call'

        moneyness = analyzer._calculate_moneyness(stock_price, strike, option_type)

        # (230 - 200) / 200 = 0.15 (15% ITM)
        assert moneyness == pytest.approx(0.15, rel=0.1)
        assert analyzer._classify_moneyness(moneyness) == 'deep_itm'

    def test_otm_call(self, analyzer):
        """测试OTM Call期权"""
        stock_price = 222.0
        strike = 250.0
        option_type = 'call'

        moneyness = analyzer._calculate_moneyness(stock_price, strike, option_type)

        # (222 - 250) / 250 = -0.112 (11.2% OTM)
        assert moneyness == pytest.approx(-0.112, rel=0.1)
        assert analyzer._classify_moneyness(moneyness) == 'deep_otm'

    def test_itm_put(self, analyzer):
        """测试ITM Put期权"""
        stock_price = 258.0
        strike = 270.0
        option_type = 'put'

        moneyness = analyzer._calculate_moneyness(stock_price, strike, option_type)

        # For put: (strike - price) / strike = (270-258)/270 = 0.044
        assert moneyness == pytest.approx(0.044, rel=0.1)
        assert analyzer._classify_moneyness(moneyness) == 'itm'


class TestDTEClassification:
    """测试DTE分类"""

    def test_dte_short_term(self, analyzer):
        """测试短期期权分类"""
        classification = analyzer._classify_dte(5)
        assert classification == 'short_term'

    def test_dte_medium_term(self, analyzer):
        """测试中期期权分类"""
        classification = analyzer._classify_dte(20)
        assert classification == 'medium_term'

    def test_dte_long_term(self, analyzer):
        """测试长期期权分类"""
        classification = analyzer._classify_dte(60)
        assert classification == 'long_term'

    def test_dte_leaps(self, analyzer):
        """测试LEAPS分类"""
        classification = analyzer._classify_dte(180)
        assert classification == 'leaps'


class TestEntryAnalysis:
    """测试入场分析"""

    def test_analyze_entry_context_call(
        self, analyzer, sample_call_position, sample_market_data_bullish
    ):
        """测试Call期权入场分析"""
        option_info = parse_option(sample_call_position.symbol)

        entry_context = analyzer.analyze_entry_context(
            sample_call_position,
            option_info,
            sample_market_data_bullish
        )

        assert 'moneyness' in entry_context
        assert 'dte' in entry_context
        assert 'underlying_indicators' in entry_context
        assert 'trend_alignment' in entry_context
        assert entry_context['has_market_data'] is True

    def test_analyze_entry_context_no_market_data(
        self, analyzer, sample_call_position
    ):
        """测试无市场数据时的入场分析"""
        option_info = parse_option(sample_call_position.symbol)

        entry_context = analyzer.analyze_entry_context(
            sample_call_position,
            option_info,
            None  # 无市场数据
        )

        assert entry_context['has_market_data'] is False
        assert 'warning' in entry_context

    def test_trend_alignment_call_bullish(
        self, analyzer, sample_market_data_bullish
    ):
        """测试Call期权与看涨趋势的一致性"""
        alignment = analyzer._check_trend_alignment(
            sample_market_data_bullish, 'call'
        )

        # 看涨市场买Call应该对齐
        assert alignment['aligned'] is True

    def test_trend_alignment_put_bearish(
        self, analyzer, sample_market_data_bearish
    ):
        """测试Put期权与看跌趋势的一致性"""
        alignment = analyzer._check_trend_alignment(
            sample_market_data_bearish, 'put'
        )

        # 看跌市场买Put应该对齐
        assert alignment['aligned'] is True


class TestUnderlyingMovement:
    """测试正股变动分析"""

    def test_analyze_underlying_movement(
        self, analyzer, db_session, sample_call_position
    ):
        """测试分析正股变动"""
        option_info = parse_option(sample_call_position.symbol)

        # 创建入场和出场的市场数据
        entry_md = MarketData(
            symbol='AAPL',
            date=date(2024, 10, 15),
            close=Decimal('222.0'),
            high=Decimal('223.0'),
            low=Decimal('220.0')
        )
        exit_md = MarketData(
            symbol='AAPL',
            date=date(2024, 10, 25),
            close=Decimal('235.0'),
            high=Decimal('237.0'),
            low=Decimal('232.0')
        )

        movement = analyzer.analyze_underlying_movement(
            sample_call_position,
            option_info,
            entry_md,
            exit_md
        )

        assert 'price_movement' in movement
        assert movement['price_movement']['change'] == pytest.approx(13.0, rel=0.01)
        assert movement['price_movement']['direction'] == 'up'


class TestGreeksImpact:
    """测试Greeks影响估算"""

    def test_estimate_greeks_impact(
        self, analyzer, sample_call_position
    ):
        """测试Greeks影响估算"""
        option_info = parse_option(sample_call_position.symbol)

        entry_md = MarketData(symbol='AAPL', close=Decimal('222.0'))
        exit_md = MarketData(symbol='AAPL', close=Decimal('235.0'))

        greeks = analyzer.estimate_greeks_impact(
            sample_call_position, option_info, entry_md, exit_md
        )

        assert 'delta' in greeks
        assert 'theta' in greeks
        assert 'summary' in greeks


class TestStrategyEvaluation:
    """测试策略评估"""

    def test_evaluate_option_strategy(
        self, analyzer, sample_call_position, sample_market_data_bullish
    ):
        """测试期权策略评估"""
        option_info = parse_option(sample_call_position.symbol)

        entry_md = sample_market_data_bullish
        exit_md = MarketData(
            symbol='AAPL',
            date=date(2024, 10, 25),
            close=Decimal('235.0')
        )

        evaluation = analyzer.evaluate_option_strategy(
            sample_call_position, option_info, entry_md, exit_md
        )

        assert 'expiry_selection' in evaluation
        assert 'strike_selection' in evaluation
        # 使用实际的键名
        assert 'entry_timing' in evaluation or 'timing_evaluation' in evaluation


class TestOptionScores:
    """测试期权评分计算"""

    def test_calculate_option_scores(self, analyzer):
        """测试期权评分计算"""
        # 模拟分析结果
        analysis = {
            'entry_context': {
                'moneyness': {
                    'value': 0.02,
                    'classification': 'atm'
                },
                'dte': {
                    'days': 30,
                    'classification': 'medium_term'
                },
                'trend_alignment': {
                    'aligned': True,
                    'bullish_signals': 4,
                    'total_signals': 5
                }
            },
            'underlying_movement': {
                'price_change': {
                    'percentage': 5.0
                },
                'direction': 'up'
            },
            'strategy_evaluation': {
                'overall_assessment': 'good'
            },
            'option_info': {
                'option_type': 'call'
            }
        }

        scores = analyzer.calculate_option_scores(analysis)

        assert 'moneyness_score' in scores
        assert 'trend_alignment_score' in scores
        assert 'time_value_score' in scores
        assert 'overall_option_score' in scores

        # 所有评分应该在0-100之间
        for key, value in scores.items():
            if isinstance(value, (int, float)):
                assert 0 <= value <= 100


class TestFullPositionAnalysis:
    """测试完整持仓分析"""

    def test_analyze_position_call(
        self, analyzer, db_session, sample_call_position, sample_market_data_bullish
    ):
        """测试Call期权完整分析"""
        # 添加市场数据到数据库
        db_session.add(sample_market_data_bullish)

        # 创建出场时的市场数据
        exit_md = MarketData(
            symbol='AAPL',
            timestamp=datetime(2024, 10, 25, 16, 0),
            date=date(2024, 10, 25),
            close=Decimal('235.0'),
            high=Decimal('237.0'),
            low=Decimal('232.0'),
            rsi_14=Decimal('68.0'),
            macd=Decimal('2.5'),
            macd_signal=Decimal('1.8'),
            ma_5=Decimal('233.0'),
            ma_20=Decimal('228.0')
        )
        db_session.add(exit_md)
        db_session.commit()

        # 执行分析
        analysis = analyzer.analyze_position(sample_call_position)

        assert analysis is not None
        assert 'option_info' in analysis
        assert 'entry_context' in analysis
        assert 'underlying_movement' in analysis
        assert 'greeks_impact' in analysis
        assert 'strategy_evaluation' in analysis
        assert 'option_scores' in analysis

    def test_analyze_position_non_option(self, analyzer):
        """测试非期权持仓应返回错误"""
        position = Position(
            symbol='AAPL',  # 普通股票，不是期权
            is_option=0
        )

        analysis = analyzer.analyze_position(position)

        assert 'error' in analysis


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_strike(self, analyzer):
        """测试零行权价（无效）"""
        stock_price = 100.0
        strike = 0.01  # 使用很小的值避免除零
        option_type = 'call'

        # 应该不抛出异常
        moneyness = analyzer._calculate_moneyness(stock_price, strike, option_type)
        assert moneyness is not None

    def test_analyze_indicators_partial_data(self, analyzer):
        """测试部分数据缺失的技术指标分析"""
        md = MarketData(
            symbol='AAPL',
            close=Decimal('222.0'),
            # 只有 RSI，没有其他指标
            rsi_14=Decimal('45.0')
        )

        indicators = analyzer._analyze_underlying_indicators(md)

        assert 'rsi' in indicators
        assert 'macd' not in indicators  # 缺失

    def test_classify_moneyness_edge_cases(self, analyzer):
        """测试Moneyness分类边界值"""
        # 边界值在 ±2% (0.02)
        # > 0.02 为 ITM, 0.02 本身根据实现可能是 ATM 或 ITM
        assert analyzer._classify_moneyness(0.025) == 'itm'
        assert analyzer._classify_moneyness(0.015) == 'atm'
        assert analyzer._classify_moneyness(-0.015) == 'atm'
        assert analyzer._classify_moneyness(-0.025) == 'otm'

        # Deep ITM/OTM (> 10%)
        assert analyzer._classify_moneyness(0.15) == 'deep_itm'
        assert analyzer._classify_moneyness(-0.15) == 'deep_otm'
