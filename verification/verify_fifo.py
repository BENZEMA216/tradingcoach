#!/usr/bin/env python3
"""
FIFO匹配验证工具

用于人工验证交易的FIFO（先进先出）匹配逻辑是否正确。

Usage:
    python verify_fifo.py AAPL              # 验证单个股票
    python verify_fifo.py AAPL TSLA         # 验证多个股票
    python verify_fifo.py AAPL --verbose    # 详细模式
    python verify_fifo.py --top 10          # 验证交易最多的前10个股票
    python verify_fifo.py --list            # 列出所有可验证的股票
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
import argparse

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.trade import Trade, TradeDirection
from src.models.position import Position, PositionStatus
from sqlalchemy import func

# 数据库路径（相对于verification/目录）
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def green(cls, text):
        return f"{cls.GREEN}{text}{cls.END}"

    @classmethod
    def red(cls, text):
        return f"{cls.RED}{text}{cls.END}"

    @classmethod
    def yellow(cls, text):
        return f"{cls.YELLOW}{text}{cls.END}"

    @classmethod
    def blue(cls, text):
        return f"{cls.BLUE}{text}{cls.END}"

    @classmethod
    def bold(cls, text):
        return f"{cls.BOLD}{text}{cls.END}"


class FIFOVerifier:
    """FIFO匹配验证器"""

    def __init__(self, verbose=False, debug=False):
        """
        初始化验证器

        Args:
            verbose: 详细模式
            debug: 调试模式
        """
        self.verbose = verbose
        self.debug = debug
        self.session = None

    def connect_db(self):
        """连接数据库"""
        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Database not found at: {DB_PATH}\n"
                f"Please ensure you're running from the verification/ directory "
                f"and the main database exists."
            )

        init_database(f'sqlite:///{DB_PATH}', echo=False)
        self.session = get_session()

    def verify_symbol(self, symbol: str) -> bool:
        """
        验证单个股票的FIFO匹配

        Args:
            symbol: 股票代码

        Returns:
            bool: 验证是否通过
        """
        print(f"\n{'='*100}")
        print(Colors.bold(f"FIFO 验证报告: {symbol}"))
        print(f"{'='*100}\n")

        # 获取交易序列
        trades = self._get_trades(symbol)
        if not trades:
            print(Colors.red(f"❌ 没有找到 {symbol} 的交易记录"))
            return False

        # 显示交易序列
        self._print_trade_sequence(trades)

        # 手动模拟FIFO匹配
        manual_positions = self._manual_fifo_match(trades)

        # 获取数据库中的持仓
        db_positions = self._get_db_positions(symbol)

        # 对比结果
        passed = self._compare_results(manual_positions, db_positions)

        # 显示验证结果
        self._print_verification_result(passed)

        return passed

    def _get_trades(self, symbol: str) -> List[Trade]:
        """获取指定股票的所有交易"""
        trades = self.session.query(Trade).filter(
            Trade.symbol == symbol,
            Trade.filled_quantity.isnot(None),
            Trade.filled_time.isnot(None)
        ).order_by(Trade.filled_time).all()

        return trades

    def _get_db_positions(self, symbol: str) -> List[Position]:
        """获取数据库中的持仓"""
        positions = self.session.query(Position).filter(
            Position.symbol == symbol,
            Position.status == PositionStatus.CLOSED
        ).order_by(Position.open_time).all()

        return positions

    def _print_trade_sequence(self, trades: List[Trade]):
        """打印交易序列"""
        print(Colors.bold("【交易序列】") + " (按时间顺序)\n")

        print(f"{'时间':<22} {'方向':<10} {'数量':>6} {'价格':>10} {'手续费':>8} {'累计持仓':>10}")
        print("-" * 100)

        net_position = 0
        for trade in trades:
            direction_cn = {
                'buy': '买入',
                'sell': '卖出',
                'buy_to_open': '买入开仓',
                'sell_to_open': '卖空',
                'buy_to_close': '买入平仓',
                'sell_to_close': '卖出平仓'
            }.get(trade.direction.value, trade.direction.value)

            # 计算净持仓变化
            if trade.direction.value in ['buy', 'buy_to_open', 'buy_to_close']:
                net_position += trade.filled_quantity
                sign = '+'
            else:
                net_position -= trade.filled_quantity
                sign = ''

            time_str = trade.filled_time.strftime('%Y-%m-%d %H:%M:%S')
            price_str = f"${trade.filled_price:.2f}"
            fee_str = f"${trade.total_fee:.2f}" if trade.total_fee else "N/A"
            position_str = f"{sign}{net_position}"

            print(f"{time_str:<22} {direction_cn:<10} {trade.filled_quantity:>6} "
                  f"{price_str:>10} {fee_str:>8} {position_str:>10}")

        print()

    def _manual_fifo_match(self, trades: List[Trade]) -> List[Dict]:
        """
        手动模拟FIFO匹配

        Returns:
            List[Dict]: 手动计算的持仓列表
        """
        print(Colors.bold("【FIFO匹配过程】") + " (手动模拟)\n")

        positions = []
        open_queue = deque()  # 未匹配的买入交易

        match_num = 0

        for trade in trades:
            is_buy = trade.direction.value in ['buy', 'buy_to_open']

            if is_buy:
                # 买入交易进入队列
                open_queue.append({
                    'trade': trade,
                    'remaining_qty': trade.filled_quantity
                })
                if self.verbose:
                    print(f"  → 买入 {trade.filled_quantity} @ ${trade.filled_price:.2f} 进入队列")

            else:
                # 卖出交易，开始匹配
                sell_qty = trade.filled_quantity
                sell_remaining = sell_qty

                while sell_remaining > 0 and open_queue:
                    match_num += 1

                    # FIFO: 取最早的买入
                    buy_entry = open_queue[0]
                    buy_trade = buy_entry['trade']

                    # 计算匹配数量
                    match_qty = min(sell_remaining, buy_entry['remaining_qty'])

                    # 创建持仓记录
                    position = self._create_manual_position(
                        match_num, buy_trade, trade, match_qty, buy_entry
                    )
                    positions.append(position)

                    # 打印匹配详情
                    if self.verbose or True:  # 总是显示匹配过程
                        self._print_match_detail(
                            match_num, buy_trade, trade, match_qty,
                            buy_entry['remaining_qty'], sell_remaining, position
                        )

                    # 更新剩余数量
                    buy_entry['remaining_qty'] -= match_qty
                    sell_remaining -= match_qty

                    # 如果买入完全匹配，移出队列
                    if buy_entry['remaining_qty'] == 0:
                        open_queue.popleft()

        # 显示未匹配的买入
        if open_queue:
            print(Colors.yellow("\n【未平仓持仓】"))
            for entry in open_queue:
                trade = entry['trade']
                print(f"  买入 {entry['remaining_qty']} @ ${trade.filled_price:.2f} "
                      f"({trade.filled_time.strftime('%Y-%m-%d')})")

        print()
        return positions

    def _create_manual_position(
        self, match_num: int, buy_trade: Trade, sell_trade: Trade,
        match_qty: int, buy_entry: Dict
    ) -> Dict:
        """创建手动计算的持仓记录"""
        # 计算手续费分配
        buy_total_qty = buy_trade.filled_quantity
        buy_matched_qty_so_far = buy_total_qty - buy_entry['remaining_qty']
        buy_fee_allocation = (match_qty / buy_total_qty) * (buy_trade.total_fee or 0)

        sell_fee_allocation = (match_qty / sell_trade.filled_quantity) * (sell_trade.total_fee or 0)

        # 计算盈亏
        entry_price = buy_trade.filled_price
        exit_price = sell_trade.filled_price
        realized_pnl = (exit_price - entry_price) * match_qty
        net_pnl = realized_pnl - buy_fee_allocation - sell_fee_allocation

        # 持仓周期
        holding_days = (sell_trade.filled_time - buy_trade.filled_time).days

        return {
            'match_num': match_num,
            'symbol': buy_trade.symbol,
            'quantity': match_qty,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'entry_fee': buy_fee_allocation,
            'exit_fee': sell_fee_allocation,
            'total_fee': buy_fee_allocation + sell_fee_allocation,
            'realized_pnl': realized_pnl,
            'net_pnl': net_pnl,
            'net_pnl_pct': (net_pnl / (entry_price * match_qty)) * 100,
            'holding_days': holding_days,
            'open_time': buy_trade.filled_time,
            'close_time': sell_trade.filled_time,
        }

    def _print_match_detail(
        self, match_num: int, buy_trade: Trade, sell_trade: Trade,
        match_qty: int, buy_remaining: int, sell_remaining: int, position: Dict
    ):
        """打印匹配详情"""
        print(Colors.blue(f"匹配 #{match_num}:"))
        print(f"  开仓交易: 买入 {buy_trade.filled_quantity} @ "
              f"${buy_trade.filled_price:.2f} ({buy_trade.filled_time.strftime('%Y-%m-%d %H:%M')})")
        print(f"  平仓交易: 卖出 {sell_trade.filled_quantity} @ "
              f"${sell_trade.filled_price:.2f} ({sell_trade.filled_time.strftime('%Y-%m-%d %H:%M')})")
        print(f"  匹配数量: {Colors.bold(str(match_qty))} 股")

        if self.verbose:
            print(f"\n  计算详情:")
            print(f"    进场价格: ${position['entry_price']:.2f}")
            print(f"    出场价格: ${position['exit_price']:.2f}")
            print(f"    进场手续费: ${position['entry_fee']:.2f} "
                  f"({match_qty}/{buy_trade.filled_quantity} × ${buy_trade.total_fee:.2f})")
            print(f"    出场手续费: ${position['exit_fee']:.2f} "
                  f"({match_qty}/{sell_trade.filled_quantity} × ${sell_trade.total_fee:.2f})")
            print(f"    盈亏: (${position['exit_price']:.2f} - ${position['entry_price']:.2f}) × {match_qty} "
                  f"= ${position['realized_pnl']:.2f}")
            print(f"    净盈亏: ${position['realized_pnl']:.2f} - ${position['entry_fee']:.2f} - "
                  f"${position['exit_fee']:.2f} = ${position['net_pnl']:.2f}")
            print(f"    盈亏率: {position['net_pnl_pct']:.2f}%")
            print(f"    持仓天数: {position['holding_days']} 天")

        print()

    def _compare_results(
        self, manual_positions: List[Dict], db_positions: List[Position]
    ) -> bool:
        """对比手动计算与数据库结果"""
        print(Colors.bold("【数据库持仓记录对比】\n"))

        if len(manual_positions) != len(db_positions):
            print(Colors.red(f"❌ 持仓数量不匹配！"))
            print(f"   手动计算: {len(manual_positions)} 个持仓")
            print(f"   数据库:   {len(db_positions)} 个持仓")
            return False

        # 表头
        print(f"{'#':<4} {'Position ID':<12} {'数量':>6} {'进场价':>10} {'出场价':>10} "
              f"{'净盈亏':>10} {'状态':<8} {'验证':>6}")
        print("-" * 100)

        all_match = True
        for i, (manual, db_pos) in enumerate(zip(manual_positions, db_positions), 1):
            # 检查各项是否匹配
            qty_match = manual['quantity'] == db_pos.quantity
            entry_match = abs(manual['entry_price'] - float(db_pos.open_price)) < 0.01
            exit_match = abs(manual['exit_price'] - float(db_pos.close_price)) < 0.01
            pnl_match = abs(manual['net_pnl'] - float(db_pos.net_pnl or 0)) < 0.01

            all_fields_match = qty_match and entry_match and exit_match and pnl_match

            # 状态标记
            status_mark = Colors.green("✓ 匹配") if all_fields_match else Colors.red("✗ 不匹配")

            print(f"{i:<4} {db_pos.id:<12} {db_pos.quantity:>6} "
                  f"${db_pos.open_price:>9.2f} ${db_pos.close_price:>9.2f} "
                  f"${db_pos.net_pnl:>9.2f} "
                  f"{db_pos.status.value:<8} {status_mark:>6}")

            if not all_fields_match:
                all_match = False
                if self.verbose:
                    print(f"     手动计算: qty={manual['quantity']}, "
                          f"entry=${manual['entry_price']:.2f}, "
                          f"exit=${manual['exit_price']:.2f}, "
                          f"pnl=${manual['net_pnl']:.2f}")

        print()
        return all_match

    def _print_verification_result(self, passed: bool):
        """打印验证结果"""
        print(Colors.bold("【验证结果】"))

        if passed:
            print(Colors.green("✅ 通过"))
            print("- FIFO顺序: ✓")
            print("- 数量匹配: ✓")
            print("- 价格匹配: ✓")
            print("- 手续费分配: ✓")
            print("- 盈亏计算: ✓")
        else:
            print(Colors.red("❌ 失败"))
            print("请检查上述不匹配项")

        print()

    def list_available_symbols(self):
        """列出所有可验证的股票"""
        symbols = self.session.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count')
        ).group_by(Trade.symbol).order_by(
            func.count(Trade.id).desc()
        ).all()

        print(f"\n{'='*60}")
        print(Colors.bold("可验证的股票列表"))
        print(f"{'='*60}\n")

        print(f"{'股票代码':<15} {'交易数量':>10}")
        print("-" * 60)

        for symbol, count in symbols[:50]:  # 只显示前50个
            print(f"{symbol:<15} {count:>10}")

        if len(symbols) > 50:
            print(f"\n... 还有 {len(symbols) - 50} 个股票未显示")

        print(f"\n总计: {len(symbols)} 个股票")
        print()

    def verify_top_symbols(self, top_n: int):
        """验证交易最多的前N个股票"""
        symbols = self.session.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count')
        ).group_by(Trade.symbol).order_by(
            func.count(Trade.id).desc()
        ).limit(top_n).all()

        print(f"\n{'='*60}")
        print(Colors.bold(f"验证交易最多的前 {top_n} 个股票"))
        print(f"{'='*60}\n")

        passed_count = 0
        failed_count = 0

        for symbol, count in symbols:
            passed = self.verify_symbol(symbol)
            if passed:
                passed_count += 1
            else:
                failed_count += 1

        print(f"\n{'='*60}")
        print(Colors.bold("总体验证结果"))
        print(f"{'='*60}")
        print(f"通过: {Colors.green(str(passed_count))}")
        print(f"失败: {Colors.red(str(failed_count))}")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='FIFO匹配验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s AAPL                  # 验证AAPL
  %(prog)s AAPL TSLA             # 验证多个股票
  %(prog)s AAPL --verbose        # 详细模式
  %(prog)s --top 10              # 验证前10个股票
  %(prog)s --list                # 列出所有股票
        """
    )

    parser.add_argument(
        'symbols',
        nargs='*',
        help='股票代码（可指定多个）'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细模式'
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='调试模式'
    )
    parser.add_argument(
        '--top',
        type=int,
        metavar='N',
        help='验证交易最多的前N个股票'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可验证的股票'
    )

    args = parser.parse_args()

    # 创建验证器
    verifier = FIFOVerifier(verbose=args.verbose, debug=args.debug)

    try:
        # 连接数据库
        verifier.connect_db()

        # 根据参数执行不同操作
        if args.list:
            verifier.list_available_symbols()
        elif args.top:
            verifier.verify_top_symbols(args.top)
        elif args.symbols:
            for symbol in args.symbols:
                verifier.verify_symbol(symbol)
        else:
            parser.print_help()
            print(f"\n{Colors.yellow('提示: 请指定股票代码或使用 --list 查看可用股票')}")

    except FileNotFoundError as e:
        print(Colors.red(f"\n错误: {e}"))
        sys.exit(1)
    except Exception as e:
        print(Colors.red(f"\n错误: {e}"))
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        if verifier.session:
            verifier.session.close()


if __name__ == '__main__':
    main()
