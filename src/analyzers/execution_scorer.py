"""
ExecutionQualityScorer - 执行质量评分器

评估订单执行质量:
1. 滑点控制 (50%)
2. 分批执行效率 (30%)
3. 时机选择 (20%)
"""

import logging
from datetime import datetime, time
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExecutionScore:
    """执行质量评分结果"""
    total_score: float  # 综合评分 0-100
    slippage_score: float  # 滑点评分
    scaling_score: float  # 分批执行评分
    timing_score: float  # 时机评分
    details: Dict[str, Any] = field(default_factory=dict)


class ExecutionQualityScorer:
    """
    执行质量评分器

    评估订单执行的质量:
    - 滑点是否控制良好
    - 是否合理使用分批建仓
    - 入场时机是否避开高波动时段
    """

    # 权重配置
    WEIGHT_SLIPPAGE = 0.50
    WEIGHT_SCALING = 0.30
    WEIGHT_TIMING = 0.20

    # 滑点阈值 (%)
    SLIPPAGE_EXCELLENT = 0.1
    SLIPPAGE_GOOD = 0.3
    SLIPPAGE_ACCEPTABLE = 0.5
    SLIPPAGE_POOR = 1.0

    # 高波动时段 (美东时间)
    HIGH_VOL_OPEN_START = time(9, 30)
    HIGH_VOL_OPEN_END = time(10, 0)
    HIGH_VOL_CLOSE_START = time(15, 30)
    HIGH_VOL_CLOSE_END = time(16, 0)

    def __init__(self):
        """初始化执行质量评分器"""
        logger.info("ExecutionQualityScorer initialized")

    def score(
        self,
        position: Any,
        trades: Optional[List[Any]] = None
    ) -> ExecutionScore:
        """
        计算执行质量评分

        Args:
            position: 持仓对象
            trades: 关联的交易列表

        Returns:
            ExecutionScore: 评分结果
        """
        details = {}

        # 1. 滑点评分 (50%)
        slippage_score, slip_details = self._score_slippage(position, trades)
        details['slippage'] = slip_details

        # 2. 分批执行评分 (30%)
        scaling_score, scale_details = self._score_scaling(position, trades)
        details['scaling'] = scale_details

        # 3. 时机评分 (20%)
        timing_score, timing_details = self._score_timing(position)
        details['timing'] = timing_details

        # 计算综合评分
        total_score = (
            slippage_score * self.WEIGHT_SLIPPAGE +
            scaling_score * self.WEIGHT_SCALING +
            timing_score * self.WEIGHT_TIMING
        )

        return ExecutionScore(
            total_score=round(total_score, 2),
            slippage_score=slippage_score,
            scaling_score=scaling_score,
            timing_score=timing_score,
            details=details
        )

    def _score_slippage(
        self,
        position: Any,
        trades: Optional[List[Any]]
    ) -> tuple[float, Dict]:
        """
        滑点评分

        滑点 = |成交价 - 订单价| / 订单价 * 100%
        """
        details = {}

        if not trades:
            # 尝试从position计算
            return self._estimate_slippage_from_position(position)

        total_slippage = 0
        total_amount = 0
        slippages = []

        for trade in trades:
            order_price = getattr(trade, 'order_price', None)
            filled_price = getattr(trade, 'filled_price', None)
            amount = getattr(trade, 'filled_amount', None)

            if order_price and filled_price and amount:
                order_price = float(order_price)
                filled_price = float(filled_price)
                amount = float(amount)

                if order_price > 0:
                    slip_pct = abs(filled_price - order_price) / order_price * 100
                    slippages.append({
                        'order_price': order_price,
                        'filled_price': filled_price,
                        'slippage_pct': slip_pct
                    })
                    total_slippage += slip_pct * amount
                    total_amount += amount

        if total_amount > 0:
            avg_slippage = total_slippage / total_amount
        else:
            avg_slippage = 0

        details['avg_slippage_pct'] = avg_slippage
        details['trade_slippages'] = slippages[:5]  # 只保留前5条

        # 评分
        if avg_slippage <= self.SLIPPAGE_EXCELLENT:
            score = 95
            details['status'] = 'excellent'
        elif avg_slippage <= self.SLIPPAGE_GOOD:
            score = 80
            details['status'] = 'good'
        elif avg_slippage <= self.SLIPPAGE_ACCEPTABLE:
            score = 65
            details['status'] = 'acceptable'
        elif avg_slippage <= self.SLIPPAGE_POOR:
            score = 50
            details['status'] = 'poor'
        else:
            score = 35
            details['status'] = 'very_poor'

        return score, details

    def _estimate_slippage_from_position(
        self,
        position: Any
    ) -> tuple[float, Dict]:
        """
        从position估算滑点
        """
        details = {'method': 'estimated'}

        # 如果有市场数据，比较入场价与开盘价的差异
        open_price = float(position.open_price) if position.open_price else None

        if not open_price:
            return 75.0, {'status': 'no_data'}

        # 简单假设: 入场价在当日区间内的位置反映执行质量
        # 这是一个简化的估算
        details['entry_price'] = open_price

        # 给一个基础分数
        return 75.0, details

    def _score_scaling(
        self,
        position: Any,
        trades: Optional[List[Any]]
    ) -> tuple[float, Dict]:
        """
        分批执行评分

        评估是否合理使用分批建仓:
        - 大额交易应分批执行
        - 小额交易一次性执行合理
        """
        details = {}

        # 计算交易金额
        if position.open_price and position.quantity:
            multiplier = 100 if position.is_option else 1
            trade_amount = float(position.open_price) * position.quantity * multiplier
            details['trade_amount'] = trade_amount
        else:
            return 75.0, {'status': 'no_data'}

        # 小额交易 (<$3000) 不需要分批
        if trade_amount < 3000:
            details['status'] = 'small_trade'
            details['description'] = '小额交易，无需分批'
            return 90.0, details

        # 检查是否有多笔交易
        if not trades:
            # 无交易明细，假设是一次性交易
            if trade_amount < 5000:
                return 80.0, {'status': 'single_trade', 'trade_amount': trade_amount}
            elif trade_amount < 10000:
                return 70.0, {'status': 'single_trade_large', 'trade_amount': trade_amount}
            else:
                details['status'] = 'single_trade_very_large'
                details['description'] = '大额交易未分批，可能有滑点风险'
                return 55.0, details

        # 有交易明细，分析分批情况
        entry_trades = [t for t in trades if getattr(t, 'direction', '') in ['buy', 'buy_to_open']]
        exit_trades = [t for t in trades if getattr(t, 'direction', '') in ['sell', 'sell_to_close']]

        entry_count = len(entry_trades)
        exit_count = len(exit_trades)

        details['entry_count'] = entry_count
        details['exit_count'] = exit_count

        # 评分逻辑
        if trade_amount >= 10000:
            # 大额交易
            if entry_count >= 3:
                score = 95
                details['status'] = 'well_scaled'
            elif entry_count >= 2:
                score = 80
                details['status'] = 'partially_scaled'
            else:
                score = 55
                details['status'] = 'not_scaled'
        elif trade_amount >= 5000:
            # 中等交易
            if entry_count >= 2:
                score = 90
                details['status'] = 'scaled'
            else:
                score = 70
                details['status'] = 'single_entry'
        else:
            # 较小交易
            score = 85
            details['status'] = 'appropriate'

        return score, details

    def _score_timing(
        self,
        position: Any
    ) -> tuple[float, Dict]:
        """
        时机评分

        评估入场时机:
        - 避开开盘和收盘前30分钟的高波动时段
        - 非交易时段不评分
        """
        details = {}

        if not position.open_time:
            return 75.0, {'status': 'no_time_data'}

        entry_time = position.open_time

        # 转换为时间对象
        if isinstance(entry_time, datetime):
            entry_t = entry_time.time()
            details['entry_time'] = str(entry_t)
        else:
            return 75.0, {'status': 'invalid_time'}

        # 检查是否在高波动时段
        # 注意: 数据可能存储的是UTC时间，这里假设是美东时间
        in_open_volatility = self.HIGH_VOL_OPEN_START <= entry_t <= self.HIGH_VOL_OPEN_END
        in_close_volatility = self.HIGH_VOL_CLOSE_START <= entry_t <= self.HIGH_VOL_CLOSE_END

        details['in_open_vol'] = in_open_volatility
        details['in_close_vol'] = in_close_volatility

        if in_open_volatility:
            # 开盘波动时段
            details['status'] = 'open_volatility'
            details['description'] = '开盘30分钟内入场，波动较大'
            # 开盘入场有时是有策略的，给予中等评分
            return 60.0, details

        elif in_close_volatility:
            # 收盘波动时段
            details['status'] = 'close_volatility'
            details['description'] = '收盘30分钟内入场，波动较大'
            return 65.0, details

        else:
            # 正常交易时段
            # 进一步检查是否在午间低波动时段 (11:30-14:00)
            lunch_start = time(11, 30)
            lunch_end = time(14, 0)

            if lunch_start <= entry_t <= lunch_end:
                details['status'] = 'lunch_hours'
                details['description'] = '午间低波动时段入场'
                return 85.0, details
            else:
                details['status'] = 'normal_hours'
                details['description'] = '正常交易时段入场'
                return 90.0, details

    def __repr__(self) -> str:
        return (
            f"ExecutionQualityScorer("
            f"slippage={self.WEIGHT_SLIPPAGE:.0%}, "
            f"scaling={self.WEIGHT_SCALING:.0%}, "
            f"timing={self.WEIGHT_TIMING:.0%})"
        )
