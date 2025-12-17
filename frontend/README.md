# frontend - React 前端应用

现代化的 React SPA 应用，为 Trading Coach 提供交互式用户界面。

## 设计思路

采用组件化架构，将 UI 拆分为可复用的独立组件：

```
frontend/
├── src/
│   ├── main.tsx           # 应用入口
│   ├── App.tsx            # 根组件 + 路由
│   ├── pages/             # 页面组件
│   │   ├── Dashboard.tsx  # 仪表板首页
│   │   ├── Positions.tsx  # 持仓列表
│   │   ├── PositionDetail.tsx # 持仓详情
│   │   ├── Statistics.tsx # 统计报告 (报告式布局)
│   │   ├── Reports.tsx    # 报告页面
│   │   └── System.tsx     # 系统信息
│   ├── components/        # 可复用组件
│   │   ├── layout/        # 布局组件
│   │   │   ├── Layout.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── dashboard/     # 仪表板组件
│   │   │   ├── KPICard.tsx
│   │   │   └── RecentTradesTable.tsx
│   │   ├── charts/        # 图表组件
│   │   │   ├── EquityCurveChart.tsx
│   │   │   ├── EquityDrawdownChart.tsx
│   │   │   ├── MonthlyPerformanceChart.tsx
│   │   │   ├── PnLDistributionChart.tsx
│   │   │   ├── RollingWinRateChart.tsx
│   │   │   ├── TradingHeatmap.tsx
│   │   │   ├── HourlyPerformanceChart.tsx
│   │   │   ├── DurationPnLChart.tsx
│   │   │   ├── SymbolRiskQuadrant.tsx
│   │   │   ├── AssetTypeChart.tsx
│   │   │   ├── StrategyPerformanceChart.tsx
│   │   │   ├── StrategyPieChart.tsx
│   │   │   └── PriceChart.tsx
│   │   ├── report/        # 报告专用组件
│   │   │   ├── ReportSection.tsx    # 带编号的章节
│   │   │   ├── ChartWithInsight.tsx # 图表+洞察
│   │   │   ├── HeroSummary.tsx      # 顶部摘要
│   │   │   └── CollapsibleTable.tsx # 可折叠表格
│   │   ├── common/        # 通用组件
│   │   │   ├── DrillDownModal.tsx
│   │   │   └── InfoTooltip.tsx
│   │   └── insights/      # AI 洞察组件
│   │       └── AICoachPanel.tsx
│   ├── api/               # API 客户端
│   │   └── client.ts
│   ├── stores/            # 状态管理 (Zustand)
│   ├── types/             # TypeScript 类型定义
│   ├── i18n/              # 国际化配置
│   └── utils/             # 工具函数
│       ├── format.ts      # 格式化工具
│       └── insights.ts    # 洞察文案生成
├── public/                # 静态资源
└── package.json           # 依赖配置
```

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 19.2 |
| 语言 | TypeScript | 5.9 |
| 构建工具 | Vite | 7.2 |
| 样式 | Tailwind CSS | 4.1 |
| 路由 | React Router | 7.10 |
| 状态管理 | Zustand | 5.0 |
| 数据请求 | TanStack Query | 5.90 |
| 图表 | Recharts | 3.5 |
| HTTP 客户端 | Axios | 1.13 |
| 图标 | Lucide React | 0.555 |

## 页面结构

### Dashboard (仪表板)
- KPI 卡片：总盈亏、胜率、交易次数等
- 权益曲线图
- 策略分布饼图
- 最近交易列表

### Positions (持仓)
- 持仓列表表格 (分页+筛选)
- 支持按 symbol、direction、status 过滤
- 支持按评分、盈亏排序

### Statistics (统计报告)

采用报告式布局，从"看表格"转变为"读报告"的体验：

**设计风格**: Dashboard Pro - 双色极简 (黑白为主，红绿仅用于盈亏)

**页面结构**:
- **Hero Summary**: 顶部大数字摘要 - 净盈亏 + 关键指标
- **01 / Performance**: 权益曲线 + 月度表现 + 洞察文案
- **02 / Risk Analysis**: 风险指标 + 盈亏分布 + 滚动胜率
- **03 / Trading Behavior**: 交易热力图 + 时段分析 + 持仓时长
- **04 / Portfolio**: 标的风险象限 + 资产类型 + 策略分布
- **05 / Detailed Data**: 可折叠的详细表格

**报告组件** (`components/report/`):
- `ReportSection` - 带编号的章节组件 (01/, 02/, etc.)
- `ChartWithInsight` - 图表+洞察文字组合
- `HeroSummary` - 顶部大数字摘要区域
- `CollapsibleTable` - 可折叠表格

**洞察生成** (`utils/insights.ts`):
- 自动生成图表洞察文案 (支持中英文)
- 包含权益曲线、月度表现、盈亏分布、时段分析等

### System (系统)
- 健康检查
- 数据库统计
- 系统版本信息

## 启动开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

开发服务器默认运行在 http://localhost:5173

## 构建生产版本

```bash
# 类型检查 + 构建
npm run build

# 预览构建结果
npm run preview
```

构建产物输出到 `dist/` 目录。

## API 对接

前端通过 Axios 与后端 FastAPI 通信：

```typescript
// src/services/api.ts
const API_BASE_URL = 'http://localhost:8000/api/v1';

export const dashboardApi = {
  getOverview: () => axios.get(`${API_BASE_URL}/dashboard/overview`),
  getKPIs: () => axios.get(`${API_BASE_URL}/dashboard/kpis`),
  getRecentTrades: () => axios.get(`${API_BASE_URL}/dashboard/recent-trades`),
  getEquityCurve: () => axios.get(`${API_BASE_URL}/dashboard/equity-curve`),
};

export const positionsApi = {
  getList: (params) => axios.get(`${API_BASE_URL}/positions`, { params }),
  getById: (id) => axios.get(`${API_BASE_URL}/positions/${id}`),
};
```

## 状态管理

使用 Zustand 进行轻量级状态管理：

```typescript
// src/stores/useFilterStore.ts
import { create } from 'zustand';

interface FilterState {
  symbol: string;
  direction: string;
  setSymbol: (symbol: string) => void;
  setDirection: (direction: string) => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  symbol: '',
  direction: '',
  setSymbol: (symbol) => set({ symbol }),
  setDirection: (direction) => set({ direction }),
}));
```

## 数据请求

使用 TanStack Query 管理服务端状态：

```typescript
// src/pages/Dashboard.tsx
import { useQuery } from '@tanstack/react-query';

function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'kpis'],
    queryFn: () => dashboardApi.getKPIs(),
    staleTime: 30_000, // 30秒缓存
  });

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;

  return <KPICards data={data} />;
}
```

## 组件设计

### KPICard 组件

```tsx
interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
}

function KPICard({ title, value, change, icon }: KPICardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <span className="text-gray-500">{title}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold mt-2">{value}</div>
      {change !== undefined && (
        <span className={change >= 0 ? 'text-green-500' : 'text-red-500'}>
          {change >= 0 ? '+' : ''}{change}%
        </span>
      )}
    </div>
  );
}
```

### 布局组件

```tsx
// src/components/layout/Layout.tsx
function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-6 bg-gray-50">
        {children}
      </main>
    </div>
  );
}
```

## 代码规范

### ESLint

```bash
# 运行代码检查
npm run lint
```

### TypeScript

所有组件使用严格类型：

```typescript
// src/types/position.ts
export interface Position {
  id: number;
  symbol: string;
  direction: 'long' | 'short';
  open_price: number;
  close_price?: number;
  quantity: number;
  net_pnl?: number;
  overall_score?: number;
  score_grade?: string;
}
```

## 环境变量

创建 `.env.local` 配置环境变量：

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=Trading Coach
```

## 样式规范

使用 Tailwind CSS 4 utility-first 方法：

```tsx
// 响应式设计
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

// 暗色模式 (计划中)
<div className="bg-white dark:bg-gray-800">

// 动画
<button className="transition-colors hover:bg-blue-600">
```

## 扩展计划

- [x] 暗色模式支持 (已完成)
- [x] 国际化 i18n (已完成 - 中/英文)
- [x] 报告式布局 (Statistics 页面)
- [ ] PWA 支持
- [ ] 单元测试 (Vitest)
- [ ] E2E 测试 (Playwright)
- [ ] PDF 导出
