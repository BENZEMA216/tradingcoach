#!/usr/bin/env python3
"""
持仓验证工具

用于验证特定持仓ID的详细信息和计算准确性。

Usage:
    python verify_positions.py 1234           # 验证持仓ID 1234
    python verify_positions.py 1234 1235      # 验证多个持仓
    python verify_positions.py 1234 --full    # 显示完整交易链
"""

import sys
from pathlib import Path
import argparse

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.position import Position
from src.models.trade import Trade

# 数据库路径
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


class PositionVerifier:
    """持仓验证器"""

    def __init__(self, full_chain=False):
        self.full_chain = full_chain
        self.session = None

    def connect_db(self):
        """连接数据库"""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found at: {DB_PATH}")

        init_database(f'sqlite:///{DB_PATH}', echo=False)
        self.session = get_session()

    def verify_position(self, position_id: int):
        """验证单个持仓"""
        # 获取持仓
        position = self.session.query(Position).filter(
            Position.id == position_id
        ).first()

        if not position:
            print(f"\n❌ 找不到持仓 ID: {position_id}")
            return

        print(f"\n{'='*100}")
        print(f"持仓验证报告: ID {position_id}")
        print(f"{'='*100}\n")

        # 基本信息
        print("【基本信息】")
        print(f"  股票代码: {position.symbol}")
        print(f"  方向: {position.direction}")
        print(f"  数量: {position.quantity}")
        print(f"  状态: {position.status.value}")

        # 价格信息
        print(f"\n【价格信息】")
        print(f"  进场价格: ${position.open_price:.2f}")
        if position.close_price:
            print(f"  出场价格: ${position.close_price:.2f}")
            price_diff = float(position.close_price) - float(position.open_price)
            print(f"  价格差异: ${price_diff:.2f} ({price_diff/float(position.open_price)*100:.2f}%)")

        # 时间信息
        print(f"\n【时间信息】")
        print(f"  开仓时间: {position.open_time}")
        if position.close_time:
            print(f"  平仓时间: {position.close_time}")
            print(f"  持仓周期: {position.holding_period_days} 天")

        # 盈亏信息
        print(f"\n【盈亏信息】")
        if position.realized_pnl is not None:
            print(f"  盈亏: ${position.realized_pnl:.2f}")
            print(f"  手续费: ${position.total_fees:.2f}")
            print(f"  净盈亏: ${position.net_pnl:.2f}")
            print(f"  净盈亏率: {position.net_pnl_pct:.2f}%")

        # 验证计算
        self._verify_calculations(position)

        # 显示交易链
        if self.full_chain:
            self._show_trade_chain(position)

    def _verify_calculations(self, position: Position):
        """验证计算是否正确"""
        print(f"\n【计算验证】")

        if position.close_price is None:
            print("  ⚠️  持仓未平仓，跳过盈亏验证")
            return

        # 验证盈亏计算
        expected_pnl = (float(position.close_price) - float(position.open_price)) * position.quantity
        actual_pnl = float(position.realized_pnl or 0)

        pnl_match = abs(expected_pnl - actual_pnl) < 0.01

        print(f"  盈亏计算: {'✓ 正确' if pnl_match else '✗ 错误'}")
        if not pnl_match:
            print(f"    预期: ${expected_pnl:.2f}")
            print(f"    实际: ${actual_pnl:.2f}")
            print(f"    差异: ${abs(expected_pnl - actual_pnl):.2f}")

        # 验证净盈亏计算
        expected_net_pnl = actual_pnl - float(position.total_fees or 0)
        actual_net_pnl = float(position.net_pnl or 0)

        net_pnl_match = abs(expected_net_pnl - actual_net_pnl) < 0.01

        print(f"  净盈亏计算: {'✓ 正确' if net_pnl_match else '✗ 错误'}")
        if not net_pnl_match:
            print(f"    预期: ${expected_net_pnl:.2f}")
            print(f"    实际: ${actual_net_pnl:.2f}")

        # 验证盈亏率计算
        if position.net_pnl_pct is not None:
            cost_basis = float(position.open_price) * position.quantity
            expected_pct = (actual_net_pnl / cost_basis) * 100
            actual_pct = float(position.net_pnl_pct)

            pct_match = abs(expected_pct - actual_pct) < 0.01

            print(f"  盈亏率计算: {'✓ 正确' if pct_match else '✗ 错误'}")
            if not pct_match:
                print(f"    预期: {expected_pct:.2f}%")
                print(f"    实际: {actual_pct:.2f}%")

    def _show_trade_chain(self, position: Position):
        """显示完整交易链"""
        print(f"\n【交易链】")

        # 这里需要根据实际的TradeQuantity关联来追踪
        # 简化版本：直接显示可能相关的交易
        opening_trades = self.session.query(Trade).filter(
            Trade.symbol == position.symbol,
            Trade.filled_time <= position.open_time,
            Trade.direction.in_(['buy', 'buy_to_open'])
        ).order_by(Trade.filled_time.desc()).limit(3).all()

        if opening_trades:
            print(f"\n  可能的开仓交易:")
            for t in opening_trades:
                print(f"    {t.filled_time} | {t.direction.value:<15} | "
                      f"{t.filled_quantity:>6} @ ${t.filled_price:.2f}")

        if position.close_time:
            closing_trades = self.session.query(Trade).filter(
                Trade.symbol == position.symbol,
                Trade.filled_time >= position.open_time,
                Trade.filled_time <= position.close_time,
                Trade.direction.in_(['sell', 'sell_to_close'])
            ).order_by(Trade.filled_time).all()

            if closing_trades:
                print(f"\n  平仓交易:")
                for t in closing_trades:
                    print(f"    {t.filled_time} | {t.direction.value:<15} | "
                          f"{t.filled_quantity:>6} @ ${t.filled_price:.2f}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='持仓验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s 1234                  # 验证持仓ID 1234
  %(prog)s 1234 1235 1236        # 验证多个持仓
  %(prog)s 1234 --full           # 显示完整交易链
        """
    )

    parser.add_argument(
        'position_ids',
        nargs='+',
        type=int,
        help='持仓ID（可指定多个）'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='显示完整交易链'
    )

    args = parser.parse_args()

    # 创建验证器
    verifier = PositionVerifier(full_chain=args.full)

    try:
        # 连接数据库
        verifier.connect_db()

        # 验证每个持仓
        for position_id in args.position_ids:
            verifier.verify_position(position_id)

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if verifier.session:
            verifier.session.close()


if __name__ == '__main__':
    main()
