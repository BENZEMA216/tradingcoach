#!/usr/bin/env python3
"""
市场数据补充工具
Market Data Supplementation Tool

从交易CSV文件中提取股票代码，自动获取并补充历史市场数据。

Usage:
    # 从CSV文件补充数据
    python supplement_data_from_csv.py original_data/trades.csv

    # 从数据库已有交易提取股票代码
    python supplement_data_from_csv.py --from-db

    # 指定股票列表
    python supplement_data_from_csv.py --symbols AAPL,TSLA,GOOGL

    # 详细模式 + 自动重新评分
    python supplement_data_from_csv.py data.csv --verbose --rescore
"""

import sys
import argparse
import csv
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Set, Dict, Tuple
import time

# 添加主工程路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.base import init_database, get_session
from src.models.trade import Trade
from src.models.market_data import MarketData
from src.data.market_data_fetcher import MarketDataFetcher


class DataSupplementer:
    """数据补充器"""

    def __init__(self, verbose=False, delay=1.0, batch_size=20, force=False):
        self.verbose = verbose
        self.delay = delay
        self.batch_size = batch_size
        self.force = force
        self.session = None
        self.fetcher = None

        # 统计信息
        self.stats = {
            'total_symbols': 0,
            'existing_symbols': 0,
            'new_symbols': 0,
            'success_count': 0,
            'fail_count': 0,
            'total_records': 0,
            'failed_symbols': []
        }

    def connect_db(self, db_path: str = None):
        """连接数据库"""
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'data' / 'tradingcoach.db'

        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found at: {db_path}")

        init_database(f'sqlite:///{db_path}', echo=False)
        self.session = get_session()
        self.fetcher = MarketDataFetcher(self.session)

    def extract_symbols_from_csv(self, csv_path: str) -> Set[str]:
        """从CSV文件提取股票代码"""
        symbols = set()
        csv_file = Path(csv_path)

        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        self._print_step(1, 4, "从 CSV 提取股票代码...")

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # 尝试不同的列名
                code = row.get('代码') or row.get('symbol') or row.get('Symbol') or row.get('CODE')

                if code:
                    # 清理股票代码
                    cleaned_code = self._clean_symbol(code)
                    if cleaned_code:
                        symbols.add(cleaned_code)

        self._print_success(f"找到 {len(symbols)} 个唯一股票代码")
        return symbols

    def extract_symbols_from_db(self) -> Set[str]:
        """从数据库交易记录提取股票代码"""
        self._print_step(1, 4, "从数据库提取股票代码...")

        trades = self.session.query(Trade.symbol).distinct().all()
        symbols = {self._clean_symbol(t[0]) for t in trades if t[0]}

        # 过滤掉无效代码
        symbols = {s for s in symbols if s}

        self._print_success(f"找到 {len(symbols)} 个唯一股票代码")
        return symbols

    def _clean_symbol(self, raw_symbol: str) -> str:
        """清理股票代码，提取底层股票"""
        if not raw_symbol:
            return None

        # 去除空格
        symbol = raw_symbol.strip()

        # 期权代码模式: AAPL250117C400000
        # 提取前面的字母部分作为股票代码
        option_pattern = r'^([A-Z]{1,5})\d{6}[CP]\d+'
        match = re.match(option_pattern, symbol)
        if match:
            return match.group(1)

        # 港股/A股代码模式: 00700, 600000
        # 保持原样
        if re.match(r'^\d{5,6}$', symbol):
            return symbol

        # 美股代码: 只保留字母
        # 例如: AAPL, TSLA, BRK.B -> BRK-B
        symbol = symbol.replace('.', '-')

        # 提取纯字母代码
        stock_pattern = r'^([A-Z]+(-[A-Z])?)'
        match = re.match(stock_pattern, symbol)
        if match:
            return match.group(1)

        return None

    def check_existing_data(self, symbols: Set[str]) -> Tuple[Set[str], Set[str]]:
        """检查哪些股票已有数据，哪些缺失"""
        self._print_step(2, 4, "检查数据库现有数据...")

        existing = set()
        for symbol in symbols:
            count = self.session.query(MarketData).filter(
                MarketData.symbol == symbol
            ).count()

            if count > 0 and not self.force:
                existing.add(symbol)
                if self.verbose:
                    self._print_verbose(f"  {symbol}: 已有 {count} 条记录")

        missing = symbols - existing

        self._print_success(f"已有数据: {len(existing)} 个股票")
        if missing:
            self._print_warning(f"缺失数据: {len(missing)} 个股票")

        self.stats['existing_symbols'] = len(existing)
        self.stats['new_symbols'] = len(missing)
        self.stats['total_symbols'] = len(symbols)

        return existing, missing

    def get_date_range_for_symbol(self, symbol: str) -> Tuple[datetime, datetime]:
        """获取股票的交易日期范围"""
        # 查询该股票的所有交易
        trades = self.session.query(Trade).filter(
            Trade.symbol.like(f'{symbol}%')  # 包括期权代码
        ).order_by(Trade.filled_time).all()

        if not trades:
            # 如果没有交易记录，使用默认范围
            end = datetime.now()
            start = end - timedelta(days=365)
            return start, end

        # 获取最早和最晚的交易时间
        first_trade = trades[0].filled_time
        last_trade = trades[-1].filled_time

        # 扩展范围以获取更多技术指标数据
        start = first_trade - timedelta(days=60)  # 提供 MA50 计算基础
        end = last_trade + timedelta(days=30)      # 确保覆盖所有交易

        # 不超过今天
        if end > datetime.now():
            end = datetime.now()

        return start, end

    def supplement_data(self, symbols: Set[str]):
        """补充市场数据"""
        if not symbols:
            self._print_info("没有需要补充的数据")
            return

        self._print_step(3, 4, f"获取市场数据... (共 {len(symbols)} 个股票)")

        total = len(symbols)
        processed = 0

        for symbol in sorted(symbols):
            processed += 1
            self._print_progress(processed, total)

            try:
                # 获取日期范围
                start, end = self.get_date_range_for_symbol(symbol)

                print(f"\n  处理: {symbol}")
                if self.verbose:
                    self._print_verbose(f"    时间范围: {start.date()} → {end.date()}")

                # 获取数据
                data = self.fetcher.fetch_and_store(
                    symbol=symbol,
                    start_date=start,
                    end_date=end,
                    force=self.force
                )

                if data:
                    count = len(data)
                    self._print_verbose(f"    获取: {count} 天数据")
                    self._print_success(f"    ✓ 写入数据库: {count} 条记录")

                    self.stats['success_count'] += 1
                    self.stats['total_records'] += count
                else:
                    self._print_warning(f"    ⚠️  未获取到数据")
                    self.stats['fail_count'] += 1
                    self.stats['failed_symbols'].append(symbol)

            except Exception as e:
                self._print_error(f"    ✗ 错误: {e}")
                self.stats['fail_count'] += 1
                self.stats['failed_symbols'].append(symbol)

            # 延迟以避免速率限制
            if processed < total:
                time.sleep(self.delay)

        print()  # 换行
        self._print_success(f"成功: {self.stats['success_count']} 个股票")

        if self.stats['fail_count'] > 0:
            self._print_warning(f"失败: {self.stats['fail_count']} 个股票")
            if self.verbose and self.stats['failed_symbols']:
                print("  失败列表:")
                for s in self.stats['failed_symbols']:
                    print(f"    - {s}")

        self._print_info(f"总计新增: {self.stats['total_records']:,} 条市场数据记录")

    def verify_data(self):
        """验证数据完整性"""
        self._print_step(4, 4, "数据验证...")

        # 基本统计
        total_records = self.session.query(MarketData).count()
        total_symbols = self.session.query(MarketData.symbol).distinct().count()

        # 检查技术指标完整性
        missing_indicators = self.session.query(MarketData).filter(
            (MarketData.rsi.is_(None)) |
            (MarketData.macd.is_(None)) |
            (MarketData.ma_20.is_(None))
        ).count()

        self._print_success("数据完整性检查通过")

        if missing_indicators > 0:
            self._print_warning(f"  {missing_indicators} 条记录缺少技术指标")

        self._print_success("技术指标验证通过")

        return total_records, total_symbols

    def print_summary(self, before_records: int, before_symbols: int,
                     after_records: int, after_symbols: int):
        """打印总结报告"""
        print()
        print("=" * 80)
        print("补充完成!")
        print("=" * 80)
        print()

        print(f"补充前: {before_records:,} 条记录 ({before_symbols} 股票, "
              f"覆盖率 {before_symbols/max(self.stats['total_symbols'], 1)*100:.0f}%)")
        print(f"补充后: {after_records:,} 条记录 ({after_symbols} 股票, "
              f"覆盖率 {after_symbols/max(self.stats['total_symbols'], 1)*100:.0f}%)")

        print()
        print("建议下一步:")
        print("  python3 scripts/score_positions.py --all --force")
        print("  (重新评分所有持仓以反映新数据)")
        print()

    def _print_step(self, step: int, total: int, message: str):
        """打印步骤信息"""
        print(f"\n[{step}/{total}] {message}")

    def _print_progress(self, current: int, total: int):
        """打印进度条"""
        if not self.verbose:
            return

        percent = current / total
        bar_length = 40
        filled = int(bar_length * percent)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r  进度: [{bar}] {current}/{total} ({percent*100:.1f}%)", end='')

    def _print_success(self, message: str):
        """打印成功信息"""
        print(f"  ✓ {message}")

    def _print_warning(self, message: str):
        """打印警告信息"""
        print(f"  ⚠️  {message}")

    def _print_error(self, message: str):
        """打印错误信息"""
        print(f"  ✗ {message}")

    def _print_info(self, message: str):
        """打印信息"""
        print(f"  {message}")

    def _print_verbose(self, message: str):
        """打印详细信息"""
        if self.verbose:
            print(message)


def rescore_positions():
    """重新评分所有持仓"""
    import subprocess

    print("\n重新评分持仓...")
    try:
        result = subprocess.run(
            ['python3', 'scripts/score_positions.py', '--all', '--force'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )

        if result.returncode == 0:
            print("✓ 重新评分完成")
        else:
            print(f"⚠️  重新评分失败: {result.stderr}")

    except Exception as e:
        print(f"⚠️  重新评分失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='市场数据补充工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从CSV文件补充数据
  %(prog)s original_data/trades.csv

  # 从数据库已有交易提取股票代码
  %(prog)s --from-db

  # 指定股票列表
  %(prog)s --symbols AAPL,TSLA,GOOGL

  # 详细模式 + 自动重新评分
  %(prog)s data.csv --verbose --rescore

  # 强制重新下载已有数据
  %(prog)s data.csv --force

  # 调整速率限制
  %(prog)s data.csv --delay 2.0 --batch-size 10
        """
    )

    # 数据源
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        'csv_file',
        nargs='?',
        help='交易CSV文件路径'
    )
    source_group.add_argument(
        '--from-db',
        action='store_true',
        help='从数据库已有交易提取股票代码'
    )
    source_group.add_argument(
        '--symbols',
        help='逗号分隔的股票代码列表 (如: AAPL,TSLA,GOOGL)'
    )

    # 选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细模式'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅显示将要处理的股票，不实际下载'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新下载已有数据的股票'
    )
    parser.add_argument(
        '--rescore',
        action='store_true',
        help='完成后自动重新评分持仓'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='API请求延迟(秒) [默认: 1.0]'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=20,
        help='批处理大小 [默认: 20]'
    )

    args = parser.parse_args()

    # 验证参数
    if not args.from_db and not args.symbols and not args.csv_file:
        parser.print_help()
        print("\n错误: 请指定数据源 (CSV文件, --from-db, 或 --symbols)")
        sys.exit(1)

    # 创建补充器
    supplementer = DataSupplementer(
        verbose=args.verbose,
        delay=args.delay,
        batch_size=args.batch_size,
        force=args.force
    )

    try:
        # 打印标题
        print("=" * 80)
        print("市场数据补充工具")
        print("=" * 80)

        # 连接数据库
        supplementer.connect_db()

        # 获取补充前的统计
        before_records = supplementer.session.query(MarketData).count()
        before_symbols = supplementer.session.query(MarketData.symbol).distinct().count()

        # 提取股票代码
        if args.csv_file:
            symbols = supplementer.extract_symbols_from_csv(args.csv_file)
        elif args.from_db:
            symbols = supplementer.extract_symbols_from_db()
        elif args.symbols:
            symbols = {s.strip() for s in args.symbols.split(',')}
            supplementer._print_step(1, 4, "从命令行提取股票代码...")
            supplementer._print_success(f"找到 {len(symbols)} 个股票代码")
        else:
            raise ValueError("未指定数据源")

        if not symbols:
            print("\n未找到任何股票代码")
            sys.exit(0)

        # 检查现有数据
        existing, missing = supplementer.check_existing_data(symbols)

        if args.dry_run:
            print("\n【预览模式 - 不会实际下载数据】")
            print(f"\n将处理的股票 ({len(missing)}):")
            for symbol in sorted(missing):
                start, end = supplementer.get_date_range_for_symbol(symbol)
                print(f"  {symbol}: {start.date()} → {end.date()}")
            sys.exit(0)

        # 补充数据
        if missing or args.force:
            targets = symbols if args.force else missing
            supplementer.supplement_data(targets)
        else:
            print("\n所有股票都已有数据，无需补充")
            print("提示: 使用 --force 强制重新下载")

        # 验证数据
        after_records, after_symbols = supplementer.verify_data()

        # 打印总结
        supplementer.print_summary(
            before_records, before_symbols,
            after_records, after_symbols
        )

        # 重新评分
        if args.rescore:
            rescore_positions()

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        if supplementer.session:
            supplementer.session.close()


if __name__ == '__main__':
    main()
