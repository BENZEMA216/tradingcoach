# adapters/ - 券商适配器

> 一旦我所属的文件夹有所变化，请更新我

## 架构说明

存放各券商的专用适配器实现。大多数券商可以使用 GenericAdapter 配合 YAML 配置，
仅需要特殊解析逻辑时才创建专用适配器。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出适配器类、注册到 Registry |
| `generic_adapter.py` | 通用适配器 | 纯 YAML 驱动，无自定义逻辑 |
| `futu_adapter.py` | 富途适配器 | 期权符号解析、中英文自动检测 |

---

## GenericAdapter

纯 YAML 配置驱动的通用适配器，适用于大多数券商：

```python
from src.importers.adapters.generic_adapter import GenericAdapter
from src.importers.configs.schema import BrokerConfig

# 加载配置
config = BrokerConfig(**yaml.safe_load(open('configs/my_broker.yaml')))

# 创建适配器
adapter = GenericAdapter(config)
df = adapter.parse('trades.csv')
```

### 何时使用 GenericAdapter

- CSV 格式标准，只需列名映射
- 无需特殊的数据处理逻辑
- 所有转换都可通过 YAML 配置表达

---

## FutuAdapter

富途证券专用适配器，包含以下特殊处理：

### 1. 中英文格式自动检测

```python
CN_MARKER_COLUMNS = {'方向', '代码', '名称', '成交时间', '市场', '交易状态'}
EN_MARKER_COLUMNS = {'Side', 'Symbol', 'Name', 'Fill Time', 'Markets', 'Status'}
```

### 2. 期权符号解析

```python
# 输入: NVDA260618C205
# 输出:
#   underlying_symbol = NVDA
#   expiration_date = 2026-06-18
#   option_type = CALL
#   strike_price = 205.0
```

### 使用示例

```python
from src.importers.adapters.futu_adapter import FutuAdapter
from src.importers.core.adapter_registry import registry

# 获取配置
config = registry.get_config('futu_cn')

# 创建适配器
adapter = FutuAdapter(config)
df = adapter.parse('futu_trades.csv')

# 期权信息已自动解析
print(df[['symbol', 'underlying_symbol', 'option_type', 'strike_price']])
```

---

## 创建新适配器

### 场景示例

- 期权符号格式特殊，需要自定义解析
- 日期格式非标准，需要预处理
- 有多个子账户，需要合并处理

### 实现步骤

1. 创建适配器类

```python
# adapters/my_broker_adapter.py
from ..core.base_adapter import BaseCSVAdapter
import pandas as pd

class MyBrokerAdapter(BaseCSVAdapter):
    @classmethod
    def get_broker_id(cls) -> str:
        return "my_broker"

    def parse(self, file_path: str) -> pd.DataFrame:
        # 1. 调用基类解析
        df = super().parse(file_path)

        # 2. 自定义后处理
        df = self._parse_special_format(df)

        return df

    def _parse_special_format(self, df: pd.DataFrame) -> pd.DataFrame:
        # 特殊处理逻辑
        return df

    @classmethod
    def can_parse(cls, file_path, sample_df, config):
        # 可选：自定义检测逻辑
        can, confidence = super().can_parse(file_path, sample_df, config)
        # 额外检测...
        return can, confidence
```

2. 注册适配器

```python
# adapters/__init__.py
from .my_broker_adapter import MyBrokerAdapter
from ..core.adapter_registry import registry

registry.register(MyBrokerAdapter)
```

3. 创建 YAML 配置

```yaml
# configs/my_broker.yaml
broker_id: my_broker
broker_name: My Broker
# ... 配置内容
```

---

## 适配器 vs YAML 配置

| 场景 | 方案 |
|------|------|
| 标准 CSV 格式 | 仅 YAML 配置 |
| 列名映射 + 类型转换 | 仅 YAML 配置 |
| 期权符号特殊解析 | YAML + 专用适配器 |
| 多文件合并 | 专用适配器 |
| 复杂预处理逻辑 | 专用适配器 |
| 条件性字段映射 | 专用适配器 |

---

## 当前支持的券商

| broker_id | 适配器 | 状态 |
|-----------|--------|------|
| futu_cn | FutuAdapter | ✅ 完整支持 |
| futu_en | FutuAdapter | ✅ 完整支持 |
| citic | GenericAdapter | 🔜 配置待完成 |
| huatai | GenericAdapter | 🔜 配置待完成 |
| eastmoney | GenericAdapter | 🔜 配置待完成 |
| tiger | - | 🔜 计划中 |
| ibkr | - | 🔜 计划中 |
