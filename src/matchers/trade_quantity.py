"""
TradeQuantity - 部分成交追踪器

用于追踪交易的剩余可配对数量，支持部分成交场景
"""

from typing import Optional
from src.models.trade import Trade
import logging

logger = logging.getLogger(__name__)


class TradeQuantity:
    """
    交易数量追踪器

    用于FIFO配对中追踪单笔交易的剩余可配对数量。
    当交易被部分配对时，remaining_quantity会逐步减少。

    Example:
        >>> trade = Trade(filled_quantity=100, ...)
        >>> tq = TradeQuantity(trade)
        >>> tq.consume(60)  # 配对60股
        >>> tq.remaining_quantity
        40
        >>> tq.is_fully_consumed()
        False
        >>> tq.consume(40)  # 配对剩余40股
        >>> tq.is_fully_consumed()
        True
    """

    def __init__(self, trade: Trade):
        """
        初始化交易数量追踪器

        Args:
            trade: 交易记录
        """
        if not trade:
            raise ValueError("Trade cannot be None")

        if not trade.filled_quantity or trade.filled_quantity <= 0:
            raise ValueError(f"Invalid filled_quantity: {trade.filled_quantity}")

        self.trade = trade
        self.original_quantity = trade.filled_quantity
        self.remaining_quantity = trade.filled_quantity
        self.matched_positions = []  # 记录所有匹配到的持仓ID

        logger.debug(f"Created TradeQuantity for {trade.symbol} {trade.direction.value} "
                    f"{self.original_quantity} shares")

    def consume(self, quantity: int) -> bool:
        """
        消耗指定数量用于配对

        Args:
            quantity: 要消耗的数量

        Returns:
            bool: True表示完全消耗，False表示还有剩余

        Raises:
            ValueError: 如果消耗数量大于剩余数量
        """
        if quantity <= 0:
            raise ValueError(f"Consume quantity must be positive, got {quantity}")

        if quantity > self.remaining_quantity:
            raise ValueError(
                f"Cannot consume {quantity}, only {self.remaining_quantity} remaining "
                f"(original: {self.original_quantity})"
            )

        self.remaining_quantity -= quantity

        logger.debug(f"Consumed {quantity} from {self.trade.symbol} {self.trade.direction.value}, "
                    f"remaining: {self.remaining_quantity}/{self.original_quantity}")

        return self.is_fully_consumed()

    def is_fully_consumed(self) -> bool:
        """
        检查是否已完全消耗

        Returns:
            bool: True表示已完全配对，False表示还有剩余
        """
        return self.remaining_quantity == 0

    def add_matched_position(self, position_id: int):
        """
        记录匹配到的持仓ID

        Args:
            position_id: 持仓记录ID
        """
        self.matched_positions.append(position_id)

    def get_consumed_quantity(self) -> int:
        """
        获取已消耗的数量

        Returns:
            int: 已配对的数量
        """
        return self.original_quantity - self.remaining_quantity

    def calculate_fee_allocation(self, matched_quantity: int) -> float:
        """
        计算费用分摊

        当交易被部分配对时，费用按比例分摊

        Args:
            matched_quantity: 本次配对的数量

        Returns:
            float: 分摊的费用（保留2位小数）

        Example:
            >>> # 总费用$10，配对60/100股
            >>> tq.calculate_fee_allocation(60)
            6.0
        """
        if not self.trade.total_fee:
            return 0.0

        if self.original_quantity == 0:
            return 0.0

        # 比例分摊：(配对数量 / 原始数量) * 总费用
        # 转换 Decimal 为 float
        total_fee = float(self.trade.total_fee) if self.trade.total_fee else 0.0
        allocated_fee = (matched_quantity / self.original_quantity) * total_fee

        return round(allocated_fee, 2)

    def __repr__(self) -> str:
        """字符串表示"""
        status = "FULLY_CONSUMED" if self.is_fully_consumed() else "PARTIAL"
        return (f"TradeQuantity({self.trade.symbol} {self.trade.direction.value} "
                f"{self.remaining_quantity}/{self.original_quantity} {status})")

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        return self.__repr__()
