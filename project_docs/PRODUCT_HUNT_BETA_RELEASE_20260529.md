# TradingCoach Product Hunt Beta 发布执行记录

日期：2026-05-29

## 本轮已完成

- 匿名临时 workspace：
  - 新增 `POST /api/v1/workspaces` 创建 workspace token。
  - 前端通过 `X-Workspace-Token` 自动发送 token。
  - 用户数据接口不再无 token 回落到全局数据库；无 token 返回空数据，失效 token 返回 401。
  - 每个 workspace 使用独立 SQLite DB，默认 72 小时 TTL，创建/访问时执行过期清理。
  - 新增 `DELETE /api/v1/workspaces/current` 删除当前 workspace 数据并让 token 失效。
- Sample-first demo：
  - 新增 `POST /api/v1/workspaces/sample`，创建独立 workspace 并导入匿名 sample CSV。
  - Landing 主 CTA 改为 `Try Sample Data`，次 CTA 为 `Upload Your CSV`。
  - 样本数据导入后可进入 Statistics，并能看到 Positions/Backtest/AI Coach 所需的基础数据。
- 真实 CSV 上传：
  - Landing 和 `/upload` 在创建任务前会先确保 workspace token 存在。
  - 预检仍然只读，不要求 workspace token。
  - 任务创建、状态查询、取消、列表都按 workspace DB 隔离。
- 隐私/发布口径：
  - Landing 增加 Beta 数据说明：CSV-only、no broker login、not investment advice、72h TTL。
  - `.env.example` 增加 `WORKSPACE_TTL_HOURS` / `WORKSPACE_DATA_DIR`。
  - 前端 `.env.example` 增加 beta API 子域名示例。

## 验收结果

- 后端目标测试：
  - `/opt/homebrew/bin/python3.11 -m pytest tests/unit/test_import_preflight.py tests/integration/test_api_upload_preflight.py tests/unit/test_workspace_service.py tests/integration/test_api_workspaces.py tests/unit/test_incremental_importer_workspace.py -q`
  - 结果：12 passed。
- 前端目标测试：
  - `npm run typecheck`
  - `npm run test:unit -- workspaceToken.test.ts --run`
  - 结果：通过。
- 浏览器 QA：
  - Landing desktop：主/次 CTA 可见，无 console error。
  - Sample flow：`Try Sample Data` → `/statistics`，显示 5 个持仓的样本分析，无 `NaN/undefined`。
  - Upload flow：使用 `tests/fixtures/test_trades.csv`，预检通过，`Start Analysis` 可点击，进入 `/analysis/:taskId` 并完成任务。
  - Mobile 390px：Landing 无横向溢出，sample CTA 可见，无 console error。

## 仍需完成

- 部署前：
  - 配置真实 `CORS_ORIGINS=https://beta.<domain>`。
  - 配置前端 `VITE_API_BASE_URL=https://api-beta.<domain>/api/v1`。
  - 确认 `DEBUG=false`，`ADMIN_TOKEN` 已设置。
  - 若启用 Sentry，确认 headers/cookies/body/token scrub。
- PH 素材：
  - Gallery 1：Sample data 一键体验。
  - Gallery 2：上传预检。
  - Gallery 3：AI Coach 行为问题。
  - Gallery 4：Position detail 复盘。
  - Gallery 5：Backtest 历史模拟。
  - 录制 30-45 秒 demo video。
- 发布文案：
  - Name: `TradingCoach`
  - Tagline: `Find the trading habits your P&L won’t show you`
  - Maker comment 需明确：交易复盘工具，不是投资建议；目前 CSV-only；希望大家反馈券商格式和分析可解释性。
