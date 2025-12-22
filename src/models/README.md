# models/

一旦我所属的文件夹有所变化，请更新我

## 架构说明

SQLAlchemy ORM 数据模型定义层。定义核心业务实体（Trade/Position/MarketData），
建立表间关系映射，提供数据库会话管理。是整个系统的数据基础。

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `__init__.py` | 模块入口 | 导出所有模型类 |
| `base.py` | 数据库基础 | 连接管理、Session工厂、Base类定义 |
| `trade.py` | 交易模型 | 原子交易记录：买卖方向、价格、数量、费用 |
| `position.py` | 持仓模型 | 配对后持仓：盈亏、评分、期权扩展字段 |
| `market_data.py` | 市场数据模型 | OHLCV数据、技术指标字段 |
| `market_environment.py` | 市场环境模型 | 趋势状态、波动率、市场情绪快照 |
| `stock_classification.py` | 股票分类模型 | 板块、行业、市值分类 |

---

## 设计思路

采用领域驱动设计 (DDD) 思想，将业务实体映射为数据库表：

- **Trade**: 原子交易记录，每笔买卖操作
- **Position**: 配对后的持仓周期，包含盈亏和评分
- **MarketData**: 市场 OHLCV 数据和技术指标
- **MarketEnvironment**: 市场环境快照（趋势、波动率等）

## 文件说明

| 文件 | 说明 |
|------|------|
| `base.py` | 数据库连接管理、Session 工厂 |
| `trade.py` | 交易记录模型 |
| `position.py` | 持仓记录模型（含期权扩展字段） |
| `market_data.py` | 市场数据和技术指标模型 |
| `market_environment.py` | 市场环境模型 |
| `stock_classification.py` | 股票分类模型 |

## 核心模型

### Trade (交易记录)

```python
class Trade(Base):
    # 基本信息
    symbol: str              # 股票代码
    direction: TradeDirection  # 交易方向 (buy/sell/sell_short/buy_to_cover)
    status: TradeStatus      # 交易状态 (filled/cancelled/pending)

    # 成交信息
    filled_price: Decimal    # 成交价格
    filled_quantity: int     # 成交数量
    filled_time: datetime    # 成交时间

    # 费用明细
    commission: Decimal      # 佣金
    total_fee: Decimal       # 合计费用

    # 期权信息
    is_option: int           # 是否期权 (0/1)
    underlying_symbol: str   # 标的代码
    strike_price: Decimal    # 行权价
    expiration_date: date    # 到期日
```

**枚举类型**:
- `TradeDirection`: BUY, SELL, SELL_SHORT, BUY_TO_COVER
- `TradeStatus`: FILLED, PARTIALLY_FILLED, CANCELLED, PENDING
- `MarketType`: US_STOCK, HK_STOCK, CN_STOCK

### Position (持仓记录)

```python
class Position(Base):
    # 基本信息
    symbol: str              # 股票代码
    direction: str           # 方向 (long/short)
    status: PositionStatus   # 状态 (open/closed)

    # 开平仓信息
    open_price: Decimal      # 开仓价格
    close_price: Decimal     # 平仓价格
    open_time: datetime      # 开仓时间
    close_time: datetime     # 平仓时间

    # 盈亏指标
    realized_pnl: Decimal    # 实现盈亏
    net_pnl: Decimal         # 净盈亏（扣费后）
    mae: Decimal             # 最大不利偏移
    mfe: Decimal             # 最大有利偏移

    # 质量评分 (四维度)
    entry_quality_score: float   # 入场质量 (0-100)
    exit_quality_score: float    # 出场质量 (0-100)
    trend_quality_score: float   # 趋势把握 (0-100)
    risk_mgmt_score: float       # 风险管理 (0-100)
    overall_score: float         # 综合评分 (0-100)
    score_grade: str             # 评分等级 (A/B/C/D/F)

    # 期权扩展字段
    is_option: int               # 是否期权
    option_type: str             # call/put
    strike_price: Decimal        # 行权价
    expiry_date: date            # 到期日
    entry_moneyness: float       # 入场 Moneyness
    entry_dte: int               # 入场 DTE
    option_entry_score: float    # 期权入场评分
    option_exit_score: float     # 期权出场评分
    option_strategy_score: float # 期权策略评分
```

### MarketData (市场数据)

```python
class MarketData(Base):
    # OHLCV 数据
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    # 技术指标
    rsi_14: float            # RSI(14)
    macd: float              # MACD DIF
    macd_signal: float       # MACD DEA
    macd_hist: float         # MACD 柱
    bb_upper: float          # 布林带上轨
    bb_middle: float         # 布林带中轨
    bb_lower: float          # 布林带下轨
    atr_14: float            # ATR(14)
    adx: float               # ADX 趋势强度
    ma_5/10/20/50/200: float # 移动平均线
```

## 关系设计

```
Trade ──────────────────┐
  │ position_id (FK)    │
  │ market_data_id (FK) │
  │ market_env_id (FK)  │
  ▼                     │
Position ◄──────────────┘
  │ entry_market_env_id (FK)
  │ exit_market_env_id (FK)
  ▼
MarketEnvironment
```

## 索引设计

### Trade 索引
- `idx_symbol_filled_time`: 按代码和时间查询
- `idx_direction_status`: 按方向和状态查询
- `idx_underlying_symbol_time`: 期权标的查询

### Position 索引
- `idx_pos_symbol_open_time`: 按代码和开仓时间
- `idx_pos_overall_score`: 按评分排序
- `idx_pos_is_option`: 期权筛选
- `idx_pos_expiry_date`: 期权到期日筛选

## 使用示例

```python
from src.models.base import init_database, get_session
from src.models.trade import Trade, TradeDirection
from src.models.position import Position, PositionStatus

# 初始化数据库
init_database('sqlite:///tradingcoach.db')
session = get_session()

# 查询所有已平仓持仓
closed = session.query(Position)\
    .filter(Position.status == PositionStatus.CLOSED)\
    .order_by(Position.close_time.desc())\
    .all()

# 查询盈利的期权交易
profitable_options = session.query(Position)\
    .filter(Position.is_option == 1)\
    .filter(Position.net_pnl > 0)\
    .all()

# 查询评分 A 级的交易
a_grade = session.query(Position)\
    .filter(Position.score_grade == 'A')\
    .all()
```

## 数据库初始化

```python
from src.models.base import init_database, create_all_tables

# 初始化并创建表
engine = init_database('sqlite:///tradingcoach.db')
create_all_tables()
```
