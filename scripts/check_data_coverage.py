#!/usr/bin/env python3
"""
市场数据覆盖率检查工具
Check Market Data Coverage

检查哪些股票有市场数据，哪些缺失。
支持期权代码检测：期权如果其标的股票有数据，则视为"覆盖"。

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
from src.utils.option_parser import OptionParser
from sqlalchemy import func

# 数据库路径
DB_PATH = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'


def check_coverage(verbose=False, missing_only=False):
    """检查市场数据覆盖率（支持期权标的检测）"""

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

        # 分类统计
        stocks = []  # 股票
        options_covered = []  # 期权（标的有数据）
        options_missing = []  # 期权（标的无数据）
        stocks_covered = []  # 有数据的股票
        stocks_missing = []  # 无数据的股票

        for symbol, trade_count in trade_counts:
            if OptionParser.is_option_symbol(symbol):
                underlying = OptionParser.extract_underlying(symbol)
                if underlying in symbols_with_data:
                    options_covered.append((symbol, trade_count, underlying))
                else:
                    options_missing.append((symbol, trade_count, underlying))
            else:
                if symbol in symbols_with_data:
                    stocks_covered.append((symbol, trade_count))
                else:
                    stocks_missing.append((symbol, trade_count))

        # 计算覆盖率
        total_symbols = len(trade_counts)
        total_stocks = len(stocks_covered) + len(stocks_missing)
        total_options = len(options_covered) + len(options_missing)

        covered_count = len(stocks_covered) + len(options_covered)
        coverage_pct = (covered_count / total_symbols * 100) if total_symbols > 0 else 0

        # 打印报告
        print("=" * 100)
        print("市场数据覆盖率报告 (支持期权标的检测)")
        print("=" * 100)
        print()

        # 总体统计
        print(f"{'类型':<15} {'总数':>8} {'有数据':>10} {'缺失':>8} {'覆盖率':>10}")
        print("-" * 60)

        stock_coverage = len(stocks_covered) / max(total_stocks, 1) * 100
        option_coverage = len(options_covered) / max(total_options, 1) * 100

        print(f"{'股票':<15} {total_stocks:>8} {len(stocks_covered):>10} {len(stocks_missing):>8} {stock_coverage:>9.1f}%")
        print(f"{'期权(标的)':<15} {total_options:>8} {len(options_covered):>10} {len(options_missing):>8} {option_coverage:>9.1f}%")
        print("-" * 60)
        print(f"{'合计':<15} {total_symbols:>8} {covered_count:>10} {total_symbols - covered_count:>8} {coverage_pct:>9.1f}%")
        print()

        # 详细列表
        if not missing_only:
            print("=" * 100)
            print("股票详情")
            print("=" * 100)
            print(f"{'代码':<15} {'类型':<8} {'交易次数':>10} {'市场数据':>12} {'状态':>10}")
            print("-" * 100)

            # 显示有数据的股票
            for symbol, trade_count in stocks_covered:
                data_count = symbols_with_data.get(symbol, 0)
                print(f"{symbol:<15} {'股票':<8} {trade_count:>10} {data_count:>12} {'✓':>10}")

            # 显示有数据的期权
            for symbol, trade_count, underlying in options_covered:
                data_count = symbols_with_data.get(underlying, 0)
                print(f"{symbol:<15} {'期权':<8} {trade_count:>10} {data_count:>12} {'✓ →' + underlying:>10}")

        # 缺失数据的代码
        all_missing = stocks_missing + [(s, c, u) for s, c, u in options_missing]

        if all_missing or stocks_missing or options_missing:
            print()
            print("=" * 100)
            print(f"缺失市场数据 ({len(stocks_missing)} 股票 + {len(options_missing)} 期权)")
            print("=" * 100)
            print()

            if stocks_missing:
                print("【缺失股票】")
                print(f"{'代码':<15} {'交易次数':>10} {'首次交易':>15} {'最后交易':>15}")
                print("-" * 60)

                for symbol, trade_count in sorted(stocks_missing, key=lambda x: x[1], reverse=True):
                    first_trade = session.query(Trade.filled_time).filter(
                        Trade.symbol == symbol
                    ).order_by(Trade.filled_time).first()

                    last_trade = session.query(Trade.filled_time).filter(
                        Trade.symbol == symbol
                    ).order_by(Trade.filled_time.desc()).first()

                    first_time = first_trade[0].strftime('%Y-%m-%d') if first_trade else 'N/A'
                    last_time = last_trade[0].strftime('%Y-%m-%d') if last_trade else 'N/A'

                    print(f"{symbol:<15} {trade_count:>10} {first_time:>15} {last_time:>15}")
                print()

            if options_missing:
                print("【缺失期权（标的无数据）】")

                # 按标的分组
                underlyings = {}
                for symbol, trade_count, underlying in options_missing:
                    if underlying not in underlyings:
                        underlyings[underlying] = []
                    underlyings[underlying].append((symbol, trade_count))

                print(f"{'标的':<10} {'期权数':>8} {'期权代码示例':<30}")
                print("-" * 60)

                for underlying, opts in sorted(underlyings.items()):
                    example = opts[0][0] if opts else ''
                    print(f"{underlying:<10} {len(opts):>8} {example:<30}")
                print()

        else:
            print()
            print("✓ 所有代码都有市场数据!")
            print()

        # 详细信息
        if verbose:
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
                print(f"数据时间范围: {earliest} 至 {latest}")

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
        description='市场数据覆盖率检查工具（支持期权标的检测）',
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
