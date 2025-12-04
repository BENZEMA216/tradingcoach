"""
StrategyClassifier - 策略分类器

基于入场时的技术指标自动推断交易策略类型
"""

import logging
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session

from src.models.position import Position, PositionStatus
from src.models.market_data import MarketData
from src.utils.option_parser import OptionParser
from config import (
    RSI_OVERSOLD,
    RSI_OVERBOUGHT,
    STOCH_OVERSOLD,
    STOCH_OVERBOUGHT,
    ADX_WEAK_TREND,
    ADX_MODERATE_TREND,
    ADX_STRONG_TREND
)

logger = logging.getLogger(__name__)


class StrategyClassifier:
    """
    策略分类器

    策略类型:
    - trend: 趋势跟踪 - ADX强+方向一致
    - mean_reversion: 均值回归 - RSI/Stoch超买超卖+BB边界
    - breakout: 突破交易 - 价格突破+放量
    - range: 震荡交易 - ADX弱+RSI中性
    - momentum: 动量交易 - MACD金叉死叉+RSI确认
    """

    # 策略类型中文映射
    STRATEGY_NAMES = {
        'trend': '趋势跟踪',
        'mean_reversion': '均值回归',
        'breakout': '突破交易',
        'range': '震荡交易',
        'momentum': '动量交易',
        'unknown': '未知策略'
    }

    def __init__(self):
        logger.info("StrategyClassifier initialized")

    def _calculate_bb_percent_b(self, md: MarketData) -> Optional[float]:
        """
        计算布林带%B值

        %B = (Close - Lower) / (Upper - Lower)
        返回值: 0表示在下轨，1表示在上轨，0.5表示在中轨
        """
        if md.close is None or md.bb_upper is None or md.bb_lower is None:
            return None

        close = float(md.close)
        upper = float(md.bb_upper)
        lower = float(md.bb_lower)

        if upper == lower:
            return 0.5  # 避免除零

        return (close - lower) / (upper - lower)

    def classify(
        self,
        position: Position,
        market_data: Optional[MarketData]
    ) -> Tuple[str, float]:
        """
        分类单个持仓的策略类型

        Args:
            position: 持仓对象
            market_data: 入场时的市场数据

        Returns:
            (strategy_type, confidence): 策略类型和置信度
        """
        if not market_data:
            return 'unknown', 0.0

        is_long = position.direction in ['buy', 'buy_to_open', 'long']

        # 收集各策略的得分
        scores = {
            'trend': self._score_trend_strategy(market_data, is_long),
            'mean_reversion': self._score_mean_reversion_strategy(market_data, is_long),
            'breakout': self._score_breakout_strategy(market_data, is_long),
            'range': self._score_range_strategy(market_data, is_long),
            'momentum': self._score_momentum_strategy(market_data, is_long)
        }

        # 找到最高分的策略
        best_strategy = max(scores, key=scores.get)
        best_score = scores[best_strategy]

        # 如果最高分太低，标记为未知
        if best_score < 30:
            return 'unknown', best_score

        return best_strategy, best_score

    def _score_trend_strategy(
        self,
        md: MarketData,
        is_long: bool
    ) -> float:
        """
        评估趋势跟踪策略

        规则:
        - ADX > 25 (中等以上趋势)
        - 方向与趋势一致 (+DI > -DI 做多, -DI > +DI 做空)
        - 均线多头/空头排列
        """
        score = 0.0

        # ADX趋势强度 (最高40分)
        if md.adx is not None:
            adx = float(md.adx)
            if adx >= ADX_STRONG_TREND:
                score += 40
            elif adx >= ADX_MODERATE_TREND:
                score += 30
            elif adx >= ADX_WEAK_TREND:
                score += 15
            else:
                score -= 10  # 弱趋势扣分

        # 方向一致性 (最高30分)
        if md.plus_di is not None and md.minus_di is not None:
            plus_di = float(md.plus_di)
            minus_di = float(md.minus_di)

            if is_long and plus_di > minus_di:
                score += 30
            elif not is_long and minus_di > plus_di:
                score += 30
            else:
                score -= 15  # 逆势扣分

        # 均线排列 (最高30分)
        if md.ma_5 and md.ma_20 and md.ma_50:
            ma5 = float(md.ma_5)
            ma20 = float(md.ma_20)
            ma50 = float(md.ma_50)

            if is_long:
                if ma5 > ma20 > ma50:
                    score += 30  # 多头排列
                elif ma5 > ma20:
                    score += 15  # 部分多头
            else:
                if ma5 < ma20 < ma50:
                    score += 30  # 空头排列
                elif ma5 < ma20:
                    score += 15  # 部分空头

        return max(0, score)

    def _score_mean_reversion_strategy(
        self,
        md: MarketData,
        is_long: bool
    ) -> float:
        """
        评估均值回归策略

        规则:
        - RSI超买超卖区域
        - Stochastic超买超卖
        - 价格在布林带边界
        """
        score = 0.0

        # RSI超买超卖 (最高35分)
        if md.rsi_14 is not None:
            rsi = float(md.rsi_14)
            if is_long and rsi < RSI_OVERSOLD:
                score += 35
            elif is_long and rsi < 35:
                score += 20
            elif not is_long and rsi > RSI_OVERBOUGHT:
                score += 35
            elif not is_long and rsi > 65:
                score += 20

        # Stochastic超买超卖 (最高35分)
        if md.stoch_k is not None:
            stoch = float(md.stoch_k)
            if is_long and stoch < STOCH_OVERSOLD:
                score += 35
            elif is_long and stoch < 30:
                score += 20
            elif not is_long and stoch > STOCH_OVERBOUGHT:
                score += 35
            elif not is_long and stoch > 70:
                score += 20

        # 布林带边界 (最高30分)
        bb_pct = self._calculate_bb_percent_b(md)
        if bb_pct is not None:
            if is_long and bb_pct < 0.1:
                score += 30  # 下轨下方
            elif is_long and bb_pct < 0.2:
                score += 20  # 接近下轨
            elif not is_long and bb_pct > 0.9:
                score += 30  # 上轨上方
            elif not is_long and bb_pct > 0.8:
                score += 20  # 接近上轨

        return max(0, score)

    def _score_breakout_strategy(
        self,
        md: MarketData,
        is_long: bool
    ) -> float:
        """
        评估突破交易策略

        规则:
        - 价格突破布林带
        - 成交量放大
        - ADX开始上升(趋势形成中)
        """
        score = 0.0

        # 布林带突破 (最高40分)
        bb_pct = self._calculate_bb_percent_b(md)
        if bb_pct is not None:
            if is_long and bb_pct > 1.0:
                score += 40  # 突破上轨
            elif is_long and bb_pct > 0.9:
                score += 25
            elif not is_long and bb_pct < 0.0:
                score += 40  # 突破下轨
            elif not is_long and bb_pct < 0.1:
                score += 25

        # 成交量放大 (最高35分)
        if md.volume is not None and md.volume_sma_20 is not None:
            if md.volume_sma_20 > 0:
                vol_ratio = float(md.volume) / float(md.volume_sma_20)
                if vol_ratio >= 2.0:
                    score += 35
                elif vol_ratio >= 1.5:
                    score += 25
                elif vol_ratio >= 1.2:
                    score += 15

        # ADX中等趋势 (最高25分) - 突破后趋势形成中
        if md.adx is not None:
            adx = float(md.adx)
            if ADX_WEAK_TREND <= adx < ADX_MODERATE_TREND:
                score += 25  # 趋势正在形成
            elif adx >= ADX_MODERATE_TREND:
                score += 15  # 趋势已形成

        return max(0, score)

    def _score_range_strategy(
        self,
        md: MarketData,
        is_long: bool
    ) -> float:
        """
        评估震荡交易策略

        规则:
        - ADX < 20 (弱趋势/无趋势)
        - RSI在中性区域
        - 价格在布林带中间区域
        """
        score = 0.0

        # ADX弱趋势 (最高40分)
        if md.adx is not None:
            adx = float(md.adx)
            if adx < ADX_WEAK_TREND:
                score += 40  # 无明显趋势
            elif adx < ADX_MODERATE_TREND:
                score += 20
            else:
                score -= 20  # 有趋势扣分

        # RSI中性区域 (最高30分)
        if md.rsi_14 is not None:
            rsi = float(md.rsi_14)
            if 40 <= rsi <= 60:
                score += 30  # 中性区域
            elif 35 <= rsi <= 65:
                score += 15

        # 布林带中间区域 (最高30分)
        bb_pct = self._calculate_bb_percent_b(md)
        if bb_pct is not None:
            if 0.3 <= bb_pct <= 0.7:
                score += 30  # 中间区域
            elif 0.2 <= bb_pct <= 0.8:
                score += 15

        return max(0, score)

    def _score_momentum_strategy(
        self,
        md: MarketData,
        is_long: bool
    ) -> float:
        """
        评估动量交易策略

        规则:
        - MACD金叉/死叉
        - RSI方向确认
        - 价格站上/跌破均线
        """
        score = 0.0

        # MACD金叉/死叉 (最高40分)
        if md.macd is not None and md.macd_signal is not None:
            macd = float(md.macd)
            signal = float(md.macd_signal)
            macd_diff = macd - signal

            if is_long and macd_diff > 0:
                score += 40 if macd > 0 else 30  # 金叉
            elif not is_long and macd_diff < 0:
                score += 40 if macd < 0 else 30  # 死叉

        # RSI方向确认 (最高30分)
        if md.rsi_14 is not None:
            rsi = float(md.rsi_14)
            if is_long and 50 < rsi < RSI_OVERBOUGHT:
                score += 30  # 上升动量
            elif not is_long and RSI_OVERSOLD < rsi < 50:
                score += 30  # 下降动量

        # 价格与均线关系 (最高30分)
        if md.close and md.ma_20:
            close = float(md.close)
            ma20 = float(md.ma_20)

            if is_long and close > ma20:
                score += 30
            elif not is_long and close < ma20:
                score += 30

        return max(0, score)

    def classify_position(
        self,
        session: Session,
        position: Position
    ) -> Tuple[str, float]:
        """
        分类持仓并获取市场数据

        Args:
            session: 数据库会话
            position: 持仓对象

        Returns:
            (strategy_type, confidence)
        """
        # 获取入场时的市场数据
        market_data = self._get_entry_market_data(session, position)

        return self.classify(position, market_data)

    def _get_entry_market_data(
        self,
        session: Session,
        position: Position
    ) -> Optional[MarketData]:
        """获取入场时的市场数据"""
        if not position.open_time:
            return None

        # 处理期权
        symbol = position.symbol
        if OptionParser.is_option_symbol(symbol):
            symbol = OptionParser.extract_underlying(symbol)

        target_date = position.open_time.date()

        return session.query(MarketData).filter(
            MarketData.symbol == symbol,
            MarketData.date == target_date
        ).first()

    def classify_all_positions(
        self,
        session: Session,
        update_db: bool = True
    ) -> Dict[str, int]:
        """
        批量分类所有已平仓持仓

        Args:
            session: 数据库会话
            update_db: 是否更新数据库

        Returns:
            统计信息
        """
        positions = session.query(Position).filter(
            Position.status == PositionStatus.CLOSED
        ).all()

        stats = {
            'total': len(positions),
            'classified': 0,
            'trend': 0,
            'mean_reversion': 0,
            'breakout': 0,
            'range': 0,
            'momentum': 0,
            'unknown': 0
        }

        for position in positions:
            try:
                strategy_type, confidence = self.classify_position(session, position)

                if update_db:
                    position.strategy_type = strategy_type
                    position.strategy_confidence = confidence

                stats['classified'] += 1
                stats[strategy_type] = stats.get(strategy_type, 0) + 1

                logger.debug(
                    f"Position {position.id} ({position.symbol}): "
                    f"{strategy_type} ({confidence:.1f}%)"
                )

            except Exception as e:
                logger.error(f"Failed to classify position {position.id}: {e}")

        if update_db:
            session.commit()
            logger.info(f"Updated {stats['classified']} positions with strategy types")

        return stats

    @classmethod
    def get_strategy_name(cls, strategy_type: str) -> str:
        """获取策略类型的中文名称"""
        return cls.STRATEGY_NAMES.get(strategy_type, strategy_type)
