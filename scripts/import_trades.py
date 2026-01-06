"""
交易数据导入脚本

从CSV文件导入交易记录到数据库

Usage:
    python scripts/import_trades.py <csv_path>
    python scripts/import_trades.py original_data/历史-保证金综合账户*.csv
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import argparse

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.models.trade import Trade, TradeDirection
from src.importers.csv_parser import CSVParser
from src.importers.data_cleaner import DataCleaner
import pandas as pd
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_DIR / 'import_trades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clean_value(value):
    """Convert pandas NaN/None to Python None"""
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, np.floating)):
        if np.isnan(value):
            return None
        return float(value) if isinstance(value, np.floating) else int(value)
    return value


class TradeImporter:
    """交易数据导入器"""

    def __init__(self, csv_path: str, dry_run: bool = False):
        """
        初始化导入器

        Args:
            csv_path: CSV文件路径
            dry_run: 是否为测试运行（不写入数据库）
        """
        self.csv_path = Path(csv_path)
        self.dry_run = dry_run
        self.session = None

        self.stats = {
            'csv_total_rows': 0,
            'csv_filtered': 0,
            'cleaned_rows': 0,
            'trades_created': 0,
            'trades_updated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
        }

    def run(self):
        """执行导入流程"""
        self.stats['start_time'] = datetime.now()
        logger.info("="*60)
        logger.info("Starting trade import process...")
        logger.info(f"CSV file: {self.csv_path}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("="*60)

        try:
            # 1. 解析CSV
            logger.info("\n[Step 1/4] Parsing CSV file...")
            df = self._parse_csv()

            # 2. 清洗数据
            logger.info("\n[Step 2/4] Cleaning data...")
            cleaned_df, clean_stats = self._clean_data(df)

            # 3. 转换为Trade对象
            logger.info("\n[Step 3/4] Converting to Trade objects...")
            trades = self._convert_to_trades(cleaned_df)

            # 4. 保存到数据库
            logger.info("\n[Step 4/4] Saving to database...")
            if not self.dry_run:
                self._save_to_database(trades)
            else:
                logger.info("DRY RUN: Skipping database save")
                self.stats['trades_created'] = len(trades)

            # 完成
            self.stats['end_time'] = datetime.now()
            self._print_summary()

        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            self.stats['end_time'] = datetime.now()
            self._print_summary()
            raise

        finally:
            if self.session:
                self.session.close()

    def _parse_csv(self):
        """解析CSV文件"""
        parser = CSVParser(str(self.csv_path))
        df = parser.parse()

        self.stats['csv_total_rows'] = len(df)

        # 过滤已成交订单
        completed_df = parser.filter_completed_trades()
        self.stats['csv_filtered'] = self.stats['csv_total_rows'] - len(completed_df)

        logger.info(f"Parsed {self.stats['csv_total_rows']} rows from CSV")
        logger.info(f"Filtered to {len(completed_df)} completed trades")

        return completed_df

    def _clean_data(self, df):
        """清洗数据"""
        cleaner = DataCleaner(df)
        cleaned_df = cleaner.clean()
        clean_stats = cleaner.get_statistics()

        self.stats['cleaned_rows'] = len(cleaned_df)

        logger.info(f"Cleaned data: {len(cleaned_df)} rows")
        logger.info(f"Partial fills detected: {clean_stats['partial_fills_split']}")
        logger.info(f"Symbols parsed: {clean_stats['symbols_parsed']}")

        if clean_stats['errors']:
            logger.warning(f"Cleaning warnings: {len(clean_stats['errors'])}")
            for error in clean_stats['errors'][:5]:  # 只显示前5个
                logger.warning(f"  - {error}")

        return cleaned_df, clean_stats

    def _convert_to_trades(self, df):
        """
        将DataFrame转换为Trade对象列表

        Args:
            df: 清洗后的DataFrame

        Returns:
            List[Trade]: Trade对象列表
        """
        trades = []

        for idx, row in df.iterrows():
            try:
                trade = self._row_to_trade(row)
                if trade is not None:  # Skip invalid rows
                    trades.append(trade)
            except Exception as e:
                logger.error(f"Error converting row {idx}: {e}")
                logger.error(f"Row data: {row.to_dict()}")
                self.stats['errors'] += 1

        logger.info(f"Converted {len(trades)} DataFrame rows to Trade objects")
        return trades

    def _row_to_trade(self, row) -> Trade:
        """
        将DataFrame行转换为Trade对象

        Args:
            row: DataFrame行

        Returns:
            Trade: Trade对象，如果数据无效则返回None
        """
        # Validate required fields
        symbol = clean_value(row.get('symbol'))
        direction = clean_value(row.get('direction'))
        filled_qty = clean_value(row.get('filled_quantity'))
        filled_time = clean_value(row.get('filled_time_utc'))

        if not symbol or not direction or not filled_qty or not filled_time:
            # Skip invalid rows
            return None

        # 推断 market 字段
        market = clean_value(row.get('market'))
        exchange = clean_value(row.get('exchange'))

        # 如果没有 market，尝试从 exchange 推断
        if not market and exchange:
            exchange_to_market = {
                '上交所': 'CN_STOCK', '深交所': 'CN_STOCK',
                '上海A股': 'CN_STOCK', '深圳A股': 'CN_STOCK',
                '沪市': 'CN_STOCK', '深市': 'CN_STOCK',
            }
            market = exchange_to_market.get(exchange, 'CN_STOCK')

        # 如果还是没有 market，从 symbol 推断（A股 symbol 格式）
        if not market and symbol:
            # A股：600xxx(沪), 601xxx(沪), 603xxx(沪), 000xxx(深), 002xxx(深), 300xxx(深)
            if symbol[:3] in ['600', '601', '603', '000', '002', '300']:
                market = 'CN_STOCK'

        # 推断 currency
        currency = clean_value(row.get('currency'))
        if not currency:
            currency = 'CNY' if market == 'CN_STOCK' else 'USD'

        # 基本信息
        trade = Trade(
            symbol=symbol,
            symbol_name=clean_value(row.get('symbol_name')),
            direction=direction,
            market=market,
            currency=currency,
        )

        # 订单信息
        trade.order_price = clean_value(row.get('order_price'))
        trade.order_quantity = clean_value(row.get('order_quantity'))
        trade.order_amount = clean_value(row.get('order_amount'))
        trade.order_type = clean_value(row.get('order_type'))
        trade.order_time = clean_value(row.get('order_time_utc'))

        # 成交信息
        trade.filled_price = clean_value(row.get('filled_price'))
        trade.filled_quantity = filled_qty  # Already validated and cleaned
        trade.filled_amount = clean_value(row.get('filled_amount'))
        trade.filled_time = filled_time  # Already validated and cleaned

        # Trade date (extracted from filled_time)
        if trade.filled_time:
            trade.trade_date = trade.filled_time.date()

        # 费用信息
        trade.commission = clean_value(row.get('commission'))
        trade.platform_fee = clean_value(row.get('platform_fee'))
        trade.clearing_fee = clean_value(row.get('clearing_fee'))
        trade.stamp_duty = clean_value(row.get('stamp_duty'))
        trade.transaction_fee = clean_value(row.get('transaction_fee'))
        trade.sec_fee = clean_value(row.get('sec_fee'))
        trade.option_regulatory_fee = clean_value(row.get('option_regulatory_fee'))
        trade.option_clearing_fee = clean_value(row.get('option_clearing_fee'))
        trade.total_fee = clean_value(row.get('total_fee')) or 0

        # A股特有字段
        trade.exchange = exchange  # 已在前面获取
        trade.transfer_fee = clean_value(row.get('transfer_fee'))
        trade.shareholder_code = clean_value(row.get('shareholder_code'))

        # Symbol解析信息
        trade.is_option = 1 if clean_value(row.get('parsed_is_option')) else 0
        trade.underlying_symbol = clean_value(row.get('parsed_underlying_symbol'))
        trade.option_type = clean_value(row.get('parsed_option_type'))
        trade.strike_price = clean_value(row.get('parsed_strike_price'))

        # Convert expiration_date to Python date if it's a pandas Timestamp
        exp_date = clean_value(row.get('parsed_expiration_date'))
        if exp_date is not None and hasattr(exp_date, 'date'):
            trade.expiration_date = exp_date.date() if callable(exp_date.date) else exp_date
        elif exp_date is not None:
            trade.expiration_date = exp_date
        else:
            trade.expiration_date = None

        # NOTE: is_partial_fill is a computed property, don't set it

        # 其他字段
        trade.notes = clean_value(row.get('notes'))

        # Store additional fields in metadata_json
        metadata = {}
        for field in ['status', 'broker', 'order_source']:
            val = clean_value(row.get(field))
            if val:
                metadata[field] = val

        # Store additional fees that don't have dedicated columns
        for fee_field in ['fhb_levy', 'option_settlement_fee', 'sec_levy',
                          'trading_activity_fee', 'trading_system_fee', 'audit_trail_fee']:
            val = clean_value(row.get(fee_field))
            if val:
                metadata[fee_field] = val

        if metadata:
            trade.metadata_json = metadata

        return trade

    def _save_to_database(self, trades):
        """
        保存Trade对象到数据库

        Args:
            trades: Trade对象列表
        """
        # 初始化数据库
        engine = init_database(config.DATABASE_URL, echo=False)
        create_all_tables()

        # 获取session
        self.session = get_session()

        try:
            # 批量保存
            created = 0
            for trade in trades:
                self.session.add(trade)
                created += 1

                # 每100条提交一次
                if created % 100 == 0:
                    self.session.commit()
                    logger.info(f"  Saved {created}/{len(trades)} trades...")

            # 提交剩余的
            self.session.commit()

            self.stats['trades_created'] = created
            logger.info(f"Successfully saved {created} trades to database")

        except Exception as e:
            logger.error(f"Database error: {e}")
            self.session.rollback()
            raise

    def _print_summary(self):
        """打印导入摘要"""
        logger.info("\n" + "="*60)
        logger.info("IMPORT SUMMARY")
        logger.info("="*60)

        logger.info(f"CSV total rows:       {self.stats['csv_total_rows']}")
        logger.info(f"CSV filtered:         {self.stats['csv_filtered']}")
        logger.info(f"Cleaned rows:         {self.stats['cleaned_rows']}")
        logger.info(f"Trades created:       {self.stats['trades_created']}")
        logger.info(f"Trades updated:       {self.stats['trades_updated']}")
        logger.info(f"Errors:               {self.stats['errors']}")

        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            logger.info(f"Duration:             {duration.total_seconds():.2f} seconds")

        logger.info("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Import trading data from CSV file to database'
    )
    parser.add_argument(
        'csv_path',
        type=str,
        help='Path to CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without saving to database'
    )

    args = parser.parse_args()

    # 检查文件是否存在
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    # 执行导入
    importer = TradeImporter(
        csv_path=args.csv_path,
        dry_run=args.dry_run
    )
    importer.run()


if __name__ == '__main__':
    main()
