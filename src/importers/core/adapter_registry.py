"""
Adapter Registry - 适配器注册与自动检测

input: CSV 文件路径
output: 匹配的适配器实例
pos: 适配器工厂 - 自动检测 CSV 格式并返回合适的适配器

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type
import pandas as pd
import logging

from .base_adapter import BaseCSVAdapter
from ..configs.schema import BrokerConfig

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    适配器注册表

    管理所有券商适配器的注册、配置加载和自动检测。
    使用单例模式确保全局唯一。
    """

    _instance = None
    _adapters: Dict[str, Type[BaseCSVAdapter]] = {}
    _configs: Dict[str, BrokerConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_configs()

    def _load_configs(self) -> None:
        """加载所有 YAML 配置"""
        config_dir = Path(__file__).parent.parent / 'configs'

        if not config_dir.exists():
            logger.warning(f"Config directory not found: {config_dir}")
            return

        for yaml_file in config_dir.glob('*.yaml'):
            if yaml_file.name.startswith('_'):
                continue  # 跳过模板文件

            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                if config_data:
                    config = BrokerConfig(**config_data)
                    self._configs[config.broker_id] = config
                    logger.info(f"Loaded config: {config.broker_id} ({config.broker_name_cn})")

            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")

    def register(self, adapter_cls: Type[BaseCSVAdapter]) -> None:
        """
        注册适配器类

        Args:
            adapter_cls: 适配器类
        """
        broker_id = adapter_cls.get_broker_id()
        self._adapters[broker_id] = adapter_cls
        logger.debug(f"Registered adapter: {broker_id}")

    def get_adapter(self, broker_id: str) -> Optional[BaseCSVAdapter]:
        """
        通过 ID 获取适配器实例

        Args:
            broker_id: 券商 ID

        Returns:
            适配器实例，如果不存在返回 None
        """
        adapter_cls = self._adapters.get(broker_id)
        config = self._configs.get(broker_id)

        if adapter_cls and config:
            return adapter_cls(config)
        elif config:
            # 配置存在但无专用适配器，使用通用适配器
            from ..adapters.generic_adapter import GenericAdapter
            return GenericAdapter(config)

        return None

    def detect_and_get_adapter(self, file_path: str) -> Tuple[Optional[BaseCSVAdapter], float]:
        """
        自动检测 CSV 格式并返回适配器

        Args:
            file_path: CSV 文件路径

        Returns:
            Tuple[适配器实例, 置信度]
        """
        logger.info(f"Auto-detecting format for: {file_path}")

        best_adapter = None
        best_config = None
        best_confidence = 0.0

        # 尝试多种编码读取文件头
        sample_df = self._read_sample(file_path)
        if sample_df is None:
            logger.error("Failed to read file sample")
            return None, 0.0

        logger.debug(f"Sample columns: {list(sample_df.columns)}")

        # 遍历所有配置检测
        for broker_id, config in self._configs.items():
            try:
                adapter_cls = self._adapters.get(broker_id)
                if adapter_cls:
                    can_parse, confidence = adapter_cls.can_parse(file_path, sample_df, config)
                else:
                    # 使用基类的检测方法
                    can_parse, confidence = BaseCSVAdapter.can_parse(file_path, sample_df, config)

                if can_parse and confidence > best_confidence:
                    best_confidence = confidence
                    best_config = config
                    best_adapter_cls = adapter_cls

                logger.debug(f"{broker_id}: confidence={confidence:.2f}, can_parse={can_parse}")

            except Exception as e:
                logger.debug(f"Detection failed for {broker_id}: {e}")

        if best_config:
            if best_adapter_cls:
                best_adapter = best_adapter_cls(best_config)
            else:
                # 使用通用适配器
                from ..adapters.generic_adapter import GenericAdapter
                best_adapter = GenericAdapter(best_config)

            logger.info(f"Detected: {best_config.broker_id} (confidence={best_confidence:.2f})")
        else:
            logger.warning("No suitable adapter found")

        return best_adapter, best_confidence

    def _read_sample(self, file_path: str, nrows: int = 5) -> Optional[pd.DataFrame]:
        """尝试多种编码读取文件样本"""
        encodings = ['utf-8-sig', 'utf-8', 'gb18030', 'gbk', 'gb2312']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=nrows)
                logger.debug(f"Successfully read with encoding: {encoding}")
                return df
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue

        return None

    def list_adapters(self) -> List[str]:
        """列出所有注册的适配器"""
        return list(self._adapters.keys())

    def list_configs(self) -> List[str]:
        """列出所有加载的配置"""
        return list(self._configs.keys())

    def list_brokers(self) -> List[Dict]:
        """
        列出所有可用的券商信息

        Returns:
            券商信息列表，每个包含 broker_id, broker_name, broker_name_cn
        """
        brokers = []
        for broker_id, config in self._configs.items():
            brokers.append({
                'broker_id': config.broker_id,
                'broker_name': config.broker_name,
                'broker_name_cn': config.broker_name_cn,
                'markets': config.markets,
                'has_adapter': broker_id in self._adapters,
            })
        return sorted(brokers, key=lambda x: x['broker_id'])

    def get_config(self, broker_id: str) -> Optional[BrokerConfig]:
        """获取券商配置"""
        return self._configs.get(broker_id)

    def reload_configs(self) -> None:
        """重新加载所有配置"""
        self._configs.clear()
        self._load_configs()


# 全局注册表实例
registry = AdapterRegistry()


def get_adapter_for_file(file_path: str) -> Optional[BaseCSVAdapter]:
    """
    便捷函数：获取文件对应的适配器

    Args:
        file_path: CSV 文件路径

    Returns:
        适配器实例
    """
    adapter, confidence = registry.detect_and_get_adapter(file_path)
    return adapter


def get_adapter_by_id(broker_id: str) -> Optional[BaseCSVAdapter]:
    """
    便捷函数：通过 ID 获取适配器

    Args:
        broker_id: 券商 ID

    Returns:
        适配器实例
    """
    return registry.get_adapter(broker_id)
