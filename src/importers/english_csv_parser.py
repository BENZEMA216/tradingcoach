"""
英文CSV解析器

解析富途证券英文版导出的交易记录和持仓快照
"""

import pandas as pd
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# 英文字段名映射（交易历史）
HISTORY_FIELD_MAPPING = {
    'Side': 'direction',
    'Symbol': 'symbol',
    'Name': 'symbol_name',
    'Order Price': 'order_price',
    'Order Qty': 'order_quantity',
    'Order Amount': 'order_amount',
    'Status': 'status',
    'Filled@Avg Price': 'filled_info',
    'Order Time': 'order_time',
    'Order Type': 'order_type',
    'Time-in-Force': 'duration',
    'Allow Pre-Market': 'pre_market',
    'Session': 'session',
    'Trigger price': 'trigger_price',
    'Position Opening': 'allow_open',
    'Markets': 'market',
    'Currency': 'currency',
    'Order Source': 'order_source',
    'Fill Qty': 'filled_quantity',
    'Fill Price': 'filled_price',
    'Fill Amount': 'filled_amount',
    'Fill Time': 'filled_time',
    'Counterparty': 'broker',
    'Remarks': 'notes',
    'Commission': 'commission',
    'Platform Fees': 'platform_fee',
    'Settlement Fees': 'clearing_fee',
    'Options Regulatory Fees': 'option_regulatory_fee',
    'OCC Fees': 'occ_fee',
    'Option Settlement Fees': 'option_settlement_fee',
    'SEC Fees': 'sec_fee',
    'Trading Activity Fees': 'trading_activity_fee',
    'Stamp Duty': 'stamp_duty',
    'Trading Fees': 'transaction_fee',
    'SFC Levy': 'sfc_levy',
    'FRC Levy': 'frc_levy',
    'Trading Tariff': 'trading_tariff',
    'Consolidated Audit Trail Fees': 'audit_trail_fee',
    'Total': 'total_fee',
}

# 持仓文件字段映射
POSITION_FIELD_MAPPING = {
    'Symbol': 'symbol',
    'Name': 'symbol_name',
    'Quantity': 'quantity',
    'Current price': 'current_price',
    'Average Cost': 'avg_cost',
    'Market Value': 'market_value',
    '% Unrealized P/L': 'unrealized_pnl_pct',
    'Total P/L': 'total_pnl',
    'Unrealized P/L': 'unrealized_pnl',
    'Realized P/L': 'realized_pnl',
    "Today's P/L": 'today_pnl',
    '% of Portfolio': 'portfolio_pct',
    'Currency': 'currency',
    "Today's Turnover": 'today_turnover',
    "Today's Purchase@Avg Price": 'today_purchase',
    "Today's Sales@Avg Price": 'today_sales',
    'Initial Margin': 'initial_margin',
    'Delta': 'delta',
    'Gamma (options only)': 'gamma',
    'Vega (options only)': 'vega',
    'Theta (options only)': 'theta',
    'Rho (options only)': 'rho',
    'IV (options only)': 'iv',
    'Intrinsic Value (options only)': 'intrinsic_value',
    'Extrinsic Value (options only)': 'extrinsic_value',
}

# 方向映射
DIRECTION_MAPPING = {
    'Buy': 'buy',
    'Sell': 'sell',
    'Sell Short': 'sell_short',
    'Short Sell': 'sell_short',  # 富途实际使用的格式
    'Buy to Cover': 'buy_to_cover',
}

# 状态映射 - 映射到枚举值 (TradeStatus)
STATUS_MAPPING = {
    'Filled': 'filled',
    'Partially Filled': 'partially_filled',
    'Cancelled': 'cancelled',
    'Rejected': 'cancelled',
    'Pending': 'pending',
}


class EnglishCSVParser:
    """英文CSV文件解析器"""

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
        self.raw_df = None
        self.file_type = None  # 'history' or 'position'

    def parse(self) -> pd.DataFrame:
        """
        解析CSV文件，自动检测文件类型

        Returns:
            pd.DataFrame: 解析后的数据
        """
        logger.info(f"Parsing English CSV file: {self.csv_path}")

        try:
            # 读取CSV文件
            self.raw_df = pd.read_csv(
                self.csv_path,
                encoding='utf-8-sig',
                low_memory=False
            )

            logger.info(f"Loaded {len(self.raw_df)} rows from CSV")

            # 检测文件类型
            self.file_type = self._detect_file_type()
            logger.info(f"Detected file type: {self.file_type}")

            # 根据类型选择映射
            if self.file_type == 'history':
                self.df = self._parse_history()
            elif self.file_type == 'position':
                self.df = self._parse_position()
            else:
                raise ValueError(f"Unknown file type: {self.file_type}")

            return self.df

        except Exception as e:
            logger.error(f"Error parsing CSV: {e}", exc_info=True)
            raise

    def _detect_file_type(self) -> str:
        """检测CSV文件类型"""
        columns = set(self.raw_df.columns)

        # 检查是否是持仓文件
        if 'Average Cost' in columns and 'Current price' in columns:
            return 'position'

        # 检查是否是交易历史
        if 'Side' in columns and 'Order Time' in columns:
            return 'history'

        return 'unknown'

    def _parse_history(self) -> pd.DataFrame:
        """解析交易历史文件"""
        df = self.raw_df.copy()

        # 重命名列
        rename_dict = {k: v for k, v in HISTORY_FIELD_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        # 标准化方向
        if 'direction' in df.columns:
            df['direction'] = df['direction'].map(
                lambda x: DIRECTION_MAPPING.get(x, x) if pd.notna(x) else x
            )

        # 标准化状态
        if 'status' in df.columns:
            df['status'] = df['status'].map(
                lambda x: STATUS_MAPPING.get(x, x) if pd.notna(x) else x
            )

        # 解析时间
        df = self._parse_times(df)

        # 解析数量（处理 "3unit(s)" 格式）
        df = self._parse_quantities(df)

        # 清洗数值字段
        df = self._clean_numeric_fields(df)

        # 解析组合订单
        df = self._parse_spread_orders(df)

        # 解析期权信息（用于历史文件）
        df = self._parse_option_info(df)

        # 计算交易指纹
        df['trade_fingerprint'] = df.apply(self._calculate_fingerprint, axis=1)

        return df

    def _parse_position(self) -> pd.DataFrame:
        """解析持仓快照文件"""
        df = self.raw_df.copy()

        # 重命名列
        rename_dict = {k: v for k, v in POSITION_FIELD_MAPPING.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        # 清洗数值字段
        numeric_cols = ['quantity', 'current_price', 'avg_cost', 'market_value',
                        'unrealized_pnl', 'realized_pnl', 'total_pnl', 'delta',
                        'gamma', 'vega', 'theta', 'rho', 'iv']

        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_number)

        # 解析百分比
        pct_cols = ['unrealized_pnl_pct', 'portfolio_pct']
        for col in pct_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._parse_percentage)

        # 解析期权信息
        df = self._parse_option_info(df)

        return df

    def _parse_times(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析时间字段"""
        time_cols = ['order_time', 'filled_time']

        for col in time_cols:
            if col in df.columns:
                df[col + '_parsed'] = df[col].apply(self._parse_datetime)

        return df

    def _parse_datetime(self, time_str: str) -> Optional[datetime]:
        """
        解析时间字符串

        格式: "Dec 17, 2025 12:05:15 ET"
        """
        if pd.isna(time_str) or not time_str:
            return None

        try:
            # 移除时区标识
            time_str = str(time_str).strip()
            time_str = re.sub(r'\s*(ET|EST|EDT|PT|PST|PDT|HKT|CST|SGT)\s*$', '', time_str)

            # 解析日期
            formats = [
                '%b %d, %Y %H:%M:%S',  # Dec 17, 2025 12:05:15
                '%Y/%m/%d %H:%M:%S',   # 2025/12/17 12:05:15
                '%Y-%m-%d %H:%M:%S',   # 2025-12-17 12:05:15
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str.strip(), fmt)
                except ValueError:
                    continue

            logger.warning(f"Could not parse datetime: {time_str}")
            return None

        except Exception as e:
            logger.warning(f"Error parsing datetime '{time_str}': {e}")
            return None

    def _parse_quantities(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析数量字段"""
        qty_cols = ['order_quantity', 'filled_quantity']

        for col in qty_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._extract_quantity)

        return df

    def _extract_quantity(self, value) -> Optional[int]:
        """
        提取数量值

        处理格式: "3unit(s)", "10", etc.
        """
        if pd.isna(value) or value == '':
            return None

        try:
            value_str = str(value)

            # 移除 "unit(s)" 后缀
            value_str = re.sub(r'\s*unit\(s\)\s*', '', value_str, flags=re.IGNORECASE)

            # 移除逗号
            value_str = value_str.replace(',', '')

            # 提取数字
            match = re.search(r'[\d.]+', value_str)
            if match:
                return int(float(match.group()))

            return None

        except Exception:
            return None

    def _clean_number(self, value) -> Optional[float]:
        """清洗数值"""
        if pd.isna(value) or value == '' or value == '--':
            return None

        try:
            value_str = str(value)
            # 移除逗号、美元符号
            value_str = value_str.replace(',', '').replace('$', '').strip()

            if value_str == '' or value_str == '--':
                return None

            return float(value_str)

        except Exception:
            return None

    def _parse_percentage(self, value) -> Optional[float]:
        """解析百分比"""
        if pd.isna(value) or value == '' or value == '--':
            return None

        try:
            value_str = str(value)
            # 移除百分号和符号
            value_str = value_str.replace('%', '').replace('+', '').strip()

            if value_str == '' or value_str == '--':
                return None

            return float(value_str)

        except Exception:
            return None

    def _clean_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数值字段"""
        numeric_cols = ['order_price', 'order_amount', 'filled_price',
                        'filled_amount', 'commission', 'platform_fee',
                        'clearing_fee', 'total_fee']

        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_number)

        return df

    def _parse_spread_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析组合订单（垂直价差等）"""
        # 标记组合订单
        if 'symbol' in df.columns:
            df['is_spread'] = df['symbol'].apply(
                lambda x: '/' in str(x) if pd.notna(x) else False
            )

            # 解析组合类型
            df['spread_type'] = df['symbol'].apply(self._detect_spread_type)

        return df

    def _detect_spread_type(self, symbol: str) -> Optional[str]:
        """检测组合类型"""
        if pd.isna(symbol):
            return None

        symbol_str = str(symbol)

        if '/' not in symbol_str:
            return None

        # 垂直价差: NVDA260618C205/215
        if re.match(r'^[A-Z]+\d{6}[CP]\d+/\d+$', symbol_str):
            return 'vertical'

        return 'unknown_spread'

    def _parse_option_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """解析期权信息"""
        if 'symbol' not in df.columns:
            return df

        # 检测是否是期权
        df['is_option'] = df['symbol'].apply(self._is_option_symbol)

        # 解析期权详情
        option_info = df['symbol'].apply(self._parse_option_symbol)
        df['underlying_symbol'] = option_info.apply(lambda x: x.get('underlying') if x else None)
        df['option_type'] = option_info.apply(lambda x: x.get('option_type') if x else None)
        df['strike_price'] = option_info.apply(lambda x: x.get('strike') if x else None)
        df['expiry_date'] = option_info.apply(lambda x: x.get('expiry') if x else None)

        return df

    def _is_option_symbol(self, symbol: str) -> bool:
        """判断是否是期权代码"""
        if pd.isna(symbol):
            return False

        symbol_str = str(symbol)

        # 美股期权格式: AAPL250117C00150000 或 NVDA260618C205/215
        if re.match(r'^[A-Z]{1,5}\d{6}[CP]', symbol_str):
            return True

        return False

    def _parse_option_symbol(self, symbol: str) -> Optional[Dict]:
        """
        解析期权代码

        格式: AAPL250117C00150000
        - 标的: AAPL
        - 到期日: 250117 (2025-01-17)
        - 类型: C (Call) / P (Put)
        - 行权价: 150.00
        """
        if pd.isna(symbol):
            return None

        symbol_str = str(symbol)

        # 处理垂直价差
        if '/' in symbol_str:
            # NVDA260618C205/215 -> 取第一个腿
            symbol_str = symbol_str.split('/')[0]
            if not symbol_str[-1].isdigit():
                # 如果最后不是数字，需要特殊处理
                match = re.match(r'^([A-Z]+)(\d{6})([CP])(\d+)', symbol_str)
                if match:
                    pass  # 继续处理
                else:
                    return None

        # 标准期权格式
        match = re.match(r'^([A-Z]{1,5})(\d{6})([CP])(\d+)$', symbol_str)
        if match:
            underlying = match.group(1)
            expiry_str = match.group(2)
            option_type = 'call' if match.group(3) == 'C' else 'put'
            strike_raw = match.group(4)

            # 解析到期日
            try:
                expiry = datetime.strptime(expiry_str, '%y%m%d').date()
            except ValueError:
                expiry = None

            # 解析行权价（除以1000）
            if len(strike_raw) >= 5:
                strike = float(strike_raw) / 1000
            else:
                strike = float(strike_raw)

            return {
                'underlying': underlying,
                'expiry': expiry,
                'option_type': option_type,
                'strike': strike,
            }

        return None

    def _calculate_fingerprint(self, row: pd.Series) -> Optional[str]:
        """计算交易唯一指纹"""
        try:
            # 只对有效成交计算指纹
            if pd.isna(row.get('filled_time_parsed')) or pd.isna(row.get('filled_quantity')):
                return None

            components = [
                str(row.get('symbol', '')),
                str(row.get('filled_time_parsed', '')),
                str(row.get('direction', '')),
                str(row.get('filled_quantity', '')),
                f"{row.get('filled_price', 0):.4f}",
                str(row.get('market', '')),
            ]

            fingerprint_str = '|'.join(components)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

        except Exception:
            return None

    def filter_completed_trades(self) -> pd.DataFrame:
        """过滤出已成交的订单"""
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        if self.file_type != 'history':
            raise ValueError("This method is only for history files")

        # 过滤已成交 (支持中文、英文和枚举值格式)
        completed_df = self.df[
            self.df['status'].isin([
                '全部成交', '部分成交',           # 中文格式
                'Filled', 'Partially Filled',    # 英文原始格式
                'filled', 'partially_filled',    # 枚举值格式
            ])
        ].copy()

        # 过滤有效成交（有成交时间和数量）
        completed_df = completed_df[
            completed_df['filled_time_parsed'].notna() &
            completed_df['filled_quantity'].notna() &
            (completed_df['filled_quantity'] > 0)
        ]

        logger.info(f"Filtered: {len(completed_df)} completed / {len(self.df)} total")

        return completed_df

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if self.df is None:
            raise ValueError("CSV not parsed yet")

        if self.file_type == 'history':
            return {
                'file_type': 'history',
                'total_rows': len(self.df),
                'completed_trades': len(self.df[self.df['status'].isin(['全部成交', 'filled'])]),
                'cancelled_orders': len(self.df[self.df['status'].isin(['已撤单', 'cancelled'])]),
                'unique_symbols': len(self.df['symbol'].dropna().unique()),
                'spread_orders': len(self.df[self.df['is_spread'] == True]),
                'option_trades': len(self.df[self.df['is_option'] == True]),
            }
        else:
            return {
                'file_type': 'position',
                'total_positions': len(self.df),
                'unique_symbols': len(self.df['symbol'].dropna().unique()),
                'option_positions': len(self.df[self.df['is_option'] == True]),
                'currencies': self.df['currency'].value_counts().to_dict(),
            }


class PositionSnapshotParser:
    """持仓快照解析器"""

    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.parser = EnglishCSVParser(csv_path)

    def parse(self) -> pd.DataFrame:
        """解析持仓快照"""
        df = self.parser.parse()

        if self.parser.file_type != 'position':
            raise ValueError("File is not a position snapshot")

        return df

    def get_positions_list(self) -> List[Dict]:
        """获取持仓列表（用于对账）"""
        df = self.parser.df

        positions = []
        for _, row in df.iterrows():
            pos = {
                'symbol': row.get('symbol'),
                'symbol_name': row.get('symbol_name'),
                'quantity': row.get('quantity'),
                'avg_cost': row.get('avg_cost'),
                'current_price': row.get('current_price'),
                'market_value': row.get('market_value'),
                'unrealized_pnl': row.get('unrealized_pnl'),
                'realized_pnl': row.get('realized_pnl'),
                'currency': row.get('currency'),
                'is_option': row.get('is_option', False),
                'underlying_symbol': row.get('underlying_symbol'),
                'option_type': row.get('option_type'),
                'strike_price': row.get('strike_price'),
                'expiry_date': row.get('expiry_date'),
                # Greeks
                'delta': row.get('delta'),
                'gamma': row.get('gamma'),
                'vega': row.get('vega'),
                'theta': row.get('theta'),
            }
            positions.append(pos)

        return positions


def detect_csv_language(csv_path: str) -> str:
    """
    检测CSV文件语言

    Returns:
        'chinese' or 'english'
    """
    df = pd.read_csv(csv_path, encoding='utf-8-sig', nrows=1)
    columns = set(df.columns)

    # 检查中文标志列
    chinese_markers = {'方向', '代码', '名称', '成交时间'}
    if chinese_markers & columns:
        return 'chinese'

    # 检查英文标志列
    english_markers = {'Side', 'Symbol', 'Name', 'Fill Time'}
    if english_markers & columns:
        return 'english'

    return 'unknown'


def load_english_csv(csv_path: str, filter_completed: bool = True) -> pd.DataFrame:
    """
    便捷函数：加载并解析英文CSV

    Args:
        csv_path: CSV文件路径
        filter_completed: 是否只保留已成交订单

    Returns:
        pd.DataFrame: 解析后的数据
    """
    parser = EnglishCSVParser(csv_path)
    df = parser.parse()

    if filter_completed and parser.file_type == 'history':
        df = parser.filter_completed_trades()

    return df
