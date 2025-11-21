#!/usr/bin/env python3
"""
市场数据覆盖率检查工具
Check Market Data Coverage

检查哪些股票有市场数据，哪些缺失。

Usage:
    python check_data_coverage.py
    python check_data_coverage.py --verbose
    python check_data_coverage.py --missing-only
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.trade import Trade
from src.models.market_data import MarketData
from sqlalchemy import func

# 数据库路径
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


def check_coverage(verbose=False, missing_only=False):
    """检查市场数据覆盖率"""

    # 连接数据库
    if not DB_PATH.exists():
        print(f"❌ 数据库未找到: {DB_PATH}")
        sys.exit(1)

    init_database(f'sqlite:///{DB_PATH}', echo=False)
    session = get_session()

    try:
        # 获取所有交易的股票代码及其交易次数
        trade_counts = session.query(
            Trade.symbol,
            func.count(Trade.id).label('trade_count')
        ).group_by(Trade.symbol).order_by(func.count(Trade.id).desc()).all()

        if not trade_counts:
            print("❌ 数据库中没有交易记录")
            return

        # 获取所有有市场数据的股票
        symbols_with_data = {}
        market_data_counts = session.query(
            MarketData.symbol,
            func.count(MarketData.id).label('data_count')
        ).group_by(MarketData.symbol).all()

        for symbol, count in market_data_counts:
            symbols_with_data[symbol] = count

        # 打印报告
        print("=" * 100)
        print("市场数据覆盖率报告")
        print("=" * 100)
        print()

        # 统计
        total_symbols = len(trade_counts)
        symbols_with_data_count = sum(1 for s, _ in trade_counts if s in symbols_with_data)
        coverage_pct = (symbols_with_data_count / total_symbols * 100) if total_symbols > 0 else 0

        print(f"总股票数: {total_symbols}")
        print(f"有数据: {symbols_with_data_count}")
        print(f"缺失: {total_symbols - symbols_with_data_count}")
        print(f"覆盖率: {coverage_pct:.1f}%")
        print()

        # 详细列表
        if not missing_only:
            print(f"{'股票代码':<12} {'交易次数':>10} {'市场数据记录':>15} {'覆盖率':>10} {'状态':>8}")
            print("-" * 100)

        missing_symbols = []

        for symbol, trade_count in trade_counts:
            data_count = symbols_with_data.get(symbol, 0)

            if data_count > 0:
                # 计算覆盖率
                # 假设每个交易日应该有一条市场数据
                first_trade = session.query(Trade.filled_time).filter(
                    Trade.symbol == symbol
                ).order_by(Trade.filled_time).first()

                last_trade = session.query(Trade.filled_time).filter(
                    Trade.symbol == symbol
                ).order_by(Trade.filled_time.desc()).first()

                if first_trade and last_trade:
                    days = (last_trade[0] - first_trade[0]).days + 1
                    expected_data = max(days // 7 * 5, 1)  # 粗略估算工作日
                    coverage = min(data_count / expected_data * 100, 100)
                else:
                    coverage = 100

                status = "✓"

                if not missing_only:
                    print(f"{symbol:<12} {trade_count:>10} {data_count:>15} {coverage:>9.0f}% {status:>8}")

            else:
                missing_symbols.append((symbol, trade_count))
                status = "✗ 缺失"

                if not missing_only:
                    print(f"{symbol:<12} {trade_count:>10} {0:>15} {0:>9.0f}% {status:>8}")

        # 缺失数据的股票
        if missing_symbols:
            print()
            print("=" * 100)
            print(f"缺失市场数据的股票 ({len(missing_symbols)})")
            print("=" * 100)
            print()

            print(f"{'股票代码':<12} {'交易次数':>10} {'首次交易':>20} {'最后交易':>20}")
            print("-" * 100)

            for symbol, trade_count in sorted(missing_symbols, key=lambda x: x[1], reverse=True):
                first_trade = session.query(Trade.filled_time).filter(
                    Trade.symbol == symbol
                ).order_by(Trade.filled_time).first()

                last_trade = session.query(Trade.filled_time).filter(
                    Trade.symbol == symbol
                ).order_by(Trade.filled_time.desc()).first()

                first_time = first_trade[0].strftime('%Y-%m-%d') if first_trade else 'N/A'
                last_time = last_trade[0].strftime('%Y-%m-%d') if last_trade else 'N/A'

                print(f"{symbol:<12} {trade_count:>10} {first_time:>20} {last_time:>20}")

            print()
            print("建议:")
            print(f"  python3 scripts/supplement_data_from_csv.py --from-db")
            print()

        else:
            print()
            print("✓ 所有股票都有市场数据!")
            print()

        # 详细信息
        if verbose and not missing_only:
            print()
            print("=" * 100)
            print("详细统计")
            print("=" * 100)
            print()

            # 市场数据总量
            total_market_data = session.query(MarketData).count()
            print(f"市场数据总记录数: {total_market_data:,}")

            # 最早和最晚的数据
            earliest = session.query(func.min(MarketData.date)).scalar()
            latest = session.query(func.max(MarketData.date)).scalar()

            if earliest and latest:
                print(f"数据时间范围: {earliest.date()} 至 {latest.date()}")

            # 技术指标完整性
            with_rsi = session.query(MarketData).filter(
                MarketData.rsi.isnot(None)
            ).count()

            with_macd = session.query(MarketData).filter(
                MarketData.macd.isnot(None)
            ).count()

            with_ma = session.query(MarketData).filter(
                MarketData.ma_20.isnot(None)
            ).count()

            print(f"\n技术指标完整性:")
            print(f"  RSI: {with_rsi:,} / {total_market_data:,} ({with_rsi/max(total_market_data,1)*100:.1f}%)")
            print(f"  MACD: {with_macd:,} / {total_market_data:,} ({with_macd/max(total_market_data,1)*100:.1f}%)")
            print(f"  MA: {with_ma:,} / {total_market_data:,} ({with_ma/max(total_market_data,1)*100:.1f}%)")
            print()

    finally:
        session.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='市场数据覆盖率检查工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                # 检查所有股票
  %(prog)s --verbose      # 详细信息
  %(prog)s --missing-only # 只显示缺失数据的股票
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    parser.add_argument(
        '--missing-only',
        action='store_true',
        help='只显示缺失数据的股票'
    )

    args = parser.parse_args()

    try:
        check_coverage(verbose=args.verbose, missing_only=args.missing_only)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
