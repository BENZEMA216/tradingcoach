"""
SymbolMatcher - 单标的FIFO配对器

负责单个交易标的的买卖配对，维护FIFO队列
"""

from collections import deque
from typing import List, Optional, Tuple
from datetime import datetime
import logging

from src.models.trade import Trade, TradeDirection
from src.models.position import Position, PositionStatus
from src.matchers.trade_quantity import TradeQuantity

logger = logging.getLogger(__name__)


class SymbolMatcher:
    """
    单标的FIFO配对器

    为单个交易标的维护开仓队列，执行FIFO配对逻辑。
    支持做多（buy→sell）和做空（sell_short→buy_to_cover）。

    Attributes:
        symbol: 交易标的代码
        open_long_queue: 未配对的买入队列（FIFO）
        open_short_queue: 未配对的卖空队列（FIFO）
        matched_positions: 已配对的持仓列表
    """

    def __init__(self, symbol: str):
        """
        初始化标的配对器

        Args:
            symbol: 交易标的代码
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        self.symbol = symbol
        self.open_long_queue = deque()  # Queue[TradeQuantity] for long positions
        self.open_short_queue = deque()  # Queue[TradeQuantity] for short positions
        self.matched_positions = []  # List[Position]

        logger.info(f"Created SymbolMatcher for {symbol}")

    def process_trade(self, trade: Trade) -> List[Position]:
        """
        处理单笔交易

        Args:
            trade: 交易记录

        Returns:
            List[Position]: 本次交易产生的持仓列表（可能为空、1个或多个）

        Raises:
            ValueError: 如果交易标的与当前标的不匹配
        """
        if trade.symbol != self.symbol:
            raise ValueError(f"Trade symbol {trade.symbol} does not match matcher symbol {self.symbol}")

        logger.debug(f"Processing trade: {trade.symbol} {trade.direction.value} {trade.filled_quantity}")

        # 根据交易方向分发处理
        if trade.is_opening_trade:
            return self._handle_opening_trade(trade)
        elif trade.is_closing_trade:
            return self._handle_closing_trade(trade)
        else:
            logger.warning(f"Unknown trade direction: {trade.direction}")
            return []

    def _handle_opening_trade(self, trade: Trade) -> List[Position]:
        """
        处理开仓交易（买入或卖空）

        Args:
            trade: 交易记录

        Returns:
            List[Position]: 通常返回空列表，只有在反向平仓时才返回持仓
        """
        tq = TradeQuantity(trade)

        if trade.direction == TradeDirection.BUY:
            # 买入：加入做多队列
            self.open_long_queue.append(tq)
            logger.debug(f"Added to long queue: {tq}, queue size: {len(self.open_long_queue)}")
            return []

        elif trade.direction == TradeDirection.SELL_SHORT:
            # 卖空：加入做空队列
            self.open_short_queue.append(tq)
            logger.debug(f"Added to short queue: {tq}, queue size: {len(self.open_short_queue)}")
            return []

        return []

    def _handle_closing_trade(self, trade: Trade) -> List[Position]:
        """
        处理平仓交易（卖出或买券还券）

        使用FIFO算法从队列头部匹配

        Args:
            trade: 交易记录

        Returns:
            List[Position]: 生成的持仓列表
        """
        if trade.direction == TradeDirection.SELL:
            # 卖出：配对做多队列
            return self._match_against_queue(
                trade,
                self.open_long_queue,
                position_direction='long'
            )

        elif trade.direction == TradeDirection.BUY_TO_COVER:
            # 买券还券：配对做空队列
            return self._match_against_queue(
                trade,
                self.open_short_queue,
                position_direction='short'
            )

        return []

    def _match_against_queue(
        self,
        closing_trade: Trade,
        queue: deque,
        position_direction: str
    ) -> List[Position]:
        """
        将平仓交易与队列中的开仓交易配对

        FIFO算法：从队列头部开始匹配，直到平仓交易完全配对

        Args:
            closing_trade: 平仓交易
            queue: 开仓队列（做多或做空）
            position_direction: 持仓方向（'long' 或 'short'）

        Returns:
            List[Position]: 生成的持仓列表
        """
        positions = []
        remaining_qty = closing_trade.filled_quantity

        logger.debug(f"Matching {closing_trade.direction.value} {remaining_qty} against queue size {len(queue)}")

        while remaining_qty > 0 and queue:
            # FIFO：从队列头部取出最早的开仓交易
            opening_tq = queue[0]

            # 计算本次配对数量
            match_qty = min(remaining_qty, opening_tq.remaining_quantity)

            # 创建持仓记录
            position = self._create_position(
                opening_tq=opening_tq,
                closing_trade=closing_trade,
                quantity=match_qty,
                direction=position_direction
            )

            positions.append(position)

            # 更新剩余数量
            opening_tq.consume(match_qty)
            remaining_qty -= match_qty

            logger.debug(f"Matched {match_qty}: {opening_tq.trade.filled_time} -> {closing_trade.filled_time}")

            # 如果开仓交易已完全消耗，从队列移除
            if opening_tq.is_fully_consumed():
                queue.popleft()
                logger.debug(f"Opening trade fully consumed, removed from queue")

        # 检查是否有未配对的平仓交易（理论上不应发生）
        if remaining_qty > 0:
            logger.warning(
                f"Orphaned closing trade: {closing_trade.symbol} {closing_trade.direction.value} "
                f"{remaining_qty} shares have no matching opening trade"
            )

        return positions

    def _create_position(
        self,
        opening_tq: TradeQuantity,
        closing_trade: Trade,
        quantity: int,
        direction: str
    ) -> Position:
        """
        创建持仓记录

        Args:
            opening_tq: 开仓交易数量追踪器
            closing_trade: 平仓交易
            quantity: 配对数量
            direction: 持仓方向 ('long' 或 'short')

        Returns:
            Position: 持仓记录
        """
        opening_trade = opening_tq.trade

        # 基本信息
        position = Position(
            symbol=opening_trade.symbol,
            symbol_name=opening_trade.symbol_name,
            direction=direction,
            status=PositionStatus.CLOSED,
            quantity=quantity,
            market=opening_trade.market.value if hasattr(opening_trade.market, 'value') else opening_trade.market,
            currency=opening_trade.currency,
            is_option=opening_trade.is_option,
            underlying_symbol=opening_trade.underlying_symbol
        )

        # 开仓信息
        position.open_time = opening_trade.filled_time
        position.open_date = opening_trade.trade_date
        position.open_price = opening_trade.filled_price
        position.open_fee = opening_tq.calculate_fee_allocation(quantity)

        # 平仓信息
        position.close_time = closing_trade.filled_time
        position.close_date = closing_trade.trade_date
        position.close_price = closing_trade.filled_price

        # 计算平仓费用分摊（如果平仓交易也是部分成交）
        if closing_trade.filled_quantity > 0:
            total_fee = float(closing_trade.total_fee) if closing_trade.total_fee else 0.0
            close_fee_per_share = total_fee / closing_trade.filled_quantity
            position.close_fee = round(close_fee_per_share * quantity, 2)
        else:
            position.close_fee = 0.0

        # 计算持仓时间
        if position.open_time and position.close_time:
            delta = position.close_time - position.open_time
            position.holding_period_days = delta.days
            position.holding_period_hours = round(delta.total_seconds() / 3600, 2)

        # 计算盈亏（在position_calculator中实现更详细的计算）
        self._calculate_basic_pnl(position)

        # 记录关联
        opening_tq.add_matched_position(position.id if position.id else 0)

        logger.info(f"Created position: {position.symbol} {direction} {quantity} shares, "
                   f"P&L: ${position.net_pnl:.2f}")

        return position

    def _calculate_basic_pnl(self, position: Position):
        """
        计算基础盈亏

        Args:
            position: 持仓记录
        """
        if not position.open_price or not position.close_price or not position.quantity:
            return

        # 转换 Decimal 为 float
        open_price = float(position.open_price)
        close_price = float(position.close_price)
        quantity = int(position.quantity)

        # 计算价差盈亏
        if position.direction == 'long':
            # 做多：盈利 = (卖出价 - 买入价) × 数量
            price_diff = close_price - open_price
        else:  # short
            # 做空：盈利 = (卖空价 - 买券还券价) × 数量
            price_diff = open_price - close_price

        position.realized_pnl = round(price_diff * quantity, 2)

        # 计算百分比
        if open_price > 0:
            position.realized_pnl_pct = round((price_diff / open_price) * 100, 2)

        # 计算净盈亏（扣除费用）
        position.total_fees = (position.open_fee or 0) + (position.close_fee or 0)
        position.net_pnl = round(position.realized_pnl - position.total_fees, 2)

        # 净盈亏百分比
        cost_basis = open_price * quantity
        if cost_basis > 0:
            position.net_pnl_pct = round((position.net_pnl / cost_basis) * 100, 2)

    def finalize_open_positions(self) -> List[Position]:
        """
        完成配对，为未配对的交易创建未平仓持仓

        在所有交易处理完成后调用

        Returns:
            List[Position]: 未平仓持仓列表
        """
        open_positions = []

        # 处理未平仓做多
        for opening_tq in self.open_long_queue:
            position = self._create_open_position(opening_tq, 'long')
            open_positions.append(position)

        # 处理未平仓做空
        for opening_tq in self.open_short_queue:
            position = self._create_open_position(opening_tq, 'short')
            open_positions.append(position)

        if open_positions:
            logger.info(f"{self.symbol}: Created {len(open_positions)} open positions")

        return open_positions

    def _create_open_position(self, opening_tq: TradeQuantity, direction: str) -> Position:
        """
        创建未平仓持仓

        Args:
            opening_tq: 开仓交易数量追踪器
            direction: 持仓方向

        Returns:
            Position: 未平仓持仓记录
        """
        opening_trade = opening_tq.trade

        position = Position(
            symbol=opening_trade.symbol,
            symbol_name=opening_trade.symbol_name,
            direction=direction,
            status=PositionStatus.OPEN,
            quantity=opening_tq.remaining_quantity,  # 使用剩余数量
            market=opening_trade.market.value if hasattr(opening_trade.market, 'value') else opening_trade.market,
            currency=opening_trade.currency,
            is_option=opening_trade.is_option,
            underlying_symbol=opening_trade.underlying_symbol
        )

        # 开仓信息
        position.open_time = opening_trade.filled_time
        position.open_date = opening_trade.trade_date
        position.open_price = opening_trade.filled_price
        position.open_fee = opening_tq.calculate_fee_allocation(opening_tq.remaining_quantity)

        # 未平仓字段设为None
        position.close_time = None
        position.close_date = None
        position.close_price = None
        position.close_fee = None
        position.holding_period_days = None
        position.holding_period_hours = None
        position.realized_pnl = None
        position.net_pnl = None

        logger.info(f"Created open position: {position.symbol} {direction} {position.quantity} shares")

        return position

    def get_statistics(self) -> dict:
        """
        获取配对统计信息

        Returns:
            dict: 统计数据
        """
        return {
            'symbol': self.symbol,
            'matched_positions': len(self.matched_positions),
            'open_long_trades': len(self.open_long_queue),
            'open_short_trades': len(self.open_short_queue),
            'total_open_quantity': (
                sum(tq.remaining_quantity for tq in self.open_long_queue) +
                sum(tq.remaining_quantity for tq in self.open_short_queue)
            )
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return (f"SymbolMatcher({self.symbol}, long_queue={len(self.open_long_queue)}, "
                f"short_queue={len(self.open_short_queue)}, positions={len(self.matched_positions)})")
