# TradingCoach 数据完整性走查文档

> 本文档定义数据完整性检查点，为后续自动化测试提供基础

---

## 1. 项目概述

TradingCoach 是交易复盘分析系统，核心数据流如下：

```
CSV 文件 → 导入去重 → Trade 表 → FIFO 配对 → Position 表 → 质量评分 → API 展示
```

### 核心表结构

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `trades` | 原子交易记录 | symbol, direction, filled_quantity, filled_price, trade_fingerprint |
| `positions` | 配对后持仓 | symbol, direction, status, open_price, close_price, net_pnl, overall_score |
| `market_data` | 技术指标数据 | symbol, timestamp, interval, OHLCV, RSI, MACD, etc. |
| `market_environment` | 市场环境快照 | date, vix, market_trend, sector_performance |
| `news_context` | 新闻上下文 | position_id, sentiment_score, news_alignment_score |

---

## 2. 数据完整性检查清单

### 2.1 Trade 表完整性

#### DI-TRADE-001: 交易指纹唯一性
**检查点**: `trade_fingerprint` 列值唯一，无重复记录
```sql
SELECT trade_fingerprint, COUNT(*) as cnt
FROM trade
GROUP BY trade_fingerprint
HAVING cnt > 1;
-- 期望结果: 0 行
```

#### DI-TRADE-002: 必填字段非空
**检查点**: 核心字段不能为 NULL
```sql
SELECT COUNT(*) FROM trade
WHERE symbol IS NULL
   OR direction IS NULL
   OR filled_quantity IS NULL
   OR filled_price IS NULL
   OR filled_time IS NULL;
-- 期望结果: 0
```

#### DI-TRADE-003: 方向枚举值有效
**检查点**: direction 值必须在有效范围内
```sql
SELECT DISTINCT direction FROM trade
WHERE direction NOT IN ('BUY', 'SELL', 'SELL_SHORT', 'BUY_TO_COVER');
-- 期望结果: 0 行
```

#### DI-TRADE-004: 数量和价格为正数
**检查点**: filled_quantity > 0, filled_price > 0
```sql
SELECT COUNT(*) FROM trade
WHERE filled_quantity <= 0 OR filled_price <= 0;
-- 期望结果: 0
```

#### DI-TRADE-005: 费用非负
**检查点**: 所有费用字段 >= 0
```sql
SELECT COUNT(*) FROM trade
WHERE commission < 0
   OR platform_fee < 0
   OR total_fee < 0;
-- 期望结果: 0
```

#### DI-TRADE-006: 总费用计算正确
**检查点**: total_fee = 各项费用之和（允许 0.01 误差）
```sql
SELECT COUNT(*) FROM trade
WHERE ABS(total_fee - (
    COALESCE(commission, 0) +
    COALESCE(platform_fee, 0) +
    COALESCE(clearing_fee, 0) +
    COALESCE(transaction_fee, 0) +
    COALESCE(stamp_duty, 0) +
    COALESCE(sec_fee, 0) +
    COALESCE(option_regulatory_fee, 0) +
    COALESCE(option_clearing_fee, 0)
)) > 0.01;
-- 期望结果: 0
```

#### DI-TRADE-007: 期权字段一致性
**检查点**: is_option = 1 时，期权字段完整
```sql
SELECT COUNT(*) FROM trade
WHERE is_option = 1
  AND (underlying_symbol IS NULL
       OR option_type IS NULL
       OR strike_price IS NULL
       OR expiration_date IS NULL);
-- 期望结果: 0
```

---

### 2.2 Position 表完整性

#### DI-POS-001: 基础字段非空
**检查点**: 核心字段不能为 NULL
```sql
SELECT COUNT(*) FROM position
WHERE symbol IS NULL
   OR direction IS NULL
   OR status IS NULL
   OR open_price IS NULL
   OR open_time IS NULL
   OR quantity IS NULL;
-- 期望结果: 0
```

#### DI-POS-002: 方向枚举值有效
**检查点**: direction 必须是 'long' 或 'short'
```sql
SELECT DISTINCT direction FROM position
WHERE direction NOT IN ('long', 'short');
-- 期望结果: 0 行
```

#### DI-POS-003: 状态枚举值有效
**检查点**: status 必须在有效范围内
```sql
SELECT DISTINCT status FROM position
WHERE status NOT IN ('OPEN', 'CLOSED', 'PARTIALLY_CLOSED');
-- 期望结果: 0 行
```

#### DI-POS-004: 已平仓持仓字段完整
**检查点**: CLOSED 状态必须有平仓信息
```sql
SELECT COUNT(*) FROM position
WHERE status = 'CLOSED'
  AND (close_price IS NULL
       OR close_time IS NULL
       OR net_pnl IS NULL);
-- 期望结果: 0
```

#### DI-POS-005: 开放持仓字段为空
**检查点**: OPEN 状态不应有平仓信息
```sql
SELECT COUNT(*) FROM position
WHERE status = 'OPEN'
  AND (close_price IS NOT NULL
       OR close_time IS NOT NULL);
-- 期望结果: 0
```

#### DI-POS-006: 盈亏计算正确 (多头)
**检查点**: 多头 realized_pnl = (close_price - open_price) × quantity × multiplier
```sql
SELECT COUNT(*) FROM position
WHERE direction = 'long'
  AND status = 'CLOSED'
  AND ABS(realized_pnl - (close_price - open_price) * quantity *
      CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01;
-- 期望结果: 0
```

#### DI-POS-007: 盈亏计算正确 (空头)
**检查点**: 空头 realized_pnl = (open_price - close_price) × quantity × multiplier
```sql
SELECT COUNT(*) FROM position
WHERE direction = 'short'
  AND status = 'CLOSED'
  AND ABS(realized_pnl - (open_price - close_price) * quantity *
      CASE WHEN is_option = 1 THEN 100 ELSE 1 END) > 0.01;
-- 期望结果: 0
```

#### DI-POS-008: 净盈亏计算正确
**检查点**: net_pnl = realized_pnl - total_fees
```sql
SELECT COUNT(*) FROM position
WHERE status = 'CLOSED'
  AND ABS(net_pnl - (realized_pnl - total_fees)) > 0.01;
-- 期望结果: 0
```

#### DI-POS-009: 持仓天数计算正确
**检查点**: holding_period_days 与时间差一致
```sql
SELECT COUNT(*) FROM position
WHERE status = 'CLOSED'
  AND ABS(holding_period_days -
      (julianday(close_time) - julianday(open_time))) > 0.1;
-- 期望结果: 0
```

#### DI-POS-010: 评分范围有效
**检查点**: 所有评分在 0-100 范围内
```sql
SELECT COUNT(*) FROM position
WHERE overall_score IS NOT NULL
  AND (overall_score < 0 OR overall_score > 100);
-- 期望结果: 0

-- 同样检查各维度评分
SELECT COUNT(*) FROM position
WHERE entry_quality_score NOT BETWEEN 0 AND 100
   OR exit_quality_score NOT BETWEEN 0 AND 100
   OR trend_quality_score NOT BETWEEN 0 AND 100
   OR risk_mgmt_score NOT BETWEEN 0 AND 100
   OR market_env_score NOT BETWEEN 0 AND 100
   OR behavior_score NOT BETWEEN 0 AND 100
   OR execution_score NOT BETWEEN 0 AND 100;
-- 期望结果: 0
```

#### DI-POS-011: 评分等级与分数匹配
**检查点**: score_grade 与 overall_score 一致
```sql
SELECT COUNT(*) FROM position
WHERE overall_score IS NOT NULL
  AND score_grade IS NOT NULL
  AND NOT (
    (overall_score >= 90 AND score_grade = 'A') OR
    (overall_score >= 80 AND overall_score < 90 AND score_grade = 'B') OR
    (overall_score >= 70 AND overall_score < 80 AND score_grade = 'C') OR
    (overall_score >= 60 AND overall_score < 70 AND score_grade = 'D') OR
    (overall_score < 60 AND score_grade = 'F')
  );
-- 期望结果: 0
```

#### DI-POS-012: 期权字段一致性
**检查点**: is_option = 1 时，期权字段完整
```sql
SELECT COUNT(*) FROM position
WHERE is_option = 1
  AND (option_type IS NULL
       OR strike_price IS NULL
       OR expiry_date IS NULL);
-- 期望结果: 0
```

---

### 2.3 FIFO 配对完整性

#### DI-MATCH-001: 每个已平仓持仓有关联交易
**检查点**: CLOSED 持仓至少有 2 笔交易（开仓 + 平仓）
```sql
SELECT p.id, p.symbol, COUNT(t.id) as trade_count
FROM position p
LEFT JOIN trade t ON t.position_id = p.id
WHERE p.status = 'CLOSED'
GROUP BY p.id
HAVING trade_count < 2;
-- 期望结果: 0 行
```

#### DI-MATCH-002: 开放持仓只有开仓交易
**检查点**: OPEN 持仓只有 1 笔交易
```sql
SELECT p.id, p.symbol, COUNT(t.id) as trade_count
FROM position p
LEFT JOIN trade t ON t.position_id = p.id
WHERE p.status = 'OPEN'
GROUP BY p.id
HAVING trade_count != 1;
-- 期望结果: 0 行
```

#### DI-MATCH-003: 交易方向与持仓方向一致
**检查点**: long 持仓的开仓方向是 BUY
```sql
SELECT COUNT(*) FROM position p
JOIN trade t ON t.position_id = p.id
WHERE p.direction = 'long'
  AND t.direction NOT IN ('BUY', 'SELL');
-- 期望结果: 0

SELECT COUNT(*) FROM position p
JOIN trade t ON t.position_id = p.id
WHERE p.direction = 'short'
  AND t.direction NOT IN ('SELL_SHORT', 'BUY_TO_COVER');
-- 期望结果: 0
```

#### DI-MATCH-004: 无孤立交易
**检查点**: 每笔有效交易都属于某个持仓
```sql
SELECT COUNT(*) FROM trade
WHERE position_id IS NULL
  AND status = 'FILLED';
-- 期望结果: 取决于业务规则，可能允许未配对交易
```

#### DI-MATCH-005: 费用分配守恒
**检查点**: 分配到持仓的费用之和 = 原交易总费用
```sql
-- 验证每笔交易的费用被完整分配
WITH trade_position_fees AS (
    SELECT
        t.id as trade_id,
        t.total_fee as trade_total_fee,
        SUM(CASE
            WHEN t.direction IN ('BUY', 'SELL_SHORT') THEN p.open_fee
            ELSE p.close_fee
        END) as allocated_fee
    FROM trade t
    JOIN position p ON t.position_id = p.id
    WHERE t.status = 'FILLED'
    GROUP BY t.id
)
SELECT COUNT(*) FROM trade_position_fees
WHERE ABS(trade_total_fee - COALESCE(allocated_fee, 0)) > 0.01;
-- 期望结果: 0
```

---

### 2.4 外键关系完整性

#### DI-FK-001: Trade.position_id 有效
**检查点**: 所有非空 position_id 指向有效 Position
```sql
SELECT COUNT(*) FROM trade t
LEFT JOIN position p ON t.position_id = p.id
WHERE t.position_id IS NOT NULL
  AND p.id IS NULL;
-- 期望结果: 0
```

#### DI-FK-002: Trade.market_data_id 有效
**检查点**: 所有非空 market_data_id 指向有效 MarketData
```sql
SELECT COUNT(*) FROM trade t
LEFT JOIN market_data m ON t.market_data_id = m.id
WHERE t.market_data_id IS NOT NULL
  AND m.id IS NULL;
-- 期望结果: 0
```

#### DI-FK-003: Position.entry_market_env_id 有效
```sql
SELECT COUNT(*) FROM position p
LEFT JOIN market_environment m ON p.entry_market_env_id = m.id
WHERE p.entry_market_env_id IS NOT NULL
  AND m.id IS NULL;
-- 期望结果: 0
```

#### DI-FK-004: NewsContext.position_id 有效且唯一
```sql
-- 检查外键有效
SELECT COUNT(*) FROM news_context n
LEFT JOIN position p ON n.position_id = p.id
WHERE n.position_id IS NOT NULL
  AND p.id IS NULL;
-- 期望结果: 0

-- 检查一对一关系
SELECT position_id, COUNT(*) as cnt
FROM news_context
WHERE position_id IS NOT NULL
GROUP BY position_id
HAVING cnt > 1;
-- 期望结果: 0 行
```

---

### 2.5 MarketData 完整性

#### DI-MD-001: 唯一约束有效
**检查点**: (symbol, timestamp, interval) 组合唯一
```sql
SELECT symbol, timestamp, interval, COUNT(*) as cnt
FROM market_data
GROUP BY symbol, timestamp, interval
HAVING cnt > 1;
-- 期望结果: 0 行
```

#### DI-MD-002: OHLC 逻辑正确
**检查点**: low <= open, close <= high
```sql
SELECT COUNT(*) FROM market_data
WHERE low > open OR low > close
   OR high < open OR high < close;
-- 期望结果: 0
```

#### DI-MD-003: 技术指标范围有效
**检查点**: RSI 在 0-100 之间
```sql
SELECT COUNT(*) FROM market_data
WHERE rsi_14 IS NOT NULL
  AND (rsi_14 < 0 OR rsi_14 > 100);
-- 期望结果: 0
```

---

### 2.6 MarketEnvironment 完整性

#### DI-ME-001: 日期唯一
**检查点**: 每天只有一条记录
```sql
SELECT date, COUNT(*) as cnt
FROM market_environment
GROUP BY date
HAVING cnt > 1;
-- 期望结果: 0 行
```

#### DI-ME-002: VIX 等级与数值一致
**检查点**: vix_level 与 vix 数值匹配
```sql
SELECT COUNT(*) FROM market_environment
WHERE vix IS NOT NULL
  AND vix_level IS NOT NULL
  AND NOT (
    (vix < 15 AND vix_level = 'low') OR
    (vix >= 15 AND vix < 25 AND vix_level = 'medium') OR
    (vix >= 25 AND vix < 35 AND vix_level = 'high') OR
    (vix >= 35 AND vix_level = 'extreme')
  );
-- 期望结果: 0
```

---

## 3. 业务规则检查

### 3.1 时序一致性

#### DI-BIZ-001: 开仓时间早于平仓时间
```sql
SELECT COUNT(*) FROM position
WHERE status = 'CLOSED'
  AND open_time >= close_time;
-- 期望结果: 0
```

#### DI-BIZ-002: 交易时间在合理范围内
```sql
-- 假设交易数据从 2020 年开始
SELECT COUNT(*) FROM trade
WHERE filled_time < '2020-01-01'
   OR filled_time > datetime('now', '+1 day');
-- 期望结果: 0
```

### 3.2 数值合理性

#### DI-BIZ-003: 持仓盈亏百分比合理
**检查点**: 单笔盈亏百分比在合理范围（如 -100% ~ 1000%）
```sql
SELECT COUNT(*) FROM position
WHERE net_pnl_pct IS NOT NULL
  AND (net_pnl_pct < -100 OR net_pnl_pct > 1000);
-- 期望结果: 根据实际情况，可能为 0 或很少
```

#### DI-BIZ-004: MAE/MFE 合理性
**检查点**: MAE 负数或零，MFE 正数或零
```sql
SELECT COUNT(*) FROM position
WHERE (mae IS NOT NULL AND mae > 0)
   OR (mfe IS NOT NULL AND mfe < 0);
-- 期望结果: 0
```

### 3.3 跨表一致性

#### DI-BIZ-005: 持仓数量与交易数量一致
**检查点**: 持仓数量 = 开仓交易数量
```sql
SELECT p.id, p.quantity, t.filled_quantity
FROM position p
JOIN trade t ON t.position_id = p.id
WHERE t.direction IN ('BUY', 'SELL_SHORT')
  AND p.quantity != t.filled_quantity;
-- 期望结果: 0 行（或允许部分成交的情况）
```

#### DI-BIZ-006: 持仓价格与交易价格一致
**检查点**: open_price = 开仓交易的 filled_price
```sql
SELECT p.id, p.open_price, t.filled_price
FROM position p
JOIN trade t ON t.position_id = p.id
WHERE t.direction IN ('BUY', 'SELL_SHORT')
  AND ABS(p.open_price - t.filled_price) > 0.0001;
-- 期望结果: 0 行
```

---

## 4. 自动化测试框架建议

### 4.1 测试文件结构

```
tests/
├── data_integrity/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures
│   ├── test_trade_integrity.py   # Trade 表检查
│   ├── test_position_integrity.py # Position 表检查
│   ├── test_matching_integrity.py # FIFO 配对检查
│   ├── test_fk_integrity.py      # 外键关系检查
│   ├── test_market_data.py       # 市场数据检查
│   └── test_business_rules.py    # 业务规则检查
```

### 4.2 示例测试代码

```python
# tests/data_integrity/conftest.py
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_PATH

@pytest.fixture(scope="session")
def db_session():
    engine = create_engine(f"sqlite:///{DATABASE_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# tests/data_integrity/test_trade_integrity.py
import pytest

class TestTradeIntegrity:

    def test_di_trade_001_fingerprint_unique(self, db_session):
        """DI-TRADE-001: 交易指纹唯一性"""
        result = db_session.execute(text("""
            SELECT trade_fingerprint, COUNT(*) as cnt
            FROM trade
            GROUP BY trade_fingerprint
            HAVING cnt > 1
        """)).fetchall()
        assert len(result) == 0, f"发现 {len(result)} 个重复指纹"

    def test_di_trade_002_required_fields(self, db_session):
        """DI-TRADE-002: 必填字段非空"""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM trade
            WHERE symbol IS NULL
               OR direction IS NULL
               OR filled_quantity IS NULL
               OR filled_price IS NULL
               OR filled_time IS NULL
        """)).scalar()
        assert result == 0, f"发现 {result} 条记录缺少必填字段"

    def test_di_trade_003_valid_direction(self, db_session):
        """DI-TRADE-003: 方向枚举值有效"""
        result = db_session.execute(text("""
            SELECT DISTINCT direction FROM trade
            WHERE direction NOT IN ('BUY', 'SELL', 'SELL_SHORT', 'BUY_TO_COVER')
        """)).fetchall()
        assert len(result) == 0, f"发现无效方向值: {result}"

# tests/data_integrity/test_position_integrity.py
class TestPositionIntegrity:

    def test_di_pos_004_closed_position_complete(self, db_session):
        """DI-POS-004: 已平仓持仓字段完整"""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM position
            WHERE status = 'CLOSED'
              AND (close_price IS NULL
                   OR close_time IS NULL
                   OR net_pnl IS NULL)
        """)).scalar()
        assert result == 0, f"发现 {result} 条已平仓持仓缺少平仓信息"

    def test_di_pos_008_net_pnl_calculation(self, db_session):
        """DI-POS-008: 净盈亏计算正确"""
        result = db_session.execute(text("""
            SELECT COUNT(*) FROM position
            WHERE status = 'CLOSED'
              AND ABS(net_pnl - (realized_pnl - total_fees)) > 0.01
        """)).scalar()
        assert result == 0, f"发现 {result} 条持仓净盈亏计算错误"
```

### 4.3 运行方式

```bash
# 运行所有数据完整性测试
python -m pytest tests/data_integrity/ -v

# 运行特定检查
python -m pytest tests/data_integrity/test_trade_integrity.py -v

# 生成测试报告
python -m pytest tests/data_integrity/ --html=reports/integrity_report.html
```

---

## 5. 检查清单汇总

| 编号 | 类别 | 检查项 | 优先级 |
|------|------|--------|--------|
| DI-TRADE-001 | Trade | 交易指纹唯一性 | P0 |
| DI-TRADE-002 | Trade | 必填字段非空 | P0 |
| DI-TRADE-003 | Trade | 方向枚举值有效 | P0 |
| DI-TRADE-004 | Trade | 数量和价格为正数 | P0 |
| DI-TRADE-005 | Trade | 费用非负 | P1 |
| DI-TRADE-006 | Trade | 总费用计算正确 | P1 |
| DI-TRADE-007 | Trade | 期权字段一致性 | P1 |
| DI-POS-001 | Position | 基础字段非空 | P0 |
| DI-POS-002 | Position | 方向枚举值有效 | P0 |
| DI-POS-003 | Position | 状态枚举值有效 | P0 |
| DI-POS-004 | Position | 已平仓字段完整 | P0 |
| DI-POS-005 | Position | 开放持仓字段为空 | P0 |
| DI-POS-006 | Position | 多头盈亏计算 | P0 |
| DI-POS-007 | Position | 空头盈亏计算 | P0 |
| DI-POS-008 | Position | 净盈亏计算 | P0 |
| DI-POS-009 | Position | 持仓天数计算 | P1 |
| DI-POS-010 | Position | 评分范围有效 | P1 |
| DI-POS-011 | Position | 评分等级匹配 | P1 |
| DI-POS-012 | Position | 期权字段一致性 | P1 |
| DI-MATCH-001 | FIFO | 已平仓有交易关联 | P0 |
| DI-MATCH-002 | FIFO | 开放持仓交易数 | P0 |
| DI-MATCH-003 | FIFO | 交易方向一致 | P0 |
| DI-MATCH-004 | FIFO | 无孤立交易 | P1 |
| DI-MATCH-005 | FIFO | 费用分配守恒 | P1 |
| DI-FK-001 | FK | Trade.position_id | P0 |
| DI-FK-002 | FK | Trade.market_data_id | P1 |
| DI-FK-003 | FK | Position.entry_market_env_id | P1 |
| DI-FK-004 | FK | NewsContext.position_id | P1 |
| DI-MD-001 | MarketData | 唯一约束 | P0 |
| DI-MD-002 | MarketData | OHLC 逻辑 | P1 |
| DI-MD-003 | MarketData | RSI 范围 | P2 |
| DI-ME-001 | MarketEnv | 日期唯一 | P0 |
| DI-ME-002 | MarketEnv | VIX 等级 | P2 |
| DI-BIZ-001 | 业务 | 时序一致性 | P0 |
| DI-BIZ-002 | 业务 | 时间范围合理 | P1 |
| DI-BIZ-003 | 业务 | 盈亏百分比合理 | P2 |
| DI-BIZ-004 | 业务 | MAE/MFE 合理 | P2 |
| DI-BIZ-005 | 业务 | 持仓数量一致 | P0 |
| DI-BIZ-006 | 业务 | 持仓价格一致 | P0 |

**优先级说明**:
- **P0**: 核心数据完整性，必须通过
- **P1**: 重要业务规则，应该通过
- **P2**: 数据质量检查，建议通过

---

## 6. 维护说明

本文档随项目演进需同步更新：

1. **新增表/字段** → 添加对应检查项
2. **业务规则变更** → 更新检查逻辑和期望结果
3. **发现新问题** → 补充检查项并标注优先级

最后更新: 2025-12-24

---

## 7. 实测结果 (2025-12-24)

首次运行自动化测试，发现以下数据问题：

### 测试统计
- **通过**: 26 项
- **失败**: 7 项

### 发现的问题

| 检查项 | 问题数量 | 说明 |
|--------|----------|------|
| DI-TRADE-006 | 343 条 | 总费用计算不正确（费用字段累加 ≠ total_fee） |
| DI-POS-011 | 1 条 | 评分等级与分数不匹配 |
| DI-POS-012 | 109 条 | 期权持仓缺少完整字段（option_type/strike_price/expiry_date） |
| DI-MATCH-001 | 待确认 | 部分已平仓持仓关联交易数不足 |
| DI-MATCH-003 | 待确认 | 空头持仓交易方向不一致 |
| DI-BIZ-005 | 81 条 | 持仓数量与开仓交易数量不一致 |
| DI-BIZ-006 | 11 条 | 持仓价格与开仓交易价格不一致 |

### 问题分析

1. **费用计算问题 (DI-TRADE-006)**:
   - 可能原因：部分费用字段未包含在累加公式中
   - 建议：检查是否有额外费用字段（如 exchange_fee）

2. **期权字段缺失 (DI-POS-012)**:
   - 可能原因：早期数据导入时未解析期权符号
   - 建议：运行数据修复脚本补全期权信息

3. **持仓-交易数量/价格不一致 (DI-BIZ-005/006)**:
   - 可能原因：FIFO 配对逻辑中部分成交处理方式
   - 建议：检查 symbol_matcher.py 中的加权平均价格计算

### 后续行动

1. [ ] 调查费用计算差异的根本原因
2. [ ] 修复期权字段缺失数据
3. [ ] 确认 FIFO 配对逻辑是否符合预期
4. [ ] 将测试集成到 CI/CD 流程
