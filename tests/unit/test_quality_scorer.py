"""
测试 QualityScorer - 交易质量评分器

测试覆盖：
1. 进场质量评分
2. 出场质量评分
3. 趋势把握评分
4. 风险管理评分
5. 综合评分和等级分配
6. 批量评分功能
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.analyzers import QualityScorer


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
def scorer():
    """创建QualityScorer实例"""
    return QualityScorer()


@pytest.fixture
def sample_market_data_bullish():
    """创建一个看涨的市场数据样本"""
    return MarketData(
        symbol='AAPL',
        timestamp=datetime(2024, 10, 15, 16, 0),
        date=datetime(2024, 10, 15).date(),
        open=170.0,
        high=171.5,
        low=169.5,
        close=170.5,
        volume=1000000,
        # 技术指标 - 看涨信号
        rsi_14=28.5,  # 超卖
        macd=1.5,
        macd_signal=0.8,
        macd_hist=1.4,
        bb_upper=180.0,
        bb_middle=172.0,
        bb_lower=164.0,  # 价格在下轨附近
        atr_14=3.0,
        ma_5=169.0,
        ma_10=168.5,
        ma_20=167.0,
        ma_50=165.0,
        ma_200=160.0
    )


@pytest.fixture
def sample_market_data_bearish():
    """创建一个看跌的市场数据样本"""
    return MarketData(
        symbol='TSLA',
        timestamp=datetime(2024, 9, 20, 16, 0),
        date=datetime(2024, 9, 20).date(),
        open=245.0,
        high=246.0,
        low=244.0,
        close=248.0,  # 价格在上轨附近
        volume=800000,
        # 技术指标 - 看跌信号
        rsi_14=72.3,  # 超买
        macd=-1.2,
        macd_signal=-0.5,
        macd_hist=-1.4,
        bb_upper=250.0,
        bb_middle=240.0,
        bb_lower=230.0,  # 价格在上轨附近（248接近250）
        atr_14=4.5,
        ma_5=234.0,  # 空头排列
        ma_10=236.0,
        ma_20=238.0,
        ma_50=242.0,  # MA5 < MA20 < MA50
        ma_200=250.0
    )


@pytest.fixture
def sample_position_long_profit(db_session, sample_market_data_bullish):
    """创建一个盈利的做多持仓"""
    # 添加市场数据到数据库
    db_session.add(sample_market_data_bullish)

    # 创建出场市场数据
    exit_md = MarketData(
        symbol='AAPL',
        timestamp=datetime(2024, 10, 25, 16, 0),
        date=datetime(2024, 10, 25).date(),
        close=178.2,
        rsi_14=68.0,
        macd=2.5,
        macd_signal=2.8,
        macd_hist=-0.6,
        atr_14=3.2
    )
    db_session.add(exit_md)

    db_session.commit()

    # 创建持仓
    position = Position(
        symbol='AAPL',
        direction='long',
        open_time=datetime(2024, 10, 15, 16, 0),
        open_date=datetime(2024, 10, 15).date(),
        open_price=170.5,
        quantity=100,
        close_time=datetime(2024, 10, 25, 16, 0),
        close_date=datetime(2024, 10, 25).date(),
        close_price=178.2,
        realized_pnl=770.0,
        realized_pnl_pct=4.52,
        holding_period_days=10,
        mae_pct=-0.5,  # 最大回撤0.5%
        mfe_pct=6.0,   # 最大盈利6%
        status=PositionStatus.CLOSED
    )

    db_session.add(position)
    db_session.commit()

    return position


@pytest.fixture
def sample_position_long_loss(db_session, sample_market_data_bearish):
    """创建一个亏损的做多持仓（追高）"""
    db_session.add(sample_market_data_bearish)

    exit_md = MarketData(
        symbol='TSLA',
        timestamp=datetime(2024, 9, 27, 16, 0),
        date=datetime(2024, 9, 27).date(),
        close=238.5,
        rsi_14=45.0,
        macd=-2.0,
        macd_signal=-1.5,
        macd_hist=-1.0,
        atr_14=4.2
    )
    db_session.add(exit_md)

    db_session.commit()

    position = Position(
        symbol='TSLA',
        direction='long',
        open_time=datetime(2024, 9, 20, 16, 0),
        open_date=datetime(2024, 9, 20).date(),
        open_price=245.0,
        quantity=50,
        close_time=datetime(2024, 9, 27, 16, 0),
        close_date=datetime(2024, 9, 27).date(),
        close_price=238.5,
        realized_pnl=-325.0,
        realized_pnl_pct=-2.65,
        holding_period_days=7,
        mae_pct=-4.0,
        mfe_pct=1.5,
        status=PositionStatus.CLOSED
    )

    db_session.add(position)
    db_session.commit()

    return position


# ==================== 初始化测试 ====================

class TestQualityScorerInit:
    """测试QualityScorer初始化"""

    def test_init(self, scorer):
        """测试初始化 - 默认使用V2权重"""
        assert scorer is not None
        # V2 权重配置
        assert scorer.weights['entry'] == 0.18
        assert scorer.weights['exit'] == 0.17
        assert scorer.weights['trend'] == 0.14
        assert scorer.weights['risk'] == 0.12

    def test_init_v1_weights(self):
        """测试V1权重配置（兼容模式）"""
        scorer_v1 = QualityScorer(use_v2=False)
        # V1 使用 config.py 中的原始权重
        assert scorer_v1.weights['entry'] == 0.30
        assert scorer_v1.weights['exit'] == 0.25
        assert scorer_v1.weights['trend'] == 0.25
        assert scorer_v1.weights['risk'] == 0.20


# ==================== 进场质量评分测试 ====================

class TestEntryQualityScoring:
    """测试进场质量评分"""

    def test_score_entry_quality_bullish(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试看涨信号的进场评分（应该高分）"""
        result = scorer.score_entry_quality(sample_position_long_profit, sample_market_data_bullish)

        assert 'entry_score' in result
        assert result['entry_score'] >= 70  # 多指标共振，应该高分
        assert 'indicator_score' in result
        assert 'position_score' in result

    def test_score_entry_quality_bearish_long(self, scorer, sample_position_long_loss, sample_market_data_bearish):
        """测试在看跌信号时做多（应该低分）"""
        result = scorer.score_entry_quality(sample_position_long_loss, sample_market_data_bearish)

        assert 'entry_score' in result
        assert result['entry_score'] < 60  # 逆势操作，应该低分

    def test_score_entry_quality_no_data(self, scorer, sample_position_long_profit):
        """测试无市场数据时的评分"""
        result = scorer.score_entry_quality(sample_position_long_profit, None)

        assert result['entry_score'] == 50.0  # 默认中等分

    def test_score_entry_indicators_rsi_oversold(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试RSI超卖区买入"""
        score = scorer._score_entry_indicators(sample_position_long_profit, sample_market_data_bullish)

        assert score >= 80  # RSI超卖+MACD金叉+布林带下轨，应该高分

    def test_score_entry_indicators_rsi_overbought_long(self, scorer, sample_position_long_loss, sample_market_data_bearish):
        """测试RSI超买区买入（追高）"""
        score = scorer._score_entry_indicators(sample_position_long_loss, sample_market_data_bearish)

        assert score < 60  # 超买区买入，应该低分


# ==================== 出场质量评分测试 ====================

class TestExitQualityScoring:
    """测试出场质量评分"""

    def test_score_exit_quality_profit(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试盈利交易的出场评分"""
        # 模拟出场市场数据
        exit_md = MarketData(
            symbol='AAPL',
            date=datetime(2024, 10, 25).date(),
            timestamp=datetime(2024, 10, 25, 16, 0),
            close=178.2,
            rsi_14=68.0,
            macd=2.5,
            macd_signal=2.8
        )

        result = scorer.score_exit_quality(sample_position_long_profit, exit_md)

        assert 'exit_score' in result
        assert result['exit_score'] >= 60
        assert 'timing_score' in result
        assert 'target_score' in result
        assert 'stop_score' in result
        assert 'duration_score' in result

    def test_score_profit_target_big_win(self, scorer, sample_position_long_profit):
        """测试大幅盈利目标达成"""
        sample_position_long_profit.realized_pnl_pct = 5.5
        score = scorer._score_profit_target(sample_position_long_profit)

        assert score >= 90  # 大幅盈利应该高分

    def test_score_profit_target_small_loss(self, scorer, sample_position_long_loss):
        """测试小幅亏损（及时止损）"""
        sample_position_long_loss.realized_pnl_pct = -1.5
        score = scorer._score_profit_target(sample_position_long_loss)

        assert 65 <= score <= 75  # 小亏但止损及时

    def test_score_stop_loss_excellent(self, scorer, sample_position_long_profit):
        """测试优秀的止损控制"""
        sample_position_long_profit.mae_pct = -0.5
        score = scorer._score_stop_loss(sample_position_long_profit)

        assert score >= 90  # MAE控制在0.5%内

    def test_score_stop_loss_poor(self, scorer, sample_position_long_loss):
        """测试糟糕的止损控制"""
        sample_position_long_loss.mae_pct = -8.0
        score = scorer._score_stop_loss(sample_position_long_loss)

        assert score < 50  # MAE过大

    def test_score_holding_duration_efficient(self, scorer, sample_position_long_profit):
        """测试高效的持仓时间"""
        # 日均收益 = 4.52% / 10天 = 0.452%/天
        score = scorer._score_holding_duration(sample_position_long_profit)

        assert score >= 80  # 日均收益高


# ==================== 趋势把握评分测试 ====================

class TestTrendQualityScoring:
    """测试趋势把握评分"""

    def test_score_trend_quality(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试趋势把握综合评分"""
        exit_md = MarketData(
            symbol='AAPL',
            date=datetime(2024, 10, 25).date(),
            timestamp=datetime(2024, 10, 25, 16, 0),
            close=178.2,
            ma_5=177.0,
            ma_20=175.0,
            ma_50=172.0
        )

        result = scorer.score_trend_quality(sample_position_long_profit, sample_market_data_bullish, exit_md)

        assert 'trend_score' in result
        assert 'direction_score' in result
        assert 'strength_score' in result
        assert 'consistency_score' in result

    def test_score_trend_direction_aligned(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试趋势方向一致性（多头排列+做多）"""
        score = scorer._score_trend_direction(sample_position_long_profit, sample_market_data_bullish)

        assert score >= 80  # 均线多头排列+MACD正值+价格在MA上方

    def test_score_trend_direction_against(self, scorer, sample_position_long_loss, sample_market_data_bearish):
        """测试趋势方向不一致（空头排列+做多）"""
        score = scorer._score_trend_direction(sample_position_long_loss, sample_market_data_bearish)

        assert score < 60  # 逆势而为

    def test_score_trend_strength_strong(self, scorer, sample_market_data_bullish):
        """测试强趋势"""
        # MA5与MA50分离度 = (169-165)/165 = 2.4%
        score = scorer._score_trend_strength(sample_market_data_bullish)

        assert score >= 55  # 中等偏弱趋势

    def test_score_trend_consistency_profit(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试趋势持续性（盈利）"""
        score = scorer._score_trend_consistency(sample_position_long_profit, sample_market_data_bullish, None)

        assert score >= 75  # 盈利说明趋势持续


# ==================== 风险管理评分测试 ====================

class TestRiskManagementScoring:
    """测试风险管理评分"""

    def test_score_risk_management(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试风险管理综合评分"""
        result = scorer.score_risk_management(sample_position_long_profit, sample_market_data_bullish)

        assert 'risk_score' in result
        assert 'rr_ratio_score' in result
        assert 'mae_mfe_score' in result
        assert 'position_size_score' in result

    def test_score_risk_reward_ratio(self, scorer, sample_position_long_profit, sample_market_data_bullish):
        """测试RR比评分"""
        score = scorer._score_risk_reward_ratio(sample_position_long_profit, sample_market_data_bullish)

        assert score >= 70  # ATR为3.0, 理想RR比应该合理

    def test_score_mae_mfe_excellent(self, scorer, sample_position_long_profit):
        """测试优秀的MAE/MFE比"""
        # MFE=6%, MAE=0.5%, 比率=12
        score = scorer._score_mae_mfe(sample_position_long_profit)

        assert score >= 90  # 极好的RR比

    def test_score_mae_mfe_poor(self, scorer, sample_position_long_loss):
        """测试糟糕的MAE/MFE比"""
        # MFE=1.5%, MAE=4%, 比率=0.375
        score = scorer._score_mae_mfe(sample_position_long_loss)

        assert score < 60  # RR比差

    def test_score_position_size_ideal(self, scorer, sample_position_long_profit):
        """测试理想仓位大小"""
        # entry_amount = 17050 (large position)
        score = scorer._score_position_size(sample_position_long_profit)

        assert score == 50  # 仓位过大（>$10000）


# ==================== 综合评分测试 ====================

class TestOverallScoring:
    """测试综合评分功能"""

    def test_calculate_overall_score_excellent_trade(self, scorer, db_session, sample_position_long_profit):
        """测试优秀交易的综合评分"""
        result = scorer.calculate_overall_score(db_session, sample_position_long_profit)

        assert 'overall_score' in result
        assert 'grade' in result
        assert result['overall_score'] >= 70  # 优秀交易
        assert result['grade'] in ['A+', 'A', 'A-', 'B+', 'B', 'B-']

    def test_calculate_overall_score_poor_trade(self, scorer, db_session, sample_position_long_loss):
        """测试糟糕交易的综合评分"""
        result = scorer.calculate_overall_score(db_session, sample_position_long_loss)

        assert 'overall_score' in result
        assert 'grade' in result
        assert result['overall_score'] < 70  # 中等或差的交易
        assert result['grade'] in ['C+', 'C', 'C-', 'D', 'F']

    def test_assign_grade_A_plus(self, scorer):
        """测试A+等级"""
        assert scorer._assign_grade(97) == 'A+'

    def test_assign_grade_A(self, scorer):
        """测试A等级"""
        assert scorer._assign_grade(92) == 'A'

    def test_assign_grade_B(self, scorer):
        """测试B等级"""
        assert scorer._assign_grade(77) == 'B'

    def test_assign_grade_C(self, scorer):
        """测试C等级"""
        assert scorer._assign_grade(62) == 'C'

    def test_assign_grade_D(self, scorer):
        """测试D等级"""
        assert scorer._assign_grade(52) == 'D'

    def test_assign_grade_F(self, scorer):
        """测试F等级"""
        assert scorer._assign_grade(45) == 'F'


# ==================== 批量处理测试 ====================

class TestBatchScoring:
    """测试批量评分功能"""

    def test_score_all_positions(self, scorer, db_session, sample_position_long_profit, sample_position_long_loss):
        """测试批量评分所有持仓"""
        stats = scorer.score_all_positions(db_session, update_db=True)

        assert stats['total'] == 2
        assert stats['scored'] >= 1  # 至少评分成功一个
        assert stats['failed'] <= 1  # 失败数不超过1

        # 验证数据库已更新
        db_session.refresh(sample_position_long_profit)
        assert sample_position_long_profit.overall_score is not None
        assert sample_position_long_profit.score_grade is not None

    def test_score_all_positions_no_update(self, scorer, db_session, sample_position_long_profit):
        """测试批量评分但不更新数据库"""
        original_score = sample_position_long_profit.overall_score

        stats = scorer.score_all_positions(db_session, update_db=False)

        # 验证数据库未更新
        db_session.refresh(sample_position_long_profit)
        assert sample_position_long_profit.overall_score == original_score


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""

    def test_missing_market_data(self, scorer, db_session, sample_position_long_profit):
        """测试缺失市场数据的情况"""
        # 清空市场数据
        db_session.query(MarketData).delete()
        db_session.commit()

        result = scorer.calculate_overall_score(db_session, sample_position_long_profit)

        # 应该仍能计算评分，使用默认值
        assert 'overall_score' in result
        assert 40 <= result['overall_score'] <= 70  # 默认中等分数

    def test_incomplete_indicators(self, scorer, sample_position_long_profit, db_session):
        """测试技术指标不完整的情况"""
        md = MarketData(
            symbol='AAPL',
            timestamp=datetime(2024, 10, 15),
            date=datetime(2024, 10, 15).date(),
            close=170.5,
            # 只有部分指标
            rsi_14=50.0
            # 缺失MACD, BB, ATR等
        )

        result = scorer.score_entry_quality(sample_position_long_profit, md)

        # 应该能处理，使用可用的指标评分
        assert 'entry_score' in result
        assert result['entry_score'] > 0


# ==================== 字符串表示测试 ====================

class TestStringRepresentation:
    """测试字符串表示"""

    def test_repr(self, scorer):
        """测试__repr__方法 - V2版本"""
        repr_str = repr(scorer)

        assert 'QualityScorer' in repr_str
        # V2 权重：entry=18%, exit=17%, trend=14%, risk=12%
        assert '18%' in repr_str  # entry权重
        assert '17%' in repr_str  # exit权重
        assert '14%' in repr_str  # trend权重
        assert '12%' in repr_str  # risk权重
