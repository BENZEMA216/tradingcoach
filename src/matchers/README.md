# matchers/

一旦我所属的文件夹有所变化，请更新我

## 架构说明

FIFO交易配对引擎，将原子交易记录配对为完整持仓周期。支持做多/做空配对、
部分成交处理、跨日持仓追踪。按标的分组独立配对，输出Position记录。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出配对器类 |
| `fifo_matcher.py` | 总协调器 | 按标的分组、调度SymbolMatcher、汇总结果，add_all批量插入优化 |
| `symbol_matcher.py` | 单标的配对器 | FIFO核心算法实现，处理做多/做空 |
| `trade_quantity.py` | 数量追踪器 | 追踪交易剩余数量，支持部分配对 |

---

## 设计思路

### 核心概念

**问题**: 原始交易记录是独立的买卖操作，需要配对成完整的持仓周期才能计算盈亏。

**解决方案**: FIFO 算法 - 按时间顺序，先买入的先卖出。

```
交易记录:
  [T1] 买入 AAPL 100股 @150
  [T2] 买入 AAPL  50股 @155
  [T3] 卖出 AAPL 120股 @160

FIFO 配对结果:
  [P1] 买100@150 → 卖100@160 (盈利 $1000)
  [P2] 买 20@155 → 卖 20@160 (盈利 $100)
  [P3] 持有 30股 @155 (未平仓)
```

### 架构设计

```
FIFOMatcher (总协调器)
    │
    ├── SymbolMatcher (AAPL)
    │       └── TradeQuantity (数量追踪)
    │
    ├── SymbolMatcher (TSLA)
    │       └── TradeQuantity
    │
    └── SymbolMatcher (...)
```

## 文件说明

| 文件 | 说明 | 行数 |
|------|------|------|
| `fifo_matcher.py` | 总协调器，管理所有标的配对 | ~300 |
| `symbol_matcher.py` | 单标的配对器，核心算法 | ~400 |
| `trade_quantity.py` | 交易数量追踪器 | ~100 |

## FIFOMatcher

总协调器，负责：
1. 加载所有已完成交易
2. 按标的分组
3. 按时间顺序处理
4. 保存持仓到数据库

### 使用示例

```python
from src.matchers.fifo_matcher import FIFOMatcher, match_trades_from_database

session = get_session()

# 完整用法
matcher = FIFOMatcher(session, dry_run=False)
result = matcher.match_all_trades()

print(f"处理交易: {result['total_trades']}")
print(f"生成持仓: {result['positions_created']}")
print(f"已平仓: {result['closed_positions']}")
print(f"未平仓: {result['open_positions']}")

# 便捷函数
result = match_trades_from_database(session)
```

### 配对流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 加载交易                                            │
│  SELECT * FROM trades WHERE status='filled' ORDER BY time    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 按标的分组                                          │
│  AAPL: [T1, T3, T5]                                          │
│  TSLA: [T2, T4, T6]                                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 每个标的独立配对 (SymbolMatcher)                    │
│  维护买入队列，遇到卖出时 FIFO 配对                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: 生成 Position 记录                                  │
│  计算盈亏、持仓天数等                                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: 保存到数据库                                        │
│  批量 INSERT positions                                       │
└─────────────────────────────────────────────────────────────┘
```

## SymbolMatcher

单标的配对器，实现 FIFO 核心算法。

### 支持的配对场景

| 场景 | 开仓方向 | 平仓方向 | 说明 |
|------|---------|---------|------|
| 做多 | BUY | SELL | 先买后卖 |
| 做空 | SELL_SHORT | BUY_TO_COVER | 先卖后买 |
| 部分平仓 | - | - | 一笔大单拆分配对多笔小单 |

### 算法详解

```python
# 伪代码
long_queue = []   # 做多开仓队列 (BUY)
short_queue = []  # 做空开仓队列 (SELL_SHORT)

def process_trade(trade):
    if trade.direction == BUY:
        long_queue.append(trade)

    elif trade.direction == SELL:
        # FIFO: 从队列头部取出匹配
        while sell_quantity > 0 and long_queue:
            open_trade = long_queue[0]
            matched_qty = min(sell_quantity, open_trade.remaining)

            create_position(open_trade, trade, matched_qty)

            open_trade.remaining -= matched_qty
            sell_quantity -= matched_qty

            if open_trade.remaining == 0:
                long_queue.pop(0)
```

### 使用示例

```python
from src.matchers.symbol_matcher import SymbolMatcher

matcher = SymbolMatcher('AAPL')

# 处理交易
for trade in trades:
    positions = matcher.process_trade(trade)

# 完成配对，处理未平仓
open_positions = matcher.finalize_open_positions()

# 获取统计
stats = matcher.get_statistics()
```

## TradeQuantity

辅助类，追踪交易的剩余数量（用于部分配对）。

```python
from src.matchers.trade_quantity import TradeQuantity

tq = TradeQuantity(trade)
print(f"原始数量: {tq.original_quantity}")
print(f"剩余数量: {tq.remaining_quantity}")

# 消耗数量
tq.consume(50)
print(f"已配对: {tq.matched_quantity}")
```

## 边界情况处理

### 1. 部分成交

```
买入 100股 @150
卖出  60股 @160   → Position 1 (60股)
卖出  40股 @165   → Position 2 (40股)
```

### 2. 跨日持仓

自动计算持仓天数和小时数。

### 3. 期权配对

期权交易正常参与配对，标的代码保持完整期权代码。

### 4. 做空配对

```
SELL_SHORT 100股 @150  (开仓)
BUY_TO_COVER 100股 @140  (平仓)
→ Position (short, 盈利 $1000)
```

## 配置选项

```python
matcher = FIFOMatcher(
    session=session,
    dry_run=True  # 演练模式，不保存到数据库
)
```

## 输出统计

```python
{
    'total_trades': 500,        # 处理的交易总数
    'positions_created': 200,   # 生成的持仓数
    'closed_positions': 180,    # 已平仓
    'open_positions': 20,       # 未平仓
    'symbols_processed': 50,    # 处理的标的数
    'warnings': [...]           # 异常情况警告
}
```
