# configs/ - 券商配置

> 一旦我所属的文件夹有所变化，请更新我

## 架构说明

存放券商 CSV 格式的 YAML 配置文件。每个券商一个配置文件，
定义字段映射、枚举转换、验证规则等，实现零代码添加新券商支持。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出配置类 |
| `schema.py` | 配置模式 | Pydantic 验证 YAML 配置结构 |
| `_template.yaml` | 模板文件 | 新券商配置模板 |
| `futu_cn.yaml` | 富途中文 | 富途证券中文 CSV 配置 |
| `futu_en.yaml` | 富途英文 | 富途证券英文 CSV 配置 |
| `tiger_cn.yaml` | 老虎中文 | 老虎证券中文 CSV 配置 |
| `citic_cn.yaml` | 中信证券 | 中信证券中文 CSV 配置（A股） |
| `huatai_cn.yaml` | 华泰证券 | 华泰证券中文 CSV 配置（A股） |

---

## 配置结构

### 基本信息

```yaml
broker_id: futu_cn           # 唯一标识，小写+下划线
broker_name: Futu Securities  # 英文名称
broker_name_cn: 富途证券       # 中文名称
version: "1.0"
```

### 文件格式

```yaml
encoding: utf-8-sig          # 编码: utf-8, utf-8-sig, gb18030, gbk
delimiter: ","               # 分隔符
quote_char: '"'              # 引号字符
header_row: 0                # 表头行号 (0-based)
skip_rows: []                # 跳过的行号列表
```

### 自动检测规则

```yaml
detection:
  columns:                   # 特征列 (用于识别此格式)
    - "方向"
    - "代码"
    - "成交时间"
  unique_columns:            # 此券商特有的列 (加分项)
    - "平台使用费"
  encoding_hint: utf-8-sig   # 建议的编码
  confidence_threshold: 0.8  # 最低置信度阈值
```

### 字段映射

```yaml
field_mappings:
  - source: "方向"           # CSV 列名
    target: direction        # Trade 模型字段名
    required: true           # 是否必填
    aliases:                 # 备选列名
      - "交易方向"
      - "买卖"

  - source: "成交价格"
    target: filled_price
    required: true
    transform:
      type: number           # 数据类型转换

  - source: "成交时间"
    target: filled_time
    required: true
    transform:
      type: datetime
      format: "%Y/%m/%d %H:%M:%S"
```

### 枚举映射

```yaml
# 交易方向
direction_mapping:
  买入: buy
  卖出: sell
  卖空: sell_short
  买券还券: buy_to_cover

# 交易状态
status_mapping:
  全部成交: filled
  部分成交: partially_filled
  已撤单: cancelled
  待成交: pending

# 市场类型
market_mapping:
  美股: us
  港股: hk
  沪深: cn
```

### 费用配置

```yaml
fees:
  fields:                    # 费用列名列表
    - 佣金
    - 印花税
    - 过户费
  total_field: "合计费用"     # 预计算的总费用列
  calculate_total: false     # 是否重新计算总费用
  field_mapping:             # 费用列到模型字段的映射
    佣金: commission
    过户费: transfer_fee
```

### 验证规则

```yaml
validations:
  - field: filled_quantity
    rule: range
    params:
      min: 1
    error_message: "成交数量必须大于0"
    level: error             # error 或 warning

  - field: symbol
    rule: regex
    params:
      pattern: "^[A-Z0-9]+$"
    error_message: "代码格式无效"
    level: warning
```

---

## 支持的转换类型

| 类型 | 说明 | 参数 |
|------|------|------|
| `string` | 字符串 | strip, uppercase, lowercase, default |
| `number` | 浮点数 | - |
| `integer` | 整数 | - |
| `datetime` | 日期时间 | format, timezone |
| `date` | 日期 | format |
| `boolean` | 布尔值 | - |
| `enum` | 枚举映射 | mapping |

---

## 添加新券商

1. 复制 `_template.yaml` 为 `<broker_id>.yaml`
2. 填写基本信息和文件格式
3. 配置 `detection.columns` 用于自动检测
4. 定义字段映射 `field_mappings`
5. 配置枚举映射 (direction/status/market)
6. 可选：添加验证规则

### 示例：中信证券配置

```yaml
broker_id: citic
broker_name: CITIC Securities
broker_name_cn: 中信证券
version: "1.0"

encoding: gb18030
delimiter: ","

detection:
  columns:
    - "证券代码"
    - "买卖方向"
    - "成交价格"
    - "成交数量"
  unique_columns:
    - "股东代码"
    - "席位代码"

field_mappings:
  - source: "证券代码"
    target: symbol
    required: true
  - source: "买卖方向"
    target: direction
    required: true
  - source: "成交价格"
    target: filled_price
    transform:
      type: number
  - source: "成交数量"
    target: filled_quantity
    transform:
      type: integer
  - source: "成交时间"
    target: filled_time
    transform:
      type: datetime
      format: "%Y%m%d %H:%M:%S"
  - source: "股东代码"
    target: shareholder_code
  - source: "席位代码"
    target: seat_code

direction_mapping:
  买入: buy
  卖出: sell
  融资买入: buy
  融券卖出: sell_short

status_mapping:
  成交: filled
  部成: partially_filled

market_mapping:
  上海A: cn
  深圳A: cn
```
