"""
adapters - 券商适配器模块

input: CSV 文件, BrokerConfig 配置
output: 标准化 DataFrame
pos: 适配器层 - 各券商的具体实现

支持的券商:
- FutuAdapter: 富途证券 (中文/英文)
- GenericAdapter: 通用适配器 (YAML 配置驱动)

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from .generic_adapter import GenericAdapter
from .futu_adapter import FutuAdapter

__all__ = [
    'GenericAdapter',
    'FutuAdapter',
]
