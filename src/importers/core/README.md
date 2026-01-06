# core/ - 适配器核心框架

> 一旦我所属的文件夹有所变化，请更新我

## 架构说明

定义 CSV 适配器系统的核心抽象层。提供基类、注册表、字段转换器，
支持 YAML 配置驱动的券商格式解析。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出核心类 |
| `base_adapter.py` | 适配器基类 | 定义解析流程、字段映射、验证、指纹计算 |
| `adapter_registry.py` | 注册表 | 适配器注册、自动格式检测、配置加载 |
| `field_transformer.py` | 转换器 | 数据类型转换（日期、数值、枚举等） |

---

## BaseCSVAdapter

所有券商适配器的抽象基类，定义标准解析流程：

```
读取CSV → 字段映射 → 数据转换 → 枚举映射 → 费用处理 → 验证 → 指纹计算 → 元数据
```

### 核心方法

```python
class BaseCSVAdapter(ABC):
    def parse(self, file_path: str) -> pd.DataFrame:
        """完整解析流程"""

    def filter_completed_trades(self) -> pd.DataFrame:
        """过滤已成交订单"""

    def set_import_batch_id(self, batch_id: str):
        """设置外部导入批次ID"""

    @classmethod
    def can_parse(cls, file_path, sample_df, config) -> Tuple[bool, float]:
        """判断是否能解析此文件，返回(能否解析, 置信度)"""

    @classmethod
    @abstractmethod
    def get_broker_id(cls) -> str:
        """返回券商唯一标识"""
```

### 解析流程

1. `_read_csv()`: 读取文件，处理编码
2. `_map_fields()`: 根据配置映射列名
3. `_transform_fields()`: 数据类型转换
4. `_apply_enum_mappings()`: 方向/状态/市场枚举映射
5. `_process_fees()`: 费用字段处理
6. `_validate()`: 执行验证规则
7. `_calculate_fingerprints()`: 计算交易指纹
8. `_add_metadata()`: 添加 broker_id, batch_id 等

---

## AdapterRegistry

单例模式的适配器注册表，管理所有券商适配器。

### 核心功能

```python
class AdapterRegistry:
    def get_adapter(self, broker_id: str) -> BaseCSVAdapter:
        """通过ID获取适配器"""

    def detect_and_get_adapter(self, file_path: str) -> Tuple[BaseCSVAdapter, float]:
        """自动检测格式并返回最佳适配器"""

    def list_brokers(self) -> List[Dict]:
        """列出所有可用券商"""

    def register(self, adapter_cls: Type[BaseCSVAdapter]):
        """注册适配器类"""
```

### 自动检测算法

1. 尝试多种编码读取文件样本
2. 遍历所有配置，计算匹配置信度
3. 返回置信度最高的适配器

置信度计算：
```python
confidence = (匹配列数 / 期望列数) + 0.1 * (特有列匹配比例)
```

---

## FieldTransformer

数据类型转换器，支持多种转换规则：

| 类型 | 说明 | 示例 |
|------|------|------|
| `string` | 字符串处理 | strip, uppercase, lowercase |
| `number` | 数值转换 | 移除逗号、货币符号、百分号 |
| `integer` | 整数转换 | 四舍五入 |
| `datetime` | 日期时间 | 自动格式解析、时区转换 |
| `date` | 日期 | 提取日期部分 |
| `boolean` | 布尔值 | true/false, 1/0, yes/no |
| `enum` | 枚举映射 | 自定义值映射 |

### 使用示例

```python
from src.importers.core.field_transformer import FieldTransformer
from src.importers.configs.schema import FieldTransform, TransformType

transformer = FieldTransformer()

# 数值转换
transform = FieldTransform(type=TransformType.NUMBER)
series = transformer.transform_column(df['price'], transform, config)

# 日期转换
transform = FieldTransform(
    type=TransformType.DATETIME,
    format="%Y/%m/%d %H:%M:%S"
)
series = transformer.transform_column(df['time'], transform, config)
```

---

## 扩展指南

### 创建新适配器

```python
from src.importers.core.base_adapter import BaseCSVAdapter

class MyBrokerAdapter(BaseCSVAdapter):
    @classmethod
    def get_broker_id(cls) -> str:
        return "my_broker"

    def parse(self, file_path: str) -> pd.DataFrame:
        # 调用基类方法
        df = super().parse(file_path)
        # 自定义处理
        df = self._custom_processing(df)
        return df

    def _custom_processing(self, df):
        # 特殊解析逻辑
        pass
```

### 注册适配器

```python
from src.importers.core.adapter_registry import registry

registry.register(MyBrokerAdapter)
```
