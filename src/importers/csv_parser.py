"""
CSV解析器

解析券商导出的交易记录CSV文件
"""

import pandas as pd
from typing import List, Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 中文字段名到英文字段名的映射
FIELD_MAPPING = {
    '方向': 'direction',
    '代码': 'symbol',
    '名称': 'symbol_name',
    '订单价格': 'order_price',
    '订单数量': 'order_quantity',
    '订单金额': 'order_amount',
    '交易状态': 'status',
    '已成交@均价': 'filled_info',
    '下单时间': 'order_time',
    '订单类型': 'order_type',
    '期限': 'duration',
    '盘前竞价': 'pre_market',
    '时段': 'session',
    '触发价': 'trigger_price',
    '允许开仓': 'allow_open',
    '市场': 'market',
    '币种': 'currency',
    '订单来源': 'order_source',
    '成交数量': 'filled_quantity',
    '成交价格': 'filled_price',
    '成交金额': 'filled_amount',
    '成交时间': 'filled_time',
    '对手经纪': 'broker',
    '备注': 'notes',
    '佣金': 'commission',
    '平台使用费': 'platform_fee',
    '交收费': 'clearing_fee',
    '印花税': 'stamp_duty',
    '交易费': 'transaction_fee',
    '证监会征费': 'sec_fee',
    '财汇局征费': 'fhb_levy',
    '期权监管费': 'option_regulatory_fee',
    '期权清算费': 'option_clearing_fee',
    '期权交收费': 'option_settlement_fee',
    '证监会规费': 'sec_levy',
    '交易活动费': 'trading_activity_fee',
    '交易系统使用费': 'trading_system_fee',
    '综合审计跟踪监管费': 'audit_trail_fee',
    '合计费用': 'total_fee',
}


class CSVParser:
    """CSV文件解析器"""

    def __init__(self, csv_path: str):
        """
        初始化解析器

        Args:
            csv_path: CSV文件路径
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        self.df = None
        self.raw_df = None  # 保留原始数据

    def parse(self) -> pd.DataFrame:
        """
        解析CSV文件

        Returns:
            pd.DataFrame: 解析后的数据
        """
        logger.info(f"Parsing CSV file: {self.csv_path}")

        try:
            # 读取CSV文件 (UTF-8 with BOM编码)
            self.raw_df = pd.read_csv(
                self.csv_path,
                encoding='utf-8-sig',  # 处理BOM
                low_memory=False
            )

            logger.info(f"Loaded {len(self.raw_df)} rows from CSV")

            # 重命名列
            self.df = self._rename_columns(self.raw_df.copy())

            # 显示解析的列名
            logger.info(f"Columns after mapping: {list(self.df.columns)}")

            return self.df

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}", exc_info=True)
            raise

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重命名列名（中文 -> 英文）

        Args:
            df: 原始DataFrame

        Returns:
            pd.DataFrame: 重命名后的DataFrame
        """
        # 创建映射字典（只映射存在的列）
        rename_dict = {}
        for cn_name, en_name in FIELD_MAPPING.items():
            if cn_name in df.columns:
                rename_dict[cn_name] = en_name

        # 重命名
        df = df.rename(columns=rename_dict)

        # 记录未映射的列
        unmapped_cols = [col for col in df.columns if col not in FIELD_MAPPING.values()]
        if unmapped_cols:
            logger.warning(f"Unmapped columns: {unmapped_cols}")

        return df

    def get_records(self) -> List[Dict]:
        """
        获取所有记录（字典列表格式）

        Returns:
            List[Dict]: 记录列表
        """
        if self.df is None:
            raise ValueError("CSV not parsed yet. Call parse() first.")

        records = self.df.to_dict('records')
        logger.info(f"Converted to {len(records)} records")

        return records

    def filter_completed_trades(self) -> pd.DataFrame:
        """
        过滤出已成交的订单（排除撤单、下单失败等）

        Returns:
            pd.DataFrame: 已成交订单
        """
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        # 过滤条件：交易状态为"全部成交"或"部分成交"
        completed_df = self.df[
            self.df['status'].isin(['全部成交', '部分成交'])
        ].copy()

        logger.info(f"Filtered: {len(completed_df)} completed / {len(self.df)} total")

        return completed_df

    def get_unique_symbols(self) -> List[str]:
        """
        获取所有唯一的symbol

        Returns:
            List[str]: symbol列表
        """
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        symbols = self.df['symbol'].dropna().unique().tolist()
        logger.info(f"Found {len(symbols)} unique symbols")

        return symbols

    def get_date_range(self) -> tuple:
        """
        获取交易日期范围

        Returns:
            tuple: (最早日期, 最晚日期)
        """
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        # 从成交时间中提取日期
        filled_times = pd.to_datetime(
            self.df['filled_time'],
            format='%Y/%m/%d %H:%M:%S',
            errors='coerce'
        )

        min_date = filled_times.min()
        max_date = filled_times.max()

        logger.info(f"Date range: {min_date} to {max_date}")

        return (min_date, max_date)

    def get_statistics(self) -> Dict:
        """
        获取CSV数据统计信息

        Returns:
            dict: 统计信息
        """
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        stats = {
            'total_rows': len(self.df),
            'completed_trades': len(self.df[self.df['status'] == '全部成交']),
            'cancelled_orders': len(self.df[self.df['status'] == '已撤单']),
            'failed_orders': len(self.df[self.df['status'] == '下单失败']),
            'unique_symbols': len(self.df['symbol'].unique()),
            'markets': self.df['market'].value_counts().to_dict(),
            'directions': self.df['direction'].value_counts().to_dict(),
        }

        return stats

    def validate_data(self) -> List[str]:
        """
        验证数据完整性

        Returns:
            List[str]: 错误信息列表
        """
        errors = []

        if self.df is None:
            errors.append("CSV not parsed yet")
            return errors

        # 检查必需字段
        required_fields = ['symbol', 'direction', 'filled_time', 'market']
        for field in required_fields:
            if field not in self.df.columns:
                errors.append(f"Missing required field: {field}")

        # 检查空值
        for field in required_fields:
            if field in self.df.columns:
                null_count = self.df[field].isnull().sum()
                if null_count > 0:
                    errors.append(f"Field '{field}' has {null_count} null values")

        # 检查数据类型
        if 'filled_quantity' in self.df.columns:
            non_numeric = self.df['filled_quantity'].apply(
                lambda x: not str(x).replace(',', '').replace('.', '').isdigit()
                if pd.notna(x) else False
            ).sum()
            if non_numeric > 0:
                errors.append(f"filled_quantity has {non_numeric} non-numeric values")

        return errors


def load_csv(csv_path: str, filter_completed: bool = True) -> pd.DataFrame:
    """
    便捷函数：加载并解析CSV

    Args:
        csv_path: CSV文件路径
        filter_completed: 是否只保留已成交订单

    Returns:
        pd.DataFrame: 解析后的数据
    """
    parser = CSVParser(csv_path)
    df = parser.parse()

    if filter_completed:
        df = parser.filter_completed_trades()

    return df
