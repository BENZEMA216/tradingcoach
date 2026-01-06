"""
core - CSV 适配器核心框架

input: CSV 文件, YAML 配置
output: 标准化 DataFrame, Trade 对象
pos: 适配器核心层 - 提供适配器基类、注册表、转换器

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from .base_adapter import BaseCSVAdapter
from .adapter_registry import AdapterRegistry, get_adapter_for_file
from .field_transformer import FieldTransformer

__all__ = [
    'BaseCSVAdapter',
    'AdapterRegistry',
    'get_adapter_for_file',
    'FieldTransformer',
]
