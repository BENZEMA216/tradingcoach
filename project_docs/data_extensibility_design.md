# 数据扩展性设计文档

## 1. 概述

本文档阐述交易复盘系统的数据扩展性设计方案，确保系统能够灵活集成多种外部数据源，支持未来功能迭代。

### 1.1 设计目标

- **可扩展性**: 预留接口和表结构，支持未来新增数据源
- **性能优化**: 通过分层架构和缓存机制优化查询性能
- **数据一致性**: 确保多源数据的时间对齐和关联准确性
- **解耦设计**: 外部数据模块与核心交易分析模块松耦合

## 2. 数据分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                     应用层 (Analysis Layer)                  │
│              交易质量评分、复盘报告、AI分析                    │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                  计算层 (Computation Layer)                  │
│         技术指标计算、交易配对、盈亏统计、风险指标             │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                   数据整合层 (Integration Layer)              │
│         时间对齐、数据关联、缓存管理、数据验证                 │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌──────────────┬──────────────┬──────────────┬────────────────┐
│  原始交易数据  │  市场行情数据  │  基本面数据   │  市场环境数据   │
│ (用户CSV)     │ (OHLCV)      │ (行业/财报)   │ (VIX/SPY等)   │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

### 2.1 分层说明

**数据源层 (Data Source Layer)**
- 原始交易数据: 用户券商导出的CSV文件
- 市场行情数据: 外部API获取的OHLCV和技术指标
- 基本面数据: 公司行业分类、财务指标
- 市场环境数据: 大盘指数、波动率指数

**数据整合层 (Integration Layer)**
- 时间对齐: 将不同数据源的时间戳统一到交易时间
- 数据关联: 建立交易记录与市场数据的关联关系
- 缓存管理: 三级缓存减少重复API调用
- 数据验证: 检查数据完整性和一致性

**计算层 (Computation Layer)**
- 技术指标计算: RSI, MACD, Bollinger Bands等
- 交易配对: FIFO算法匹配买入/卖出
- 盈亏统计: 计算已实现/未实现盈亏
- 风险指标: MAE, MFE, Sharpe Ratio等

**应用层 (Analysis Layer)**
- 交易质量评分: 四维度评分系统
- 复盘报告: 周期性报告生成
- AI分析: 模式识别、建议生成

## 3. 外部数据源分类

### 3.1 数据源类型

| 数据类型 | 用途 | 更新频率 | 优先级 |
|----------|------|----------|--------|
| **市场行情 (OHLCV)** | 技术指标计算 | 每日/实时 | P0 |
| **技术指标** | 交易质量评分 | 每日 | P0 |
| **市场环境** | 大盘背景分析 | 每日 | P1 |
| **基本面数据** | 行业分析 | 每周 | P2 |
| **新闻事件** | AI增强分析 | 实时 | P3 |

### 3.2 数据获取策略

**MVP阶段**:
- 市场行情: 使用免费API (yfinance)
- 技术指标: 本地计算 (pandas-ta/TA-Lib)
- 市场环境: 获取主要指数 (SPY, VIX)

**未来扩展**:
- 付费API: 更稳定的数据源 (Alpha Vantage, Polygon)
- 实时数据: WebSocket连接获取tick数据
- 新闻数据: 情绪分析整合

## 4. 数据库Schema设计

### 4.1 核心设计原则

1. **外键预留**: 为外部数据表预留关联字段
2. **JSON灵活字段**: 存储非结构化或频繁变化的数据
3. **时间序列优化**: 为时间范围查询建立索引
4. **分表策略**: 低频访问数据分离到单独表

### 4.2 表结构设计

#### 4.2.1 核心交易表 (trades)

```sql
CREATE TABLE trades (
    -- 主键和基础信息
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,

    -- 交易详情
    order_price DECIMAL(10, 4),
    filled_price DECIMAL(10, 4),
    order_quantity INTEGER,
    filled_quantity INTEGER,

    -- 时间信息
    filled_time TIMESTAMP NOT NULL,
    trade_date DATE GENERATED ALWAYS AS (DATE(filled_time)) STORED,

    -- 费用
    total_fee DECIMAL(10, 2),

    -- 扩展字段 (预留外键)
    market_data_id INTEGER,    -- 关联市场行情
    market_env_id INTEGER,     -- 关联市场环境
    matched_trade_id INTEGER,  -- 对应的平仓交易
    position_id INTEGER,       -- 所属持仓

    -- 灵活字段
    metadata JSON,  -- 期权详情、特殊事件等

    -- 索引
    INDEX idx_symbol (symbol),
    INDEX idx_filled_time (filled_time),
    INDEX idx_trade_date (trade_date)
);
```

#### 4.2.2 市场行情数据表 (market_data)

```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    timestamp TIMESTAMP NOT NULL,

    -- OHLCV数据
    open DECIMAL(10, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    close DECIMAL(10, 4),
    volume BIGINT,

    -- 技术指标 (预计算缓存)
    rsi_14 DECIMAL(6, 2),
    macd DECIMAL(10, 4),
    macd_signal DECIMAL(10, 4),
    bb_upper DECIMAL(10, 4),
    bb_middle DECIMAL(10, 4),
    bb_lower DECIMAL(10, 4),
    atr_14 DECIMAL(10, 4),
    ma_20 DECIMAL(10, 4),
    ma_50 DECIMAL(10, 4),

    -- 元数据
    data_source VARCHAR(20) DEFAULT 'yfinance',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 唯一约束
    UNIQUE (symbol, timestamp),
    INDEX idx_symbol_date (symbol, date)
);
```

#### 4.2.3 市场环境表 (market_environment)

```sql
CREATE TABLE market_environment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,

    -- 大盘指数
    spy_close DECIMAL(10, 2),
    spy_change_pct DECIMAL(6, 2),
    vix DECIMAL(6, 2),

    -- 市场趋势
    market_trend VARCHAR(20),  -- 'bullish' / 'neutral' / 'bearish'

    -- 行业强弱 (JSON存储)
    sector_performance JSON,

    INDEX idx_date (date)
);
```

#### 4.2.4 股票分类表 (stock_classifications)

```sql
CREATE TABLE stock_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL UNIQUE,

    -- 基本信息
    company_name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),

    -- 市值和估值
    market_cap BIGINT,
    pe_ratio DECIMAL(8, 2),

    -- 更新时间
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_sector (sector)
);
```

#### 4.2.5 持仓表 (positions)

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,

    -- 时间
    open_time TIMESTAMP NOT NULL,
    close_time TIMESTAMP,

    -- 持仓详情
    direction VARCHAR(10),
    open_price DECIMAL(10, 4),
    close_price DECIMAL(10, 4),
    quantity INTEGER,

    -- 盈亏
    realized_pnl DECIMAL(15, 2),
    net_pnl DECIMAL(15, 2),

    -- 质量评分
    entry_quality_score DECIMAL(5, 2),
    exit_quality_score DECIMAL(5, 2),
    overall_score DECIMAL(5, 2),

    -- 关联市场环境
    entry_market_env_id INTEGER,
    exit_market_env_id INTEGER,

    INDEX idx_symbol (symbol),
    INDEX idx_close_time (close_time)
);
```

#### 4.2.6 新闻事件表 (news_events) - 预留

```sql
CREATE TABLE news_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20),
    title TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,

    -- 情绪分析
    sentiment_score DECIMAL(4, 2),  -- -1.0 to 1.0
    sentiment_label VARCHAR(20),

    -- 重要性
    importance VARCHAR(20),

    INDEX idx_symbol_published (symbol, published_at)
);
```

### 4.3 数据关联设计

```
trades (交易记录)
    │
    ├──> market_data (symbol + filled_time)
    │       └──> 获取入场时的技术指标
    │
    ├──> market_environment (trade_date)
    │       └──> 获取当日市场背景
    │
    ├──> stock_classifications (symbol)
    │       └──> 获取行业分类
    │
    └──> positions (position_id)
            └──> 所属持仓

positions (持仓)
    │
    ├──> trades (一对多)
    │       └──> 组成该持仓的所有交易
    │
    └──> market_environment (entry/exit)
            └──> 开仓和平仓时的市场环境
```

## 5. 扩展性保障机制

### 5.1 Schema演进策略

**添加新数据源时的步骤**:

1. **创建新表**: 设计独立的外部数据表
2. **添加外键字段**: 在trades或positions表添加关联字段
3. **保持向后兼容**: 新字段允许NULL值
4. **数据迁移脚本**: 提供历史数据回填工具

**示例：添加期权Greeks数据**

```sql
-- 第一步：创建新表
CREATE TABLE option_greeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    delta DECIMAL(6, 4),
    gamma DECIMAL(6, 4),
    theta DECIMAL(6, 4),
    vega DECIMAL(6, 4),
    UNIQUE (symbol, date)
);

-- 第二步：添加外键 (可选)
ALTER TABLE trades ADD COLUMN option_greeks_id INTEGER;

-- 第三步：建立关联查询视图
CREATE VIEW trades_with_greeks AS
SELECT t.*, og.delta, og.gamma, og.theta, og.vega
FROM trades t
LEFT JOIN option_greeks og
    ON t.symbol = og.symbol
    AND t.trade_date = og.date;
```

### 5.2 JSON字段使用规范

**适用场景**:
- 非核心查询字段
- 结构频繁变化的数据
- 特定symbol的特殊属性

**示例：trades.metadata字段**

```json
{
  "option_details": {
    "contract_type": "CALL",
    "strike_price": 180.0,
    "expiration_date": "2024-12-20",
    "implied_volatility": 0.35
  },
  "special_events": {
    "earnings_report": true,
    "stock_split": false
  },
  "notes": "财报前一天开仓"
}
```

**查询JSON字段** (SQLite 3.38+):

```sql
-- 查询所有看涨期权交易
SELECT * FROM trades
WHERE json_extract(metadata, '$.option_details.contract_type') = 'CALL';

-- 查询财报日交易
SELECT * FROM trades
WHERE json_extract(metadata, '$.special_events.earnings_report') = 1;
```

### 5.3 版本控制与迁移

使用Alembic进行数据库版本管理:

```python
# migrations/versions/001_initial_schema.py
def upgrade():
    op.create_table('trades', ...)
    op.create_table('market_data', ...)

def downgrade():
    op.drop_table('market_data')
    op.drop_table('trades')

# migrations/versions/002_add_news_events.py
def upgrade():
    op.create_table('news_events', ...)
    op.add_column('trades', sa.Column('news_event_id', sa.Integer))

def downgrade():
    op.drop_column('trades', 'news_event_id')
    op.drop_table('news_events')
```

## 6. 数据同步策略

### 6.1 增量更新原则

- **历史数据**: 一次性获取并缓存
- **日常更新**: 仅获取最新日期到今天的数据
- **重要事件**: 触发特定symbol的数据刷新

### 6.2 时间对齐策略

**问题**: 不同市场的交易时间不同
- 美股: 美东时间 9:30-16:00
- 港股: 香港时间 9:30-16:00
- A股: 北京时间 9:30-15:00

**解决方案**:
1. 所有时间戳存储为UTC
2. 查询时根据市场类型转换时区
3. 技术指标计算使用交易日概念

```python
# 时间对齐示例
from datetime import datetime
import pytz

def align_trade_to_market_data(trade_time, market):
    """将交易时间对齐到市场数据时间"""
    if market == '美股':
        tz = pytz.timezone('America/New_York')
    elif market == '港股':
        tz = pytz.timezone('Asia/Hong_Kong')

    # 转换为本地时间
    local_time = trade_time.astimezone(tz)

    # 取当日收盘数据
    market_date = local_time.date()

    return market_date
```

## 7. 性能考虑

### 7.1 索引策略

**复合索引** - 常用联合查询:
```sql
CREATE INDEX idx_market_data_lookup ON market_data(symbol, date);
CREATE INDEX idx_trades_analysis ON trades(symbol, filled_time, direction);
```

**覆盖索引** - 包含所有查询字段:
```sql
CREATE INDEX idx_positions_summary ON positions(
    symbol, close_time, realized_pnl, overall_score
) WHERE close_time IS NOT NULL;
```

### 7.2 查询优化

**使用JOIN代替多次查询**:
```sql
-- 好：一次查询获取交易和市场环境
SELECT t.*, me.vix, me.market_trend
FROM trades t
LEFT JOIN market_environment me ON t.trade_date = me.date
WHERE t.symbol = 'AAPL';

-- 差：两次查询
SELECT * FROM trades WHERE symbol = 'AAPL';
SELECT * FROM market_environment WHERE date IN (...);
```

### 7.3 分区策略 (未来扩展)

当数据量增长后，考虑按时间分区:

```sql
-- PostgreSQL分区示例
CREATE TABLE market_data (
    symbol VARCHAR(20),
    date DATE,
    ...
) PARTITION BY RANGE (date);

CREATE TABLE market_data_2024 PARTITION OF market_data
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE market_data_2025 PARTITION OF market_data
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

## 8. 未来扩展路径

### 8.1 数据库迁移路径

**阶段1: SQLite (MVP)**
- 适用场景: 单用户，数据量 < 1GB
- 优势: 零配置，文件数据库

**阶段2: PostgreSQL**
- 迁移时机: 数据量 > 1GB 或需要多用户
- 迁移工具: SQLAlchemy ORM保证兼容性

**阶段3: TimescaleDB**
- 迁移时机: 需要高频数据或复杂时间序列查询
- 优势: 时间序列优化，压缩存储

### 8.2 实时数据集成

**WebSocket数据流**:
```
外部API (WebSocket)
    │
    ▼
消息队列 (Redis/RabbitMQ)
    │
    ▼
实时处理器 (Python)
    │
    ▼
数据库 (热数据) + 缓存
```

### 8.3 机器学习特征库

预留ML特征计算接口:
```sql
CREATE TABLE ml_features (
    id INTEGER PRIMARY KEY,
    position_id INTEGER,
    feature_vector JSON,  -- 存储特征向量
    model_version VARCHAR(20),
    created_at TIMESTAMP
);
```

## 9. 总结

### 9.1 核心设计思想

1. **分层解耦**: 数据源、整合、计算、应用四层分离
2. **灵活扩展**: 外键预留 + JSON字段
3. **性能优先**: 预计算缓存 + 合理索引
4. **平滑演进**: 版本管理 + 向后兼容

### 9.2 MVP实现范围

| 组件 | MVP状态 | 说明 |
|------|---------|------|
| trades表 | ✓ 实现 | 核心交易记录 |
| market_data表 | ✓ 实现 | OHLCV + 技术指标 |
| market_environment表 | ✓ 实现 | SPY + VIX |
| stock_classifications表 | ✓ 实现 | 基础行业分类 |
| positions表 | ✓ 实现 | 持仓管理 |
| news_events表 | ✗ 预留 | 未来迭代 |

---

**文档版本**: v1.0
**创建日期**: 2025-11-16
**相关文档**:
- `technical_indicators_research.md` - 技术指标研究
- `technical_implementation_plan.md` - 技术实现方案
