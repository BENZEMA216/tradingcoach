# fixtures - 测试数据固件

一旦我所属的文件夹有所变化，请更新我

## 架构说明

存放固定的测试数据，确保数据完整性测试可重复、与生产数据隔离。测试数据涵盖股票/期权、做多/做空、盈利/亏损等核心场景。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| test_data.sql | SQL 固件 | 固定的交易和持仓测试数据 |
| README.md | 文档 | 本文件 |

## 测试数据覆盖

### 交易记录 (20 条)

| ID | 场景 | 类型 | 方向 |
|----|------|------|------|
| 1-2 | AAPL 做多盈利 | 股票 | long |
| 3-4 | GOOGL 做多亏损 | 股票 | long |
| 5-6 | TSLA 做空盈利 | 股票 | short |
| 7-8 | NVDA 做空亏损 | 股票 | short |
| 9-10 | NVDA 期权盈利 | CALL | long |
| 11-12 | TSLA 期权亏损 | PUT | long |
| 13-14 | META 零费用 | 股票 | long |
| 15-16 | AMZN 日内交易 | 股票 | long |
| 17 | MSFT 未平仓 | 股票 | long |
| 18-20 | AMD 分批买入 | 股票 | long |

### 持仓记录 (10 条)

| ID | 场景 | PnL | 评分 |
|----|------|-----|------|
| 1 | 股票做多盈利 | +$1498 | B |
| 2 | 股票做多亏损 | -$501 | D |
| 3 | 股票做空盈利 | +$898.5 | C |
| 4 | 股票做空亏损 | -$1002 | F |
| 5 | 期权CALL盈利 | +$4743.5 | B |
| 6 | 期权PUT亏损 | -$3013 | F |
| 7 | 零费用交易 | +$200 | C |
| 8 | 日内交易 | +$61.5 | D |
| 9 | 未平仓 | N/A | N/A |
| 10 | 分批买入 | +$648.5 | B |

## 边界情况覆盖

- [x] 零费用交易 (Position 7)
- [x] 日内交易 (Position 8)
- [x] 未平仓持仓 (Position 9)
- [x] 分批买入 (Position 10)
- [x] 期权合约乘数 (Position 5, 6)
- [x] 做空盈利/亏损 (Position 3, 4)

## 使用方法

```python
# 在 conftest.py 中加载测试数据
import sqlite3
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

def load_test_data(connection):
    with open(FIXTURES_DIR / "test_data.sql") as f:
        connection.executescript(f.read())
```
