# data - 处理后数据目录

存放系统处理后的数据库文件和派生数据。

## 设计思路

所有处理后的数据统一存储在 SQLite 数据库中：

```
data/
├── README.md                # 本文档
└── tradingcoach.db          # SQLite 数据库 (~11MB)
```

## 数据库结构

### 核心表

| 表名 | 说明 | 记录数 |
|------|------|--------|
| trades | 原始交易记录 | ~1000+ |
| trade_quantities | 交易数量拆分 | ~1500+ |
| positions | FIFO 配对后的持仓 | ~500+ |
| market_data | 市场 OHLCV 数据 | ~50000+ |

### 表关系

```
trades (1) ──┬─→ (n) trade_quantities ──┬─→ (1) positions
             │                          │
             └──────────────────────────┘
                     FIFO 匹配

market_data ←── (symbol, date) ──→ positions
                 指标关联
```

### trades 表

原始交易记录：

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,          -- 证券代码
    symbol_name VARCHAR(100),              -- 证券名称
    direction VARCHAR(10) NOT NULL,        -- 买入/卖出
    order_price NUMERIC(15, 4),            -- 委托价格
    order_quantity INTEGER,                -- 委托数量
    filled_price NUMERIC(15, 4) NOT NULL,  -- 成交价格
    filled_quantity INTEGER NOT NULL,      -- 成交数量
    order_time DATETIME,                   -- 委托时间 (UTC)
    filled_time DATETIME NOT NULL,         -- 成交时间 (UTC)
    total_fee NUMERIC(15, 4),              -- 总手续费
    market VARCHAR(20),                    -- 交易市场
    currency VARCHAR(10),                  -- 币种
    remaining_quantity INTEGER,            -- 剩余未配对数量
    created_at DATETIME                    -- 创建时间
);
```

### positions 表

FIFO 配对后的持仓：

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,           -- 证券代码
    direction VARCHAR(10) NOT NULL,        -- long/short
    open_price NUMERIC(15, 4),             -- 开仓价格
    close_price NUMERIC(15, 4),            -- 平仓价格
    quantity INTEGER,                      -- 持仓数量
    open_date DATETIME,                    -- 开仓时间
    close_date DATETIME,                   -- 平仓时间
    status VARCHAR(20),                    -- open/closed

    -- 盈亏
    realized_pnl NUMERIC(15, 4),           -- 已实现盈亏
    net_pnl NUMERIC(15, 4),                -- 净盈亏 (扣除手续费)
    net_pnl_pct NUMERIC(10, 4),            -- 净盈亏百分比

    -- 评分
    entry_score NUMERIC(5, 2),             -- 入场评分
    exit_score NUMERIC(5, 2),              -- 出场评分
    trend_score NUMERIC(5, 2),             -- 趋势评分
    risk_score NUMERIC(5, 2),              -- 风险评分
    overall_score NUMERIC(5, 2),           -- 综合评分
    score_grade VARCHAR(5),                -- 评分等级 A/B/C/D/F

    -- 期权字段
    is_option BOOLEAN,                     -- 是否期权
    option_type VARCHAR(10),               -- call/put
    strike_price NUMERIC(15, 4),           -- 行权价
    expiry_date DATE,                      -- 到期日

    created_at DATETIME
);
```

### market_data 表

市场 OHLCV 和技术指标：

```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,           -- 证券代码
    date DATE NOT NULL,                    -- 交易日期

    -- OHLCV
    open NUMERIC(15, 4),
    high NUMERIC(15, 4),
    low NUMERIC(15, 4),
    close NUMERIC(15, 4),
    volume BIGINT,

    -- 技术指标
    rsi_14 NUMERIC(10, 4),                 -- RSI(14)
    macd NUMERIC(10, 4),                   -- MACD 线
    macd_signal NUMERIC(10, 4),            -- 信号线
    macd_histogram NUMERIC(10, 4),         -- 柱状图
    bb_upper NUMERIC(15, 4),               -- 布林带上轨
    bb_middle NUMERIC(15, 4),              -- 布林带中轨
    bb_lower NUMERIC(15, 4),               -- 布林带下轨
    atr_14 NUMERIC(10, 4),                 -- ATR(14)
    adx_14 NUMERIC(10, 4),                 -- ADX(14)
    ma_5 NUMERIC(15, 4),                   -- MA(5)
    ma_20 NUMERIC(15, 4),                  -- MA(20)
    ma_50 NUMERIC(15, 4),                  -- MA(50)

    created_at DATETIME,
    UNIQUE(symbol, date)
);
```

## 数据访问

### Python 访问

```python
from src.models.base import init_database, get_session
from src.models.position import Position
from src.models.trade import Trade

# 初始化
init_database('sqlite:///data/tradingcoach.db')
session = get_session()

# 查询
positions = session.query(Position).filter(
    Position.status == 'closed',
    Position.overall_score >= 80
).all()
```

### SQLite 命令行

```bash
# 打开数据库
sqlite3 data/tradingcoach.db

# 查看表结构
.schema positions

# 查询数据
SELECT symbol, COUNT(*) as cnt, SUM(net_pnl) as total_pnl
FROM positions
WHERE status = 'closed'
GROUP BY symbol
ORDER BY total_pnl DESC
LIMIT 10;

# 导出数据
.headers on
.mode csv
.output positions.csv
SELECT * FROM positions WHERE status = 'closed';
```

## 备份恢复

### 备份

```bash
# 复制文件
cp data/tradingcoach.db data/tradingcoach.db.backup

# 或使用 SQLite dump
sqlite3 data/tradingcoach.db .dump > backup.sql
```

### 恢复

```bash
# 从文件恢复
cp data/tradingcoach.db.backup data/tradingcoach.db

# 从 dump 恢复
sqlite3 data/tradingcoach.db < backup.sql
```

## 数据维护

### 重建数据库

```bash
# 完全重建（清空所有数据）
python scripts/init_db.py --rebuild

# 重新导入
python scripts/import_trades.py --file original_data/*.csv
python scripts/run_matching.py --all
python scripts/preload_market_data.py --all
python scripts/calculate_indicators.py --all
python scripts/score_positions.py --all
```

### 数据统计

```bash
# 查看数据库大小
ls -lh data/tradingcoach.db

# 查看表记录数
sqlite3 data/tradingcoach.db "SELECT 'trades', COUNT(*) FROM trades UNION ALL SELECT 'positions', COUNT(*) FROM positions UNION ALL SELECT 'market_data', COUNT(*) FROM market_data;"
```

## 注意事项

- 数据库文件不应提交到版本控制 (已在 .gitignore)
- 定期备份重要数据
- 大批量操作前先备份
