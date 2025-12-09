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
│   │   ├── Statistics.tsx # 统计分析
│   │   └── System.tsx     # 系统信息
│   ├── components/        # 可复用组件
│   │   ├── layout/        # 布局组件
│   │   │   ├── Layout.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── dashboard/     # 仪表板组件
│   │   │   ├── KPICard.tsx
│   │   │   └── RecentTradesTable.tsx
│   │   └── charts/        # 图表组件
│   │       ├── EquityCurveChart.tsx
│   │       └── StrategyPieChart.tsx
│   ├── services/          # API 服务层
│   ├── stores/            # 状态管理 (Zustand)
│   ├── types/             # TypeScript 类型定义
│   └── utils/             # 工具函数
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

### Statistics (统计)
- 按股票统计
- 按月份统计
- 按策略统计

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

- [ ] 暗色模式支持
- [ ] 国际化 (i18n)
- [ ] PWA 支持
- [ ] 单元测试 (Vitest)
- [ ] E2E 测试 (Playwright)
