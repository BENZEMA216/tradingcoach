"""
FIFO Matcher - 交易配对总协调器

input: Trade表(已成交交易), SymbolMatcher(单标的配对器)
output: Position记录(已平仓/未平仓), 配对统计结果
pos: 配对引擎层核心 - 按标的分组调度配对，汇总生成持仓

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from collections import defaultdict
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

from src.models.trade import Trade, TradeStatus
from src.models.position import Position
from src.matchers.symbol_matcher import SymbolMatcher

logger = logging.getLogger(__name__)


class FIFOMatcher:
    """
    FIFO交易配对器

    总协调器，负责：
    1. 加载所有已完成的交易
    2. 按标的分组，分配给对应的SymbolMatcher
    3. 按时间顺序处理所有交易
    4. 收集所有生成的持仓记录
    5. 保存到数据库

    Usage:
        >>> from src.models.base import get_session
        >>> session = get_session()
        >>> matcher = FIFOMatcher(session)
        >>> result = matcher.match_all_trades()
        >>> print(f"Created {result['positions_created']} positions")
    """

    def __init__(self, session: Session, dry_run: bool = False):
        """
        初始化FIFO配对器

        Args:
            session: 数据库会话
            dry_run: 是否为演练模式（不保存到数据库）
        """
        self.session = session
        self.dry_run = dry_run

        # 每个标的一个SymbolMatcher
        self.symbol_matchers: Dict[str, SymbolMatcher] = {}

        # 统计信息
        self.stats = {
            'total_trades': 0,
            'positions_created': 0,
            'open_positions': 0,
            'closed_positions': 0,
            'warnings': [],
            'symbols_processed': 0
        }

        logger.info(f"Initialized FIFOMatcher (dry_run={dry_run})")

    def match_all_trades(self) -> dict:
        """
        执行完整的配对流程

        流程：
        1. 加载所有已完成的交易
        2. 按时间顺序处理每笔交易
        3. 完成配对，处理未平仓持仓
        4. 保存到数据库
        5. 返回统计信息

        Returns:
            dict: 配对统计信息
        """
        logger.info("=" * 60)
        logger.info("Starting FIFO Matching Process")
        logger.info("=" * 60)

        # Step 1: 加载交易
        trades = self._load_trades()
        if not trades:
            logger.warning("No trades to process")
            return self.stats

        self.stats['total_trades'] = len(trades)

        # Step 2: 处理所有交易
        logger.info(f"Processing {len(trades)} trades...")
        all_positions = self._process_all_trades(trades)

        # Step 3: 完成配对，创建未平仓持仓
        open_positions = self._finalize_all_matchers()
        all_positions.extend(open_positions)

        # Step 4: 统计
        self._calculate_statistics(all_positions)

        # Step 5: 保存到数据库
        if not self.dry_run:
            self._save_positions(all_positions)
            self._update_trade_references(all_positions)
            self.session.commit()
            logger.info("Changes committed to database")
        else:
            logger.info("DRY RUN - No changes saved to database")

        # Step 6: 生成报告
        self._print_summary()

        logger.info("=" * 60)
        logger.info("FIFO Matching Completed Successfully")
        logger.info("=" * 60)

        return self.stats

    def _load_trades(self) -> List[Trade]:
        """
        从数据库加载所有已完成的交易

        按filled_time排序，确保FIFO顺序

        Returns:
            List[Trade]: 交易列表
        """
        logger.info("Loading trades from database...")

        trades = self.session.query(Trade)\
            .filter(Trade.status == TradeStatus.FILLED)\
            .order_by(Trade.filled_time)\
            .all()

        logger.info(f"Loaded {len(trades)} completed trades")

        return trades

    def _process_all_trades(self, trades: List[Trade]) -> List[Position]:
        """
        处理所有交易

        按时间顺序遍历，分配给对应的SymbolMatcher处理

        Args:
            trades: 交易列表（已按时间排序）

        Returns:
            List[Position]: 所有生成的持仓
        """
        all_positions = []

        for i, trade in enumerate(trades, 1):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(trades)} trades...")

            # 获取或创建该标的的matcher
            if trade.symbol not in self.symbol_matchers:
                self.symbol_matchers[trade.symbol] = SymbolMatcher(trade.symbol)

            matcher = self.symbol_matchers[trade.symbol]

            # 处理交易，可能产生0个、1个或多个持仓
            positions = matcher.process_trade(trade)
            all_positions.extend(positions)

        logger.info(f"Generated {len(all_positions)} positions from {len(trades)} trades")

        return all_positions

    def _finalize_all_matchers(self) -> List[Position]:
        """
        完成所有matcher的配对

        为未配对的交易创建未平仓持仓

        Returns:
            List[Position]: 未平仓持仓列表
        """
        logger.info("Finalizing all symbol matchers...")

        open_positions = []

        for symbol, matcher in self.symbol_matchers.items():
            positions = matcher.finalize_open_positions()
            open_positions.extend(positions)

            # 记录警告
            stats = matcher.get_statistics()
            if stats['open_short_trades'] > 0:
                warning = (f"{symbol}: {stats['open_short_trades']} open short positions "
                          f"(sell_short without buy_to_cover)")
                self.stats['warnings'].append(warning)
                logger.warning(warning)

        logger.info(f"Created {len(open_positions)} open positions")

        return open_positions

    def _calculate_statistics(self, all_positions: List[Position]):
        """
        计算统计信息

        Args:
            all_positions: 所有持仓列表
        """
        self.stats['positions_created'] = len(all_positions)
        self.stats['open_positions'] = sum(1 for p in all_positions if p.status.value == 'open')
        self.stats['closed_positions'] = sum(1 for p in all_positions if p.status.value == 'closed')
        self.stats['symbols_processed'] = len(self.symbol_matchers)

    def _save_positions(self, positions: List[Position]):
        """
        批量保存持仓到数据库

        Args:
            positions: 持仓列表
        """
        if not positions:
            return

        logger.info(f"Saving {len(positions)} positions to database...")

        # 批量插入优化
        self.session.bulk_save_objects(positions)

        logger.info("Positions saved successfully")

    def _update_trade_references(self, positions: List[Position]):
        """
        更新交易记录的position_id引用

        Args:
            positions: 持仓列表
        """
        # TODO: 实现交易到持仓的反向引用
        # 需要在Position模型中添加entry_trade_id和exit_trade_id字段
        # 或者在Trade模型中添加position_id字段
        pass

    def _print_summary(self):
        """打印配对总结"""
        logger.info("\n" + "=" * 60)
        logger.info("MATCHING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Trades Processed:    {self.stats['total_trades']}")
        logger.info(f"Symbols Processed:         {self.stats['symbols_processed']}")
        logger.info(f"Positions Created:         {self.stats['positions_created']}")
        logger.info(f"  - Closed Positions:      {self.stats['closed_positions']}")
        logger.info(f"  - Open Positions:        {self.stats['open_positions']}")

        if self.stats['warnings']:
            logger.info(f"\nWarnings ({len(self.stats['warnings'])}):")
            for warning in self.stats['warnings']:
                logger.info(f"  - {warning}")

        logger.info("=" * 60 + "\n")

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """
        获取指定标的的所有持仓

        Args:
            symbol: 交易标的

        Returns:
            List[Position]: 持仓列表
        """
        matcher = self.symbol_matchers.get(symbol)
        if not matcher:
            return []

        return matcher.matched_positions

    def get_statistics(self) -> dict:
        """
        获取配对统计信息

        Returns:
            dict: 统计数据
        """
        return self.stats.copy()


def match_trades_from_database(session: Session, dry_run: bool = False) -> dict:
    """
    便捷函数：从数据库配对所有交易

    Args:
        session: 数据库会话
        dry_run: 是否为演练模式

    Returns:
        dict: 配对统计信息

    Example:
        >>> from src.models.base import get_session
        >>> session = get_session()
        >>> result = match_trades_from_database(session)
        >>> print(f"Created {result['positions_created']} positions")
    """
    matcher = FIFOMatcher(session, dry_run=dry_run)
    return matcher.match_all_trades()
