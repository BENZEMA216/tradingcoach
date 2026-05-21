# TradingCoach 近期稳定化执行计划

> **给后续执行 Agent 的要求：** 实施本计划时，必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项执行。所有步骤使用 `- [ ]` 复选框跟踪。

**目标：** 把当前 dogfood 和 QA 分支整理成一个可发布、可审查、指标可信、验收标准清晰的 TradingCoach 版本。

**架构思路：** 本轮是稳定化收口，不是大功能重写。主要改动集中在现有 FastAPI 统计接口、React/Vite 前端页面、QA 文档和验证流程上。优先沿用现有文件边界；只有当重复计算已经导致指标不一致时，才抽出小型共享 helper。

**技术栈：** Python 3.11、FastAPI、SQLAlchemy、SQLite、pytest、React、TypeScript、Vite、TailwindCSS、Vitest、Playwright。

---

## 1. 当前状态

**主工作区：** `/Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix`

**当前分支：** `fix/dogfood-bugs`

**2026-05-21 已知状态：**
- 分支领先 `origin/main` 7 个提交。
- 分支已包含真实 CSV dogfood 修复、反事实回测、货币/期权 P&L 修复，以及 12/14 个 QA 问题修复。
- 工作区还有未提交的代码和文档改动。把这些当作已有工作处理，不要未经审查直接恢复或删除。
- 新报告 `project_docs/QA_REPORT_20260520_v2.md` 已存在。
- 旧报告 `project_docs/QA_REPORT_20260520.md` 当前处于删除状态。

**已经观察到的验证结果：**
- `/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q` 通过。
- `npm run typecheck` 通过。
- `npm run build` 通过。
- `npm run lint` 失败，问题集中在 React hooks 规则、未使用变量、显式 `any` 和 lint 范围配置。

## 2. 范围

### 本轮要做
- 整理当前 QA 文档和脏工作区，让分支进入可审查、可 PR 的状态。
- 修复 `QA_REPORT_20260520_v2.md` 里剩余的高价值数据可信度问题。
- 为带 `?` 的降级评分增加用户可理解的解释。
- 把已有的 `/dashboard/needs-review` 后端能力展示到前端 Dashboard。
- 让前端 lint 重新成为有效质量门禁。
- 把上传/处理流程里的取消按钮接到已有取消 API。
- 跑完自动化验证和浏览器验收。

### 本轮不做
- 不新增完整 AI journal 产品面。
- 不重写评分模型。
- 不新增交易笔记、标签、截图或语音备注等用户输入型功能。
- 不做大规模视觉设计系统重构，除非是验收所需的小修。

## 3. 文件地图

| 领域 | 可能涉及文件 | 责任 |
|------|--------------|------|
| QA/文档收口 | `project_docs/QA_REPORT_20260520_v2.md`, `project_docs/readme.md` | 明确当前 QA 事实源和分支状态 |
| 统计指标正确性 | `backend/app/api/v1/endpoints/statistics.py`, 可选 `backend/app/utils/statistics.py`, `tests/integration/test_api_statistics.py`, `tests/unit/test_statistics_api.py` | 保证 by-grade、Sharpe、drawdown、费用指标一致 |
| 评分解释 UI | `frontend/src/pages/Positions.tsx`, `frontend/src/pages/Statistics.tsx`, `frontend/src/components/position-detail/TradeSummaryTab.tsx`, `frontend/src/components/position-detail/RelatedPositionsTab.tsx`, `frontend/src/i18n/locales/en.ts`, `frontend/src/i18n/locales/zh.ts` | 解释 `?` 评分，避免用户过度信任降级分数 |
| Needs Review | `backend/app/api/v1/endpoints/dashboard.py`, `frontend/src/api/client.ts`, `frontend/src/pages/Dashboard.tsx`, `frontend/src/types/index.ts` | 展示后端已经识别出的待复盘持仓 |
| Backtest/表格 UX | `frontend/src/pages/Backtest.tsx`, `frontend/src/pages/Statistics.tsx`, 共享 EmptyState 组件 | 避免误导性百分比和空表格 |
| 处理取消 | `frontend/src/components/processing/ProcessingLogPanel.tsx`, `frontend/src/api/client.ts`, `backend/app/api/v1/endpoints/tasks.py` | 让取消按钮真正调用取消任务接口 |
| 前端质量门禁 | `frontend/eslint.config.js`, `npm run lint` 报错文件 | 让 lint 通过，并保留真实质量检查 |

## 4. 任务一：稳定分支和 QA 文档

**目标：** 在继续改行为之前，先确定一个清晰的文档事实源。

**文件：**
- 修改：`project_docs/readme.md`
- 保留/审查：`project_docs/QA_REPORT_20260520_v2.md`
- 决策：是否保留删除 `project_docs/QA_REPORT_20260520.md`

- [ ] 审查当前脏改动。

运行：
```bash
git status --short --branch
git diff --stat
git diff -- project_docs/readme.md
```

预期：能把文档改动和代码改动分开说明。

- [ ] 决定 `QA_REPORT_20260520.md` 是否应继续删除。

验收规则：如果 v2 报告替代 v1，则 `project_docs/readme.md` 必须索引 v2，且不再引用被删除的 v1。

- [ ] 如果文档收口可以独立提交，则先提交文档。

运行：
```bash
git add project_docs/readme.md project_docs/QA_REPORT_20260520_v2.md project_docs/NEXT_ACTIONS_20260521.md project_docs/ACCEPTANCE_CHECKLIST_20260521.md
git commit -m "docs: add near-term stabilization plan"
```

预期：提交只包含文档。

## 5. 任务二：修复统计数据可信度问题

**目标：** 真实生产数据下，Statistics 指标内部一致，关键表格不为空。

**文件：**
- 修改：`backend/app/api/v1/endpoints/statistics.py`
- 可选新增：`backend/app/utils/statistics.py`
- 测试：`tests/integration/test_api_statistics.py`
- 测试：`tests/unit/test_statistics_api.py`

- [ ] 为不完整评分等级写失败测试。

测试场景：`score_grade` 为 `C+?`、`C?`、`C-?`、`None` 的持仓，在 `/statistics/by-grade` 中必须可见，或者返回明确的空状态说明。

运行：
```bash
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/test_api_statistics.py -q
```

修复前预期：by-grade 响应遗漏不完整等级，或返回空数组。

- [ ] 实现不完整等级处理。

推荐行为：
- 保留有意义的原始标签：`C+?`、`C?`、`C-?`。
- 如果可行，增加不完整评分的布尔字段或前端可判断信号。
- 不要把不完整分数静默合并为干净的 `C`，除非 UI 明确说明。

- [ ] 统一 Sharpe ratio 计算来源。

推荐行为：
- 如果 `/statistics/performance` 和 `/statistics/risk-metrics` 都需要 Sharpe，就抽出共享函数。
- 数据不足时两个接口都返回 `null`。
- 数据足够时两个接口返回同一个四舍五入值。

- [ ] 修复最大回撤百分比行为。

推荐行为：
- 当 `max_drawdown` 和有效峰值权益存在时，返回 `max_drawdown_pct`。
- 当 trough 跌破 0 导致百分比异常时，要么限制展示，要么在 UI 上解释。
- 不展示无法解释的 100% 以上“普通回撤”。

- [ ] 重新跑后端定向测试。

运行：
```bash
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/test_api_statistics.py tests/unit/test_statistics_api.py -q
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q
```

预期：全部通过。

## 6. 任务三：让 `?` 评分在 UI 上诚实可理解

**目标：** 用户看到 `C?` 时，能理解这是“输入数据不足导致的降级评分”，不是系统坏了。

**文件：**
- 修改：`frontend/src/pages/Positions.tsx`
- 修改：`frontend/src/pages/Statistics.tsx`
- 修改：`frontend/src/components/position-detail/TradeSummaryTab.tsx`
- 修改：`frontend/src/components/position-detail/RelatedPositionsTab.tsx`
- 修改：`frontend/src/i18n/locales/en.ts`
- 修改：`frontend/src/i18n/locales/zh.ts`

- [ ] 在中英文 locale 中增加不完整评分解释。

建议中文：
```text
评分旁的 ? 表示市场数据、新闻上下文或环境数据不足，系统已降级评分，请不要把它当作完整评分。
```

建议英文：
```text
The ? means this grade was computed with incomplete market, news, or environment data. Treat it as a downgraded confidence score.
```

- [ ] 在所有关键评分展示处增加 tooltip 或内联提示。

验收规则：至少 Positions 列表、Statistics by-grade 表格、Position detail summary 都能解释 `?`。

- [ ] 确认评分筛选支持不完整等级。

验收规则：筛选 `C?`、`C+?` 或 `C-?` 时，只返回匹配等级，不静默返回无关干净等级。

- [ ] 跑前端基础检查。

运行：
```bash
npm run typecheck
npm run build
```

预期：两个命令都通过。

## 7. 任务四：在 Dashboard 展示待复盘持仓

**目标：** 使用后端已有的 `GET /dashboard/needs-review`，让需要复盘的持仓出现在 Dashboard。

**文件：**
- 修改：`frontend/src/api/client.ts`
- 修改：`frontend/src/pages/Dashboard.tsx`
- 修改：`frontend/src/types/index.ts`
- 核对：`backend/app/api/v1/endpoints/dashboard.py`

- [ ] 为 `GET /dashboard/needs-review` 增加 typed client 方法。

- [ ] 在 Dashboard 增加紧凑的待复盘区块。

推荐行为：
- 最多展示 5 个候选。
- 包含 symbol、P&L、grade、reason。
- 每一行可跳转到持仓详情页。
- 没有候选时显示空状态，不留空白区域。

- [ ] 验证暗色模式和移动端布局。

预期：无横向溢出，深浅色主题都可读。

## 8. 任务五：收口剩余 QA UX 问题

**目标：** 去掉 QA v2 中提到的误导性展示和空白状态。

**文件：**
- 修改：`frontend/src/pages/Backtest.tsx`
- 修改：`frontend/src/pages/Statistics.tsx`
- 必要时修改共享 EmptyState 组件
- 必要时修改 locale 文件

- [ ] 保护所有可空的 `savings_pct`。

验收规则：`Backtest.tsx` 不会对 `null` 或 `undefined` 调用 `.toFixed()`。

- [ ] 当基准 P&L 接近 0 时，优先展示绝对节省金额。

验收规则：Backtest 卡片以节省金额为主，百分比作为次要信息；当分母不稳定时省略或解释百分比。

- [ ] 为 Statistics 表格增加空状态。

验收规则：by-grade、drawdowns 和其他 drill-down 表格不会只显示表头和空 body。

- [ ] 为可点击表格行增加键盘可访问性。

验收规则：可点击行有 `role="button"`、`tabIndex={0}`，并支持 Enter/Space 跳转。

## 9. 任务六：接通处理流程取消按钮

**目标：** 当前可见的取消按钮必须调用已有取消 API。

**文件：**
- 修改：`frontend/src/components/processing/ProcessingLogPanel.tsx`
- 核对：`frontend/src/api/client.ts`
- 核对：`backend/app/api/v1/endpoints/tasks.py`

- [ ] 用 typed API 调用替换 `TODO: 调用取消 API`。

- [ ] 增加取消成功和失败 toast。

- [ ] 验证终态行为。

验收规则：
- 只有 pending/running 任务可以取消。
- completed、failed、cancelled 任务不显示可操作取消按钮。
- cancelled 任务展示已有取消状态。

## 10. 任务七：让前端 lint 通过

**目标：** 恢复 lint 作为有效质量门禁。

**文件：**
- 修改：`frontend/eslint.config.js`
- 修改：`npm run lint` 报错文件

- [ ] 排除生成目录和缓存目录。

至少忽略：
```text
dist
.vite
node_modules
coverage
test-results
playwright-report
```

- [ ] 修复真实 lint 问题，不做大面积规则关闭。

优先级：
1. 未使用 import 和变量。
2. app 源码里的显式 `any`。
3. 容易移出的 render 内组件定义。
4. 代表真实风险的 hooks 依赖和同步 effect 问题。

- [ ] 重新跑 lint。

运行：
```bash
npm run lint
```

预期：0 errors。

## 11. 任务八：最终验证和 PR 准备

**目标：** 分支可合并，并有证据证明核心用户流程可用。

- [ ] 跑后端验证。

运行：
```bash
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/unit/test_symbol_parser.py tests/unit/test_fifo_matcher.py -q
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/ -q
```

预期：全部通过。

- [ ] 跑前端验证。

运行：
```bash
cd frontend
npm run typecheck
npm run lint
npm run test:unit
npm run build
```

预期：全部通过。

- [ ] 跑浏览器 smoke QA。

最少覆盖页面：
- Landing/upload flow
- Dashboard
- Statistics
- Positions
- Position detail
- Backtest
- AI Coach

预期：
- 无 uncaught console errors。
- 关键表格不会无解释空白。
- 不完整评分等级有解释。
- Backtest 数值不误导。
- 后端返回待复盘候选时，Dashboard 能展示。

- [ ] 更新文档。

必需更新：
- `project_docs/readme.md`
- 如果 QA 结论变化，更新 `project_docs/QA_REPORT_20260520_v2.md`
- PR notes 或 release notes

- [ ] 创建 PR。

PR 描述必须包含：
- 改了什么。
- 哪些事项明确 deferred。
- 自动化验证命令和结果。
- 浏览器 QA 摘要。
- 关于市场数据/新闻/环境数据不足导致降级评分的已知风险。
