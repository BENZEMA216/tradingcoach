# importers - 数据导入层

> 一旦我所属的文件夹有所变化，请更新我

负责解析券商导出的 CSV 交易记录，并清洗转换为标准格式存入数据库。

## 架构概述

v2.0 引入了**适配器系统**，支持 YAML 配置驱动的券商格式解析：

```
原始 CSV → AdapterRegistry (自动检测) → BrokerAdapter (解析/映射) → Trade 模型
```

同时保留**兼容模式**支持旧的解析流程：
```
原始 CSV → CSVParser/EnglishCSVParser → DataCleaner → Trade 模型
```

## 目录结构

```
importers/
├── core/                   # 核心框架
│   ├── base_adapter.py     # 适配器基类
│   ├── adapter_registry.py # 适配器注册表
│   └── field_transformer.py# 字段转换器
├── configs/                # YAML 配置
│   ├── schema.py           # Pydantic 配置模式
│   ├── futu_cn.yaml        # 富途中文配置
│   ├── futu_en.yaml        # 富途英文配置
│   └── _template.yaml      # 新券商模板
├── adapters/               # 券商适配器
│   ├── generic_adapter.py  # 通用适配器
│   └── futu_adapter.py     # 富途专用适配器
├── transforms/             # 数据转换器
│   └── __init__.py
├── csv_parser.py           # [兼容] 中文CSV解析器
├── english_csv_parser.py   # [兼容] 英文CSV解析器
├── data_cleaner.py         # [兼容] 数据清洗器
└── incremental_importer.py # 增量导入控制器
```

## 文件清单

| 文件/目录 | 角色 | 功能 |
|-----------|------|------|
| `core/base_adapter.py` | 适配器基类 | 定义解析流程、字段映射、验证、指纹计算 |
| `core/adapter_registry.py` | 注册表 | 适配器注册、自动格式检测、配置加载 |
| `core/field_transformer.py` | 转换器 | 数据类型转换（日期、数值、枚举等） |
| `configs/schema.py` | 配置模式 | Pydantic 验证 YAML 配置结构 |
| `configs/*.yaml` | 券商配置 | 字段映射、枚举映射、验证规则 |
| `adapters/generic_adapter.py` | 通用适配器 | 纯 YAML 驱动的解析器 |
| `adapters/futu_adapter.py` | 富途适配器 | 期权符号解析等专有逻辑 |
| `incremental_importer.py` | 导入控制器 | 增量导入、去重、历史记录，批量插入优化（batch_size=500） |
| `csv_parser.py` | [兼容] 中文解析 | 旧版富途中文 CSV 解析 |
| `english_csv_parser.py` | [兼容] 英文解析 | 旧版富途英文 CSV 解析 |
| `data_cleaner.py` | [兼容] 数据清洗 | 时区转换、枚举映射、期权解析 |

## 使用方式

### 推荐：适配器模式

```python
from src.importers.incremental_importer import IncrementalImporter

# 自动检测格式
importer = IncrementalImporter(
    csv_path='trades.csv',
    dry_run=False,
    use_adapter=True  # 默认启用
)
result = importer.run()
print(f"新增: {result.new_trades}, 券商: {result.broker_name}")

# 指定券商 ID
importer = IncrementalImporter(
    csv_path='trades.csv',
    broker_id='futu_cn'  # 强制使用富途中文配置
)
```

### 命令行使用

```bash
# 自动检测格式导入
python -m src.importers.incremental_importer trades.csv

# 指定券商
python -m src.importers.incremental_importer trades.csv --broker-id futu_en

# 测试运行（不写数据库）
python -m src.importers.incremental_importer trades.csv --dry-run

# 禁用适配器系统（使用旧解析器）
python -m src.importers.incremental_importer trades.csv --no-adapter

# 列出可用券商
python -m src.importers.incremental_importer --list-brokers
```

### 直接使用适配器

```python
from src.importers.core.adapter_registry import AdapterRegistry

registry = AdapterRegistry()

# 自动检测
adapter, confidence = registry.detect_and_get_adapter('trades.csv')
if adapter:
    df = adapter.parse('trades.csv')
    completed = adapter.filter_completed_trades()
    stats = adapter.get_statistics()

# 指定券商
adapter = registry.get_adapter('futu_cn')
```

## 添加新券商

### 1. 创建 YAML 配置

复制 `configs/_template.yaml` 为 `configs/<broker_id>.yaml`，配置：

```yaml
broker_id: your_broker_id
broker_name: Your Broker Name
broker_name_cn: 你的券商名称

# 自动检测规则
detection:
  columns: ["方向", "代码", "成交时间"]  # 特征列
  unique_columns: ["特有列"]             # 加分项
  confidence_threshold: 0.8

# 字段映射
field_mappings:
  - source: "方向"
    target: direction
    required: true
  - source: "成交价格"
    target: filled_price
    transform:
      type: number

# 枚举映射
direction_mapping:
  买入: buy
  卖出: sell

status_mapping:
  全部成交: filled
  已撤单: cancelled
```

### 2. (可选) 创建专用适配器

如果需要特殊解析逻辑（如期权符号解析）：

```python
# adapters/your_broker_adapter.py
from ..core.base_adapter import BaseCSVAdapter

class YourBrokerAdapter(BaseCSVAdapter):
    @classmethod
    def get_broker_id(cls) -> str:
        return "your_broker_id"

    def _process_option_symbols(self, df):
        # 自定义逻辑
        pass
```

### 3. 注册适配器

```python
# adapters/__init__.py
from .your_broker_adapter import YourBrokerAdapter
from ..core.adapter_registry import registry

registry.register(YourBrokerAdapter)
```

## 适配器解析流程

```
┌────────────────────────────────────────────────────────────┐
│                    CSV 文件                                 │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│            1. AdapterRegistry.detect_and_get_adapter()     │
│               - 尝试多种编码读取样本                         │
│               - 遍历所有配置计算置信度                       │
│               - 返回最佳匹配的适配器                         │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│            2. Adapter.parse()                              │
│               - 读取 CSV (处理编码)                         │
│               - 字段映射 (source → target)                  │
│               - 数据转换 (string → datetime/number)         │
│               - 枚举映射 (方向/状态/市场)                    │
│               - 费用处理                                     │
│               - 验证规则                                     │
│               - 计算指纹 (SHA256)                            │
│               - 添加元数据 (broker_id, batch_id)            │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│            3. filter_completed_trades()                    │
│               - 过滤 status in ['filled', 'partially_filled']│
└────────────────────────┬───────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────┐
│            4. IncrementalImporter._incremental_import()    │
│               - 比对指纹去重                                 │
│               - 创建 Trade 对象                              │
│               - 写入数据库                                   │
└────────────────────────────────────────────────────────────┘
```

## 支持的券商

| broker_id | 名称 | 市场 | 状态 |
|-----------|------|------|------|
| futu_cn | 富途证券(中文) | 美/港/A | ✅ 完整支持 |
| futu_en | 富途证券(英文) | 美/港/A | ✅ 完整支持 |
| citic | 中信证券 | A股 | 🔜 计划中 |
| huatai | 华泰证券 | A股 | 🔜 计划中 |
| eastmoney | 东方财富 | A股 | 🔜 计划中 |
| tiger | 老虎证券 | 美/港 | 🔜 计划中 |
| ibkr | 盈透证券 | 全球 | 🔜 计划中 |

## 兼容模式

如需使用旧解析器：

```python
# 禁用适配器
importer = IncrementalImporter(
    csv_path='trades.csv',
    use_adapter=False
)

# 或直接使用旧解析器
from src.importers.csv_parser import CSVParser
from src.importers.data_cleaner import DataCleaner

parser = CSVParser('trades.csv')
df = parser.parse()
cleaner = DataCleaner(df)
cleaned_df = cleaner.clean()
```
