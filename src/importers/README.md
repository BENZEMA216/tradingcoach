# importers - 数据导入层

负责解析券商导出的 CSV 交易记录，并清洗转换为标准格式存入数据库。

## 设计思路

采用流水线模式 (Pipeline Pattern)：

```
原始 CSV → CSVParser (解析) → DataCleaner (清洗) → Trade 模型
```

**关键设计决策**:
1. **字段映射**: 中文字段名映射为英文
2. **编码处理**: 支持 UTF-8 BOM 编码
3. **数据验证**: 过滤撤单/失败订单
4. **类型转换**: 字符串转数值、日期解析

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `csv_parser.py` | CSV 解析器，字段映射 | ~280 |
| `data_cleaner.py` | 数据清洗和转换 | ~200 |

## CSVParser

### 核心功能

1. **读取 CSV**: 处理 UTF-8 BOM 编码
2. **字段映射**: 50+ 中文字段 → 英文字段名
3. **数据统计**: 行数、状态分布、Symbol 列表
4. **数据验证**: 必填字段检查、数据类型验证

### 字段映射表 (部分)

| 中文字段 | 英文字段 | 说明 |
|---------|---------|------|
| 方向 | direction | buy/sell 等 |
| 代码 | symbol | 股票代码 |
| 成交价格 | filled_price | 实际成交价 |
| 成交数量 | filled_quantity | 实际成交量 |
| 成交时间 | filled_time | 精确到秒 |
| 合计费用 | total_fee | 所有费用之和 |

### 使用示例

```python
from src.importers.csv_parser import CSVParser, load_csv

# 完整用法
parser = CSVParser('original_data/交易记录.csv')
df = parser.parse()

# 获取统计信息
stats = parser.get_statistics()
print(f"总行数: {stats['total_rows']}")
print(f"已成交: {stats['completed_trades']}")
print(f"已撤单: {stats['cancelled_orders']}")

# 获取唯一 Symbol
symbols = parser.get_unique_symbols()

# 获取日期范围
start, end = parser.get_date_range()

# 便捷函数
df = load_csv('trades.csv', filter_completed=True)
```

## DataCleaner

### 核心功能

1. **过滤无效订单**: 撤单、下单失败
2. **标准化方向**: 买入→buy, 卖出→sell
3. **解析成交信息**: "100@12.34" → quantity=100, price=12.34
4. **时区转换**: 本地时间 → UTC
5. **数值清洗**: 移除千分位逗号
6. **期权解析**: 识别期权代码，提取标的/行权价/到期日

### 数据转换规则

**交易方向映射**:
```python
'买入' → TradeDirection.BUY
'卖出' → TradeDirection.SELL
'卖空' → TradeDirection.SELL_SHORT
'买入回补' → TradeDirection.BUY_TO_COVER
```

**市场类型映射**:
```python
'美股' → MarketType.US_STOCK
'港股' → MarketType.HK_STOCK
'沪深' → MarketType.CN_STOCK
```

### 使用示例

```python
from src.importers.data_cleaner import DataCleaner

cleaner = DataCleaner()

# 清洗单条记录
cleaned_record = cleaner.clean_record(raw_record)

# 批量清洗并保存
trades = cleaner.clean_and_save_all(df, session)

# 验证数据
errors = cleaner.validate(df)
if errors:
    print(f"发现 {len(errors)} 个错误")
```

## 数据流程

```
┌─────────────────────────────────────────────────────────────┐
│                    原始 CSV 文件                             │
│  方向, 代码, 成交价格, 成交数量, 成交时间, 合计费用...        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    CSVParser.parse()                         │
│  1. 读取文件 (UTF-8 BOM)                                     │
│  2. 字段映射 (中文 → 英文)                                   │
│  3. 返回 DataFrame                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    DataCleaner.clean()                       │
│  1. 过滤 (status == '全部成交')                              │
│  2. 标准化方向 (买入 → buy)                                  │
│  3. 解析成交信息                                             │
│  4. 数值类型转换                                             │
│  5. 时区转换 (→ UTC)                                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Trade 模型                                │
│  持久化到数据库 trades 表                                    │
└─────────────────────────────────────────────────────────────┘
```

## 支持的 CSV 格式

### 券商格式
- 长桥证券 (Longbridge)
- 富途证券 (Futu)
- 盈透证券 (Interactive Brokers) - 需适配

### 必需字段
- 方向/direction
- 代码/symbol
- 成交数量/filled_quantity
- 成交时间/filled_time
- 市场/market

### 可选字段
- 成交价格、订单价格
- 各类费用明细
- 期权相关字段

## 错误处理

```python
# CSVParser 错误
FileNotFoundError: "CSV file not found: xxx"
ValueError: "CSV not parsed yet"

# DataCleaner 错误
ValueError: "Unknown direction: xxx"
ValueError: "Invalid date format: xxx"
```

## 扩展新券商

1. 创建新的字段映射字典
2. 实现 `parse()` 方法适配格式差异
3. 添加相应的数据验证规则
