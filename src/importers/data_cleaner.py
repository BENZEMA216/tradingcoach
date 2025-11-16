"""
数据清洗器

处理CSV解析后的数据：
- 标准化字段格式
- 拆分部分成交订单
- 映射交易方向
- 解析Symbol信息
- 过滤无效记录
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime
import re

from src.utils.symbol_parser import parse_symbol
from src.utils.timezone import parse_datetime_with_timezone

logger = logging.getLogger(__name__)


# 交易方向映射（中文 -> 英文枚举值）
DIRECTION_MAPPING = {
    '买入': 'buy',
    '卖出': 'sell',
    '卖空': 'sell_short',
    '买券还券': 'buy_to_cover',
    '补券': 'buy_to_cover',
}

# 需要过滤的订单状态
INVALID_STATUSES = ['已撤单', '下单失败', '待审核', '已拒绝']


class DataCleaner:
    """数据清洗器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化清洗器

        Args:
            df: 解析后的DataFrame（列名已映射为英文）
        """
        self.df = df.copy()
        self.cleaned_df = None
        self.stats = {
            'total_input': len(df),
            'filtered_invalid': 0,
            'partial_fills_split': 0,
            'direction_normalized': 0,
            'symbols_parsed': 0,
            'total_output': 0,
            'errors': []
        }

    def clean(self) -> pd.DataFrame:
        """
        执行完整的清洗流程

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        logger.info("Starting data cleaning process...")

        # 1. 过滤无效订单
        self._filter_invalid_orders()

        # 2. 清理数字格式
        self._clean_numeric_fields()

        # 3. 标准化交易方向
        self._normalize_directions()

        # 4. 解析时间字段
        self._parse_timestamps()

        # 5. 解析Symbol信息
        self._parse_symbols()

        # 6. 处理部分成交（拆分订单）
        self._handle_partial_fills()

        # 7. 数据验证
        self._validate_cleaned_data()

        self.stats['total_output'] = len(self.cleaned_df)
        logger.info(f"Data cleaning completed: {self.stats}")

        return self.cleaned_df

    def _filter_invalid_orders(self):
        """过滤无效订单（已撤单、失败等）"""
        logger.info("Filtering invalid orders...")

        initial_count = len(self.df)

        # 过滤无效状态
        if 'status' in self.df.columns:
            self.df = self.df[~self.df['status'].isin(INVALID_STATUSES)].copy()

        # 过滤空值较多的行（关键字段）
        required_fields = ['symbol', 'direction', 'filled_time']
        for field in required_fields:
            if field in self.df.columns:
                self.df = self.df[self.df[field].notna()].copy()

        filtered_count = initial_count - len(self.df)
        self.stats['filtered_invalid'] = filtered_count

        logger.info(f"Filtered {filtered_count} invalid orders, {len(self.df)} remaining")

    def _clean_numeric_fields(self):
        """清理数字字段（去除逗号、空格等）"""
        logger.info("Cleaning numeric fields...")

        numeric_fields = [
            'order_price', 'order_quantity', 'order_amount',
            'filled_price', 'filled_quantity', 'filled_amount',
            'commission', 'platform_fee', 'clearing_fee',
            'stamp_duty', 'transaction_fee', 'sec_fee',
            'fhb_levy', 'option_regulatory_fee', 'option_clearing_fee',
            'option_settlement_fee', 'sec_levy', 'trading_activity_fee',
            'trading_system_fee', 'audit_trail_fee', 'total_fee'
        ]

        for field in numeric_fields:
            if field not in self.df.columns:
                continue

            # 清理格式：去除逗号、空格、美元符号等
            self.df[field] = self.df[field].apply(self._clean_number)

        logger.info("Numeric fields cleaned")

    def _clean_number(self, value) -> Optional[float]:
        """
        清理单个数字值

        Args:
            value: 原始值

        Returns:
            float或None
        """
        if pd.isna(value):
            return None

        # 如果已经是数字，直接返回
        if isinstance(value, (int, float)):
            return float(value)

        # 字符串处理
        if isinstance(value, str):
            # 去除空格、逗号、美元符号
            cleaned = value.strip().replace(',', '').replace('$', '').replace(' ', '')

            # 处理空字符串
            if cleaned == '' or cleaned == '-':
                return None

            try:
                return float(cleaned)
            except ValueError:
                logger.warning(f"Cannot convert to number: {value}")
                return None

        return None

    def _normalize_directions(self):
        """标准化交易方向（中文 -> 英文枚举）"""
        logger.info("Normalizing trade directions...")

        if 'direction' not in self.df.columns:
            logger.warning("No 'direction' column found")
            return

        # 映射方向
        def map_direction(cn_direction):
            if pd.isna(cn_direction):
                return None
            return DIRECTION_MAPPING.get(cn_direction, cn_direction)

        self.df['direction'] = self.df['direction'].apply(map_direction)

        # 统计标准化数量
        normalized_count = self.df['direction'].isin(DIRECTION_MAPPING.values()).sum()
        self.stats['direction_normalized'] = normalized_count

        logger.info(f"Normalized {normalized_count} directions")

    def _parse_timestamps(self):
        """解析时间字段并转换为UTC"""
        logger.info("Parsing timestamps...")

        time_fields = {
            'order_time': 'order_time_utc',
            'filled_time': 'filled_time_utc',
        }

        for cn_field, en_field in time_fields.items():
            if cn_field not in self.df.columns:
                continue

            # 解析时间（带时区）
            self.df[en_field] = self.df.apply(
                lambda row: parse_datetime_with_timezone(
                    row[cn_field],
                    timezone_hint=row.get('market', None)
                ),
                axis=1
            )

        logger.info("Timestamps parsed and converted to UTC")

    def _parse_symbols(self):
        """解析Symbol信息（识别期权、窝轮等）"""
        logger.info("Parsing symbols...")

        if 'symbol' not in self.df.columns:
            logger.warning("No 'symbol' column found")
            return

        # 解析每个symbol
        symbol_info_list = []
        for idx, row in self.df.iterrows():
            symbol = row['symbol']
            symbol_name = row.get('symbol_name', None)
            market = row.get('market', None)

            # 解析symbol
            info = parse_symbol(symbol, symbol_name, market)
            symbol_info_list.append(info)

        # 创建DataFrame
        symbol_df = pd.DataFrame(symbol_info_list)

        # 合并到主DataFrame
        self.df = pd.concat([self.df, symbol_df.add_prefix('parsed_')], axis=1)

        # 统计解析数量
        self.stats['symbols_parsed'] = len(symbol_info_list)

        logger.info(f"Parsed {len(symbol_info_list)} symbols")

    def _handle_partial_fills(self):
        """
        处理部分成交订单

        逻辑：
        - 如果 order_quantity > filled_quantity，说明是部分成交
        - 拆分为两条记录：
          1. 已成交部分（filled_quantity）
          2. 未成交部分（order_quantity - filled_quantity）-> 标记为cancelled

        注意：根据需求，我们只保留已成交部分，未成交部分不入库
        """
        logger.info("Handling partial fills...")

        if 'order_quantity' not in self.df.columns or 'filled_quantity' not in self.df.columns:
            logger.warning("Missing quantity columns for partial fill detection")
            self.cleaned_df = self.df.copy()
            return

        # 检测部分成交
        partial_fills_mask = (
            (self.df['order_quantity'].notna()) &
            (self.df['filled_quantity'].notna()) &
            (self.df['order_quantity'] > self.df['filled_quantity']) &
            (self.df['filled_quantity'] > 0)
        )

        partial_fills_count = partial_fills_mask.sum()

        if partial_fills_count == 0:
            logger.info("No partial fills detected")
            self.cleaned_df = self.df.copy()
            return

        logger.info(f"Found {partial_fills_count} partial fills")

        # 对于部分成交，我们只保留已成交部分
        # 但标记 is_partial_fill = True
        self.df['is_partial_fill'] = partial_fills_mask.astype(int)

        # 对于部分成交的订单，计算未成交数量作为参考
        self.df['unfilled_quantity'] = 0.0
        self.df.loc[partial_fills_mask, 'unfilled_quantity'] = (
            self.df.loc[partial_fills_mask, 'order_quantity'] -
            self.df.loc[partial_fills_mask, 'filled_quantity']
        )

        self.stats['partial_fills_split'] = partial_fills_count
        self.cleaned_df = self.df.copy()

        logger.info(f"Marked {partial_fills_count} partial fills")

    def _validate_cleaned_data(self):
        """验证清洗后的数据"""
        logger.info("Validating cleaned data...")

        if self.cleaned_df is None:
            logger.error("No cleaned data to validate")
            return

        errors = []

        # 检查必需字段
        required_fields = ['symbol', 'direction', 'filled_quantity', 'filled_price']
        for field in required_fields:
            if field not in self.cleaned_df.columns:
                errors.append(f"Missing required field: {field}")
            else:
                null_count = self.cleaned_df[field].isnull().sum()
                if null_count > 0:
                    errors.append(f"Field '{field}' has {null_count} null values")

        # 检查数值字段的有效性
        if 'filled_quantity' in self.cleaned_df.columns:
            invalid_qty = (self.cleaned_df['filled_quantity'] <= 0).sum()
            if invalid_qty > 0:
                errors.append(f"Found {invalid_qty} records with invalid filled_quantity <= 0")

        if 'filled_price' in self.cleaned_df.columns:
            invalid_price = (self.cleaned_df['filled_price'] <= 0).sum()
            if invalid_price > 0:
                errors.append(f"Found {invalid_price} records with invalid filled_price <= 0")

        # 检查方向字段
        if 'direction' in self.cleaned_df.columns:
            valid_directions = list(DIRECTION_MAPPING.values())
            invalid_directions = ~self.cleaned_df['direction'].isin(valid_directions)
            invalid_count = invalid_directions.sum()
            if invalid_count > 0:
                errors.append(f"Found {invalid_count} records with invalid direction")

        self.stats['errors'] = errors

        if errors:
            logger.warning(f"Validation found {len(errors)} issues:")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("Validation passed: no issues found")

    def get_statistics(self) -> Dict:
        """
        获取清洗统计信息

        Returns:
            dict: 统计信息
        """
        return self.stats

    def get_cleaned_data(self) -> pd.DataFrame:
        """
        获取清洗后的数据

        Returns:
            pd.DataFrame: 清洗后的数据
        """
        if self.cleaned_df is None:
            raise ValueError("Data not cleaned yet. Call clean() first.")
        return self.cleaned_df


def clean_csv_data(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict]:
    """
    便捷函数：清洗CSV数据

    Args:
        df: 解析后的DataFrame

    Returns:
        tuple: (清洗后的DataFrame, 统计信息)
    """
    cleaner = DataCleaner(df)
    cleaned_df = cleaner.clean()
    stats = cleaner.get_statistics()

    return cleaned_df, stats
