#!/usr/bin/env python3
"""
技术指标验证工具
Technical Indicators Verification Tool

验证特定股票的技术指标数据质量。

Usage:
    python verify_indicators.py AAPL
    python verify_indicators.py AAPL --full
    python verify_indicators.py AAPL --date 2024-11-01
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime
from decimal import Decimal

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.market_data import MarketData

# 数据库路径
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


class IndicatorVerifier:
    """技术指标验证器"""

    def __init__(self, full_details=False):
        self.full_details = full_details
        self.session = None
        self.errors = []
        self.warnings = []

    def connect_db(self):
        """连接数据库"""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found at: {DB_PATH}")

        init_database(f'sqlite:///{DB_PATH}', echo=False)
        self.session = get_session()

    def verify_symbol(self, symbol: str, specific_date: str = None):
        """验证股票的技术指标"""

        print("=" * 100)
        print(f"技术指标验证: {symbol}")
        print("=" * 100)
        print()

        # 查询数据
        query = self.session.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.date)

        if specific_date:
            target_date = datetime.strptime(specific_date, '%Y-%m-%d')
            query = query.filter(MarketData.date == target_date)

        data = query.all()

        if not data:
            print(f"❌ 未找到股票 {symbol} 的市场数据")
            return

        print(f"数据记录数: {len(data)}")
        print(f"时间范围: {data[0].date.date()} 至 {data[-1].date.date()}")
        print()

        # 统计
        total = len(data)
        checks = {
            'price_range': 0,
            'volume_positive': 0,
            'rsi_range': 0,
            'ma_order': 0,
            'macd_present': 0,
            'bb_order': 0,
            'atr_positive': 0,
            'null_values': 0
        }

        # 逐条验证
        for i, md in enumerate(data):
            issues = []

            # 1. 价格范围检查
            if md.close <= 0 or md.open <= 0 or md.high <= 0 or md.low <= 0:
                issues.append("价格异常 (≤0)")
                self.errors.append(f"{md.date.date()}: 价格异常")
            else:
                checks['price_range'] += 1

            # 2. 高低价顺序
            if md.high < md.low:
                issues.append("高价 < 低价")
                self.errors.append(f"{md.date.date()}: 高价 < 低价")

            # 3. 成交量
            if md.volume < 0:
                issues.append("成交量 < 0")
                self.errors.append(f"{md.date.date()}: 成交量异常")
            else:
                checks['volume_positive'] += 1

            # 4. RSI 范围
            if md.rsi is not None:
                rsi = float(md.rsi)
                if 0 <= rsi <= 100:
                    checks['rsi_range'] += 1
                else:
                    issues.append(f"RSI超范围 ({rsi:.2f})")
                    self.errors.append(f"{md.date.date()}: RSI={rsi:.2f} 超出 0-100")
            else:
                checks['null_values'] += 1
                if i > 20:  # 前20条可能没有RSI
                    issues.append("RSI缺失")
                    self.warnings.append(f"{md.date.date()}: RSI缺失")

            # 5. MACD
            if md.macd is not None and md.macd_signal is not None:
                checks['macd_present'] += 1
            else:
                if i > 35:  # MACD需要更多数据
                    issues.append("MACD缺失")
                    self.warnings.append(f"{md.date.date()}: MACD缺失")

            # 6. 移动平均线顺序 (长期 MA 应该更平滑)
            if md.ma_5 is not None and md.ma_20 is not None and md.ma_50 is not None:
                # 不强制要求顺序，但检查是否有异常大的偏差
                ma5 = float(md.ma_5)
                ma20 = float(md.ma_20)
                ma50 = float(md.ma_50)

                # 检查MA与收盘价的合理性
                close = float(md.close)
                if abs(ma5 - close) > close * 0.5:  # MA5不应偏离收盘价太多
                    issues.append(f"MA5异常偏离")
                    self.warnings.append(f"{md.date.date()}: MA5={ma5:.2f} 远离 Close={close:.2f}")
                else:
                    checks['ma_order'] += 1

            # 7. 布林带顺序
            if md.bb_upper is not None and md.bb_middle is not None and md.bb_lower is not None:
                upper = float(md.bb_upper)
                middle = float(md.bb_middle)
                lower = float(md.bb_lower)

                if upper >= middle >= lower:
                    checks['bb_order'] += 1
                else:
                    issues.append("布林带顺序错误")
                    self.errors.append(f"{md.date.date()}: BB顺序 {upper:.2f} / {middle:.2f} / {lower:.2f}")

            # 8. ATR
            if md.atr is not None:
                atr = float(md.atr)
                if atr >= 0:
                    checks['atr_positive'] += 1
                else:
                    issues.append(f"ATR < 0 ({atr:.2f})")
                    self.errors.append(f"{md.date.date()}: ATR={atr:.2f} < 0")

            # 打印详细信息
            if self.full_details:
                status = "✗" if issues else "✓"
                print(f"{md.date.date()} {status}", end='')
                if issues:
                    print(f" - {', '.join(issues)}")
                else:
                    print()

        # 打印检查总结
        print()
        print("=" * 100)
        print("验证结果")
        print("=" * 100)
        print()

        print(f"{'检查项':<25} {'通过数量':>10} {'通过率':>10} {'状态':>10}")
        print("-" * 100)

        self._print_check_result("价格范围正常", checks['price_range'], total)
        self._print_check_result("成交量正常", checks['volume_positive'], total)
        self._print_check_result("RSI 范围 (0-100)", checks['rsi_range'], max(total - 20, 1))
        self._print_check_result("MACD 存在", checks['macd_present'], max(total - 35, 1))
        self._print_check_result("移动平均线合理", checks['ma_order'], max(total - 50, 1))
        self._print_check_result("布林带顺序正确", checks['bb_order'], max(total - 20, 1))
        self._print_check_result("ATR >= 0", checks['atr_positive'], max(total - 14, 1))

        # 错误和警告
        print()
        if self.errors:
            print(f"❌ 发现 {len(self.errors)} 个错误:")
            for err in self.errors[:10]:  # 只显示前10个
                print(f"  - {err}")
            if len(self.errors) > 10:
                print(f"  ... 还有 {len(self.errors) - 10} 个错误")
        else:
            print("✓ 未发现错误")

        print()
        if self.warnings:
            print(f"⚠️  {len(self.warnings)} 个警告:")
            for warn in self.warnings[:10]:
                print(f"  - {warn}")
            if len(self.warnings) > 10:
                print(f"  ... 还有 {len(self.warnings) - 10} 个警告")
        else:
            print("✓ 未发现警告")

        print()

        # 总体评估
        error_rate = len(self.errors) / max(total, 1)
        if error_rate == 0:
            print("✅ 数据质量: 优秀")
        elif error_rate < 0.01:
            print("✅ 数据质量: 良好 (少量错误)")
        elif error_rate < 0.05:
            print("⚠️  数据质量: 一般 (存在一些错误)")
        else:
            print("❌ 数据质量: 差 (错误较多)")

        print()

    def _print_check_result(self, name: str, passed: int, total: int):
        """打印检查结果"""
        rate = (passed / max(total, 1)) * 100
        status = "✓" if rate >= 95 else "⚠️" if rate >= 80 else "✗"
        print(f"{name:<25} {passed:>10}/{total:<5} {rate:>9.1f}% {status:>10}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='技术指标验证工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s AAPL              # 验证 AAPL 的所有数据
  %(prog)s AAPL --full       # 显示每条记录的详细信息
  %(prog)s AAPL --date 2024-11-01  # 验证特定日期
        """
    )

    parser.add_argument(
        'symbol',
        help='股票代码'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='显示每条记录的详细信息'
    )
    parser.add_argument(
        '--date',
        help='验证特定日期 (格式: YYYY-MM-DD)'
    )

    args = parser.parse_args()

    # 创建验证器
    verifier = IndicatorVerifier(full_details=args.full)

    try:
        # 连接数据库
        verifier.connect_db()

        # 验证
        verifier.verify_symbol(args.symbol, args.date)

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except ValueError as e:
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
