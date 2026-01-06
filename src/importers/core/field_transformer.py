"""
Field Transformer - 字段数据转换器

input: DataFrame 列, FieldTransform 规则
output: 转换后的列
pos: 转换层 - 处理各种数据类型的解析和转换

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import re
import logging
from datetime import datetime, date
from typing import Any, Optional
import pandas as pd

from ..configs.schema import FieldTransform, TransformType, BrokerConfig

logger = logging.getLogger(__name__)


class FieldTransformer:
    """
    字段转换器

    根据 FieldTransform 配置将 CSV 列数据转换为目标类型。
    支持字符串、数值、日期时间、枚举等多种类型。
    """

    # 时区映射
    TIMEZONE_HINTS = {
        '美东': 'America/New_York',
        'ET': 'America/New_York',
        '美西': 'America/Los_Angeles',
        'PT': 'America/Los_Angeles',
        '香港': 'Asia/Hong_Kong',
        'HKT': 'Asia/Hong_Kong',
        '北京': 'Asia/Shanghai',
        'CST': 'Asia/Shanghai',
        '沪深': 'Asia/Shanghai',
    }

    def transform_column(
        self,
        column: pd.Series,
        transform: FieldTransform,
        config: Optional[BrokerConfig] = None
    ) -> pd.Series:
        """
        转换整列数据

        Args:
            column: 源数据列
            transform: 转换规则
            config: 券商配置 (可选)

        Returns:
            pd.Series: 转换后的列
        """
        transform_type = transform.type

        if transform_type == TransformType.STRING:
            return self._transform_string(column, transform)
        elif transform_type == TransformType.NUMBER:
            return self._transform_number(column, transform)
        elif transform_type == TransformType.INTEGER:
            return self._transform_integer(column, transform)
        elif transform_type == TransformType.DATETIME:
            return self._transform_datetime(column, transform)
        elif transform_type == TransformType.DATE:
            return self._transform_date(column, transform)
        elif transform_type == TransformType.ENUM:
            return self._transform_enum(column, transform)
        elif transform_type == TransformType.BOOLEAN:
            return self._transform_boolean(column, transform)
        elif transform_type == TransformType.COMPUTED:
            return self._transform_computed(column, transform, config)
        else:
            logger.warning(f"Unknown transform type: {transform_type}")
            return column

    def _transform_string(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """字符串转换"""
        result = column.astype(str)

        if transform.strip:
            result = result.str.strip()

        if transform.lowercase:
            result = result.str.lower()

        # 处理空字符串
        result = result.replace(['', 'nan', 'None', 'NaN'], None)

        if transform.default is not None:
            result = result.fillna(transform.default)

        return result

    def _transform_number(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """数值转换"""
        def clean_number(val):
            if pd.isna(val) or val in ('', '--', 'N/A', 'n/a'):
                return None

            val_str = str(val)
            # 移除货币符号、逗号、空格
            val_str = re.sub(r'[,$\s¥€£]', '', val_str)
            # 处理百分号
            if '%' in val_str:
                val_str = val_str.replace('%', '')
                try:
                    return float(val_str) / 100
                except ValueError:
                    return None

            try:
                return float(val_str)
            except ValueError:
                return None

        result = column.apply(clean_number)

        if transform.default is not None:
            result = result.fillna(transform.default)

        return result

    def _transform_integer(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """整数转换"""
        def clean_integer(val):
            if pd.isna(val) or val in ('', '--', 'N/A', 'n/a'):
                return None

            val_str = str(val)
            # 移除逗号、空格
            val_str = re.sub(r'[,\s]', '', val_str)
            # 处理 "3unit(s)" 格式
            match = re.match(r'^(\d+)', val_str)
            if match:
                return int(match.group(1))

            try:
                return int(float(val_str))
            except ValueError:
                return None

        result = column.apply(clean_integer)

        if transform.default is not None:
            result = result.fillna(transform.default)

        return result

    def _transform_datetime(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """日期时间转换"""
        def parse_datetime(val):
            if pd.isna(val) or val in ('', '--', 'N/A'):
                return None

            val_str = str(val).strip()

            # 提取时区标记
            tz_name = None
            for hint, tz in self.TIMEZONE_HINTS.items():
                if hint in val_str:
                    tz_name = tz
                    val_str = val_str.replace(f'({hint})', '').strip()
                    val_str = val_str.replace(hint, '').strip()
                    break

            # 尝试多种格式
            formats = [
                transform.format,  # 配置指定的格式
                '%Y/%m/%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y-%m-%d %H:%M',
                '%Y%m%d %H:%M:%S',
                '%b %d, %Y %H:%M:%S',  # Dec 17, 2025 10:00:03
                '%d/%m/%Y %H:%M:%S',
                '%m/%d/%Y %H:%M:%S',
            ]

            for fmt in formats:
                if fmt is None:
                    continue
                try:
                    dt = datetime.strptime(val_str, fmt)
                    return dt
                except ValueError:
                    continue

            # 尝试 pandas 智能解析
            try:
                return pd.to_datetime(val_str)
            except Exception:
                return None

        result = column.apply(parse_datetime)
        return result

    def _transform_date(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """日期转换"""
        def parse_date(val):
            if pd.isna(val) or val in ('', '--', 'N/A'):
                return None

            val_str = str(val).strip()

            formats = [
                transform.format,
                '%Y/%m/%d',
                '%Y-%m-%d',
                '%Y%m%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
            ]

            for fmt in formats:
                if fmt is None:
                    continue
                try:
                    return datetime.strptime(val_str, fmt).date()
                except ValueError:
                    continue

            try:
                return pd.to_datetime(val_str).date()
            except Exception:
                return None

        result = column.apply(parse_date)
        return result

    def _transform_enum(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """枚举映射转换"""
        if not transform.mapping:
            return column

        def map_enum(val):
            if pd.isna(val):
                return transform.default

            val_str = str(val).strip()
            mapped = transform.mapping.get(val_str)

            if mapped is not None:
                return mapped
            elif transform.default is not None:
                return transform.default
            else:
                return val_str  # 保留原值

        return column.apply(map_enum)

    def _transform_boolean(self, column: pd.Series, transform: FieldTransform) -> pd.Series:
        """布尔值转换"""
        true_values = {'true', 'yes', '1', 'y', 't', '是', '有', '允许'}
        false_values = {'false', 'no', '0', 'n', 'f', '否', '无', '不允许'}

        def to_bool(val):
            if pd.isna(val) or val == '':
                return transform.default if transform.default is not None else None

            val_str = str(val).strip().lower()

            if val_str in true_values:
                return True
            elif val_str in false_values:
                return False
            else:
                return transform.default

        return column.apply(to_bool)

    def _transform_computed(
        self,
        column: pd.Series,
        transform: FieldTransform,
        config: Optional[BrokerConfig]
    ) -> pd.Series:
        """计算字段转换"""
        # 暂时不支持复杂计算表达式
        logger.warning("Computed transform not fully implemented")
        return column


# 便捷函数
def transform_column(
    column: pd.Series,
    transform: FieldTransform,
    config: Optional[BrokerConfig] = None
) -> pd.Series:
    """便捷函数：转换单列"""
    transformer = FieldTransformer()
    return transformer.transform_column(column, transform, config)
