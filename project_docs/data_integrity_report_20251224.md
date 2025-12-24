# 数据完整性检验报告

**检验日期**: 2025-12-24
**检验工具**: pytest + SQLite
**数据库**: data/tradingcoach.db

---

## 1. 总体概况

### 数据库统计
| 指标 | 数量 |
|------|------|
| 交易记录 (trades) | 613 |
| 持仓记录 (positions) | 444 |
| 已平仓持仓 | 402 |
| 开放持仓 | 42 |
| 期权持仓 | 109 |

### 检验结果汇总
| 状态 | 数量 | 占比 |
|------|------|------|
| **通过** | 26 | 78.8% |
| **失败** | 7 | 21.2% |
| **总计** | 33 | 100% |

---

## 2. 检验结果明细

### 2.1 通过的检查项 (26项)

| 编号 | 检查项 | 说明 |
|------|--------|------|
| DI-TRADE-001 | 交易指纹唯一性 | 无重复交易 |
| DI-TRADE-002 | 必填字段非空 | 所有必填字段完整 |
| DI-TRADE-003 | 方向枚举值有效 | BUY/SELL/SELL_SHORT/BUY_TO_COVER |
| DI-TRADE-004 | 数量和价格为正数 | 所有数值有效 |
| DI-TRADE-005 | 费用非负 | 无负数费用 |
| DI-TRADE-007 | 期权字段一致性 | trades 表期权字段完整 |
| DI-POS-001 | 基础字段非空 | 所有必填字段完整 |
| DI-POS-002 | 方向枚举值有效 | long/short |
| DI-POS-003 | 状态枚举值有效 | OPEN/CLOSED |
| DI-POS-004 | 已平仓字段完整 | 平仓信息完整 |
| DI-POS-005 | 开放持仓字段为空 | 无异常平仓信息 |
| DI-POS-006 | 多头盈亏计算 | 计算正确 |
| DI-POS-007 | 空头盈亏计算 | 计算正确 |
| DI-POS-008 | 净盈亏计算 | net_pnl = realized_pnl - total_fees |
| DI-POS-010 | 评分范围有效 | 0-100 范围内 |
| DI-MATCH-002 | 开放持仓交易数 | 每个开放持仓有 1 笔交易 |
| DI-MATCH-003 (long) | 多头方向一致 | BUY/SELL 匹配 |
| DI-FK-001 | Trade.position_id | 外键有效 |
| DI-FK-002 | Trade.market_data_id | 外键有效 |
| DI-FK-004 | NewsContext 一对一 | 关系正确 |
| DI-MD-001 | MarketData 唯一约束 | 无重复 |
| DI-MD-002 | OHLC 逻辑正确 | low <= open/close <= high |
| DI-MD-003 | RSI 范围有效 | 0-100 |
| DI-ME-001 | MarketEnvironment 日期唯一 | 无重复 |
| DI-BIZ-001 | 开仓时间早于平仓 | 时序正确 |
| DI-BIZ-002 | 交易时间合理 | 在有效范围内 |

---

### 2.2 失败的检查项 (7项)

#### DI-TRADE-006: 总费用计算不正确
- **问题数量**: 343 条 (占交易总数 55.9%)
- **严重程度**: P1 (重要)
- **问题描述**: total_fee ≠ 各费用字段之和

**样本数据**:
| ID | Symbol | total_fee | 计算值 | 差异 |
|----|--------|-----------|--------|------|
| 8 | TQQQ | 2.30 | 2.28 | 0.02 |
| 12 | 01810 | 37.49 | 37.06 | 0.43 |
| 15 | 09988 | 36.36 | 35.94 | 0.42 |

**根因分析**:
- 港股交易有额外费用（印花税、交易所费等）未拆分到独立字段
- total_fee 是原始值，各费用字段是解析后的值，存在精度丢失

**建议修复**:
- 检查 CSV 导入逻辑，确保所有费用字段被正确解析
- 或接受 total_fee 作为权威值，不做字段累加校验

---

#### DI-POS-011: 评分等级与分数不匹配
- **问题数量**: 1 条
- **严重程度**: P1 (重要)
- **问题描述**: overall_score 与 score_grade 不一致

**样本数据**:
| ID | Symbol | overall_score | score_grade | 期望等级 |
|----|--------|---------------|-------------|----------|
| 397 | TQQQ | 68.59 | C+ | D |

**根因分析**:
- 评分系统可能使用了 "C+" 这种细分等级
- 检查逻辑只支持 A/B/C/D/F 五级

**建议修复**:
- 更新检查逻辑支持 +/- 等级
- 或统一评分等级为五级制

---

#### DI-POS-012: 期权持仓字段不完整
- **问题数量**: 109 条 (占期权持仓 100%)
- **严重程度**: P0 (核心)
- **问题描述**: is_option=1 但 option_type/strike_price/expiry_date 为空

**样本数据**:
| ID | Symbol | is_option | option_type | strike_price | expiry_date |
|----|--------|-----------|-------------|--------------|-------------|
| 1 | NVDA250207C120000 | 1 | NULL | NULL | NULL |
| 2 | NVDA250214C120000 | 1 | NULL | NULL | NULL |
| 6 | TSLA250307P395000 | 1 | NULL | NULL | NULL |

**根因分析**:
- 期权符号包含完整信息 (如 NVDA250207C120000)
- 但未被解析到 option_type/strike_price/expiry_date 字段

**建议修复**:
```python
# 从符号解析期权信息
# NVDA250207C120000 → underlying=NVDA, expiry=2025-02-07, type=C, strike=120
def parse_option_symbol(symbol):
    match = re.match(r'([A-Z]+)(\d{6})([CP])(\d+)', symbol)
    if match:
        return {
            'underlying': match.group(1),
            'expiry_date': parse_date(match.group(2)),
            'option_type': 'CALL' if match.group(3) == 'C' else 'PUT',
            'strike_price': int(match.group(4)) / 1000
        }
```

---

#### DI-MATCH-001: 已平仓持仓交易数不足
- **问题数量**: 241 条 (占已平仓 60%)
- **严重程度**: P0 (核心)
- **问题描述**: CLOSED 持仓只有 1 笔关联交易

**样本数据**:
| pos_id | Symbol | Status | trade_count |
|--------|--------|--------|-------------|
| 4 | NVDA | CLOSED | 1 |
| 7 | NVDL | CLOSED | 1 |
| 8 | NVDL | CLOSED | 1 |

**根因分析**:
- FIFO 配对逻辑可能是：一笔 position 只关联开仓交易
- 平仓交易可能关联到另一个 position 或未关联

**建议修复**:
- 检查 FIFO matcher 的 position_id 分配逻辑
- 确保开仓和平仓交易都关联到同一个 position

---

#### DI-MATCH-003 (short): 空头持仓交易方向不一致
- **问题数量**: 11 条
- **严重程度**: P1 (重要)
- **问题描述**: short 持仓关联了 BUY 方向交易

**样本数据**:
| pos_id | Symbol | pos_dir | trade_dir |
|--------|--------|---------|-----------|
| 391 | COIN260417P230000 | short | BUY |
| 390 | TSLA260417P290000 | short | BUY |
| 369 | AMZN260618P195000 | short | BUY |

**根因分析**:
- 这些是卖出看跌期权 (sell put)
- 系统将 "卖出期权" 识别为 short position
- 但交易方向是 BUY (买入开仓) 而非 SELL_SHORT

**建议修复**:
- 期权的 position direction 判断逻辑需要特殊处理
- 或更新检查逻辑，允许 short + BUY 组合（卖出期权场景）

---

#### DI-BIZ-005: 持仓数量与交易数量不一致
- **问题数量**: 81 条
- **严重程度**: P1 (重要)
- **问题描述**: position.quantity ≠ trade.filled_quantity

**样本数据**:
| pos_id | Symbol | pos_qty | trade_qty | diff |
|--------|--------|---------|-----------|------|
| 420 | CONL | 21 | 70 | -49 |
| 442 | FIG | 1 | 10 | -9 |
| 435 | HIMS | 10 | 20 | -10 |

**根因分析**:
- FIFO 部分成交：一笔交易被拆分到多个持仓
- position.quantity 是配对后的数量，trade.filled_quantity 是原始数量

**建议修复**:
- 这是正常业务逻辑，检查规则需要调整
- 应检查：sum(position.quantity) = trade.filled_quantity

---

#### DI-BIZ-006: 持仓价格与交易价格不一致
- **问题数量**: 11 条
- **严重程度**: P1 (重要)
- **问题描述**: position.open_price ≠ trade.filled_price

**根因分析**:
- 可能是加权平均价格计算导致
- 或多笔开仓交易被合并

---

## 3. 问题优先级排序

| 优先级 | 检查项 | 问题数 | 影响范围 | 建议行动 |
|--------|--------|--------|----------|----------|
| **P0** | DI-POS-012 | 109 | 所有期权持仓 | 运行数据修复脚本解析期权符号 |
| **P0** | DI-MATCH-001 | 241 | 60% 已平仓 | 检查 FIFO matcher 逻辑 |
| **P1** | DI-TRADE-006 | 343 | 56% 交易 | 接受或修复费用解析 |
| **P1** | DI-MATCH-003 | 11 | 期权空头 | 更新检查逻辑支持期权 |
| **P1** | DI-BIZ-005 | 81 | 部分成交 | 更新检查逻辑 |
| **P1** | DI-BIZ-006 | 11 | 少量持仓 | 调查具体情况 |
| **P1** | DI-POS-011 | 1 | 单条记录 | 支持 +/- 等级 |

---

## 4. 建议的后续行动

### 立即修复 (P0)
1. **期权字段补全脚本**: 从 symbol 解析 option_type/strike_price/expiry_date
2. **FIFO 配对逻辑审查**: 确保开仓和平仓交易都关联到正确的 position

### 短期改进 (P1)
3. **更新检查逻辑**: 支持期权特殊场景、部分成交场景
4. **评分等级统一**: 决定使用五级制还是支持 +/- 细分

### 长期优化
5. **数据导入改进**: 确保所有费用字段被正确解析
6. **自动化检查**: 将数据完整性测试集成到 CI/CD

---

## 5. 附录：运行测试命令

```bash
# 运行所有检查
python -m pytest tests/data_integrity/ -v

# 只运行失败的检查
python -m pytest tests/data_integrity/ --lf

# 生成 HTML 报告
python -m pytest tests/data_integrity/ --html=reports/integrity_report.html
```
