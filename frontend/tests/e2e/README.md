# E2E 测试指南

一旦我所属的文件夹有所变化，请更新我

## 架构说明

E2E 测试使用 Playwright 框架，覆盖用户流程、视觉回归、控制台错误监控、性能测试和可访问性测试。

## 目录结构

```
tests/e2e/
├── README.md                       # 本文档
├── helpers/
│   └── test-utils.ts               # 测试工具函数
├── visual-regression/
│   └── visual-regression.spec.ts   # 视觉回归测试
├── console-errors.spec.ts          # 控制台错误监控
├── performance.spec.ts             # 性能测试
├── accessibility.spec.ts           # 可访问性测试
└── qa-walkthrough.spec.ts          # 用户流程测试
```

## 文件清单

| 文件名 | 角色 | 功能 |
|--------|------|------|
| `helpers/test-utils.ts` | 工具库 | 提供 ConsoleErrorCollector, VisualRegressionHelper 等 |
| `console-errors.spec.ts` | 错误监控 | 检测所有页面的控制台错误 |
| `performance.spec.ts` | 性能测试 | 验证页面加载、渲染性能 |
| `accessibility.spec.ts` | 可访问性 | 验证键盘导航、ARIA 标签等 |
| `visual-regression.spec.ts` | 视觉回归 | 截图对比检测 UI 变化 |
| `qa-walkthrough.spec.ts` | 用户流程 | 完整用户操作流程测试 |

---

## 快速开始

### 前置条件

```bash
# 安装 Playwright
npx playwright install chromium

# 确保服务运行
# 后端: http://localhost:8000
# 前端: http://localhost:5173
```

### 运行测试

```bash
# 运行所有 E2E 测试
npm run test:e2e

# 运行特定类型测试
npm run test:e2e:console   # 控制台错误测试
npm run test:e2e:perf      # 性能测试
npm run test:e2e:a11y      # 可访问性测试
npm run test:e2e:visual    # 视觉回归测试
npm run test:e2e:qa        # 用户流程测试

# UI 模式（可视化调试）
npm run test:e2e:ui
```

---

## 测试类型详解

### 1. 控制台错误监控 (`console-errors.spec.ts`)

监控所有页面的 JavaScript 错误和警告。

**测试覆盖：**
- 各页面无控制台错误
- 用户交互不产生错误
- 暗色模式切换无错误
- 语言切换无错误
- API 错误优雅处理

**运行：**
```bash
npm run test:e2e:console
```

### 2. 性能测试 (`performance.spec.ts`)

验证页面加载和渲染性能。

**性能阈值：**
| 指标 | 阈值 |
|------|------|
| 页面加载 | < 5s |
| DOM Ready | < 3s |
| 首次绘制 | < 2s |
| 图表渲染 | < 3s |
| 表格渲染 | < 2s |

**运行：**
```bash
npm run test:e2e:perf
```

### 3. 可访问性测试 (`accessibility.spec.ts`)

验证页面可访问性。

**测试覆盖：**
- 页面标题和标题标签
- 键盘导航
- 颜色对比度
- 表单标签
- ARIA 地标
- 焦点管理

**运行：**
```bash
npm run test:e2e:a11y
```

### 4. 视觉回归测试 (`visual-regression/`)

截图对比检测 UI 变化。

**测试覆盖：**
- 各页面桌面/平板/移动端截图
- 暗色模式截图
- 关键组件截图

**更新基准截图：**
```bash
npx playwright test tests/e2e/visual-regression/ --update-snapshots
```

### 5. 用户流程测试 (`qa-walkthrough.spec.ts`)

完整用户操作流程测试。

**测试覆盖：**
- Dashboard KPI 卡片
- Statistics 图表交互
- Positions 列表和筛选
- Position 详情页
- 暗色模式和国际化
- 响应式布局
- 错误处理

---

## 测试工具函数 (`helpers/test-utils.ts`)

### ConsoleErrorCollector

收集页面控制台错误：

```typescript
const collector = new ConsoleErrorCollector(page);
await page.goto('/dashboard');
await assertNoConsoleErrors(collector);
```

### VisualRegressionHelper

视觉回归测试辅助：

```typescript
const helper = new VisualRegressionHelper(page, 'screenshots');
await helper.captureFullPage('dashboard');
```

### 等待辅助函数

```typescript
await waitForNetworkIdle(page);
await waitForChartLoad(page);
await waitForTableLoad(page);
```

### 响应式测试

```typescript
import { VIEWPORTS } from './helpers/test-utils';

await page.setViewportSize(VIEWPORTS.mobile);
await page.setViewportSize(VIEWPORTS.tablet);
await page.setViewportSize(VIEWPORTS.desktop);
```

---

## CI/CD 集成

在 GitHub Actions 中配置：

```yaml
e2e:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - run: npx playwright install chromium
    - run: npm run test:e2e
```

---

## 调试技巧

### UI 模式

```bash
npx playwright test --ui
```

### 生成 Trace

```bash
npx playwright test --trace on
npx playwright show-trace trace.zip
```

### 截图调试

```bash
npx playwright test --screenshot on
```

### 慢速执行

```bash
npx playwright test --slow-mo 1000
```

---

## 常见问题

### 服务未运行

确保后端和前端服务正在运行：

```bash
# 后端
cd backend && uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm run dev
```

### 选择器失效

使用 Playwright Codegen 重新生成选择器：

```bash
npx playwright codegen http://localhost:5173
```

### 视觉回归失败

更新基准截图：

```bash
npx playwright test --update-snapshots
```
