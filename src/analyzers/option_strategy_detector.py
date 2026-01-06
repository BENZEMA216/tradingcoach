"""
OptionStrategyDetector - 期权策略识别器

input: Position 列表（包含期权和股票持仓）
output: 识别出的期权策略组合
pos: 分析器层 - 自动识别用户的期权交易策略

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md

支持识别的策略：
1. 单腿策略: Long Call, Long Put, Short Call, Short Put
2. 保护性策略: Covered Call, Protective Put, Collar
3. 价差策略: Bull Call Spread, Bear Put Spread, Bull Put Spread, Bear Call Spread
4. 波动率策略: Straddle, Strangle
5. 复合策略: Iron Condor, Iron Butterfly
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
from enum import Enum
import logging

from src.models.position import Position, PositionStatus
from src.utils.option_parser import parse_option, is_option

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """期权策略类型"""
    # 单腿策略
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"

    # 保护性策略
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    COLLAR = "collar"

    # 垂直价差
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    BULL_PUT_SPREAD = "bull_put_spread"
    BEAR_CALL_SPREAD = "bear_call_spread"

    # 波动率策略
    LONG_STRADDLE = "long_straddle"
    SHORT_STRADDLE = "short_straddle"
    LONG_STRANGLE = "long_strangle"
    SHORT_STRANGLE = "short_strangle"

    # 复合策略
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"

    # 未识别
    UNKNOWN = "unknown"


@dataclass
class OptionLeg:
    """期权腿"""
    position: Position
    option_type: str  # 'call' or 'put'
    strike: float
    expiry: date
    direction: str  # 'long' or 'short'
    quantity: int
    underlying: str


@dataclass
class DetectedStrategy:
    """识别出的策略"""
    strategy_type: StrategyType
    strategy_name: str
    strategy_name_cn: str
    underlying: str
    legs: List[OptionLeg]
    stock_position: Optional[Position] = None
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    breakeven: Optional[List[float]] = None
    entry_time: Optional[datetime] = None
    expiry_date: Optional[date] = None
    notes: str = ""


class OptionStrategyDetector:
    """
    期权策略识别器

    分析用户的持仓组合，自动识别期权策略
    """

    # 策略中文名称映射
    STRATEGY_NAMES_CN = {
        StrategyType.LONG_CALL: "买入看涨期权",
        StrategyType.LONG_PUT: "买入看跌期权",
        StrategyType.SHORT_CALL: "卖出看涨期权",
        StrategyType.SHORT_PUT: "卖出看跌期权",
        StrategyType.COVERED_CALL: "备兑看涨",
        StrategyType.PROTECTIVE_PUT: "保护性看跌",
        StrategyType.COLLAR: "领口策略",
        StrategyType.BULL_CALL_SPREAD: "牛市看涨价差",
        StrategyType.BEAR_PUT_SPREAD: "熊市看跌价差",
        StrategyType.BULL_PUT_SPREAD: "牛市看跌价差",
        StrategyType.BEAR_CALL_SPREAD: "熊市看涨价差",
        StrategyType.LONG_STRADDLE: "买入跨式",
        StrategyType.SHORT_STRADDLE: "卖出跨式",
        StrategyType.LONG_STRANGLE: "买入宽跨式",
        StrategyType.SHORT_STRANGLE: "卖出宽跨式",
        StrategyType.IRON_CONDOR: "铁鹰策略",
        StrategyType.IRON_BUTTERFLY: "铁蝶策略",
        StrategyType.UNKNOWN: "未知策略",
    }

    # 时间容差：同一策略的腿之间最大时间差（秒）
    TIME_TOLERANCE_SECONDS = 300  # 5分钟

    def __init__(self):
        """初始化策略识别器"""
        logger.info("OptionStrategyDetector initialized")

    def detect_strategies(
        self,
        positions: List[Position],
        include_closed: bool = True
    ) -> List[DetectedStrategy]:
        """
        识别持仓中的期权策略

        Args:
            positions: 持仓列表
            include_closed: 是否包含已平仓的持仓

        Returns:
            List[DetectedStrategy]: 识别出的策略列表
        """
        # 过滤持仓
        if not include_closed:
            positions = [p for p in positions if p.status == PositionStatus.OPEN]

        # 分离期权和股票持仓
        option_positions = []
        stock_positions = []

        for pos in positions:
            if is_option(pos.symbol):
                option_positions.append(pos)
            else:
                stock_positions.append(pos)

        logger.info(f"Analyzing {len(option_positions)} option positions and "
                   f"{len(stock_positions)} stock positions")

        # 按标的分组
        option_by_underlying = self._group_by_underlying(option_positions)
        stock_by_symbol = {p.symbol: p for p in stock_positions}

        detected_strategies = []

        # 对每个标的识别策略
        for underlying, options in option_by_underlying.items():
            stock_pos = stock_by_symbol.get(underlying)
            strategies = self._detect_strategies_for_underlying(
                underlying, options, stock_pos
            )
            detected_strategies.extend(strategies)

        logger.info(f"Detected {len(detected_strategies)} strategies")
        return detected_strategies

    def _group_by_underlying(
        self,
        option_positions: List[Position]
    ) -> Dict[str, List[OptionLeg]]:
        """按标的分组期权持仓"""
        groups = {}

        for pos in option_positions:
            option_info = parse_option(pos.symbol)
            if not option_info:
                logger.warning(f"Failed to parse option: {pos.symbol}")
                continue

            underlying = option_info['underlying']
            leg = OptionLeg(
                position=pos,
                option_type=option_info['option_type'],
                strike=option_info['strike'],
                expiry=option_info['expiry_date'].date() if isinstance(
                    option_info['expiry_date'], datetime
                ) else option_info['expiry_date'],
                direction=pos.direction,
                quantity=pos.quantity,
                underlying=underlying
            )

            if underlying not in groups:
                groups[underlying] = []
            groups[underlying].append(leg)

        return groups

    def _detect_strategies_for_underlying(
        self,
        underlying: str,
        option_legs: List[OptionLeg],
        stock_position: Optional[Position]
    ) -> List[DetectedStrategy]:
        """识别单个标的的策略"""
        strategies = []

        # 按到期日分组
        legs_by_expiry = {}
        for leg in option_legs:
            if leg.expiry not in legs_by_expiry:
                legs_by_expiry[leg.expiry] = []
            legs_by_expiry[leg.expiry].append(leg)

        # 对每个到期日检测策略
        for expiry, legs in legs_by_expiry.items():
            # 尝试识别复杂策略
            strategy = self._try_detect_complex_strategy(
                underlying, legs, stock_position, expiry
            )
            if strategy:
                strategies.append(strategy)
            else:
                # 识别单腿策略
                for leg in legs:
                    single_strategy = self._detect_single_leg_strategy(leg)
                    strategies.append(single_strategy)

        return strategies

    def _try_detect_complex_strategy(
        self,
        underlying: str,
        legs: List[OptionLeg],
        stock_position: Optional[Position],
        expiry: date
    ) -> Optional[DetectedStrategy]:
        """尝试识别复杂策略"""

        # 分类腿
        long_calls = [l for l in legs if l.option_type == 'call' and l.direction == 'long']
        short_calls = [l for l in legs if l.option_type == 'call' and l.direction == 'short']
        long_puts = [l for l in legs if l.option_type == 'put' and l.direction == 'long']
        short_puts = [l for l in legs if l.option_type == 'put' and l.direction == 'short']

        # 检测各种策略
        strategy = None

        # 1. Covered Call: 持有股票 + 卖出看涨期权
        if stock_position and len(short_calls) == 1 and not long_calls and not long_puts and not short_puts:
            if stock_position.direction == 'long':
                strategy = self._create_covered_call(
                    underlying, short_calls[0], stock_position, expiry
                )

        # 2. Protective Put: 持有股票 + 买入看跌期权
        elif stock_position and len(long_puts) == 1 and not short_puts and not long_calls and not short_calls:
            if stock_position.direction == 'long':
                strategy = self._create_protective_put(
                    underlying, long_puts[0], stock_position, expiry
                )

        # 3. Collar: 持有股票 + 卖出看涨 + 买入看跌
        elif stock_position and len(short_calls) == 1 and len(long_puts) == 1 and not long_calls and not short_puts:
            if stock_position.direction == 'long':
                strategy = self._create_collar(
                    underlying, short_calls[0], long_puts[0], stock_position, expiry
                )

        # 4. Bull Call Spread: 买入低行权价Call + 卖出高行权价Call
        elif len(long_calls) == 1 and len(short_calls) == 1 and not long_puts and not short_puts:
            if long_calls[0].strike < short_calls[0].strike:
                strategy = self._create_vertical_spread(
                    underlying, long_calls[0], short_calls[0], expiry,
                    StrategyType.BULL_CALL_SPREAD
                )

        # 5. Bear Put Spread: 买入高行权价Put + 卖出低行权价Put
        elif len(long_puts) == 1 and len(short_puts) == 1 and not long_calls and not short_calls:
            if long_puts[0].strike > short_puts[0].strike:
                strategy = self._create_vertical_spread(
                    underlying, long_puts[0], short_puts[0], expiry,
                    StrategyType.BEAR_PUT_SPREAD
                )

        # 6. Long Straddle: 买入同行权价Call和Put
        elif len(long_calls) == 1 and len(long_puts) == 1 and not short_calls and not short_puts:
            if abs(long_calls[0].strike - long_puts[0].strike) < 0.01:
                strategy = self._create_straddle(
                    underlying, long_calls[0], long_puts[0], expiry, is_long=True
                )

        # 7. Short Straddle: 卖出同行权价Call和Put
        elif len(short_calls) == 1 and len(short_puts) == 1 and not long_calls and not long_puts:
            if abs(short_calls[0].strike - short_puts[0].strike) < 0.01:
                strategy = self._create_straddle(
                    underlying, short_calls[0], short_puts[0], expiry, is_long=False
                )

        # 8. Long Strangle: 买入不同行权价Call和Put
        elif len(long_calls) == 1 and len(long_puts) == 1 and not short_calls and not short_puts:
            if long_calls[0].strike > long_puts[0].strike:
                strategy = self._create_strangle(
                    underlying, long_calls[0], long_puts[0], expiry, is_long=True
                )

        # 9. Iron Condor: 卖出价差策略的组合
        elif len(short_calls) == 1 and len(long_calls) == 1 and len(short_puts) == 1 and len(long_puts) == 1:
            # 验证是否符合 Iron Condor 结构
            strikes = sorted([
                long_puts[0].strike,
                short_puts[0].strike,
                short_calls[0].strike,
                long_calls[0].strike
            ])
            if (long_puts[0].strike == strikes[0] and
                short_puts[0].strike == strikes[1] and
                short_calls[0].strike == strikes[2] and
                long_calls[0].strike == strikes[3]):
                strategy = self._create_iron_condor(
                    underlying, long_puts[0], short_puts[0],
                    short_calls[0], long_calls[0], expiry
                )

        return strategy

    def _detect_single_leg_strategy(self, leg: OptionLeg) -> DetectedStrategy:
        """识别单腿策略"""
        if leg.option_type == 'call':
            if leg.direction == 'long':
                strategy_type = StrategyType.LONG_CALL
            else:
                strategy_type = StrategyType.SHORT_CALL
        else:  # put
            if leg.direction == 'long':
                strategy_type = StrategyType.LONG_PUT
            else:
                strategy_type = StrategyType.SHORT_PUT

        return DetectedStrategy(
            strategy_type=strategy_type,
            strategy_name=strategy_type.value.replace('_', ' ').title(),
            strategy_name_cn=self.STRATEGY_NAMES_CN[strategy_type],
            underlying=leg.underlying,
            legs=[leg],
            entry_time=leg.position.open_time,
            expiry_date=leg.expiry,
        )

    def _create_covered_call(
        self,
        underlying: str,
        call_leg: OptionLeg,
        stock_position: Position,
        expiry: date
    ) -> DetectedStrategy:
        """创建 Covered Call 策略"""
        return DetectedStrategy(
            strategy_type=StrategyType.COVERED_CALL,
            strategy_name="Covered Call",
            strategy_name_cn=self.STRATEGY_NAMES_CN[StrategyType.COVERED_CALL],
            underlying=underlying,
            legs=[call_leg],
            stock_position=stock_position,
            entry_time=call_leg.position.open_time,
            expiry_date=expiry,
            notes=f"持有 {stock_position.quantity} 股 + 卖出 {call_leg.quantity} 张 {call_leg.strike} Call"
        )

    def _create_protective_put(
        self,
        underlying: str,
        put_leg: OptionLeg,
        stock_position: Position,
        expiry: date
    ) -> DetectedStrategy:
        """创建 Protective Put 策略"""
        return DetectedStrategy(
            strategy_type=StrategyType.PROTECTIVE_PUT,
            strategy_name="Protective Put",
            strategy_name_cn=self.STRATEGY_NAMES_CN[StrategyType.PROTECTIVE_PUT],
            underlying=underlying,
            legs=[put_leg],
            stock_position=stock_position,
            entry_time=put_leg.position.open_time,
            expiry_date=expiry,
            notes=f"持有 {stock_position.quantity} 股 + 买入 {put_leg.quantity} 张 {put_leg.strike} Put"
        )

    def _create_collar(
        self,
        underlying: str,
        call_leg: OptionLeg,
        put_leg: OptionLeg,
        stock_position: Position,
        expiry: date
    ) -> DetectedStrategy:
        """创建 Collar 策略"""
        return DetectedStrategy(
            strategy_type=StrategyType.COLLAR,
            strategy_name="Collar",
            strategy_name_cn=self.STRATEGY_NAMES_CN[StrategyType.COLLAR],
            underlying=underlying,
            legs=[call_leg, put_leg],
            stock_position=stock_position,
            entry_time=min(call_leg.position.open_time, put_leg.position.open_time),
            expiry_date=expiry,
            notes=f"持有股票 + 卖出 {call_leg.strike} Call + 买入 {put_leg.strike} Put"
        )

    def _create_vertical_spread(
        self,
        underlying: str,
        long_leg: OptionLeg,
        short_leg: OptionLeg,
        expiry: date,
        strategy_type: StrategyType
    ) -> DetectedStrategy:
        """创建垂直价差策略"""
        return DetectedStrategy(
            strategy_type=strategy_type,
            strategy_name=strategy_type.value.replace('_', ' ').title(),
            strategy_name_cn=self.STRATEGY_NAMES_CN[strategy_type],
            underlying=underlying,
            legs=[long_leg, short_leg],
            entry_time=min(long_leg.position.open_time, short_leg.position.open_time),
            expiry_date=expiry,
            notes=f"买入 {long_leg.strike} + 卖出 {short_leg.strike}"
        )

    def _create_straddle(
        self,
        underlying: str,
        call_leg: OptionLeg,
        put_leg: OptionLeg,
        expiry: date,
        is_long: bool
    ) -> DetectedStrategy:
        """创建跨式策略"""
        strategy_type = StrategyType.LONG_STRADDLE if is_long else StrategyType.SHORT_STRADDLE
        action = "买入" if is_long else "卖出"

        return DetectedStrategy(
            strategy_type=strategy_type,
            strategy_name=strategy_type.value.replace('_', ' ').title(),
            strategy_name_cn=self.STRATEGY_NAMES_CN[strategy_type],
            underlying=underlying,
            legs=[call_leg, put_leg],
            entry_time=min(call_leg.position.open_time, put_leg.position.open_time),
            expiry_date=expiry,
            notes=f"{action}行权价 {call_leg.strike} 的 Call 和 Put"
        )

    def _create_strangle(
        self,
        underlying: str,
        call_leg: OptionLeg,
        put_leg: OptionLeg,
        expiry: date,
        is_long: bool
    ) -> DetectedStrategy:
        """创建宽跨式策略"""
        strategy_type = StrategyType.LONG_STRANGLE if is_long else StrategyType.SHORT_STRANGLE
        action = "买入" if is_long else "卖出"

        return DetectedStrategy(
            strategy_type=strategy_type,
            strategy_name=strategy_type.value.replace('_', ' ').title(),
            strategy_name_cn=self.STRATEGY_NAMES_CN[strategy_type],
            underlying=underlying,
            legs=[call_leg, put_leg],
            entry_time=min(call_leg.position.open_time, put_leg.position.open_time),
            expiry_date=expiry,
            notes=f"{action} {call_leg.strike} Call 和 {put_leg.strike} Put"
        )

    def _create_iron_condor(
        self,
        underlying: str,
        long_put: OptionLeg,
        short_put: OptionLeg,
        short_call: OptionLeg,
        long_call: OptionLeg,
        expiry: date
    ) -> DetectedStrategy:
        """创建铁鹰策略"""
        return DetectedStrategy(
            strategy_type=StrategyType.IRON_CONDOR,
            strategy_name="Iron Condor",
            strategy_name_cn=self.STRATEGY_NAMES_CN[StrategyType.IRON_CONDOR],
            underlying=underlying,
            legs=[long_put, short_put, short_call, long_call],
            entry_time=min(
                long_put.position.open_time,
                short_put.position.open_time,
                short_call.position.open_time,
                long_call.position.open_time
            ),
            expiry_date=expiry,
            notes=f"买入 {long_put.strike} Put + 卖出 {short_put.strike} Put + "
                  f"卖出 {short_call.strike} Call + 买入 {long_call.strike} Call"
        )

    def get_strategy_summary(
        self,
        strategies: List[DetectedStrategy]
    ) -> Dict:
        """
        生成策略摘要统计

        Args:
            strategies: 识别出的策略列表

        Returns:
            Dict: 策略统计摘要
        """
        summary = {
            'total_strategies': len(strategies),
            'by_type': {},
            'by_underlying': {},
            'strategy_list': []
        }

        for strategy in strategies:
            # 按类型统计
            type_name = strategy.strategy_type.value
            if type_name not in summary['by_type']:
                summary['by_type'][type_name] = 0
            summary['by_type'][type_name] += 1

            # 按标的统计
            if strategy.underlying not in summary['by_underlying']:
                summary['by_underlying'][strategy.underlying] = []
            summary['by_underlying'][strategy.underlying].append(type_name)

            # 策略列表
            summary['strategy_list'].append({
                'type': type_name,
                'type_cn': strategy.strategy_name_cn,
                'underlying': strategy.underlying,
                'expiry': strategy.expiry_date.isoformat() if strategy.expiry_date else None,
                'legs': len(strategy.legs),
                'notes': strategy.notes
            })

        return summary


def detect_option_strategies(positions: List[Position]) -> List[DetectedStrategy]:
    """
    便捷函数：识别持仓中的期权策略

    Args:
        positions: 持仓列表

    Returns:
        List[DetectedStrategy]: 识别出的策略列表
    """
    detector = OptionStrategyDetector()
    return detector.detect_strategies(positions)
