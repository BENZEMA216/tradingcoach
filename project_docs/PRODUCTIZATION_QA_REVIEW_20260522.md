# TradingCoach 产品化 QA 复盘 - 2026-05-22

> 目标：从发布前 QA 的角度，把当前项目的自动化测试、浏览器回归、残留风险和下一步验收口径整理清楚。本文不替代 `REMAINING_ACCEPTANCE_20260521.md`，而是补充本轮“产品化复盘”的事实记录。

## 1. 当前结论

当前分支已经达到“可以进入 PR 审查”的质量状态，但还不应宣称“产品化完成”。核心业务路径、前端静态门禁、后端测试、Chromium/Mobile Chrome 非视觉 e2e 都已通过；剩余风险主要集中在视觉回归基线、跨浏览器矩阵、数据导入体验、评分解释深度和跨币种聚合口径。

## 2. 自动化验证记录

| 类别 | 命令/范围 | 结果 | 备注 |
|------|-----------|------|------|
| 前端类型检查 | `cd frontend && npm run typecheck` | PASS | 2026-05-22 本轮测试修复后复跑通过 |
| 前端 lint | `cd frontend && npm run lint` | PASS | 2026-05-22 本轮测试修复后复跑通过 |
| 前端单测 | `cd frontend && npm run test:unit` | PASS | 本轮前序验证：2 files / 9 tests passed |
| 前端构建 | `cd frontend && npm run build` | PASS | 本轮前序验证通过；生产 JS 总量约 1.24MB，低于 2MB e2e 预算 |
| 后端全量测试 | `uv run --python /opt/homebrew/bin/python3.11 --with-requirements requirements.txt python -m pytest tests --tb=short` | PASS | 本轮前序验证：568 passed, 24 skipped |
| Chromium 非视觉 e2e | accessibility / console-errors / performance / qa-walkthrough | PASS | 72 expected, 0 unexpected |
| Mobile Chrome 非视觉 e2e | accessibility / console-errors / performance / qa-walkthrough | PASS | 72 expected, 0 unexpected |
| 全量 e2e | `npm run test:e2e` | FAIL 已记录 | 前序运行 129 passed 后失败，主要是视觉基线、跨浏览器环境和旧测试选择器问题；本轮已修复核心选择器，视觉/全矩阵仍列为 deferred |

## 3. 本轮修复的 QA 基础设施问题

| 问题 | 根因 | 处理 |
|------|------|------|
| 移动端 e2e 点击离屏 sidebar | CSS transform 关闭的 sidebar 在 Playwright 中仍可能被判定为 visible | 移动端导航测试改走直接路由或移动端安全路径 |
| Position detail 测试放大列表点击失败 | 详情页每个测试都先从列表点入，移动端一个点击问题会造成 4 个用例失败 | 详情页测试改为直接进入稳定 fixture `/positions/472`；列表点击保留在独立用例中 |
| Back button fallback 错误 | 详情页 direct setup 没有浏览器历史，`goBack()` 会回到 `about:blank` | fallback 改为进入 `/positions` |
| Bundle size 用例误测开发态 JS | Vite dev server 返回未优化模块，9MB 不能代表生产包 | 用例优先读取 `dist/assets/*.js` 生产构建产物；无 `dist` 时才使用宽松 dev fallback |
| 桌面导航选择器选中隐藏元素 | sidebar/nav 中存在多份响应式元素 | 选择器增加可见性过滤，并在 README 记录移动端约束 |

## 4. 浏览器人工回归

### 桌面

使用内置浏览器打开 `http://localhost:5173/dashboard`，确认：

- 页面标题为 `TradingCoach`。
- `main` 存在。
- 未出现 `NaN` / `undefined`。
- 无页面级横向溢出。
- 数据加载后 KPI、待复盘、权益曲线、策略分布、最近交易可见。

截图：`/tmp/tradingcoach-qa-20260522/dashboard-browser-final.png`

### 移动端 390 x 844

使用 Playwright 移动端视口扫过以下页面：

| 页面 | 结果 |
|------|------|
| `/dashboard` | PASS：有 `main`，无 `NaN/undefined`，无页面级横向溢出 |
| `/positions` | PASS：有 `main`，无 `NaN/undefined`，无页面级横向溢出 |
| `/positions/472` | PASS：有 `main`，无 `NaN/undefined`，无页面级横向溢出 |
| `/statistics` | PASS：有 `main`，无 `NaN/undefined`，无页面级横向溢出 |
| `/` upload/landing | PASS：有 `main`，无 `NaN/undefined`，无页面级横向溢出 |

截图目录：`/tmp/tradingcoach-qa-20260522/`

## 5. 当前残留风险

| 优先级 | 风险 | 影响 | 建议处理 |
|--------|------|------|----------|
| P0 for PR | 全量视觉回归未重新定基线 | PR 中可能有视觉截图失败 | PR 前决定：更新基线，或把视觉回归从本 PR gate 中拆出 |
| P1 | 非 Chromium 浏览器矩阵未收口 | Safari/Firefox 兼容性缺少最新结论 | 在 CI 或本机安装完整 Playwright browser 后单独跑矩阵 |
| P1 | 评分系统大量 `?` | 用户会看到“可信度不足”的评分，但不知道如何改善数据 | 在 UI 加“缺失字段原因”和“如何补齐”的解释 |
| P1 | 跨币种聚合口径 | Dashboard 总 P&L 会混合 USD/HKD 等币种，容易误读 | 后端返回 base currency + FX conversion + currency breakdown |
| P1 | 数据导入仍依赖用户导出文件 | 新用户 onboarding 摩擦大，且券商 CSV 格式不稳定 | 建 broker connection / import assistant / schema mapping 三层能力 |
| P2 | 图表 ResizeObserver/Recharts warning | 不阻断用户，但影响测试噪音和 QA 信噪比 | 固定 chart container 尺寸，减少初始宽高为 -1 的渲染 |

## 6. 下一轮验收建议

下一轮不要再只问“页面能不能打开”，要按产品化验收：

1. 新用户能在 5 分钟内导入一份真实交易记录，并看到可解释的第一份复盘报告。
2. 老用户能追加导入，系统能识别重复、增量、手续费、期权腿和币种。
3. 每个评分或建议都能说明“依据是什么、缺什么数据、下一步怎么做”。
4. AI Coach 不只是聊天，而是能生成 review queue、错因聚类、下周训练任务。
5. 隐私模式默认安全：不上传原始券商文件，不在前端日志暴露账户、订单号、token。

