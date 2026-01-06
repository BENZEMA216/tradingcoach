"""
增量导入器

input: CSV文件路径
output: 导入结果(新增数/跳过数/错误), 导入历史记录
pos: 数据导入层控制器 - 自动检测券商格式、指纹去重、增量导入

支持两种模式:
1. 适配器模式（推荐）: 使用 AdapterRegistry 自动检测券商格式
2. 兼容模式: 回退到旧的 CSVParser/EnglishCSVParser

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import sys
from pathlib import Path
import hashlib
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.models.base import init_database, get_session, create_all_tables
from src.models.trade import Trade, TradeDirection, TradeStatus, MarketType

# 新适配器系统
try:
    from src.importers.core.adapter_registry import AdapterRegistry
    ADAPTER_SYSTEM_AVAILABLE = True
except ImportError:
    ADAPTER_SYSTEM_AVAILABLE = False

# 旧解析器（兼容模式）
from src.importers.csv_parser import CSVParser
from src.importers.english_csv_parser import (
    EnglishCSVParser,
    detect_csv_language
)
from src.importers.data_cleaner import DataCleaner

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


class ImportResult:
    """导入结果"""

    def __init__(self):
        self.total_rows = 0
        self.completed_trades = 0
        self.new_trades = 0
        self.duplicates_skipped = 0
        self.errors = 0
        self.date_range_start = None
        self.date_range_end = None
        self.processing_time_ms = 0
        self.error_messages = []
        # 新增字段
        self.broker_id = None
        self.broker_name = None
        self.detection_confidence = 0.0
        self.import_batch_id = None

    def to_dict(self):
        return {
            'total_rows': self.total_rows,
            'completed_trades': self.completed_trades,
            'new_trades': self.new_trades,
            'duplicates_skipped': self.duplicates_skipped,
            'errors': self.errors,
            'date_range_start': str(self.date_range_start) if self.date_range_start else None,
            'date_range_end': str(self.date_range_end) if self.date_range_end else None,
            'processing_time_ms': self.processing_time_ms,
            'broker_id': self.broker_id,
            'broker_name': self.broker_name,
            'detection_confidence': self.detection_confidence,
            'import_batch_id': self.import_batch_id,
        }


class IncrementalImporter:
    """增量导入器"""

    def __init__(
        self,
        csv_path: str,
        dry_run: bool = False,
        use_adapter: bool = True,
        broker_id: Optional[str] = None
    ):
        """
        初始化导入器

        Args:
            csv_path: CSV文件路径
            dry_run: 是否为测试运行（不写入数据库）
            use_adapter: 是否使用新适配器系统（默认True）
            broker_id: 强制指定券商ID（可选，默认自动检测）
        """
        self.csv_path = Path(csv_path)
        self.dry_run = dry_run
        self.use_adapter = use_adapter and ADAPTER_SYSTEM_AVAILABLE
        self.forced_broker_id = broker_id
        self.session = None
        self.result = ImportResult()

        # 生成导入批次ID
        self.import_batch_id = str(uuid.uuid4())[:8]
        self.result.import_batch_id = self.import_batch_id

        # 文件信息
        self.file_hash = None
        self.file_language = None  # 兼容模式使用
        self.adapter = None  # 适配器模式使用

    def run(self) -> ImportResult:
        """执行增量导入"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting incremental import...")
        logger.info(f"File: {self.csv_path}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)

        try:
            # 1. 计算文件哈希
            self.file_hash = self._calculate_file_hash()
            logger.info(f"File hash: {self.file_hash[:16]}...")

            # 2. 检测语言并解析
            df = self._parse_csv()

            # 3. 清洗数据（仅兼容模式中文格式需要）
            if self.file_language == 'chinese':
                df = self._clean_chinese_data(df)
            # 适配器模式已自动清洗和添加指纹，无需额外处理

            # 4. 增量导入
            self._incremental_import(df)

            # 5. 记录导入历史
            if not self.dry_run:
                self._record_import_history()

            # 计算处理时间
            self.result.processing_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )

            self._print_summary()
            return self.result

        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            self.result.error_messages.append(str(e))
            raise

        finally:
            if self.session:
                self.session.close()

    def _calculate_file_hash(self) -> str:
        """计算文件SHA256哈希"""
        hasher = hashlib.sha256()
        with open(self.csv_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _parse_csv(self) -> pd.DataFrame:
        """解析CSV文件"""
        logger.info("\n[Step 1] Detecting format and parsing CSV...")

        # 优先尝试适配器模式
        if self.use_adapter:
            try:
                return self._parse_csv_with_adapter()
            except Exception as e:
                logger.warning(f"Adapter mode failed, falling back to legacy: {e}")
                # 回退到兼容模式

        # 兼容模式：使用旧的解析器
        return self._parse_csv_legacy()

    def _parse_csv_with_adapter(self) -> pd.DataFrame:
        """使用适配器系统解析CSV"""
        logger.info("Using adapter system...")

        registry = AdapterRegistry()

        # 如果指定了broker_id，直接获取对应适配器
        if self.forced_broker_id:
            self.adapter = registry.get_adapter(self.forced_broker_id)
            if self.adapter is None:
                raise ValueError(f"Unknown broker_id: {self.forced_broker_id}")
            confidence = 1.0
            logger.info(f"Using forced adapter: {self.forced_broker_id}")
        else:
            # 自动检测券商格式
            self.adapter, confidence = registry.detect_and_get_adapter(str(self.csv_path))
            if self.adapter is None:
                raise ValueError("Could not detect CSV format")

        # 更新结果信息
        self.result.broker_id = self.adapter.config.broker_id
        self.result.broker_name = self.adapter.config.broker_name_cn
        self.result.detection_confidence = confidence
        self.file_language = 'adapter'  # 标记使用适配器模式

        logger.info(f"Detected broker: {self.result.broker_name} (confidence: {confidence:.2%})")

        # 设置导入批次ID
        self.adapter.set_import_batch_id(self.import_batch_id)

        # 解析CSV
        df = self.adapter.parse(str(self.csv_path))
        self.result.total_rows = len(df)

        # 筛选已成交交易
        completed_df = self.adapter.filter_completed_trades()
        self.result.completed_trades = len(completed_df)

        logger.info(f"Total rows: {self.result.total_rows}")
        logger.info(f"Completed trades: {self.result.completed_trades}")

        return completed_df

    def _parse_csv_legacy(self) -> pd.DataFrame:
        """兼容模式：使用旧的解析器"""
        logger.info("Using legacy parser...")

        # 检测语言
        self.file_language = detect_csv_language(str(self.csv_path))
        logger.info(f"Detected language: {self.file_language}")

        if self.file_language == 'english':
            parser = EnglishCSVParser(str(self.csv_path))
            df = parser.parse()
            self.result.total_rows = len(df)

            # 筛选已成交
            completed_df = parser.filter_completed_trades()
            self.result.completed_trades = len(completed_df)

            logger.info(f"Total rows: {self.result.total_rows}")
            logger.info(f"Completed trades: {self.result.completed_trades}")

            return completed_df

        elif self.file_language == 'chinese':
            parser = CSVParser(str(self.csv_path))
            df = parser.parse()
            self.result.total_rows = len(df)

            # 筛选已成交
            completed_df = parser.filter_completed_trades()
            self.result.completed_trades = len(completed_df)

            logger.info(f"Total rows: {self.result.total_rows}")
            logger.info(f"Completed trades: {self.result.completed_trades}")

            return completed_df

        else:
            raise ValueError(f"Unknown CSV language: {self.file_language}")

    def _clean_chinese_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗中文格式数据"""
        logger.info("\n[Step 2] Cleaning data...")

        cleaner = DataCleaner(df)
        cleaned_df = cleaner.clean()

        # 添加指纹
        cleaned_df['trade_fingerprint'] = cleaned_df.apply(
            self._calculate_fingerprint_chinese, axis=1
        )

        logger.info(f"Cleaned rows: {len(cleaned_df)}")
        return cleaned_df

    def _calculate_fingerprint_chinese(self, row: pd.Series) -> Optional[str]:
        """计算中文格式的交易指纹"""
        try:
            filled_time = row.get('filled_time_utc')
            if pd.isna(filled_time):
                return None

            components = [
                str(row.get('symbol', '')),
                str(filled_time),
                str(row.get('direction', '')),
                str(row.get('filled_quantity', '')),
                f"{row.get('filled_price', 0):.4f}",
                str(row.get('market', '')),
            ]

            fingerprint_str = '|'.join(components)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

        except Exception:
            return None

    def _incremental_import(self, df: pd.DataFrame):
        """增量导入交易"""
        logger.info("\n[Step 3] Incremental import...")

        # 初始化数据库
        if not self.dry_run:
            engine = init_database(config.DATABASE_URL, echo=False)
            create_all_tables()
            self.session = get_session()

        # 获取现有指纹
        existing_fingerprints = self._get_existing_fingerprints()
        logger.info(f"Existing fingerprints in DB: {len(existing_fingerprints)}")

        # 筛选新交易
        if 'trade_fingerprint' not in df.columns:
            logger.warning("No fingerprints in DataFrame, importing all")
            new_df = df
        else:
            new_df = df[~df['trade_fingerprint'].isin(existing_fingerprints)]
            self.result.duplicates_skipped = len(df) - len(new_df)

        logger.info(f"New trades to import: {len(new_df)}")
        logger.info(f"Duplicates skipped: {self.result.duplicates_skipped}")

        if len(new_df) == 0:
            logger.info("No new trades to import")
            return

        # 获取日期范围
        if self.file_language == 'adapter':
            time_col = 'filled_time'  # 适配器模式使用标准列名
        elif self.file_language == 'english':
            time_col = 'filled_time_parsed'
        else:
            time_col = 'filled_time_utc'

        if time_col in new_df.columns:
            valid_times = new_df[time_col].dropna()
            if len(valid_times) > 0:
                self.result.date_range_start = valid_times.min()
                self.result.date_range_end = valid_times.max()

        # 导入新交易
        if not self.dry_run:
            self._save_trades(new_df)
        else:
            self.result.new_trades = len(new_df)
            logger.info("DRY RUN: Skipping database save")

    def _get_existing_fingerprints(self) -> set:
        """获取数据库中现有的指纹"""
        if self.dry_run or self.session is None:
            return set()

        try:
            from sqlalchemy import text
            result = self.session.execute(
                text("SELECT trade_fingerprint FROM trades WHERE trade_fingerprint IS NOT NULL")
            )
            return {row[0] for row in result.fetchall()}
        except Exception as e:
            logger.warning(f"Could not get existing fingerprints: {e}")
            return set()

    def _save_trades(self, df: pd.DataFrame):
        """保存交易到数据库"""
        saved = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                trade = self._row_to_trade(row)
                if trade is not None:
                    self.session.add(trade)
                    saved += 1

                    # 每100条提交一次
                    if saved % 100 == 0:
                        self.session.commit()
                        logger.info(f"  Saved {saved}/{len(df)} trades...")

            except Exception as e:
                logger.error(f"Error importing row {idx}: {e}")
                errors += 1
                self.result.error_messages.append(f"Row {idx}: {e}")

        # 提交剩余
        self.session.commit()

        self.result.new_trades = saved
        self.result.errors = errors

        logger.info(f"Saved {saved} new trades, {errors} errors")

    def _row_to_trade(self, row) -> Optional[Trade]:
        """将行转换为Trade对象"""
        # 根据模式确定列名
        if self.file_language == 'adapter':
            return self._row_to_trade_adapter(row)
        elif self.file_language == 'english':
            return self._row_to_trade_english(row)
        else:
            return self._row_to_trade_chinese(row)

    def _row_to_trade_adapter(self, row) -> Optional[Trade]:
        """适配器模式：将行转换为Trade对象"""
        # 验证必填字段
        symbol = clean_value(row.get('symbol'))
        direction_str = clean_value(row.get('direction'))
        filled_qty = clean_value(row.get('filled_quantity'))
        filled_time = clean_value(row.get('filled_time'))

        if not symbol or not direction_str or not filled_qty or not filled_time:
            return None

        # 适配器已经将方向转换为标准值 (buy/sell/sell_short/buy_to_cover)
        direction_mapping = {
            'buy': TradeDirection.BUY,
            'sell': TradeDirection.SELL,
            'sell_short': TradeDirection.SELL_SHORT,
            'buy_to_cover': TradeDirection.BUY_TO_COVER,
        }
        direction_enum = direction_mapping.get(direction_str.lower() if direction_str else '')
        if not direction_enum:
            logger.warning(f"Unknown direction: {direction_str}")
            return None

        # 适配器已经将市场转换为标准值 (us/hk/cn)
        market_str = clean_value(row.get('market')) or 'us'
        market_mapping = {
            'us': MarketType.US_STOCK,
            'hk': MarketType.HK_STOCK,
            'cn': MarketType.CN_STOCK,
        }
        market_enum = market_mapping.get(market_str.lower(), MarketType.US_STOCK)

        # 创建Trade对象
        trade = Trade(
            symbol=symbol,
            symbol_name=clean_value(row.get('symbol_name')),
            direction=direction_enum,
            market=market_enum,
            currency=clean_value(row.get('currency')) or 'USD',
        )

        # 订单信息
        trade.order_price = clean_value(row.get('order_price'))
        trade.order_quantity = clean_value(row.get('order_quantity'))
        trade.order_amount = clean_value(row.get('order_amount'))
        trade.order_type = clean_value(row.get('order_type'))
        trade.order_time = clean_value(row.get('order_time'))

        # 成交信息
        trade.filled_price = clean_value(row.get('filled_price'))
        trade.filled_quantity = filled_qty
        trade.filled_amount = clean_value(row.get('filled_amount'))
        trade.filled_time = filled_time

        # 交易日期
        if trade.filled_time:
            if hasattr(trade.filled_time, 'date'):
                trade.trade_date = trade.filled_time.date()
            else:
                trade.trade_date = trade.filled_time

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
        trade.exchange = clean_value(row.get('exchange'))
        trade.seat_code = clean_value(row.get('seat_code'))
        trade.shareholder_code = clean_value(row.get('shareholder_code'))
        trade.transfer_fee = clean_value(row.get('transfer_fee'))
        trade.handling_fee = clean_value(row.get('handling_fee'))
        trade.regulation_fee = clean_value(row.get('regulation_fee'))
        trade.other_fees = clean_value(row.get('other_fees'))

        # 期权信息
        trade.is_option = 1 if row.get('is_option', False) else 0
        trade.underlying_symbol = clean_value(row.get('underlying_symbol'))
        trade.option_type = clean_value(row.get('option_type'))
        trade.strike_price = clean_value(row.get('strike_price'))
        exp_date = clean_value(row.get('expiration_date'))

        # 处理到期日
        if exp_date is not None and hasattr(exp_date, 'date'):
            trade.expiration_date = exp_date.date() if callable(getattr(exp_date, 'date', None)) else exp_date
        else:
            trade.expiration_date = exp_date

        # 交易指纹和导入追踪
        trade.trade_fingerprint = clean_value(row.get('trade_fingerprint'))
        trade.broker_id = clean_value(row.get('broker_id'))
        trade.import_batch_id = clean_value(row.get('import_batch_id'))
        trade.source_row_number = clean_value(row.get('source_row_number'))

        # 其他
        trade.notes = clean_value(row.get('notes'))

        # 适配器已经将状态转换为标准值 (filled/cancelled/partially_filled/pending)
        raw_status = clean_value(row.get('status')) or 'filled'
        status_mapping = {
            'filled': TradeStatus.FILLED,
            'cancelled': TradeStatus.CANCELLED,
            'partially_filled': TradeStatus.PARTIALLY_FILLED,
            'pending': TradeStatus.PENDING,
        }
        trade.status = status_mapping.get(raw_status.lower(), TradeStatus.FILLED)

        return trade

    def _row_to_trade_english(self, row) -> Optional[Trade]:
        """英文格式：将行转换为Trade对象"""
        time_col = 'filled_time_parsed'

        # 验证必填字段
        symbol = clean_value(row.get('symbol'))
        direction_str = clean_value(row.get('direction'))
        filled_qty = clean_value(row.get('filled_quantity'))
        filled_time = clean_value(row.get(time_col))

        if not symbol or not direction_str or not filled_qty or not filled_time:
            return None

        # 转换方向为枚举
        direction_mapping = {
            'buy': TradeDirection.BUY,
            'sell': TradeDirection.SELL,
            'sell_short': TradeDirection.SELL_SHORT,
            'buy_to_cover': TradeDirection.BUY_TO_COVER,
        }
        direction_enum = direction_mapping.get(direction_str.lower() if direction_str else '')
        if not direction_enum:
            logger.warning(f"Unknown direction: {direction_str}")
            return None

        # 转换市场为枚举
        market_str = clean_value(row.get('market')) or 'US'
        market_mapping = {
            'US': MarketType.US_STOCK,
            'HK': MarketType.HK_STOCK,
            'CN': MarketType.CN_STOCK,
        }
        market_enum = market_mapping.get(market_str, MarketType.US_STOCK)

        # 创建Trade对象
        trade = Trade(
            symbol=symbol,
            symbol_name=clean_value(row.get('symbol_name')),
            direction=direction_enum,
            market=market_enum,
            currency=clean_value(row.get('currency')) or 'USD',
        )

        # 订单信息
        trade.order_price = clean_value(row.get('order_price'))
        trade.order_quantity = clean_value(row.get('order_quantity'))
        trade.order_amount = clean_value(row.get('order_amount'))
        trade.order_type = clean_value(row.get('order_type'))
        trade.order_time = clean_value(row.get('order_time_parsed'))

        # 成交信息
        trade.filled_price = clean_value(row.get('filled_price'))
        trade.filled_quantity = filled_qty
        trade.filled_amount = clean_value(row.get('filled_amount'))
        trade.filled_time = filled_time

        # 交易日期
        if trade.filled_time:
            if hasattr(trade.filled_time, 'date'):
                trade.trade_date = trade.filled_time.date()
            else:
                trade.trade_date = trade.filled_time

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

        # 期权信息
        trade.is_option = 1 if row.get('is_option', False) else 0
        trade.underlying_symbol = clean_value(row.get('underlying_symbol'))
        trade.option_type = clean_value(row.get('option_type'))
        trade.strike_price = clean_value(row.get('strike_price'))
        exp_date = clean_value(row.get('expiry_date'))

        # 处理到期日
        if exp_date is not None and hasattr(exp_date, 'date'):
            trade.expiration_date = exp_date.date() if callable(getattr(exp_date, 'date', None)) else exp_date
        else:
            trade.expiration_date = exp_date

        # 交易指纹
        trade.trade_fingerprint = clean_value(row.get('trade_fingerprint'))

        # 其他
        trade.notes = clean_value(row.get('notes'))

        # 转换状态为枚举
        raw_status = clean_value(row.get('status')) or 'filled'
        status_mapping = {
            'Filled': TradeStatus.FILLED,
            'Cancelled': TradeStatus.CANCELLED,
            'filled': TradeStatus.FILLED,
            'cancelled': TradeStatus.CANCELLED,
            'partially_filled': TradeStatus.PARTIALLY_FILLED,
            'pending': TradeStatus.PENDING,
        }
        trade.status = status_mapping.get(raw_status, TradeStatus.FILLED)

        return trade

    def _row_to_trade_chinese(self, row) -> Optional[Trade]:
        """中文格式：将行转换为Trade对象"""
        time_col = 'filled_time_utc'

        # 验证必填字段
        symbol = clean_value(row.get('symbol'))
        direction_str = clean_value(row.get('direction'))
        filled_qty = clean_value(row.get('filled_quantity'))
        filled_time = clean_value(row.get(time_col))

        if not symbol or not direction_str or not filled_qty or not filled_time:
            return None

        # 转换方向为枚举
        direction_mapping = {
            'buy': TradeDirection.BUY,
            'sell': TradeDirection.SELL,
            'sell_short': TradeDirection.SELL_SHORT,
            'buy_to_cover': TradeDirection.BUY_TO_COVER,
            '买入': TradeDirection.BUY,
            '卖出': TradeDirection.SELL,
        }
        direction_enum = direction_mapping.get(direction_str.lower() if direction_str else '')
        if not direction_enum:
            logger.warning(f"Unknown direction: {direction_str}")
            return None

        # 转换市场为枚举
        market_str = clean_value(row.get('market')) or 'US'
        market_mapping = {
            'US': MarketType.US_STOCK,
            '美股': MarketType.US_STOCK,
            'HK': MarketType.HK_STOCK,
            '港股': MarketType.HK_STOCK,
            'CN': MarketType.CN_STOCK,
            '沪深': MarketType.CN_STOCK,
        }
        market_enum = market_mapping.get(market_str, MarketType.US_STOCK)

        # 创建Trade对象
        trade = Trade(
            symbol=symbol,
            symbol_name=clean_value(row.get('symbol_name')),
            direction=direction_enum,
            market=market_enum,
            currency=clean_value(row.get('currency')) or 'USD',
        )

        # 订单信息
        trade.order_price = clean_value(row.get('order_price'))
        trade.order_quantity = clean_value(row.get('order_quantity'))
        trade.order_amount = clean_value(row.get('order_amount'))
        trade.order_type = clean_value(row.get('order_type'))
        trade.order_time = clean_value(row.get('order_time_utc'))

        # 成交信息
        trade.filled_price = clean_value(row.get('filled_price'))
        trade.filled_quantity = filled_qty
        trade.filled_amount = clean_value(row.get('filled_amount'))
        trade.filled_time = filled_time

        # 交易日期
        if trade.filled_time:
            if hasattr(trade.filled_time, 'date'):
                trade.trade_date = trade.filled_time.date()
            else:
                trade.trade_date = trade.filled_time

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

        # 期权信息
        trade.is_option = 1 if clean_value(row.get('parsed_is_option')) else 0
        trade.underlying_symbol = clean_value(row.get('parsed_underlying_symbol'))
        trade.option_type = clean_value(row.get('parsed_option_type'))
        trade.strike_price = clean_value(row.get('parsed_strike_price'))
        exp_date = clean_value(row.get('parsed_expiration_date'))

        # 处理到期日
        if exp_date is not None and hasattr(exp_date, 'date'):
            trade.expiration_date = exp_date.date() if callable(getattr(exp_date, 'date', None)) else exp_date
        else:
            trade.expiration_date = exp_date

        # 交易指纹
        trade.trade_fingerprint = clean_value(row.get('trade_fingerprint'))

        # 其他
        trade.notes = clean_value(row.get('notes'))

        # 转换状态为枚举
        raw_status = clean_value(row.get('status')) or 'filled'
        status_mapping = {
            '全部成交': TradeStatus.FILLED,
            '已撤单': TradeStatus.CANCELLED,
            '部分成交': TradeStatus.PARTIALLY_FILLED,
            '待成交': TradeStatus.PENDING,
            'filled': TradeStatus.FILLED,
            'cancelled': TradeStatus.CANCELLED,
            'partially_filled': TradeStatus.PARTIALLY_FILLED,
            'pending': TradeStatus.PENDING,
        }
        trade.status = status_mapping.get(raw_status, TradeStatus.FILLED)

        return trade

    def _record_import_history(self):
        """记录导入历史"""
        if self.session is None:
            return

        try:
            from sqlalchemy import text

            # Convert pandas Timestamp to Python datetime if needed
            date_start = self.result.date_range_start
            date_end = self.result.date_range_end

            if hasattr(date_start, 'to_pydatetime'):
                date_start = date_start.to_pydatetime()
            if hasattr(date_end, 'to_pydatetime'):
                date_end = date_end.to_pydatetime()

            self.session.execute(text("""
                INSERT INTO import_history (
                    import_time, file_name, file_hash, file_type,
                    total_rows, new_trades, duplicates_skipped, errors,
                    date_range_start, date_range_end, status, processing_time_ms
                ) VALUES (
                    :import_time, :file_name, :file_hash, :file_type,
                    :total_rows, :new_trades, :duplicates_skipped, :errors,
                    :date_range_start, :date_range_end, :status, :processing_time_ms
                )
            """), {
                'import_time': datetime.now(),
                'file_name': self.csv_path.name,
                'file_hash': self.file_hash,
                'file_type': self.file_language,
                'total_rows': self.result.total_rows,
                'new_trades': self.result.new_trades,
                'duplicates_skipped': self.result.duplicates_skipped,
                'errors': self.result.errors,
                'date_range_start': date_start,
                'date_range_end': date_end,
                'status': 'success' if self.result.errors == 0 else 'partial',
                'processing_time_ms': self.result.processing_time_ms,
            })
            self.session.commit()
            logger.info("Import history recorded")

        except Exception as e:
            logger.warning(f"Failed to record import history: {e}")

    def _print_summary(self):
        """打印导入摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("IMPORT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"File:                 {self.csv_path.name}")
        if self.file_language == 'adapter':
            logger.info(f"Mode:                 Adapter")
            logger.info(f"Broker:               {self.result.broker_name} ({self.result.broker_id})")
            logger.info(f"Detection confidence: {self.result.detection_confidence:.1%}")
        else:
            logger.info(f"Mode:                 Legacy ({self.file_language})")
        logger.info(f"Import batch:         {self.result.import_batch_id}")
        logger.info(f"Total rows:           {self.result.total_rows}")
        logger.info(f"Completed trades:     {self.result.completed_trades}")
        logger.info(f"New trades:           {self.result.new_trades}")
        logger.info(f"Duplicates skipped:   {self.result.duplicates_skipped}")
        logger.info(f"Errors:               {self.result.errors}")
        if self.result.date_range_start:
            logger.info(f"Date range:           {self.result.date_range_start} to {self.result.date_range_end}")
        logger.info(f"Processing time:      {self.result.processing_time_ms}ms")
        logger.info("=" * 60)


def backfill_fingerprints():
    """为现有交易补充指纹"""
    logger.info("Backfilling fingerprints for existing trades...")

    engine = init_database(config.DATABASE_URL, echo=False)
    session = get_session()

    try:
        # 获取没有指纹的交易
        from sqlalchemy import text
        result = session.execute(text("""
            SELECT id, symbol, filled_time, direction, filled_quantity,
                   filled_price, market
            FROM trades
            WHERE trade_fingerprint IS NULL
        """))

        trades = result.fetchall()
        logger.info(f"Found {len(trades)} trades without fingerprints")

        updated = 0
        for trade in trades:
            trade_id, symbol, filled_time, direction, qty, price, market = trade

            # 计算指纹
            components = [
                str(symbol or ''),
                str(filled_time or ''),
                str(direction or ''),
                str(qty or ''),
                f"{price or 0:.4f}",
                str(market or ''),
            ]
            fingerprint_str = '|'.join(components)
            fingerprint = hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

            # 更新
            session.execute(text("""
                UPDATE trades SET trade_fingerprint = :fp WHERE id = :id
            """), {'fp': fingerprint, 'id': trade_id})

            updated += 1
            if updated % 100 == 0:
                session.commit()
                logger.info(f"  Updated {updated}/{len(trades)}...")

        session.commit()
        logger.info(f"Backfilled {updated} fingerprints")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        session.rollback()
        raise

    finally:
        session.close()


def main():
    """命令行入口"""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_DIR / 'incremental_import.log'),
            logging.StreamHandler()
        ]
    )

    parser = argparse.ArgumentParser(
        description='Incremental trade importer with deduplication'
    )
    parser.add_argument(
        'csv_path',
        type=str,
        nargs='?',
        help='Path to CSV file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test run without saving to database'
    )
    parser.add_argument(
        '--backfill',
        action='store_true',
        help='Backfill fingerprints for existing trades'
    )
    parser.add_argument(
        '--broker-id',
        type=str,
        default=None,
        help='Force specific broker ID (e.g., futu_cn, futu_en, citic)'
    )
    parser.add_argument(
        '--no-adapter',
        action='store_true',
        help='Disable adapter system, use legacy parser'
    )
    parser.add_argument(
        '--list-brokers',
        action='store_true',
        help='List available broker adapters'
    )

    args = parser.parse_args()

    if args.list_brokers:
        _list_brokers()
        return

    if args.backfill:
        backfill_fingerprints()
        return

    if not args.csv_path:
        parser.print_help()
        return

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        logger.error(f"File not found: {csv_path}")
        sys.exit(1)

    importer = IncrementalImporter(
        csv_path=str(csv_path),
        dry_run=args.dry_run,
        use_adapter=not args.no_adapter,
        broker_id=args.broker_id
    )
    result = importer.run()

    # 返回码
    sys.exit(0 if result.errors == 0 else 1)


def _list_brokers():
    """列出可用的券商适配器"""
    if not ADAPTER_SYSTEM_AVAILABLE:
        print("Adapter system not available")
        return

    registry = AdapterRegistry()
    brokers = registry.list_brokers()

    print("\nAvailable broker adapters:")
    print("-" * 50)
    for broker in brokers:
        print(f"  {broker['broker_id']:15} - {broker['broker_name_cn']} ({broker['broker_name']})")
    print("-" * 50)
    print(f"Total: {len(brokers)} adapters\n")


if __name__ == '__main__':
    main()
