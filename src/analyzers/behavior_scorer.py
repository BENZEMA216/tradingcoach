"""
TradingBehaviorScorer - 交易行为评分器

检测和评估交易行为质量:
1. 追高/追跌检测
2. FOMO交易检测
3. 过度交易检测
4. 纪律性评估
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


@dataclass
class BehaviorScore:
    """交易行为评分结果"""
    total_score: float  # 综合评分 0-100
    chasing_score: float  # 追涨/追跌评分
    fomo_score: float  # FOMO评分
    overtrading_score: float  # 过度交易评分
    discipline_score: float  # 纪律性评分
    warnings: List[str] = field(default_factory=list)  # 警告信息
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息


class TradingBehaviorScorer:
    """
    交易行为评分器

    评估交易者的行为模式:
    - 是否追高/追跌入场
    - 是否在情绪化时刻(大涨大跌后)交易
    - 是否对同一标的过度交易
    - 止损/止盈纪律执行
    """

    # 权重配置
    WEIGHT_CHASING = 0.30
    WEIGHT_FOMO = 0.25
    WEIGHT_OVERTRADING = 0.20
    WEIGHT_DISCIPLINE = 0.25

    # 阈值配置
    CHASE_HIGH_THRESHOLD = 0.95  # 入场价 > 5日高点 * 0.95 视为追高
    CHASE_LOW_THRESHOLD = 1.05   # 入场价 < 5日低点 * 1.05 视为追低
    FOMO_MOVE_THRESHOLD = 3.0    # 大涨/大跌阈值 (%)
    FOMO_TIME_WINDOW = 2         # FOMO时间窗口 (小时)
    OVERTRADING_WINDOW = 7       # 过度交易检测窗口 (天)
    OVERTRADING_THRESHOLD = 3    # 同标的交易次数阈值

    def __init__(self):
        """初始化行为评分器"""
        logger.info("TradingBehaviorScorer initialized")

    def score(
        self,
        position: Any,
        market_data: Optional[Any],
        recent_trades: Optional[List[Any]] = None,
        historical_prices: Optional[Dict] = None
    ) -> BehaviorScore:
        """
        计算交易行为评分

        Args:
            position: 持仓对象
            market_data: 入场时的市场数据
            recent_trades: 最近的交易列表(用于过度交易检测)
            historical_prices: 历史价格数据 {'high_5d', 'low_5d', 'prev_close', 'prev_change_pct'}

        Returns:
            BehaviorScore: 评分结果
        """
        warnings = []
        details = {}
        is_long = position.direction in ['long', 'buy', 'buy_to_open']

        # 1. 追高/追跌评分 (30%)
        chasing_score, chasing_warnings, chasing_details = self._score_chasing(
            position, market_data, historical_prices, is_long
        )
        warnings.extend(chasing_warnings)
        details['chasing'] = chasing_details

        # 2. FOMO评分 (25%)
        fomo_score, fomo_warnings, fomo_details = self._score_fomo(
            position, market_data, historical_prices
        )
        warnings.extend(fomo_warnings)
        details['fomo'] = fomo_details

        # 3. 过度交易评分 (20%)
        overtrading_score, ot_warnings, ot_details = self._score_overtrading(
            position, recent_trades
        )
        warnings.extend(ot_warnings)
        details['overtrading'] = ot_details

        # 4. 纪律性评分 (25%)
        discipline_score, disc_warnings, disc_details = self._score_discipline(
            position
        )
        warnings.extend(disc_warnings)
        details['discipline'] = disc_details

        # 计算综合评分
        total_score = (
            chasing_score * self.WEIGHT_CHASING +
            fomo_score * self.WEIGHT_FOMO +
            overtrading_score * self.WEIGHT_OVERTRADING +
            discipline_score * self.WEIGHT_DISCIPLINE
        )

        return BehaviorScore(
            total_score=round(total_score, 2),
            chasing_score=chasing_score,
            fomo_score=fomo_score,
            overtrading_score=overtrading_score,
            discipline_score=discipline_score,
            warnings=warnings,
            details=details
        )

    def _score_chasing(
        self,
        position: Any,
        market_data: Optional[Any],
        historical_prices: Optional[Dict],
        is_long: bool
    ) -> tuple[float, List[str], Dict]:
        """
        追高/追跌检测

        规则:
        - 做多: 入场价 > 5日高点 * 95% = 追高
        - 做空: 入场价 < 5日低点 * 105% = 追低
        """
        warnings = []
        details = {}

        entry_price = float(position.open_price) if position.open_price else None

        if not entry_price:
            return 80.0, [], {'status': 'no_entry_price'}

        details['entry_price'] = entry_price

        # 从历史价格获取5日高低点
        high_5d = None
        low_5d = None

        if historical_prices:
            high_5d = historical_prices.get('high_5d')
            low_5d = historical_prices.get('low_5d')
        elif market_data:
            # 尝试从market_data获取
            if hasattr(market_data, 'high_5d'):
                high_5d = float(market_data.high_5d) if market_data.high_5d else None
            if hasattr(market_data, 'low_5d'):
                low_5d = float(market_data.low_5d) if market_data.low_5d else None

        # 如果没有5日高低点，使用当日高低点估算
        if high_5d is None and market_data and hasattr(market_data, 'high'):
            if market_data.high:
                high_5d = float(market_data.high) * 1.02  # 估算
        if low_5d is None and market_data and hasattr(market_data, 'low'):
            if market_data.low:
                low_5d = float(market_data.low) * 0.98  # 估算

        details['high_5d'] = high_5d
        details['low_5d'] = low_5d

        if is_long and high_5d:
            chase_threshold = high_5d * self.CHASE_HIGH_THRESHOLD
            if entry_price > chase_threshold:
                chase_pct = (entry_price - chase_threshold) / chase_threshold * 100
                details['chase_pct'] = chase_pct
                details['status'] = 'chasing_high'

                if chase_pct > 3:
                    warnings.append(f"严重追高: 入场价高于5日高点{chase_pct:.1f}%")
                    return 30.0, warnings, details
                elif chase_pct > 1:
                    warnings.append(f"追高入场: 接近5日高点")
                    return 50.0, warnings, details
                else:
                    return 70.0, warnings, details
            else:
                details['status'] = 'normal'
                # 计算距离5日高点的空间
                room_pct = (high_5d - entry_price) / entry_price * 100
                details['room_to_high'] = room_pct
                if room_pct > 5:
                    return 95.0, [], details  # 有充足空间
                elif room_pct > 2:
                    return 85.0, [], details
                else:
                    return 75.0, [], details

        elif not is_long and low_5d:
            chase_threshold = low_5d * self.CHASE_LOW_THRESHOLD
            if entry_price < chase_threshold:
                chase_pct = (chase_threshold - entry_price) / chase_threshold * 100
                details['chase_pct'] = chase_pct
                details['status'] = 'chasing_low'

                if chase_pct > 3:
                    warnings.append(f"严重追空: 入场价低于5日低点{chase_pct:.1f}%")
                    return 30.0, warnings, details
                elif chase_pct > 1:
                    warnings.append("追空入场: 接近5日低点")
                    return 50.0, warnings, details
                else:
                    return 70.0, warnings, details
            else:
                details['status'] = 'normal'
                return 85.0, [], details

        # 无法判断
        return 75.0, [], {'status': 'insufficient_data'}

    def _score_fomo(
        self,
        position: Any,
        market_data: Optional[Any],
        historical_prices: Optional[Dict]
    ) -> tuple[float, List[str], Dict]:
        """
        FOMO交易检测

        规则:
        - 前一日大涨/大跌 > 3% 后追入
        - 盘中大幅波动后追入
        """
        warnings = []
        details = {}

        # 获取前一日涨跌幅
        prev_change = None
        if historical_prices:
            prev_change = historical_prices.get('prev_change_pct')
        elif market_data:
            # 尝试计算
            if hasattr(market_data, 'prev_close') and hasattr(market_data, 'open'):
                if market_data.prev_close and market_data.open:
                    prev_close = float(market_data.prev_close)
                    open_price = float(market_data.open)
                    prev_change = (open_price - prev_close) / prev_close * 100

        details['prev_change'] = prev_change

        if prev_change is not None:
            abs_change = abs(prev_change)

            if abs_change > self.FOMO_MOVE_THRESHOLD * 2:
                # 极端波动
                details['status'] = 'extreme_move'
                warnings.append(f"极端波动后入场: 前日{prev_change:+.1f}%")
                return 35.0, warnings, details

            elif abs_change > self.FOMO_MOVE_THRESHOLD:
                # 大幅波动
                is_long = position.direction in ['long', 'buy', 'buy_to_open']

                # 检查是否追涨杀跌
                if (is_long and prev_change > 0) or (not is_long and prev_change < 0):
                    details['status'] = 'fomo_chasing'
                    warnings.append(f"FOMO追势: 前日{prev_change:+.1f}%后顺势入场")
                    return 50.0, warnings, details
                else:
                    # 逆势，可能是均值回归
                    details['status'] = 'contrarian'
                    return 75.0, [], details

            else:
                # 正常波动
                details['status'] = 'normal'
                return 90.0, [], details

        # 无法判断
        return 75.0, [], {'status': 'insufficient_data'}

    def _score_overtrading(
        self,
        position: Any,
        recent_trades: Optional[List[Any]]
    ) -> tuple[float, List[str], Dict]:
        """
        过度交易检测

        规则:
        - 同一标的7天内交易 > 3次视为过度交易
        """
        warnings = []
        details = {'symbol': position.symbol}

        if not recent_trades:
            # 无历史数据，给默认分
            return 85.0, [], {'status': 'no_history'}

        # 统计同标的交易次数
        symbol = position.symbol
        underlying = position.underlying_symbol or symbol

        same_symbol_count = 0
        trade_dates = []

        for trade in recent_trades:
            trade_symbol = getattr(trade, 'symbol', None)
            trade_underlying = getattr(trade, 'underlying_symbol', None) or trade_symbol

            if trade_symbol == symbol or trade_underlying == underlying:
                same_symbol_count += 1
                if hasattr(trade, 'open_time') and trade.open_time:
                    trade_dates.append(trade.open_time)

        details['same_symbol_count'] = same_symbol_count
        details['recent_trade_dates'] = [str(d) for d in trade_dates[-5:]]

        if same_symbol_count > self.OVERTRADING_THRESHOLD * 2:
            # 严重过度交易
            warnings.append(f"严重过度交易: 7天内{same_symbol_count}笔同标的交易")
            details['status'] = 'severe_overtrading'
            return 25.0, warnings, details

        elif same_symbol_count > self.OVERTRADING_THRESHOLD:
            # 过度交易
            penalty = (same_symbol_count - self.OVERTRADING_THRESHOLD) * 10
            score = max(40, 80 - penalty)
            warnings.append(f"过度交易: 7天内{same_symbol_count}笔同标的交易")
            details['status'] = 'overtrading'
            return score, warnings, details

        else:
            details['status'] = 'normal'
            return 90.0, [], details

    def _score_discipline(
        self,
        position: Any
    ) -> tuple[float, List[str], Dict]:
        """
        纪律性评估

        规则:
        - 止损执行: 亏损 > 预设止损 50% 扣分
        - 提前止盈: 盈利后快速出场 (<1小时) 扣分
        - 持仓过长: 超过预期持仓时间扣分
        """
        warnings = []
        details = {}

        scores = []

        # 1. 止损评估 (使用MAE)
        if position.mae_pct is not None:
            mae_pct = abs(float(position.mae_pct))
            details['mae_pct'] = mae_pct

            if mae_pct <= 2:
                scores.append(95)
                details['stop_status'] = 'excellent'
            elif mae_pct <= 5:
                scores.append(80)
                details['stop_status'] = 'good'
            elif mae_pct <= 10:
                scores.append(65)
                details['stop_status'] = 'acceptable'
            elif mae_pct <= 20:
                scores.append(45)
                warnings.append(f"回撤过大: MAE {mae_pct:.1f}%")
                details['stop_status'] = 'poor'
            else:
                scores.append(25)
                warnings.append(f"严重回撤: MAE {mae_pct:.1f}%")
                details['stop_status'] = 'failed'

        # 2. 盈亏情况评估
        if position.realized_pnl is not None:
            pnl = float(position.realized_pnl)
            pnl_pct = float(position.realized_pnl_pct) if position.realized_pnl_pct else 0

            details['pnl'] = pnl
            details['pnl_pct'] = pnl_pct

            if pnl > 0:
                # 盈利情况
                if position.mfe_pct:
                    mfe_pct = abs(float(position.mfe_pct))
                    profit_capture = pnl_pct / mfe_pct if mfe_pct > 0 else 0
                    details['profit_capture'] = profit_capture

                    if profit_capture >= 0.7:
                        scores.append(95)
                        details['exit_status'] = 'excellent_capture'
                    elif profit_capture >= 0.5:
                        scores.append(80)
                        details['exit_status'] = 'good_capture'
                    elif profit_capture >= 0.3:
                        scores.append(65)
                        details['exit_status'] = 'moderate_capture'
                    else:
                        scores.append(50)
                        warnings.append(f"利润回吐严重: 仅捕获{profit_capture*100:.0f}%最大浮盈")
                        details['exit_status'] = 'poor_capture'
                else:
                    scores.append(75)
            else:
                # 亏损情况 - 看是否及时止损
                if pnl_pct >= -5:
                    scores.append(75)
                    details['loss_status'] = 'controlled'
                elif pnl_pct >= -10:
                    scores.append(60)
                    details['loss_status'] = 'acceptable'
                else:
                    scores.append(40)
                    warnings.append(f"止损过晚: 亏损{pnl_pct:.1f}%")
                    details['loss_status'] = 'late_stop'

        # 3. 持仓时间评估
        if position.holding_period_hours is not None:
            hours = float(position.holding_period_hours)
            details['holding_hours'] = hours

            # 检查过短持仓 (可能是恐慌出场)
            if hours < 0.5:  # 30分钟内
                if position.realized_pnl and float(position.realized_pnl) < 0:
                    scores.append(40)
                    warnings.append("恐慌性出场: 30分钟内亏损离场")
                    details['holding_status'] = 'panic_exit'
                else:
                    scores.append(70)
                    details['holding_status'] = 'quick_trade'
            elif hours < 1:
                scores.append(75)
                details['holding_status'] = 'short_term'
            else:
                scores.append(85)
                details['holding_status'] = 'normal'

        # 计算综合纪律得分
        if scores:
            avg_score = sum(scores) / len(scores)
            return avg_score, warnings, details

        return 75.0, [], {'status': 'insufficient_data'}

    def get_recent_trades(
        self,
        session: Session,
        symbol: str,
        before_date: datetime,
        days: int = 7
    ) -> List[Any]:
        """
        获取指定标的的最近交易

        Args:
            session: 数据库会话
            symbol: 标的代码
            before_date: 截止日期
            days: 回看天数

        Returns:
            最近交易列表
        """
        from src.models.position import Position

        start_date = before_date - timedelta(days=days)

        # 查询同标的的交易
        trades = session.query(Position).filter(
            Position.open_time >= start_date,
            Position.open_time < before_date,
            (Position.symbol == symbol) |
            (Position.underlying_symbol == symbol)
        ).all()

        return trades

    def __repr__(self) -> str:
        return (
            f"TradingBehaviorScorer("
            f"chasing={self.WEIGHT_CHASING:.0%}, "
            f"fomo={self.WEIGHT_FOMO:.0%}, "
            f"overtrading={self.WEIGHT_OVERTRADING:.0%}, "
            f"discipline={self.WEIGHT_DISCIPLINE:.0%})"
        )
