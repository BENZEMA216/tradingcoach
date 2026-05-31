# sample_trades_en.csv 分析空值审计

日期：2026-05-25  
样本：`/Users/benzema/Downloads/sample_trades_en.csv`  
导入结果：876 行原始记录，627 条已成交交易，249 行跳过，生成 483 个仓位。

## 结论

这份样本能导入并生成分析结果。空值主要分三类：

1. 合理空值：OPEN 仓位没有平仓价、持仓周期、已实现盈亏和评分。
2. 能力缺口：本地没有 market data，导致 MAE/MFE、post-exit、市场快照等指标全为空。
3. 已确认 bug：未平仓单腿期权的 `option_type`、`strike_price`、`expiry_date` 在 Position 创建时被漏掉。

本轮已修复第 3 类 bug，并补了回归测试。修复后使用当前数据库交易记录 dry-run 重新配对，14 个未平仓单腿期权的期权字段缺失数从 14 降为 0。价差组合仍保留单值期权字段为空，因为一个组合 symbol 无法用单一 strike/expiry/type 准确表达。

同时发现并修复了详情 API/前端展示链路的问题：数据库补齐后，`/api/v1/positions/{id}` 原本仍不返回 `option_type`、`strike_price`、`expiry_date`，导致前端无法展示。现已补齐 schema、API response、前端类型和详情页展示。

## 数据概览

| 项目 | 数量 | 判断 |
| --- | ---: | --- |
| Trades | 627 | 正常 |
| Positions | 483 | 正常 |
| CLOSED Positions | 422 | 正常 |
| OPEN Positions | 61 | 正常 |
| 评分为空的仓位 | 61 | 合理，全部是 OPEN |
| market_data / market_environment / market_snapshots | 0 | 能力缺口，需要产品层提示 |
| 修复前期权仓位字段不完整 | 25 | 其中单腿 OPEN 为 bug，价差为空合理 |
| 修复后单腿 OPEN 期权字段不完整 | 0 | 已验证 |
| 详情 API 期权字段缺失 | 已修复 | `/positions/431` 返回 CALL / 120 / 2025-02-07 |
| 孤立平仓残量 | 45 笔，3757 股/张 | CSV 起点前已有仓位导致，需要产品提示 |

## 空值判断

### 合理空值

- OPEN 仓位的 `close_time`、`close_price`、`realized_pnl`、`net_pnl`、`holding_period_*` 为空是合理的。
- OPEN 仓位的 `overall_score`、`score_grade` 为空是当前逻辑下合理的，因为评分只覆盖 CLOSED 仓位。
- `reviewed_at`、`review_notes`、`emotion_tag`、`discipline_score` 为空是合理的，因为用户尚未做人工复盘。
- 股票仓位的 `option_type`、`strike_price`、`expiry_date` 为空是合理的。
- 价差组合如 `NVDA260618C205/215` 的单一 `option_type`、`strike_price`、`expiry_date` 为空是合理的，后续应以 legs 结构表达。

### 已修复 bug

- 问题：`SymbolMatcher._create_open_position()` 只复制了 `is_option` 和 `underlying_symbol`，没有复制 `option_type`、`strike_price`、`expiry_date`。
- 影响：未平仓单腿期权详情页会把可解析的期权字段显示为空。
- 修复：未平仓 Position 现在完整继承开仓 Trade 的期权元数据。
- API/前端补齐：PositionDetail schema、详情接口、前端类型和详情页 Trade Summary 都展示期权类型、行权价、到期日、标的。
- 本地数据回填：对当前开发库做了非破坏性回填，只补 `status=OPEN` 且字段为空、关联 Trade 已有值的单腿期权仓位；14 行已回填。
- 验证：`tests/unit/test_symbol_matcher.py` 新增 `test_finalize_open_option_preserves_option_fields`；`tests/integration/test_api_positions.py` 新增 `test_get_position_detail_includes_option_metadata`；当前数据库 dry-run 结果显示单腿 OPEN 期权字段缺失为 0；浏览器访问 `/positions/431` 能看到 `CALL`、`120.00`、`2025-02-07`、`NVDA`。

### 另一个已修复空值问题

- 问题：`/api/v1/statistics/equity-drawdown` 在权益新高点会把 `drawdown_pct=0` 返回成 `null`。
- 判断：这不是缺失数据，而是 0% 回撤，应返回 `0.0`。
- 修复：保留 0 值，仅在无法计算时返回 `null`。
- 验证：新增接口测试 `test_get_equity_drawdown_returns_zero_pct_at_peak`。

## 需要后续产品化处理

1. Market data 缺失提示  
   当前 `market_data`、`market_environment`、`market_snapshots` 都为空，因此 MAE/MFE、risk reward、post-exit、市场环境指标大量为空。页面应明确显示“需要补充行情数据”，不要让用户误以为系统算错。

2. 孤立平仓残量提示  
   样本里有 45 笔平仓残量无法配对，典型原因是 CSV 起点前已有持仓。当前系统会在日志里记录，但产品界面需要把“这些 P&L 未计入总结果”的事实展示出来。

3. 价差组合结构化  
   价差代码不能用单一 strike/expiry/type 表达。后续应引入 option legs 结构，这样 AI Coach 和详情页才能分析组合策略。

4. 未平仓仓位估值  
   OPEN 仓位目前没有未实现盈亏和动态风险指标。需要行情源后才能补齐。

5. 策略分类字段  
   `strategy_type`、`strategy_confidence` 当前全为空，说明策略分类器尚未接入主流程。这是分析能力增强任务，不是导入 bug。

## 验证记录

- `tests/unit/test_symbol_matcher.py tests/unit/test_fifo_matcher.py tests/integration/test_api_statistics.py::TestStatisticsAPIAdvanced::test_get_equity_drawdown_returns_zero_pct_at_peak`：48 passed
- `tests/integration/test_api_positions.py::TestPositionsAPI::test_get_position_detail_includes_option_metadata tests/integration/test_api_statistics.py::TestStatisticsAPIAdvanced::test_get_equity_drawdown_returns_zero_pct_at_peak tests/unit/test_symbol_matcher.py::TestSymbolMatcherOpenPositions::test_finalize_open_option_preserves_option_fields`：3 passed
- `npm run typecheck`：通过
- `npm run lint`：通过
- `npm run test:unit`：18 passed
- `npm run build`：通过
- `git diff --check`：通过
- 当前数据库 dry-run 配对：627 trades，483 positions，61 open positions，14 个单腿 OPEN 期权字段缺失为 0
- Live API：`/api/v1/positions/431` 返回 `option_type=CALL`、`strike_price=120.0`、`expiry_date=2025-02-07`
- Browser QA：`http://127.0.0.1:5174/positions/431` 正常展示期权元数据，截图保存在 `.gstack/data-audit/position-431-option-metadata.png`
- 安装缺失测试依赖 `factory-boy==3.3.3` 后，大范围 `tests/integration/test_api_positions.py tests/integration/test_api_statistics.py`：42 passed
