# TradingCoach 近期稳定化验收清单

> 本文档与 `project_docs/NEXT_ACTIONS_20260521.md` 配套使用，作为当前 `fix/dogfood-bugs` 稳定化工作的发布门禁。

## 1. 验收状态说明

验收负责人应为每一项填写状态：

| 状态 | 含义 |
|------|------|
| PASS | 已验证并通过 |
| FAIL | 已验证但不通过 |
| BLOCKED | 因缺少依赖或环境无法验证 |
| N/A | 本次发布不适用，必须写明原因 |

只要任一 P0/P1 项为 `FAIL` 或未解释的 `BLOCKED`，不得合并 PR 或发布。

## 2. P0：分支和文档卫生

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-001 | 当前工作区足够清晰可审查 | `git status --short --branch` | 只剩本轮稳定化相关改动 | |
| A-002 | QA 报告事实源清楚 | 查看 `project_docs/readme.md` | 已索引 `QA_REPORT_20260520_v2.md`；如果 v1 被替代，则不再引用被删除的 v1 | |
| A-003 | 新增计划和验收文档已索引 | 查看 `project_docs/readme.md` | `NEXT_ACTIONS_20260521.md` 和 `ACCEPTANCE_CHECKLIST_20260521.md` 均已列出 | |
| A-004 | 未恢复或删除无关用户改动 | `git diff --stat` 并人工审查 | diff 可解释，且范围属于本轮稳定化 | |

## 3. P0：数据正确性

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-101 | `/statistics/by-grade` 支持不完整评分 | API 测试或 Statistics 页面 | 真实数据中的 `C+?`、`C?`、`C-?` 能显示为有效行，或有明确空状态说明 | |
| A-102 | 评分筛选支持 `?` 等级 | Positions 页面和 API 查询 | 筛选 `C?`、`C+?`、`C-?` 只返回匹配持仓 | |
| A-103 | Sharpe ratio 只有一个事实源 | 对比 `/statistics/performance` 和 `/statistics/risk-metrics` | 两个接口返回相同数值；若数据不足，则两个都返回 `null` 并有合理解释 | |
| A-104 | 最大回撤百分比安全可解释 | API 响应和 Statistics 页面 | 可计算时返回 `max_drawdown_pct`；UI 不显示无法解释的 100% 以上回撤百分比 | |
| A-105 | 费用占比不误导 | Statistics 页面 | 费用使用稳定分母展示，或在净 P&L 过小时解释百分比不稳定 | |
| A-106 | 多货币总额没有原始混算 | API 响应和 UI 标签 | USD/HKD 已换算、拆分展示或明确标币种，不把 HKD 当 USD 展示 | |

## 4. P0：自动化验证

除非特别说明，以下命令从 `/Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix` 运行。

| ID | 命令 | 通过标准 | 状态 |
|----|------|----------|------|
| A-201 | `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q` | 0 failures | |
| A-202 | `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/ -q` | 0 failures | |
| A-203 | `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/unit/test_symbol_parser.py tests/unit/test_fifo_matcher.py -q` | 0 failures | |
| A-204 | `cd frontend && npm run typecheck` | 0 errors | |
| A-205 | `cd frontend && npm run lint` | 0 errors | |
| A-206 | `cd frontend && npm run test:unit` | 0 failures | |
| A-207 | `cd frontend && npm run build` | production build 成功 | |

## 5. P1：评分透明度

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-301 | Positions 中解释 `?` 评分 | 浏览器检查 | 用户不读文档也能理解 `C?` 含义 | |
| A-302 | Statistics 中解释 `?` 评分 | 浏览器检查 | by-grade 区块解释评分置信度不足 | |
| A-303 | Position detail 中解释 `?` 评分 | 浏览器检查 | summary badge 或附近帮助文案解释输入数据不足 | |
| A-304 | 解释文案支持中英文 | 切换语言 | 中文和英文文案都存在且表达清楚 | |

## 6. P1：Dashboard 待复盘流程

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-401 | Dashboard 调用 `/dashboard/needs-review` | Network 面板或 API mock | Dashboard 加载后发起请求 | |
| A-402 | 待复盘候选可见 | 有候选数据时浏览器检查 | 最多展示 5 条，包含 symbol、grade、P&L、reason | |
| A-403 | 无候选时有空状态 | 无候选数据时浏览器检查 | 不显示空白区块 | |
| A-404 | 候选行可跳转 | 鼠标和键盘测试 | 点击、Enter 或 Space 能进入持仓详情页 | |

## 7. P1：Backtest 和 Statistics UX

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-501 | Backtest 支持空 `savings_pct` | 单测或手工数据 fixture | 页面不崩溃，显示 `-` 或解释文案 | |
| A-502 | Backtest 优先展示节省金额 | 浏览器检查 | 绝对金额是主信息；卡片展示“实际 → 模拟”的盈亏路径，不把相对百分比当主指标 | PASS - 2026-05-26 |
| A-503 | 空表格有空状态 | 浏览器检查 | by-grade、drawdowns 等表格不会只有表头、没有内容 | |
| A-504 | 可点击行支持键盘操作 | 键盘 QA | Tab 可到达，Enter/Space 可触发 | |
| A-505 | 暗色模式可读 | 切换主题检查 | Dashboard、Statistics、Positions、Position detail、Backtest 对比度足够 | |
| A-506 | 标的表现不佳不进入全局问题流 | 单测、API、浏览器检查 | `S02` 不再作为全局 AI 教练洞察展示；标的表现保留在按标的统计上下文 | PASS - 2026-05-26 |

## 8. P1：处理取消流程

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-601 | 取消按钮调用后端 | 运行任务时查看 Network | 调用 `POST /tasks/{task_id}/cancel` 或现有等价接口 | |
| A-602 | 取消成功可见 | 手动运行处理任务 | UI 进入 cancelled 状态，并显示成功 toast/message | |
| A-603 | 取消失败可见 | mock 或强制后端失败 | UI 显示失败 toast/message，任务状态保持一致 | |
| A-604 | 已终止任务不可取消 | 手动检查 | completed、failed、cancelled 状态下隐藏或禁用取消操作 | |

## 9. P1：浏览器 Smoke QA

后端和前端 dev server 启动后执行。

| 页面 | 必查项 | 状态 |
|------|--------|------|
| Landing/upload | 文件选择、sample data、处理状态、取消按钮可见性 | |
| Dashboard | KPI 卡片、needs-review 区块、暗色模式 | |
| Statistics | 核心指标、by-grade、drawdowns、空状态、可钻取行 | |
| Positions | 筛选、评分展示、键盘导航、分页 | |
| Position detail | Summary、Execution、Risk、Related positions、评分解释 | |
| Backtest | 规则卡片、节省金额、展开图表、影响标的 | |
| AI Coach | 规则引擎模式文案、洞察展示、不误导为“服务不可用” | |

通过标准：
- 无 uncaught console errors。
- 关键内容没有无解释空白。
- 390px 宽移动端无明显横向溢出。
- 中文和英文模式都可用。

## 10. P2：发布准备

| ID | 检查项 | 验证方法 | 通过标准 | 状态 |
|----|--------|----------|----------|------|
| A-701 | PR 摘要完整 | 审查 PR body | 包含行为变化、deferred 工作、测试结果、浏览器 QA 备注 | |
| A-702 | Deferred 问题明确 | PR body 和文档 | 如果仍保留 Recharts width warning 或更深的数据完整度工作，必须明确说明 | |
| A-703 | 没有提交 secrets 或私人数据 | `git diff`，并用 `rg` 搜 known keys | 没有 API key、token、真实券商原始导出文件 | |
| A-704 | 文档和实际行为一致 | 审查 `project_docs/` | 报告不会继续声称已修复问题仍失败，或已失败问题未标注状态变化 | |

## 11. 本轮执行记录（2026-05-21）

已通过的自动化验证：

- `npm run typecheck`
- `npm run lint`
- `npm run test:unit`
- `npm run build`
- `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q`
- `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/unit/test_symbol_parser.py tests/unit/test_fifo_matcher.py -q`
- `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/ -q`

已执行浏览器 smoke：

- `http://127.0.0.1:5173/dashboard`
- `http://127.0.0.1:5173/statistics`
- `http://127.0.0.1:5173/positions`
- `http://127.0.0.1:5173/backtest`

结果：四个页面均可渲染，复跑后无 `console.error`。Landing/upload、Position detail、AI Coach 仍建议在 PR 前做人工补充检查。

## 12. 最终签收

| 角色 | 姓名 | 日期 | 结论 | 备注 |
|------|------|------|------|------|
| Engineering |  |  |  |  |
| Product |  |  |  |  |
| QA |  |  |  |  |
