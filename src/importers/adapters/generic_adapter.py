"""
Generic Adapter - 通用 CSV 适配器

input: CSV 文件, BrokerConfig 配置
output: 标准化 DataFrame
pos: 适配器层 - 纯 YAML 配置驱动，无需自定义代码

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from typing import Tuple
import pandas as pd
import logging

from ..core.base_adapter import BaseCSVAdapter
from ..configs.schema import BrokerConfig

logger = logging.getLogger(__name__)


class GenericAdapter(BaseCSVAdapter):
    """
    通用 CSV 适配器

    完全由 YAML 配置驱动，适用于简单的 CSV 格式。
    无需额外的 Python 代码，只需编写 YAML 配置文件。
    """

    def __init__(self, config: BrokerConfig):
        super().__init__(config)

    @classmethod
    def get_broker_id(cls) -> str:
        return "generic"

    @classmethod
    def can_parse(cls, file_path: str, sample_df: pd.DataFrame, config: BrokerConfig) -> Tuple[bool, float]:
        """
        通用适配器总是返回较低的置信度作为 fallback

        只有当没有其他适配器匹配时才使用通用适配器
        """
        # 使用基类的检测逻辑
        can_parse, confidence = super().can_parse(file_path, sample_df, config)

        # 降低置信度，让专用适配器优先
        return can_parse, confidence * 0.8
