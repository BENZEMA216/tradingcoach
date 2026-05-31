# TradingCoach 剩余收口任务执行计划

> **给后续执行 Agent 的要求：** 实施本计划时，必须使用 `superpowers:executing-plans`，逐项执行并在每个 P0 任务后更新本文档。当前任务偏收口和验收，不建议再并行拆太多功能改动。

**目标：** 把已经通过自动化验证的 `fix/dogfood-bugs` 工作区，整理成可审查、可提交、可 PR 的发布候选。

**架构思路：** 这不是新功能开发阶段，而是发布前收口。优先做事实确认、人工浏览器 QA、取消流程实测、提交拆分和 PR 说明；除非验收发现阻断问题，否则不要扩大功能范围。

**技术栈：** Python 3.11、FastAPI、SQLAlchemy、pytest、React、TypeScript、Vite、TailwindCSS、Vitest、Playwright。

---

## 1. 当前事实

**工作区：** `/Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix`

**分支：** `fix/dogfood-bugs`

**已完成：**

- 文档计划已提交：`a5e71b5 docs: add near-term stabilization plan`
- 后端统计口径修复已落地：by-grade 支持 `C+?`、`C?`、`C-?`，Sharpe ratio 口径统一，费用占比和回撤百分比已调整。
- 前端评分解释、Dashboard 待复盘、Backtest 空值保护、Statistics 空状态、取消 API 调用、lint 清理已落地。
- 2026-05-22 收口时又修复了：`/analysis/:taskId` 实际路径取消按钮、Landing 恢复 banner 重复 setState、Position detail ExecutionTab `position` 未定义、多币种顶部 P&L、Related Positions 内评分 tooltip 冒泡跳转、移动端页面级横向溢出。
- 自动化验证已复跑通过：
  - `cd frontend && npm run typecheck`
  - `cd frontend && npm run lint && npm run test:unit && npm run build`
  - `/opt/homebrew/bin/python3.11 -m pytest tests/unit/test_symbol_matcher.py tests/unit/test_fifo_matcher.py tests/data_integrity ...`：93 passed（集成测试在裸 Python 下缺 `factory-boy`，业务路径已通过）
  - `/opt/homebrew/bin/uv run --python /opt/homebrew/bin/python3.11 --with-requirements requirements.txt python -m pytest tests/integration/test_api_statistics.py tests/integration/test_api_positions.py`：40 passed
- 浏览器 QA 已覆盖：Landing/upload、Position detail、AI Coach、Dashboard、Statistics、Positions、Backtest、移动端 390px、中英文、评分筛选、多币种、取消 UI；复跑后无 `console.error` / `pageerror`。
- secret/privacy 扫描已完成；PR notes 草稿已新增：`project_docs/PR_NOTES_20260522.md`。

**仍未完成：**

- 最终 PR 发布尚未执行，需要用户明确批准后才能 push / open PR。
- 评分系统大量输出 `?` 的根因、聚合统计跨币种口径、完整视觉回归/a11y 专项仍作为 deferred。

## 2. 剩余任务总览

| 优先级 | 任务 | 产物 | 完成标准 |
|--------|------|------|----------|
| P0 | 审查并拆分当前代码 diff | 清晰提交或明确暂存策略 | PASS：已拆成本地提交 |
| P0 | 补完整浏览器人工 QA | QA 记录和截图/文字结论 | PASS：Landing、Position detail、AI Coach、移动端、双语通过 |
| P0 | 实测取消流程 | 取消成功/失败/终态行为记录 | PASS：取消按钮调用后端并反馈状态 |
| P0 | 最终自动化验证 | 命令输出记录 | PASS：门禁通过，环境例外已记录 |
| P1 | 安全和隐私扫描 | 扫描记录 | PASS：没有 API key、token、原始券商导出文件 |
| P1 | PR 准备 | PR body 草稿 | PASS：包含改动、验证、deferred、风险 |
| P2 | 文档状态同步 | `project_docs/readme.md` 和 QA 文档 | PASS：文档已更新收口状态 |

## 3. 任务一：审查并拆分当前代码 diff

**目标：** 把当前未提交代码整理成 reviewer 能理解的提交边界。

**执行结果：** 2026-05-22 已拆成本地提交 `cb7b3fe`、`05ca355`、`0c3ba9e`，最终文档收口另有独立提交。提交前未发现需要回滚的用户改动。

**文件：**

- 审查：全部 `git status --short` 中的代码文件
- 修改：通常不需要，除非发现明显漏改
- 文档：`project_docs/REMAINING_ACCEPTANCE_20260521.md`

- [x] 查看当前状态。

运行：

```bash
git status --short --branch
git diff --stat
git diff --check
```

预期：`git diff --check` 无输出；diff 都属于本轮稳定化。

- [x] 按主题审查 diff。

建议分组：

1. 后端统计和测试：`backend/app/api/v1/endpoints/statistics.py`、`tests/integration/test_api_statistics.py`
2. Dashboard 和评分解释：`frontend/src/components/common/GradeBadge.tsx`、`frontend/src/components/dashboard/NeedsReviewPanel.tsx`、`frontend/src/pages/Dashboard.tsx`、`frontend/src/pages/Positions.tsx`、`frontend/src/pages/Statistics.tsx`
3. Backtest、取消流程、可访问性和空状态：`frontend/src/pages/Backtest.tsx`、`frontend/src/components/processing/ProcessingLogPanel.tsx`、相关 processing/loading 组件
4. lint 清理：`frontend/eslint.config.js`、hooks、charts、测试文件
5. 文档：`project_docs/ACCEPTANCE_CHECKLIST_20260521.md`、本文档、对应验收文档

- [x] 做提交前策略决定。

推荐提交顺序：

```bash
git add backend/app/api/v1/endpoints/statistics.py tests/integration/test_api_statistics.py
git commit -m "fix(statistics): align grade and risk metrics"

git add backend/app/api/v1/endpoints/dashboard.py backend/app/api/v1/endpoints/positions.py backend/app/schemas/dashboard.py frontend/src/api/client.ts frontend/src/types/index.ts frontend/src/components/common/GradeBadge.tsx frontend/src/components/dashboard/NeedsReviewPanel.tsx frontend/src/components/dashboard/RecentTradesTable.tsx frontend/src/components/position-detail/TradeSummaryTab.tsx frontend/src/components/position-detail/RelatedPositionsTab.tsx frontend/src/pages/Dashboard.tsx frontend/src/pages/Positions.tsx frontend/src/pages/Statistics.tsx frontend/src/i18n/locales/en.ts frontend/src/i18n/locales/zh.ts frontend/src/utils/format.ts frontend/src/utils/format.test.ts
git commit -m "feat(ui): explain incomplete grades and review candidates"

git add frontend/src/pages/Backtest.tsx frontend/src/components/processing/ProcessingLogPanel.tsx frontend/src/components/processing/ProgressHeader.tsx frontend/src/components/processing/LogStream.tsx frontend/src/components/loading/BrandSection.tsx frontend/src/components/loading/ProgressPanel.tsx frontend/src/components/loading/TickingLogStream.tsx
git commit -m "fix(ui): complete backtest and cancel flow polish"

git add frontend/eslint.config.js frontend/src/components/charts frontend/src/components/common/EmptyState.tsx frontend/src/components/common/InitialCapitalModal.tsx frontend/src/components/common/Toast.tsx frontend/src/components/layout/Sidebar.tsx frontend/src/components/stats/TradingCalendar.tsx frontend/src/hooks frontend/src/pages/AnalysisLoading.tsx frontend/src/pages/LandingUpload.tsx frontend/src/pages/PositionDetail.tsx frontend/src/pages/TaskStatus.tsx frontend/src/pages/Upload.tsx frontend/src/store/usePrivacyStore.ts frontend/tests/e2e/performance.spec.ts
git commit -m "chore(frontend): restore lint gate"
```

注意：提交前如果发现某个文件包含前序用户改动，不要重置；只审查并确认它是否属于当前稳定化范围。

## 4. 任务二：补完整浏览器人工 QA

**目标：** 覆盖自动化 smoke 没有覆盖的关键用户路径。

**文件：**

- 更新：`project_docs/REMAINING_ACCEPTANCE_20260521.md`
- 必要时更新：`project_docs/QA_REPORT_20260520_v2.md`

- [x] 启动服务。

运行：

```bash
cd /Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix/backend
/Users/benzema/tradingcoach/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd /Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix/frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

如果 `8000` 已被占用，先确认已有服务是否就是当前 worktree 的后端；不要随手 kill 不明进程。

- [x] 检查 Landing/upload。

覆盖点：

- 文件选择器可打开。
- sample data 或现有上传入口可见。
- notification toggle 不报错。
- 任务恢复 banner 文案正确。
- 上传失败时错误态清楚。

- [x] 检查 Position detail。

至少打开一个真实持仓详情页，覆盖：

- Summary 评分 badge 能解释 `?`。
- Execution 表格币种和费用显示正确。
- Risk 指标不出现 `NaN`、`undefined`。
- Related positions 不因多币种或缺币种崩溃。
- News/event 区块空状态可理解。

- [x] 检查 AI Coach。

覆盖点：

- 面板能加载。
- 规则引擎 fallback 文案不误导成“服务坏了”。
- 基础提问有可见响应或明确限制。
- 没有 uncaught console error。

- [x] 检查移动端和双语。

最少视口：

- `390 x 844`
- `1365 x 900`

语言：

- 中文
- 英文

预期：无明显横向溢出；按钮文字不压出容器；关键卡片对比度可读。

## 5. 任务三：端到端实测取消流程

**目标：** 证明可见取消按钮真的能停止或请求停止后端任务。

**文件：**

- 核对：`frontend/src/components/processing/ProcessingLogPanel.tsx`
- 核对：`frontend/src/api/client.ts`
- 核对：`backend/app/api/v1/endpoints/tasks.py`
- 更新：`project_docs/REMAINING_ACCEPTANCE_20260521.md`

- [x] 创建一个 pending/running 任务。

可用方式：

- 上传一个测试 CSV。
- 或使用现有开发入口创建任务。

- [x] 点击取消按钮。

验收点：

- Network 中调用 `DELETE /api/v1/tasks/{task_id}`。
- 成功时出现 success toast。
- 任务状态变成 `cancelled` 或显示后端返回的无法取消原因。
- completed、failed、cancelled 状态不显示可操作取消按钮。

- [x] 记录失败分支。

如果后端返回 `success: false` 或 HTTP error，UI 必须显示 error toast，并保留一致状态。

## 6. 任务四：最终自动化验证

**目标：** 提交和 PR 前重跑全部门禁，避免 QA 手工检查后引入回归。

运行：

```bash
cd /Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/data_integrity/ -q
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/unit/test_symbol_parser.py tests/unit/test_fifo_matcher.py -q
/Users/benzema/tradingcoach/.venv/bin/python -m pytest tests/integration/ -q
```

```bash
cd /Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix/frontend
npm run typecheck
npm run lint
npm run test:unit
npm run build
```

预期：全部通过；结果同步到验收文档。

## 7. 任务五：安全和隐私扫描

**目标：** PR 前确认没有 secrets、token、真实券商原始导出或隐私数据进入提交。

运行：

```bash
cd /Users/benzema/tradingcoach/.claude/worktrees/tradingcoach-fix
rg -n "(sk-|api[_-]?key|secret|token|password|PRIVATE KEY|BEGIN RSA|AWS_ACCESS|OPENAI)" .
git status --short
git diff --name-only
```

验收规则：

- 没有新增 API key、token、cookie、私钥。
- 没有新增真实券商 CSV、xlsx、截图等私密原始数据。
- 如果命中是文档示例或合法环境变量名，必须在验收文档写清楚。

## 8. 任务六：PR 准备

**目标：** reviewer 能快速知道改了什么、怎么验、还有什么没做。

**文件：**

- 更新：`project_docs/QA_REPORT_20260520_v2.md`，仅当 QA 结论变化
- 更新：`project_docs/readme.md`
- 可新增：`project_docs/PR_NOTES_20260521.md`

PR body 必须包含：

- 行为变化摘要。
- 数据口径变化：by-grade、Sharpe、费用占比、回撤百分比。
- UI 变化：`?` 评分解释、Dashboard 待复盘、Backtest 展示、取消流程。
- 自动化验证命令和结果。
- 浏览器 QA 覆盖范围和未覆盖范围。
- Deferred：例如更深入的上传大文件取消 race condition、完整视觉回归、AI Coach 后续产品化。

## 9. 最终完成定义

只有同时满足以下条件，才算可以开 PR：

- 当前工作区没有未解释的 untracked 或 dirty 文件。
- P0 自动化验证全部通过。
- Landing/upload、Dashboard、Statistics、Positions、Position detail、Backtest、AI Coach 都完成浏览器验收。
- 取消流程有真实任务验证记录。
- secret/privacy 扫描无阻断。
- PR notes 或 PR body 草稿已准备好。
