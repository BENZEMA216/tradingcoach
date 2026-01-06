"""
Base CSV Adapter - 所有券商适配器的基类

input: CSV 文件路径, BrokerConfig 配置
output: 标准化 DataFrame
pos: 适配器层基类 - 定义统一接口，子类实现具体解析逻辑

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import hashlib
import logging

from ..configs.schema import BrokerConfig, FieldMapping, TransformType

logger = logging.getLogger(__name__)


class BaseCSVAdapter(ABC):
    """
    CSV 适配器基类

    所有券商适配器都继承此类，实现统一的解析接口。
    支持 YAML 配置驱动的字段映射和数据转换。
    """

    def __init__(self, config: BrokerConfig):
        """
        初始化适配器

        Args:
            config: 券商配置对象
        """
        self.config = config
        self.raw_df: Optional[pd.DataFrame] = None
        self.df: Optional[pd.DataFrame] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._import_batch_id: Optional[str] = None

    def set_import_batch_id(self, batch_id: str) -> None:
        """
        设置导入批次 ID

        Args:
            batch_id: 外部提供的批次 ID
        """
        self._import_batch_id = batch_id

    @classmethod
    @abstractmethod
    def get_broker_id(cls) -> str:
        """返回券商唯一标识"""
        pass

    @classmethod
    def can_parse(cls, file_path: str, sample_df: pd.DataFrame, config: BrokerConfig) -> Tuple[bool, float]:
        """
        判断是否能解析此文件

        Args:
            file_path: CSV 文件路径
            sample_df: 文件头部样本 DataFrame
            config: 券商配置

        Returns:
            Tuple[bool, float]: (能否解析, 置信度 0-1)
        """
        columns = set(sample_df.columns)
        detection = config.detection

        # 计算匹配的列数
        expected_columns = set(detection.columns)
        matched = expected_columns & columns
        match_ratio = len(matched) / len(expected_columns) if expected_columns else 0

        # 特有列加分
        unique_bonus = 0
        if detection.unique_columns:
            unique_matched = set(detection.unique_columns) & columns
            if unique_matched:
                unique_bonus = 0.1 * (len(unique_matched) / len(detection.unique_columns))

        confidence = min(match_ratio + unique_bonus, 1.0)
        can_parse = confidence >= detection.confidence_threshold

        logger.debug(f"{config.broker_id}: matched={len(matched)}/{len(expected_columns)}, "
                     f"confidence={confidence:.2f}, can_parse={can_parse}")

        return can_parse, confidence

    def parse(self, file_path: str) -> pd.DataFrame:
        """
        解析 CSV 文件的完整流程

        Args:
            file_path: CSV 文件路径

        Returns:
            pd.DataFrame: 标准化后的数据
        """
        logger.info(f"Parsing with {self.config.broker_id}: {file_path}")

        # 1. 读取原始文件
        self.raw_df = self._read_csv(file_path)
        logger.info(f"Loaded {len(self.raw_df)} rows, {len(self.raw_df.columns)} columns")

        # 2. 预处理钩子
        if self.config.pre_process_hook:
            self.raw_df = self._run_hook(self.config.pre_process_hook, self.raw_df)

        # 3. 字段映射
        self.df = self._map_fields(self.raw_df)

        # 4. 数据转换
        self.df = self._transform_fields(self.df)

        # 5. 方向/状态/市场映射
        self.df = self._apply_enum_mappings(self.df)

        # 6. 费用处理
        self.df = self._process_fees(self.df)

        # 7. 验证
        self._validate(self.df)

        # 8. 计算指纹
        self.df = self._calculate_fingerprints(self.df)

        # 9. 添加元数据
        self.df = self._add_metadata(self.df, file_path)

        # 10. 后处理钩子
        if self.config.post_process_hook:
            self.df = self._run_hook(self.config.post_process_hook, self.df)

        logger.info(f"Parsed {len(self.df)} rows, {len(self.errors)} errors, {len(self.warnings)} warnings")
        return self.df

    def _read_csv(self, file_path: str) -> pd.DataFrame:
        """读取 CSV 文件"""
        try:
            return pd.read_csv(
                file_path,
                encoding=self.config.encoding.value,
                delimiter=self.config.delimiter,
                quotechar=self.config.quote_char,
                header=self.config.header_row,
                skiprows=self.config.skip_rows if self.config.skip_rows else None,
                low_memory=False,
                dtype=str,  # 先全部读为字符串，后续转换
            )
        except UnicodeDecodeError:
            # 尝试备选编码
            fallback_encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'gbk']
            for encoding in fallback_encodings:
                try:
                    logger.warning(f"Trying fallback encoding: {encoding}")
                    return pd.read_csv(
                        file_path,
                        encoding=encoding,
                        delimiter=self.config.delimiter,
                        low_memory=False,
                        dtype=str,
                    )
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Cannot decode file with any supported encoding")

    def _map_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        根据配置映射字段名

        将 CSV 列名映射到 Trade 模型字段名
        """
        result = pd.DataFrame()
        columns_found = set()

        for mapping in self.config.field_mappings:
            source_col = None

            # 查找源列 (包括别名)
            if mapping.source in df.columns:
                source_col = mapping.source
            else:
                for alias in mapping.aliases:
                    if alias in df.columns:
                        source_col = alias
                        break

            if source_col:
                result[mapping.target] = df[source_col]
                columns_found.add(source_col)
            elif mapping.required:
                self.errors.append(f"Required column not found: {mapping.source}")
            else:
                # 非必填字段设为 None
                result[mapping.target] = None

        # 保留未映射的列到 raw_data
        unmapped_cols = set(df.columns) - columns_found
        if unmapped_cols:
            logger.debug(f"Unmapped columns: {unmapped_cols}")

        # 存储原始数据
        result['_raw_data'] = df.apply(lambda row: row.to_dict(), axis=1)

        return result

    def _transform_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        应用字段转换规则
        """
        from .field_transformer import FieldTransformer

        transformer = FieldTransformer()

        for mapping in self.config.field_mappings:
            if mapping.transform and mapping.target in df.columns:
                try:
                    df[mapping.target] = transformer.transform_column(
                        df[mapping.target],
                        mapping.transform,
                        self.config
                    )
                except Exception as e:
                    self.warnings.append(f"Transform failed for {mapping.target}: {e}")

        return df

    def _apply_enum_mappings(self, df: pd.DataFrame) -> pd.DataFrame:
        """应用枚举值映射 (方向、状态、市场)"""
        # 方向映射
        if 'direction' in df.columns:
            df['direction'] = df['direction'].map(
                lambda x: self.config.direction_mapping.get(str(x).strip(), x) if pd.notna(x) else x
            )

        # 状态映射
        if 'status' in df.columns:
            df['status'] = df['status'].map(
                lambda x: self.config.status_mapping.get(str(x).strip(), x) if pd.notna(x) else x
            )

        # 市场映射
        if 'market' in df.columns:
            df['market'] = df['market'].map(
                lambda x: self.config.market_mapping.get(str(x).strip(), x) if pd.notna(x) else x
            )

        return df

    def _process_fees(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理费用字段"""
        fee_config = self.config.fees

        # 映射费用列到标准字段名
        for csv_col, model_field in fee_config.field_mapping.items():
            if csv_col in self.raw_df.columns and model_field not in df.columns:
                df[model_field] = pd.to_numeric(
                    self.raw_df[csv_col].replace(r'[,\s]', '', regex=True),
                    errors='coerce'
                ).fillna(0)

        # 计算总费用
        if fee_config.calculate_total:
            fee_columns = [col for col in [
                'commission', 'platform_fee', 'clearing_fee', 'stamp_duty',
                'transaction_fee', 'sec_fee', 'option_regulatory_fee',
                'option_clearing_fee', 'transfer_fee', 'handling_fee',
                'regulation_fee', 'other_fees'
            ] if col in df.columns]

            if fee_columns:
                df['total_fee'] = df[fee_columns].sum(axis=1, skipna=True)
        elif fee_config.total_field and fee_config.total_field in self.raw_df.columns:
            df['total_fee'] = pd.to_numeric(
                self.raw_df[fee_config.total_field].replace(r'[,\s]', '', regex=True),
                errors='coerce'
            ).fillna(0)

        return df

    def _validate(self, df: pd.DataFrame) -> None:
        """执行验证规则"""
        for rule in self.config.validations:
            field = rule.field
            if field not in df.columns:
                continue

            if rule.rule == 'required':
                null_count = df[field].isna().sum()
                if null_count > 0:
                    msg = rule.error_message or f"{field} has {null_count} null values"
                    if rule.level == 'error':
                        self.errors.append(msg)
                    else:
                        self.warnings.append(msg)

            elif rule.rule == 'range':
                min_val = rule.params.get('min')
                max_val = rule.params.get('max')
                invalid = df[
                    (df[field].notna()) &
                    ((df[field] < min_val) if min_val is not None else False) |
                    ((df[field] > max_val) if max_val is not None else False)
                ]
                if len(invalid) > 0:
                    msg = rule.error_message or f"{field} has {len(invalid)} out-of-range values"
                    if rule.level == 'error':
                        self.errors.append(msg)
                    else:
                        self.warnings.append(msg)

            elif rule.rule == 'regex':
                import re
                pattern = rule.params.get('pattern', '')
                invalid = df[
                    (df[field].notna()) &
                    (~df[field].astype(str).str.match(pattern))
                ]
                if len(invalid) > 0:
                    msg = rule.error_message or f"{field} has {len(invalid)} invalid format values"
                    if rule.level == 'error':
                        self.errors.append(msg)
                    else:
                        self.warnings.append(msg)

    def _calculate_fingerprints(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算交易指纹用于去重"""
        def calc_fingerprint(row):
            # 指纹组成: symbol + filled_time + direction + quantity + price + market
            parts = [
                str(row.get('symbol', '')),
                str(row.get('filled_time', '')),
                str(row.get('direction', '')),
                str(row.get('filled_quantity', '')),
                f"{float(row.get('filled_price', 0) or 0):.4f}",
                str(row.get('market', '')),
            ]
            fingerprint_str = '|'.join(parts)
            return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:32]

        df['trade_fingerprint'] = df.apply(calc_fingerprint, axis=1)
        return df

    def _add_metadata(self, df: pd.DataFrame, file_path: str) -> pd.DataFrame:
        """添加元数据"""
        df['broker_id'] = self.config.broker_id
        df['source_row_number'] = range(1, len(df) + 1)

        # 使用外部设置的批次ID，或生成新的
        if self._import_batch_id:
            import_batch = self._import_batch_id
        else:
            import_batch = hashlib.sha256(
                f"{file_path}_{pd.Timestamp.now().isoformat()}".encode()
            ).hexdigest()[:16]
        df['import_batch_id'] = import_batch

        return df

    def _run_hook(self, hook_path: str, df: pd.DataFrame) -> pd.DataFrame:
        """运行钩子函数"""
        try:
            module_path, func_name = hook_path.rsplit('.', 1)
            import importlib
            module = importlib.import_module(module_path)
            hook_func = getattr(module, func_name)
            return hook_func(df, self.config)
        except Exception as e:
            self.warnings.append(f"Hook {hook_path} failed: {e}")
            return df

    def filter_completed_trades(self) -> pd.DataFrame:
        """过滤已成交订单"""
        if self.df is None:
            raise ValueError("CSV not parsed yet. Call parse() first.")

        completed_statuses = ['filled', 'partially_filled']
        mask = self.df['status'].isin(completed_statuses)
        result = self.df[mask].copy()

        logger.info(f"Filtered to {len(result)} completed trades from {len(self.df)} total")
        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            'broker_id': self.config.broker_id,
            'broker_name': self.config.broker_name_cn,
            'total_rows': len(self.raw_df) if self.raw_df is not None else 0,
            'parsed_rows': len(self.df) if self.df is not None else 0,
            'errors': len(self.errors),
            'warnings': len(self.warnings),
            'error_messages': self.errors[:10],  # 最多返回10条
            'warning_messages': self.warnings[:10],
        }

    def to_trade_dicts(self) -> List[Dict[str, Any]]:
        """将 DataFrame 转换为 Trade 字典列表"""
        if self.df is None:
            return []

        trades = []
        for _, row in self.df.iterrows():
            trade = row.to_dict()
            # 移除内部字段
            trade.pop('_raw_data', None)
            # 将 raw_data 转为 JSON 存储
            if '_raw_data' in row:
                trade['raw_data'] = row['_raw_data']
            trades.append(trade)

        return trades
