"""
configs - YAML 配置模块

input: YAML 配置文件
output: BrokerConfig 对象
pos: 配置层 - 定义和验证券商配置模式

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from .schema import (
    BrokerConfig,
    FieldMapping,
    FieldTransform,
    DetectionRule,
    FeeConfig,
    ValidationRule,
    EncodingType,
    MarketType,
)

__all__ = [
    'BrokerConfig',
    'FieldMapping',
    'FieldTransform',
    'DetectionRule',
    'FeeConfig',
    'ValidationRule',
    'EncodingType',
    'MarketType',
]
