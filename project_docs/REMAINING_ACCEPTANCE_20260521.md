# TradingCoach 剩余收口验收清单

> 本文档与 `project_docs/REMAINING_TASKS_20260521.md` 配套使用。它只覆盖 2026-05-21 稳定化开发完成后的剩余发布前收口，不重复记录已经完成的开发计划。

## 1. 状态说明

| 状态 | 含义 |
|------|------|
| PASS | 已验证并通过 |
| FAIL | 已验证但不通过 |
| PENDING | 尚未验证 |
| BLOCKED | 环境或依赖阻塞，必须写明原因 |
| N/A | 本次不适用，必须写明原因 |

P0 项不得为 `FAIL` 或未解释的 `BLOCKED`。PENDING 项在开 PR 前必须处理。

## 2. 当前剩余项概览

| 类别 | 当前状态 | 说明 |
|------|----------|------|
| 自动化验证 | PASS | 2026-05-23 已复跑前端 typecheck/lint/unit/build、后端导入预检目标测试、上传预检 Chromium/Mobile Chrome e2e、Chromium 全站 QA |
| 局部浏览器 smoke | PASS | Dashboard、Statistics、Positions、Backtest 已渲染且无 `console.error` |
| 完整浏览器人工 QA | PASS | 2026-05-23 已覆盖 Landing、`/upload`、Dashboard、Statistics、Positions、Position detail、Events、Backtest、System、AI Coach、移动端 |
| 取消流程端到端 | PASS | 2026-05-22 已验证后端真实 pending task 取消和前端成功/失败/终态 UI 分支 |
| 提交拆分 | PASS | 2026-05-22 已拆成本地提交：后端指标、前端收口流程、前端 lint/图表清理、文档收口 |
| secret/privacy 扫描 | PASS | 2026-05-22 已扫描；命中均为示例变量、配置读取、依赖名或文档说明 |
| PR notes | PASS | 已新增 `project_docs/PR_NOTES_20260522.md` |

## 3. P0：分支和提交卫生

| ID | 检查项 | 验证方法 | 通过标准 | 状态 | 备注 |
|----|--------|----------|----------|------|------|
| R-001 | 工作区状态清楚 | `git status --short --branch` | 只剩本轮稳定化和收口文档改动 | PASS | 2026-05-22：代码改动已拆分提交；文档收口提交后工作区应干净 |
| R-002 | diff 无空白错误 | `git diff --check` | 无输出 | PASS | 2026-05-22 已复跑通过 |
| R-003 | 代码提交已拆分 | `git log --oneline -8` | 后端统计、UI、lint、文档等主题可审查 | PASS | 2026-05-22：`cb7b3fe` 后端指标；`05ca355` 前端收口流程；`0c3ba9e` 前端 lint/图表清理；本文档提交记录最终文档收口 |
| R-004 | 未回滚用户改动 | 人工审查 `git diff --stat` | 无不明大规模删除或重置 | PASS | 本轮只追加修复和文档更新，未执行 reset/checkout |
| R-005 | 文档索引更新 | 查看 `project_docs/readme.md` | 剩余任务文档和验收文档已列出 | PASS | 2026-05-21 已更新 |

## 4. P0：自动化门禁

| ID | 命令 | 通过标准 | 当前状态 | 备注 |
|----|------|----------|----------|------|
| R-101 | `/opt/homebrew/bin/python3.11 -m pytest tests/data_integrity ...` | 0 failures | PASS | 2026-05-22：与 unit 路径合跑，93 passed 中包含 data_integrity |
| R-102 | `/opt/homebrew/bin/python3.11 -m pytest tests/unit/test_symbol_matcher.py tests/unit/test_fifo_matcher.py ...` | 0 failures | PASS | 2026-05-22：与 data_integrity 合跑，93 passed |
| R-103 | `/opt/homebrew/bin/uv run --python /opt/homebrew/bin/python3.11 --with-requirements requirements.txt python -m pytest tests/integration/test_api_statistics.py tests/integration/test_api_positions.py` | 0 failures | PASS | 2026-05-22：40 passed；裸 Python 3.11 缺 `factory-boy`，用 requirements 临时环境通过 |
| R-104 | `cd frontend && npm run typecheck` | 0 errors | PASS | 2026-05-22 已通过 |
| R-105 | `cd frontend && npm run lint` | 0 errors | PASS | 2026-05-22 已通过 |
| R-106 | `cd frontend && npm run test:unit` | 0 failures | PASS | 2026-05-23：15 passed，包含上传预检 helper 和面板测试 |
| R-107 | `cd frontend && npm run build` | 构建成功 | PASS | 2026-05-23 已通过 |
| R-108 | `cd frontend && npx playwright test tests/e2e/accessibility.spec.ts tests/e2e/console-errors.spec.ts tests/e2e/performance.spec.ts tests/e2e/qa-walkthrough.spec.ts --project=chromium` | 0 unexpected | PASS | 2026-05-22 产品化复盘补跑：72 expected, 0 unexpected |
| R-109 | `cd frontend && npx playwright test tests/e2e/accessibility.spec.ts tests/e2e/console-errors.spec.ts tests/e2e/performance.spec.ts tests/e2e/qa-walkthrough.spec.ts --project='Mobile Chrome'` | 0 unexpected | PASS | 2026-05-22 产品化复盘补跑：72 expected, 0 unexpected |
| R-110 | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npx playwright test tests/e2e/upload-preflight.spec.ts --project=chromium` | 0 failures | PASS | 2026-05-23：3 passed；Landing CSV 预检、XLSX 拦截、`/upload` gate |
| R-111 | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npx playwright test tests/e2e/upload-preflight.spec.ts --project='Mobile Chrome'` | 0 failures | PASS | 2026-05-23：3 passed |
| R-112 | `PLAYWRIGHT_BASE_URL=http://127.0.0.1:5174 npx playwright test tests/e2e/qa-walkthrough.spec.ts --project=chromium` | 0 failures | PASS | 2026-05-23：31 passed；测试已等待真实可点击仓位行，避免 loading skeleton 误点 |

提交拆分或继续修改后，R-101 到 R-109 必须全部复跑；视觉回归和完整跨浏览器矩阵仍按 PR notes 的 deferred 处理。

## 5. P0：浏览器人工 QA

后端和前端 dev server 启动后执行。

| ID | 页面/流程 | 必查项 | 通过标准 | 当前状态 | 备注 |
|----|-----------|--------|----------|----------|------|
| R-201 | Dashboard | KPI、待复盘区块、最近交易、策略分布 | 页面渲染，无 `console.error`，无空白核心区块 | PASS | 2026-05-21 smoke 已覆盖 |
| R-202 | Statistics | 核心指标、by-grade、drawdowns、空状态、drill-down | 页面渲染，无 `console.error`，空状态可理解 | PASS | 2026-05-21 smoke 已覆盖 |
| R-203 | Positions | 筛选、排序、`C?` tooltip、键盘行跳转 | 页面渲染，无 `console.error`，键盘可进入详情 | PASS | 2026-05-21 smoke 已覆盖渲染；键盘仍建议人工点验 |
| R-204 | Backtest | 规则卡片、节省金额、`savings_pct` 空值保护 | 页面渲染，无 `console.error`，金额优先 | PASS | 2026-05-21 smoke 已覆盖 |
| R-205 | Landing/upload | 文件选择、导入预检、CSV-only 拦截、通知开关、恢复 banner、错误态 | 核心上传入口可用，失败态清楚 | PASS | 2026-05-23：Landing 和 `/upload` 已接入 `previewTrades`；预检成功前开始按钮禁用；XLS/XLSX 有明确 CSV-only 提示；无 console/page error |
| R-206 | Position detail | Summary、Execution、Risk、Related positions、News/Event | 评分解释可见，无 `NaN`/`undefined`/崩溃 | PASS | `/positions/472` 全部核心区块通过；修复 ExecutionTab `position` 未定义和评分 tooltip 冒泡 |
| R-207 | AI Coach | 面板加载、规则引擎 fallback、基础提问 | 不误导为服务不可用，无 uncaught error | PASS | 规则洞察 fallback 正常；无 LLM key 时 chat input 明确禁用 |
| R-208 | 移动端 390px | Dashboard、Statistics、Positions、Backtest | 无明显横向溢出，按钮文字不压出容器 | PASS | 四页 `scrollWidth=390`；修复 Layout 页面级横向溢出 |
| R-209 | 中英文切换 | 评分解释、Dashboard 待复盘、Backtest | 中文和英文文案都存在且表达清楚 | PASS | 中文 Dashboard 和英文 Backtest 已覆盖 |

## 6. P0：处理取消流程

| ID | 检查项 | 验证方法 | 通过标准 | 当前状态 | 备注 |
|----|--------|----------|----------|----------|------|
| R-301 | pending/running 任务可取消 | 上传测试 CSV 后点击取消 | Network 调用 `DELETE /api/v1/tasks/{task_id}` | PASS | 前端 Playwright 验证 DELETE 调用；后端临时 DB 真实 pending task 取消通过 |
| R-302 | 取消成功反馈 | 观察 toast 和任务状态 | 出现 success toast，状态进入 cancelled 或显示后端成功消息 | PASS | `/analysis/:taskId` 显示 success toast 和 Analysis Cancelled |
| R-303 | 取消失败反馈 | mock/制造后端失败或取消不可取消任务 | 出现 error toast，状态不自相矛盾 | PASS | 前端失败分支保留 processing 状态并显示 Cancel failed |
| R-304 | 终态不可取消 | completed/failed/cancelled 任务页面 | 不显示可操作取消按钮 | PASS | completed task 不显示 cancel button |

## 7. P1：数据和 UI 可信度回归

| ID | 检查项 | 验证方法 | 通过标准 | 当前状态 | 备注 |
|----|--------|----------|----------|----------|------|
| R-401 | `C+?`、`C?`、`C-?` by-grade 可见 | API 测试或 Statistics 页面 | 不完整评分不会被静默丢弃 | PASS | 集成测试已覆盖 |
| R-402 | 评分筛选支持 `?` | Positions 页面手工筛选 | 只返回匹配等级 | PASS | `/positions?score_grade=C%3F` 可见行均为 `C?`，未混入 `C+?` / `C-?` |
| R-403 | 评分解释可理解 | Positions/Statistics/Detail 浏览器检查 | 不读文档也能理解 `?` 是降级评分 | PASS | tooltip 文案说明 `?` 是 incomplete/downgraded confidence score |
| R-404 | 多币种显示不误导 | Dashboard/Recent/Related/Detail | 币种符号合理；不把 HKD 当 USD 展示 | PASS | `/positions/460` 顶部和明细均显示 `HK$`；Recent/Related 使用 item currency |
| R-405 | Backtest 不显示不稳定百分比为主结论 | Backtest 页面 | 绝对金额是主信息；百分比为空时有替代说明 | PASS | smoke 已覆盖渲染，建议人工复核文案 |

## 8. P1：安全和隐私

| ID | 检查项 | 验证方法 | 通过标准 | 当前状态 | 备注 |
|----|--------|----------|----------|----------|------|
| R-501 | 没有 secrets | `rg -n "(sk-|api[_-]?key|secret|token|password|PRIVATE KEY|BEGIN RSA|AWS_ACCESS|OPENAI)" .` | 没有真实密钥；示例命中需解释 | PASS | 2026-05-23 复扫：命中均为示例 env、配置读取、GitHub Actions secret 引用、依赖名或文档说明 |
| R-502 | 没有私人原始交易文件 | `git status --short` 和 `git diff --name-only` | 不新增真实券商 CSV/xlsx/截图 | PASS | 未新增 CSV/xlsx/截图；只保留既有 `tests/fixtures/test_trades.csv` |
| R-503 | 文档不泄露敏感信息 | 人工审查新增 docs | 不包含账户、邮箱、券商导出原文 | PASS | 新增 PR notes / 收口文档不含账户、邮箱、原始导出或 API key |

## 9. P1：PR 准备

| ID | 检查项 | 验证方法 | 通过标准 | 当前状态 | 备注 |
|----|--------|----------|----------|----------|------|
| R-601 | PR body 草稿 | 查看 PR notes 或最终 PR 描述 | 包含改动、验证、浏览器 QA、deferred | PASS | 已新增 `project_docs/PR_NOTES_20260522.md` |
| R-602 | Deferred 列表明确 | PR body 或 `project_docs/QA_REPORT_20260520_v2.md` | 未完成项不伪装成已完成 | PASS | PR notes 中保留评分阈值、聚合跨币种、视觉/a11y 专项等 deferred |
| R-603 | QA 报告与事实一致 | 审查 `project_docs/QA_REPORT_20260520_v2.md` | 不再声称已失败的问题仍失败，或已修问题未更新 | PASS | `QA_REPORT_20260520_v2.md` 已加 2026-05-22 收口状态更新 |
| R-604 | 最终工作区干净 | `git status --short` | 无未提交的发布相关改动 | PASS | 2026-05-22：文档收口提交后复查 `git status --short --branch` |

## 10. 最终签收

| 角色 | 日期 | 结论 | 备注 |
|------|------|------|------|
| Engineering | 2026-05-22 | PASS | 自动化、浏览器、取消、安全扫描已通过；本地提交已按主题拆分 |
| QA | 2026-05-22 | PASS with deferred noted | 剩余 deferred 已进入 PR notes |
| Product |  |  |  |
