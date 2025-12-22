# utils/

一旦我所属的文件夹有所变化，请更新我

## 架构说明

通用工具函数层，包括时区转换、股票/期权代码解析等跨模块复用的功能。
遵循单一职责原则，每个工具专注解决一类问题。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出工具函数 |
| `timezone.py` | 时区工具 | 多市场时区转换（美东/港股/A股→UTC） |
| `symbol_parser.py` | 代码解析器 | 智能识别美股/港股/A股/期权代码 |
| `option_parser.py` | 期权解析器 | 解析期权代码：标的/到期日/行权价/类型 |

---

## 设计思路

将跨模块的通用功能抽取为独立工具，遵循单一职责原则。

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `timezone.py` | 时区转换工具 | ~205 |
| `symbol_parser.py` | 股票/期权代码解析 | ~270 |
| `option_parser.py` | 期权代码解析（简化版） | ~100 |

## timezone.py

处理多市场时区转换，统一存储为 UTC 时间。

### 支持的市场时区

| 市场 | 时区 | pytz 名称 |
|------|------|----------|
| 美股 | 美东时间 | America/New_York |
| 港股 | 香港时间 | Asia/Hong_Kong |
| 沪深 | 北京时间 | Asia/Shanghai |

### 核心函数

#### parse_datetime_with_timezone

解析带时区标记的时间字符串，转换为 UTC。

```python
from src.utils.timezone import parse_datetime_with_timezone

# 解析带时区标记的字符串
utc_time = parse_datetime_with_timezone("2025/11/03 09:38:46 (美东)")
# 结果: datetime(2025, 11, 3, 13, 38, 46, tzinfo=UTC)

# 使用时区提示
utc_time = parse_datetime_with_timezone("2025/11/03 09:38:46", timezone_hint='美股')
```

**支持的时区标记**:
- 美东、ET、EST、EDT → America/New_York
- 香港、HKT → Asia/Hong_Kong
- 中国、CST、Beijing → Asia/Shanghai

**支持的日期格式**:
- `2025/11/03 09:38:46`
- `2025-11-03 09:38:46`
- `2025/11/03 09:38`
- `2025-11-03 09:38`

#### utc_to_local

将 UTC 时间转换为本地市场时间。

```python
from src.utils.timezone import utc_to_local

local_time = utc_to_local(utc_dt, '美股')
# UTC 13:38 → 美东 09:38
```

#### is_market_open

判断给定时间市场是否开盘。

```python
from src.utils.timezone import is_market_open

is_open = is_market_open(dt, '美股')
# 美股: 9:30-16:00 美东时间，周一至周五
```

**交易时间**:
| 市场 | 交易时间 (本地) |
|------|---------------|
| 美股 | 09:30-16:00 |
| 港股 | 09:30-12:00, 13:00-16:00 |
| 沪深 | 09:30-11:30, 13:00-15:00 |

### 便捷函数

```python
from src.utils.timezone import parse_us_datetime, parse_hk_datetime, parse_cn_datetime

# 直接指定市场
utc_time = parse_us_datetime("2025/11/03 09:38:46")
utc_time = parse_hk_datetime("2025/11/03 11:38:00")
utc_time = parse_cn_datetime("2025/11/03 09:38:00")
```

## symbol_parser.py

识别和解析不同类型的交易品种。

### 支持的品种类型

| 类型 | SymbolType | 示例 |
|------|-----------|------|
| 美股 | US_STOCK | AAPL, TSLA |
| 港股 | HK_STOCK | 00700, 01810 |
| A股 | CN_STOCK | 600000, 000001 |
| 美股期权 | US_OPTION | AAPL250117C00150000 |
| 港股窝轮 | HK_WARRANT | 18099 |

### 核心函数

#### parse_symbol

智能解析 symbol，识别类型并提取信息。

```python
from src.utils.symbol_parser import parse_symbol

# 美股股票
info = parse_symbol('AAPL')
# {'type': 'us_stock', 'symbol': 'AAPL', 'is_option': False, ...}

# 美股期权
info = parse_symbol('AAPL250117C00150000')
# {
#     'type': 'us_option',
#     'symbol': 'AAPL250117C00150000',
#     'underlying_symbol': 'AAPL',
#     'expiration_date': date(2025, 1, 17),
#     'option_type': 'CALL',
#     'strike_price': 150.0,
#     'is_option': True
# }

# 港股股票
info = parse_symbol('00700', market='港股')
# {'type': 'hk_stock', 'symbol': '00700', 'is_option': False, ...}

# 港股窝轮
info = parse_symbol('18099', symbol_name='小米摩通五乙购B.C')
# {
#     'type': 'hk_warrant',
#     'symbol': '18099',
#     'underlying_symbol': '小米',
#     'option_type': 'CALL',
#     'is_option': True
# }
```

### 美股期权代码格式

```
AAPL250117C00150000
│    │     │ │
│    │     │ └── 行权价: 00150000 / 1000 = $150.00
│    │     └──── 期权类型: C=CALL, P=PUT
│    └────────── 到期日: 25/01/17 (2025年1月17日)
└─────────────── 标的: AAPL
```

### 辅助函数

```python
from src.utils.symbol_parser import (
    format_option_symbol,
    get_underlying_symbol,
    is_option_or_warrant
)

# 格式化期权代码
symbol = format_option_symbol('AAPL', date(2025,1,17), 'CALL', 150.0)
# 'AAPL250117C00150000'

# 获取标的代码
underlying = get_underlying_symbol(info)  # 'AAPL'

# 判断是否为期权/窝轮
is_opt = is_option_or_warrant(info)  # True
```

## option_parser.py

期权代码解析的简化版本（供 OptionTradeAnalyzer 使用）。

```python
from src.utils.option_parser import parse_option_code

info = parse_option_code('AAPL250117C00150000')
# {
#     'underlying': 'AAPL',
#     'expiry': date(2025, 1, 17),
#     'type': 'call',
#     'strike': 150.0
# }
```

## 识别规则

### 代码识别

```python
# 美股股票: 1-5个大写字母
r'^[A-Z]{1,5}$'

# 港股股票: 5位数字
r'^\d{5}$'

# A股股票: 6位数字
r'^\d{6}$'

# 美股期权: 标的 + 6位日期 + C/P + 8位行权价
r'^[A-Z]{1,5}\d{6}[CP]\d{8}$'
```

### 港股窝轮识别

代码为 5 位数字 + 名称包含以下关键词:
- 购、沽、认购、认沽
- Call、Put
- .C、.P

## 错误处理

```python
# 无效 symbol 返回 UNKNOWN 类型
info = parse_symbol('INVALID123')
# {'type': 'unknown', 'symbol': 'INVALID123', ...}

# NaN/None 值安全处理
info = parse_symbol(None)  # 返回 UNKNOWN
info = parse_symbol(float('nan'))  # 返回 UNKNOWN
```
