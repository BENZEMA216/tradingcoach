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
| `news_context.py` | 新闻上下文模型 | 交易日相关新闻、情感分析、新闻契合度评分 |
| `event_context.py` | 事件上下文模型 | 财报/宏观/异常事件记录、市场反应、持仓影响 |
| `task.py` | 后台任务模型 | 异步任务状态追踪 |

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
    market: MarketType       # 市场类型 (美股/港股/沪深)

    # 成交信息
    filled_price: Decimal    # 成交价格
    filled_quantity: int     # 成交数量
    filled_time: datetime    # 成交时间
    trade_date: date         # 交易日期

    # 费用明细 (通用)
    commission: Decimal      # 佣金
    platform_fee: Decimal    # 平台使用费
    clearing_fee: Decimal    # 交收费/清算费
    stamp_duty: Decimal      # 印花税 (港股)
    total_fee: Decimal       # 合计费用

    # A股特有字段 (v2.0新增)
    exchange: str            # 交易所代码 (sse=上交所, szse=深交所)
    seat_code: str           # 席位代码/营业部代码
    shareholder_code: str    # 股东代码/证券账号
    transfer_fee: Decimal    # 过户费 (万分之0.1)
    handling_fee: Decimal    # 经手费 (交易所收取)
    regulation_fee: Decimal  # 证管费 (证监会收取)
    other_fees: Decimal      # 其他费用

    # 期权信息
    is_option: int           # 是否期权 (0/1)
    underlying_symbol: str   # 标的代码
    option_type: str         # CALL/PUT
    strike_price: Decimal    # 行权价
    expiration_date: date    # 到期日

    # 导入追踪 (v2.0新增)
    trade_fingerprint: str   # 交易唯一指纹 (SHA256, 用于去重)
    broker_id: str           # 券商ID (futu_cn, citic, huatai等)
    import_batch_id: str     # 导入批次ID
    source_row_number: int   # 原始CSV行号
```

**枚举类型**:
- `TradeDirection`: BUY, SELL, SELL_SHORT, BUY_TO_COVER
- `TradeStatus`: FILLED, PARTIALLY_FILLED, CANCELLED, PENDING
- `MarketType`: US_STOCK (美股), HK_STOCK (港股), CN_STOCK (沪深)

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

### NewsContext (新闻上下文)

```python
class NewsContext(Base):
    # 关联信息
    position_id: int         # 关联持仓ID
    symbol: str              # 股票代码
    search_date: date        # 搜索中心日期

    # 新闻类别标记
    has_earnings: bool       # 是否有财报新闻
    has_product_news: bool   # 是否有产品新闻
    has_analyst_rating: bool # 是否有分析师评级
    has_sector_news: bool    # 是否有行业新闻
    has_macro_news: bool     # 是否有宏观新闻
    has_geopolitical: bool   # 是否有地缘政治新闻

    # 情感分析
    overall_sentiment: str   # bullish/bearish/neutral/mixed
    sentiment_score: Decimal # -100 to +100
    news_impact_level: str   # high/medium/low/none

    # 新闻存储
    news_items: JSON         # [{title, source, date, sentiment, category}]
    news_count: int          # 新闻数量

    # 评分
    news_alignment_score: Decimal  # 新闻契合度评分 (0-100)
    score_breakdown: JSON          # 评分细节
```

**枚举类型**:
- `NewsSentiment`: BULLISH, BEARISH, NEUTRAL, MIXED
- `NewsImpactLevel`: HIGH, MEDIUM, LOW, NONE
- `NewsCategory`: EARNINGS, PRODUCT, ANALYST, SECTOR, MACRO, GEOPOLITICAL, etc.

### EventContext (事件上下文)

```python
class EventContext(Base):
    # 关联信息
    position_id: int         # 关联持仓ID (可选)
    symbol: str              # 股票代码

    # 事件基本信息
    event_type: str          # earnings/split/macro/fed/geopolitical/price_anomaly等
    event_date: date         # 事件日期
    event_title: str         # 事件标题
    event_description: str   # 事件详情

    # 事件影响评估
    event_impact: str        # positive/negative/neutral/mixed
    event_importance: int    # 1-10 重要性评分
    is_surprise: bool        # 是否超预期
    surprise_direction: str  # beat/miss

    # 市场反应指标
    price_before: Decimal    # 事件前收盘价
    price_after: Decimal     # 事件后收盘价
    price_change_pct: Decimal # 价格变动百分比
    volume_spike: Decimal    # 成交量倍数 (相对20日均量)
    volatility_spike: Decimal # 波动率变化
    gap_pct: Decimal         # 跳空百分比

    # 持仓影响
    position_pnl_on_event: Decimal      # 事件日持仓盈亏
    position_pnl_pct_on_event: Decimal  # 事件日盈亏百分比

    # 数据来源
    source: str              # polygon/yfinance/manual/detected
    confidence: Decimal      # 置信度 (0-100)
```

**枚举类型**:
- `EventType`: EARNINGS, SPLIT, DIVIDEND, MACRO, FED, CPI, NFP, GEOPOLITICAL, PRICE_ANOMALY, etc.
- `EventImpact`: POSITIVE, NEGATIVE, NEUTRAL, MIXED, UNKNOWN

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
  │ news_context_id (FK)
  ▼
MarketEnvironment
NewsContext
```

## 索引设计

### Trade 索引
- `idx_symbol_filled_time`: 按代码和时间查询
- `idx_symbol_trade_date`: 按代码和交易日期查询
- `idx_direction_status`: 按方向和状态查询
- `idx_underlying_symbol_time`: 期权标的查询
- `idx_market_trade_date`: 按市场类型和交易日期查询
- `idx_broker_trade_date`: 按券商和交易日期查询 (v2.0新增)
- `idx_import_batch`: 按导入批次查询 (v2.0新增)

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
