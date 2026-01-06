"""
YAML 配置文件的 Pydantic 验证模式

input: YAML 配置文件内容
output: 验证后的 BrokerConfig 对象
pos: 配置验证层 - 确保 YAML 配置符合系统要求

一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Any, Union
from enum import Enum


class EncodingType(str, Enum):
    """支持的文件编码"""
    UTF8 = "utf-8"
    UTF8_BOM = "utf-8-sig"
    GBK = "gbk"
    GB2312 = "gb2312"
    GB18030 = "gb18030"


class MarketType(str, Enum):
    """市场类型"""
    US = "us"      # 美股
    HK = "hk"      # 港股
    CN = "cn"      # A股


class TransformType(str, Enum):
    """字段转换类型"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    DATETIME = "datetime"
    DATE = "date"
    ENUM = "enum"
    BOOLEAN = "boolean"
    COMPUTED = "computed"


class FieldTransform(BaseModel):
    """单字段转换规则"""
    type: TransformType
    format: Optional[str] = None  # datetime/number 格式
    mapping: Optional[Dict[str, str]] = None  # enum 映射
    expression: Optional[str] = None  # computed 表达式
    default: Optional[Any] = None  # 默认值
    nullable: bool = True  # 是否允许空值
    strip: bool = True  # 是否去除空白
    lowercase: bool = False  # 是否转小写


class FieldMapping(BaseModel):
    """字段映射配置"""
    source: str  # CSV 列名
    target: str  # Trade 模型字段名
    required: bool = False  # 是否必填
    transform: Optional[FieldTransform] = None  # 转换规则
    aliases: List[str] = Field(default_factory=list)  # 备选列名


class DetectionRule(BaseModel):
    """CSV 格式检测规则"""
    columns: List[str]  # 用于检测的特征列
    encoding_hint: EncodingType = EncodingType.UTF8
    header_row: int = 0  # 表头行号
    confidence_threshold: float = 0.8  # 最低置信度
    unique_columns: List[str] = Field(default_factory=list)  # 该券商特有列(加分项)


class FeeConfig(BaseModel):
    """费用字段配置"""
    fields: List[str] = Field(default_factory=list)  # 费用列名列表
    total_field: Optional[str] = None  # 预计算的总费用列
    calculate_total: bool = True  # 是否重新计算总费用

    # 费用字段到 Trade 模型的映射
    field_mapping: Dict[str, str] = Field(default_factory=lambda: {
        # 通用费用
        "佣金": "commission",
        "Commission": "commission",
        "平台使用费": "platform_fee",
        "Platform Fees": "platform_fee",
        "交收费": "clearing_fee",
        "Settlement Fees": "clearing_fee",
        "印花税": "stamp_duty",
        "Stamp Duty": "stamp_duty",
        "交易费": "transaction_fee",
        "Trading Fees": "transaction_fee",
        "证监会规费": "sec_fee",
        "SEC Fees": "sec_fee",
        # 期权费用
        "期权监管费": "option_regulatory_fee",
        "Options Regulatory Fees": "option_regulatory_fee",
        "期权清算费": "option_clearing_fee",
        "OCC Fees": "option_clearing_fee",
        # A股费用
        "过户费": "transfer_fee",
        "经手费": "handling_fee",
        "证管费": "regulation_fee",
    })


class ValidationRule(BaseModel):
    """验证规则"""
    field: str  # 字段名
    rule: str  # 规则类型: regex, range, enum, required, custom
    params: Dict[str, Any] = Field(default_factory=dict)  # 规则参数
    error_message: str = ""  # 错误信息
    level: str = "error"  # error 或 warning


class BrokerConfig(BaseModel):
    """券商配置主模式"""
    # 基本信息
    broker_id: str  # 唯一标识
    broker_name: str  # 英文名
    broker_name_cn: str  # 中文名
    version: str = "1.0"  # 配置版本

    # 文件格式
    encoding: EncodingType = EncodingType.UTF8
    delimiter: str = ","
    quote_char: str = '"'
    header_row: int = 0
    skip_rows: List[int] = Field(default_factory=list)

    # 格式检测
    detection: DetectionRule

    # 市场支持
    markets: List[MarketType] = Field(default_factory=lambda: [MarketType.US])
    default_market: MarketType = MarketType.US

    # 字段映射
    field_mappings: List[FieldMapping]

    # 费用配置
    fees: FeeConfig = Field(default_factory=FeeConfig)

    # 状态映射 (CSV值 -> TradeStatus)
    status_mapping: Dict[str, str] = Field(default_factory=lambda: {
        # 中文
        "全部成交": "filled",
        "部分成交": "partially_filled",
        "已撤单": "cancelled",
        "下单失败": "cancelled",
        "待成交": "pending",
        # 英文
        "Filled": "filled",
        "Partially Filled": "partially_filled",
        "Cancelled": "cancelled",
        "Pending": "pending",
    })

    # 方向映射 (CSV值 -> TradeDirection)
    direction_mapping: Dict[str, str] = Field(default_factory=lambda: {
        # 中文
        "买入": "buy",
        "卖出": "sell",
        "卖空": "sell_short",
        "买券还券": "buy_to_cover",
        "补券": "buy_to_cover",
        # 英文
        "Buy": "buy",
        "Sell": "sell",
        "Sell Short": "sell_short",
        "Buy to Cover": "buy_to_cover",
        # A股
        "证券买入": "buy",
        "证券卖出": "sell",
    })

    # 市场映射 (CSV值 -> MarketType)
    market_mapping: Dict[str, str] = Field(default_factory=lambda: {
        # 中文
        "美股": "us",
        "港股": "hk",
        "沪深": "cn",
        "沪A": "cn",
        "深A": "cn",
        # 英文
        "US": "us",
        "HK": "hk",
        "CN": "cn",
    })

    # 验证规则
    validations: List[ValidationRule] = Field(default_factory=list)

    # 钩子函数 (Python 函数路径)
    pre_process_hook: Optional[str] = None
    post_process_hook: Optional[str] = None

    @field_validator('broker_id')
    @classmethod
    def validate_broker_id(cls, v: str) -> str:
        """验证 broker_id 格式"""
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("broker_id 必须是字母数字下划线组合")
        return v.lower()

    def get_field_mapping(self, source_column: str) -> Optional[FieldMapping]:
        """根据源列名获取字段映射"""
        for mapping in self.field_mappings:
            if mapping.source == source_column:
                return mapping
            if source_column in mapping.aliases:
                return mapping
        return None

    def get_target_columns(self) -> Dict[str, str]:
        """获取所有 source -> target 的映射字典"""
        result = {}
        for mapping in self.field_mappings:
            result[mapping.source] = mapping.target
            for alias in mapping.aliases:
                result[alias] = mapping.target
        return result

    def get_required_fields(self) -> List[str]:
        """获取必填字段列表"""
        return [m.target for m in self.field_mappings if m.required]
