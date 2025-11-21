#!/usr/bin/env python3
"""
计算结果对比工具

用于将人工计算的结果（CSV文件）与数据库中的持仓进行对比。

CSV格式要求:
symbol,quantity,entry_price,exit_price,expected_pnl,notes

Usage:
    python compare_calculations.py manual_calc.csv
    python compare_calculations.py manual_calc.csv --verbose
"""

import sys
from pathlib import Path
import argparse
import csv

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.position import Position, PositionStatus

# 数据库路径
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


class CalculationComparer:
    """计算结果对比器"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.session = None

    def connect_db(self):
        """连接数据库"""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found at: {DB_PATH}")

        init_database(f'sqlite:///{DB_PATH}', echo=False)
        self.session = get_session()

    def compare_csv(self, csv_path: str):
        """对比CSV文件中的计算结果"""
        csv_file = Path(csv_path)
        if not csv_file.exists():
            print(f"\n❌ 找不到文件: {csv_path}")
            return

        print(f"\n{'='*100}")
        print(f"计算结果对比: {csv_file.name}")
        print(f"{'='*100}\n")

        # 读取CSV
        manual_calcs = self._read_csv(csv_file)
        if not manual_calcs:
            print("❌ CSV文件为空或格式错误")
            return

        # 逐行对比
        matches = 0
        mismatches = 0

        print(f"{'#':<4} {'Symbol':<10} {'Qty':>6} {'Entry':>10} {'Exit':>10} "
              f"{'Expected PnL':>12} {'Actual PnL':>12} {'状态':>10}")
        print("-" * 100)

        for i, calc in enumerate(manual_calcs, 1):
            result = self._compare_one(i, calc)
            if result:
                matches += 1
            else:
                mismatches += 1

        # 总结
        print(f"\n{'='*100}")
        print("对比结果总结")
        print(f"{'='*100}")
        print(f"✅ 匹配: {matches}")
        print(f"❌ 不匹配: {mismatches}")
        print(f"总计: {matches + mismatches}")
        print()

    def _read_csv(self, csv_file: Path) -> list:
        """读取CSV文件"""
        manual_calcs = []

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    calc = {
                        'symbol': row['symbol'],
                        'quantity': int(row['quantity']),
                        'entry_price': float(row['entry_price']),
                        'exit_price': float(row['exit_price']),
                        'expected_pnl': float(row['expected_pnl']),
                        'notes': row.get('notes', '')
                    }
                    manual_calcs.append(calc)
                except (KeyError, ValueError) as e:
                    print(f"⚠️  跳过无效行: {row} ({e})")
                    continue

        return manual_calcs

    def _compare_one(self, index: int, calc: dict) -> bool:
        """对比单个计算结果"""
        # 查找匹配的持仓
        positions = self.session.query(Position).filter(
            Position.symbol == calc['symbol'],
            Position.quantity == calc['quantity'],
            Position.status == PositionStatus.CLOSED
        ).all()

        # 尝试找到最接近的持仓
        best_match = None
        min_diff = float('inf')

        for pos in positions:
            entry_diff = abs(float(pos.open_price) - calc['entry_price'])
            exit_diff = abs(float(pos.close_price) - calc['exit_price'])
            total_diff = entry_diff + exit_diff

            if total_diff < min_diff:
                min_diff = total_diff
                best_match = pos

        if not best_match:
            status = "❌ 未找到"
            actual_pnl = "N/A"
            matched = False
        else:
            actual_pnl = float(best_match.net_pnl or 0)
            pnl_diff = abs(actual_pnl - calc['expected_pnl'])

            if pnl_diff < 0.01:
                status = "✅ 匹配"
                matched = True
            else:
                status = f"⚠️  差异 {pnl_diff:.2f}"
                matched = False

            actual_pnl = f"${actual_pnl:.2f}"

        print(f"{index:<4} {calc['symbol']:<10} {calc['quantity']:>6} "
              f"${calc['entry_price']:>9.2f} ${calc['exit_price']:>9.2f} "
              f"${calc['expected_pnl']:>11.2f} {actual_pnl:>12} {status:>10}")

        if self.verbose and best_match:
            print(f"     匹配持仓ID: {best_match.id}")
            if calc['notes']:
                print(f"     备注: {calc['notes']}")

        return matched

    def generate_template(self, output_file: str):
        """生成CSV模板文件"""
        template_path = Path(output_file)

        with open(template_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['symbol', 'quantity', 'entry_price', 'exit_price', 'expected_pnl', 'notes'])
            writer.writerow(['AAPL', '100', '150.00', '155.00', '500.00', '示例持仓'])
            writer.writerow(['TSLA', '50', '200.00', '210.00', '500.00', ''])

        print(f"\n✅ 已生成模板文件: {template_path}")
        print("\n请按以下格式填写:")
        print("  symbol: 股票代码")
        print("  quantity: 数量")
        print("  entry_price: 进场价格")
        print("  exit_price: 出场价格")
        print("  expected_pnl: 预期净盈亏（扣除手续费后）")
        print("  notes: 备注（可选）")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='计算结果对比工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV格式要求:
  symbol,quantity,entry_price,exit_price,expected_pnl,notes
  AAPL,100,150.00,155.00,500.00,示例持仓

示例:
  %(prog)s manual_calc.csv             # 对比CSV中的计算
  %(prog)s manual_calc.csv --verbose   # 详细模式
  %(prog)s --template output.csv       # 生成模板文件
        """
    )

    parser.add_argument(
        'csv_file',
        nargs='?',
        help='包含人工计算结果的CSV文件'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细模式'
    )
    parser.add_argument(
        '--template',
        metavar='FILE',
        help='生成CSV模板文件'
    )

    args = parser.parse_args()

    # 创建对比器
    comparer = CalculationComparer(verbose=args.verbose)

    try:
        if args.template:
            # 生成模板
            comparer.generate_template(args.template)
        elif args.csv_file:
            # 连接数据库并对比
            comparer.connect_db()
            comparer.compare_csv(args.csv_file)
        else:
            parser.print_help()
            print("\n提示: 请指定CSV文件或使用 --template 生成模板")

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if comparer.session:
            comparer.session.close()


if __name__ == '__main__':
    main()
