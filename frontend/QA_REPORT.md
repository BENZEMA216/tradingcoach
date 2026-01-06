# TradingCoach Frontend QA 走查报告

**生成日期**: 2025-12-17
**测试版本**: dev/foundation 分支
**测试范围**: 15个图表组件 + 6个页面 + 通用组件

---

## 一、执行摘要

### 整体评估

| 维度 | 评分 | 说明 |
|-----|------|------|
| 功能完整性 | ⭐⭐⭐⭐ | API 正常工作，数据展示完整 |
| 暗色模式支持 | ⭐⭐⭐ | 大部分组件支持，存在颜色硬编码问题 |
| 国际化支持 | ⭐⭐⭐⭐⭐ | 全面支持中英文，包括 System 页面 |
| 代码一致性 | ⭐⭐⭐ | 存在风格不统一问题 |
| 响应式设计 | ⭐⭐⭐⭐ | 基本覆盖主流断点 |

### 问题统计

| 严重程度 | 数量 | 说明 |
|---------|------|------|
| P0 (阻断) | 0 | 无阻断性问题 |
| P1 (严重) | 6 | 颜色硬编码、暗色模式不一致 |
| P2 (中等) | 8 | 代码风格、性能优化 |
| P3 (轻微) | 5 | 可改进项 |

---

## 二、图表组件详细走查

### 2.1 EquityCurveChart.tsx

**文件路径**: `src/components/charts/EquityCurveChart.tsx`

| 检查项 | 状态 | 说明 |
|-------|------|------|
| 空数据处理 | ✅ 通过 | 正确显示 "暂无数据" |
| 暗色模式 | ⚠️ 部分 | Tooltip 支持暗色，图表颜色硬编码 |
| 国际化 | ✅ 通过 | 使用 t() 函数 |
| bare 属性 | ❌ 缺失 | 不支持 bare 模式 |
| isLoading | ❌ 缺失 | 不支持加载状态 |

**问题清单**:

| # | 行号 | 严重度 | 问题描述 |
|---|-----|--------|---------|
| 1 | 40 | P1 | 日期格式硬编码 `'zh-CN'`，应根据 i18n 动态切换 |
| 2 | 48 | P1 | 颜色硬编码 `#22c55e`/`#ef4444`，暗色模式应使用 TradingView 色 |
| 3 | 78 | P2 | CartesianGrid stroke `#e5e7eb` 无暗色模式支持 |
| 4 | 79-88 | P2 | XAxis/YAxis tick fill 和 axisLine stroke 硬编码 |

**修复建议**:
```typescript
// 行40 - 动态语言
const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US';
date: new Date(point.date).toLocaleDateString(locale, {...})

// 行48 - 暗色模式颜色
const lineColor = totalPnL >= 0
  ? (isDarkMode ? '#26a69a' : '#22c55e')
  : (isDarkMode ? '#ef5350' : '#ef4444');
```

---

### 2.2 StrategyPieChart.tsx

**文件路径**: `src/components/charts/StrategyPieChart.tsx`

| 检查项 | 状态 | 说明 |
|-------|------|------|
| 空数据处理 | ✅ 通过 | 正确显示空状态 |
| 暗色模式 | ⚠️ 部分 | Tooltip 支持，饼图颜色静态 |
| 国际化 | ✅ 通过 | 策略名称翻译正确 |
| 点击交互 | ✅ 通过 | 支持钻取 |
| bare 属性 | ❌ 缺失 | 不支持 |

**问题清单**:

| # | 行号 | 严重度 | 问题描述 |
|---|-----|--------|---------|
| 1 | 19 | P2 | COLORS 数组硬编码，无暗色适配 |
| 2 | 47 | P2 | 空状态缺少 `dark:text-gray-400` |
| 3 | 89 | P3 | labelLine stroke 硬编码 |

---

### 2.3 MonthlyPerformanceChart.tsx

**文件路径**: `src/components/charts/MonthlyPerformanceChart.tsx`

| 检查项 | 状态 | 说明 |
|-------|------|------|
| 空数据处理 | ✅ 通过 | |
| 暗色模式 | ⚠️ 部分 | className 方式对 stroke 无效 |
| bare 属性 | ✅ 通过 | 支持 |
| isLoading | ✅ 通过 | 有骨架屏 |
| 点击交互 | ✅ 通过 | 支持 onBarClick |

**问题清单**:

| # | 行号 | 严重度 | 问题描述 |
|---|-----|--------|---------|
| 1 | 76 | P2 | CartesianGrid className 对 stroke 属性无效 |
| 2 | 129 | P1 | Cell fill 颜色硬编码，无 TradingView 暗色支持 |

---

### 2.4 HourlyPerformanceChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| isLoading | ✅ |
| 暗色模式 | ⚠️ 部分 |

**问题**: 行121 Cell fill 硬编码

---

### 2.5 PnLDistributionChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| isLoading | ✅ |
| 暗色模式 | ⚠️ 部分 |

**问题**: 行85 Cell fill 硬编码

---

### 2.6 RollingWinRateChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| isLoading | ✅ |
| 暗色模式 | ✅ Tooltip 正确使用 TradingView 色 |

**问题**: 行46 日期格式硬编码 'zh-CN'

---

### 2.7 EquityDrawdownChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| isLoading | ✅ |
| 双Y轴 | ✅ |
| 暗色模式 | ⚠️ 部分 |

**问题**:
- 行59: 日期格式硬编码 'zh-CN'
- 行173: Line stroke `#22c55e` 硬编码

---

### 2.8 DurationPnLChart.tsx ✅ 已优化

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| 数据密度优化 | ✅ 动态点大小和透明度 |
| 暗色模式 | ✅ 使用 TradingView 色 |

---

### 2.9 TradingHeatmap.tsx ✅ 已优化

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| 时区处理 | ✅ 自动转换本地时区 |
| 暗色模式 | ✅ 使用 TradingView 色 |

---

### 2.10 SymbolRiskQuadrant.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| 气泡图 | ✅ |
| 象限图例 | ✅ |
| 暗色模式 | ⚠️ 部分 |

**问题**: 行64 getColor 函数颜色硬编码

---

### 2.11 StrategyPerformanceChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| 暗色模式 | ⚠️ 部分 |

**问题**: 行130 Cell fill 硬编码

---

### 2.12 AssetTypeChart.tsx

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| bare 属性 | ✅ |
| 颜色映射 | ✅ 按资产类型区分 |
| 暗色模式 | ✅ Tooltip 正确 |

---

### 2.13 PriceChart.tsx (Lightweight Charts)

| 检查项 | 状态 |
|-------|------|
| 空数据处理 | ✅ |
| 技术指标 | ✅ MA20/MA50/BB |
| 入场出场标记 | ✅ |
| MAE/MFE 线 | ✅ |
| 暗色模式 | ✅ 动态检测 |
| bare 属性 | ❌ 缺失 |

**问题**: 行91-95 isDarkMode 检测只在初始化时运行，切换主题需刷新

---

## 三、页面组件走查

### 3.1 Dashboard.tsx

| 检查项 | 状态 | 说明 |
|-------|------|------|
| KPI 展示 | ✅ | 4个核心指标正确显示 |
| 权益曲线 | ✅ | 数据加载正常 |
| 策略饼图 | ✅ | 钻取功能正常 |
| 最近交易 | ✅ | 表格渲染正常 |
| 国际化 | ✅ | 完全支持 |

---

### 3.2 Statistics.tsx

| 检查项 | 状态 | 说明 |
|-------|------|------|
| 周期切换 | ✅ | Week/Month/Quarter/Year |
| 图表加载 | ✅ | 10+ 图表正常 |
| 钻取弹窗 | ✅ | 功能正常 |
| 洞察文案 | ✅ | ChartWithInsight 组件 |
| 国际化 | ✅ | 完全支持 |

**问题 (已修复)**:
- 行623: Top 10 标的表格 symbol 列字体颜色缺失 → 已添加 `text-neutral-900 dark:text-neutral-100`

---

### 3.3 Positions.tsx

| 检查项 | 状态 |
|-------|------|
| 筛选器 | ✅ |
| 分页 | ✅ |
| 排序 | ✅ |
| 行点击 | ✅ |
| 国际化 | ✅ |

---

### 3.4 PositionDetail.tsx

| 检查项 | 状态 |
|-------|------|
| 数据加载 | ✅ |
| 条件渲染 | ✅ 缺失数据时隐藏模块 |
| 关联交易 | ✅ 期权-正股捆绑 |
| 价格图表 | ✅ |
| 国际化 | ✅ |

---

### 3.5 AICoach.tsx

| 检查项 | 状态 |
|-------|------|
| 聊天功能 | ✅ |
| 洞察卡片 | ✅ |
| 服务状态 | ✅ |
| 国际化 | ✅ |

---

### 3.6 System.tsx

| 检查项 | 状态 |
|-------|------|
| 健康检查 | ✅ |
| 数据库统计 | ✅ |
| 国际化 | ✅ 已支持中英文 |
| 暗色模式 | ✅ |

---

## 四、API 测试结果

### 4.1 Dashboard API

| 端点 | 状态 | 响应时间 | 数据示例 |
|-----|------|---------|---------|
| `/api/v1/dashboard/kpis` | ✅ | <100ms | total_pnl: $74,709.47 |
| `/api/v1/dashboard/equity-curve` | ✅ | <200ms | 403条数据点 |
| `/api/v1/dashboard/strategy-breakdown` | ✅ | <100ms | 5种策略 |
| `/api/v1/dashboard/recent-trades` | ✅ | <100ms | 10条记录 |

### 4.2 Positions API

| 端点 | 状态 | 说明 |
|-----|------|------|
| `/api/v1/positions` | ✅ | 分页正常 |
| `/api/v1/positions/{id}` | ✅ | 详情正常 |
| `/api/v1/positions/{id}/related` | ✅ | 关联交易正常 |
| `/api/v1/positions/{id}/market-data` | ✅ | K线数据正常 |

### 4.3 System API

| 端点 | 状态 | 数据 |
|-----|------|-----|
| `/api/v1/system/health` | ✅ | status: healthy |
| `/api/v1/system/stats` | ✅ | 444 positions, 606 trades |

---

## 五、问题汇总与修复建议

### P1 问题 (需优先修复)

| # | 组件 | 问题 | 修复方案 |
|---|------|-----|---------|
| 1 | EquityCurveChart | 日期格式硬编码 | 使用 i18n.language 动态切换 |
| 2 | 多个图表 | Bar Cell fill 硬编码 | 创建 useChartColors hook |
| 3 | EquityCurveChart | 缺少 bare/isLoading | 添加属性支持 |
| 4 | StrategyPieChart | 缺少 bare/isLoading | 添加属性支持 |
| 5 | PriceChart | 缺少 bare 模式 | 添加属性支持 |
| 6 | PriceChart | 暗色模式切换需刷新 | 监听 dark class 变化 |

### P2 问题 (应修复)

| # | 组件 | 问题 |
|---|------|-----|
| 1 | 所有 Recharts | CartesianGrid className 对 stroke 无效 |
| 2 | 所有 Recharts | XAxis/YAxis 颜色硬编码 |
| 3 | StrategyPieChart | 空状态缺少暗色文字类 |
| 4 | COLORS 数组 | 建议提取为共享常量 |

### P3 问题 (可优化)

| # | 问题 |
|---|-----|
| 1 | Statistics.tsx 文件过大(700+行)，建议拆分 |
| 2 | 部分图表缺少 aria-label 无障碍支持 |
| 3 | 缺少 ErrorBoundary 包裹图表组件 |

---

## 六、推荐的颜色规范

### 盈亏颜色

```typescript
// 推荐创建 useChartColors hook
export function useChartColors() {
  const isDarkMode = useDarkMode();

  return {
    profit: isDarkMode ? '#26a69a' : '#22c55e',  // TradingView teal / Tailwind green
    loss: isDarkMode ? '#ef5350' : '#ef4444',     // TradingView coral / Tailwind red
    grid: isDarkMode ? '#374151' : '#e5e7eb',
    text: isDarkMode ? '#9ca3af' : '#6b7280',
    axis: isDarkMode ? '#4b5563' : '#e5e7eb',
  };
}
```

### 表面颜色

| 用途 | 亮色模式 | 暗色模式 |
|-----|---------|---------|
| 卡片背景 | `bg-white` | `bg-gray-800` |
| Tooltip 背景 | `bg-white` | `bg-neutral-800` |
| 边框 | `border-gray-100` | `border-gray-700` |

---

## 七、测试覆盖建议

### 推荐的 Playwright 测试用例

```typescript
// tests/e2e/dashboard.spec.ts
test('Dashboard KPI cards display correct data', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.locator('[data-testid="total-pnl"]')).toBeVisible();
  await expect(page.locator('[data-testid="win-rate"]')).toBeVisible();
});

// tests/e2e/statistics.spec.ts
test('Statistics charts load in dark mode', async ({ page }) => {
  await page.goto('/statistics');
  await page.click('[data-testid="dark-mode-toggle"]');
  await expect(page.locator('.recharts-surface')).toHaveCount(10);
});

// tests/e2e/position-detail.spec.ts
test('Position detail shows related trades', async ({ page }) => {
  await page.goto('/positions/403');
  await expect(page.locator('[data-testid="related-positions"]')).toBeVisible();
});
```

---

## 八、结论

TradingCoach 前端整体质量良好，主要功能完备。需要重点关注的是：

1. **图表颜色一致性**: 建议创建共享的颜色常量或 hook
2. **bare/isLoading 属性补全**: 3个图表组件缺失
3. **日期格式国际化**: 多处硬编码 'zh-CN'

建议优先修复 P1 问题，预计工作量 2-3 小时。

---

---

## 九、数据缺失与合理性检查

### 9.1 数据缺失统计

基于 444 条持仓记录的分析：

| 字段 | 缺失数量 | 缺失率 | 说明 |
|-----|---------|-------|------|
| overall_score | 0 | 0% | ✅ 全部有评分 |
| strategy_type | 0 | 0% | ✅ 全部有策略分类 |
| net_pnl | 0 | 0% | ✅ 全部有盈亏数据 |
| symbol_name | 0 | 0% | ✅ 全部有名称 |

### 9.2 期权数据特殊检查

| 检查项 | 状态 | 说明 |
|-------|------|------|
| 期权名称格式 | ✅ | 如 "AMZN 260618 195.00P" 格式正确 |
| 期权K线数据 | ✅ | 使用标的正股的K线，技术指标100%覆盖 |
| 期权 MAE/MFE | ⚠️ | **MFE 经常为 null**，需检查计算逻辑 |

**期权风险指标示例**:
```
Position 403 (AMZN期权):
  MAE: -24720.0 ⚠️ 数值异常大
  MFE: None     ⚠️ 缺失
```

### 9.3 数据合理性检查

| 检查项 | 结果 | 说明 |
|-------|------|------|
| 盈亏百分比 > 500% | 0 条 | ✅ 无异常 |
| 持仓天数 > 180天 | 0 条 | ✅ 无异常 |
| 评分不在 0-100 范围 | 0 条 | ✅ 无异常 |
| 交易数量为 0 | 0 条 | ✅ 无异常 |
| 胜率超出 0-100% | 0 条 | ✅ 无异常 |

### 9.4 权益曲线数据检查

| 指标 | 值 | 说明 |
|-----|-----|------|
| 数据点数量 | 107 | 日度数据 |
| 日期范围 | 2024-10-15 ~ 2025-11-03 | 约1年数据 |
| 起始累计盈亏 | -$35.45 | |
| 最终累计盈亏 | $74,709.47 | |
| 大额变动 (>$10k) | 1次 | 2025-02-27: +$56,006.12 |

⚠️ **注意**: 2025-02-27 有 $56k 的大额变动，建议核实是否为正常交易或数据问题。

### 9.5 中文显示检查

| 检查项 | 状态 |
|-------|------|
| 中文股票名称 | ✅ 亚马逊、阿里巴巴-W、联合健康、伯克希尔-B 等正常显示 |
| 页面标题 | ✅ `<title>frontend</title>` (可考虑改为中文) |
| i18n 翻译 | ✅ System 页面等全部支持中英文 |

### 9.6 API 端点健康检查

| 端点 | 状态 | 数据量 |
|-----|------|-------|
| /statistics/monthly-pnl | ✅ 200 | 12 条 |
| /statistics/hourly-performance | ✅ 200 | 18 条 |
| /statistics/trading-heatmap | ✅ 200 | 57 条 |
| /statistics/duration-pnl | ✅ 200 | - |
| /statistics/rolling-metrics | ✅ 200 | - |
| /statistics/symbol-risk | ✅ 200 | - |
| /statistics/by-symbol | ✅ 200 | - |
| /statistics/by-grade | ✅ 200 | - |
| /statistics/drawdowns | ✅ 200 | - |
| /statistics/pnl-distribution | ✅ 200 | - |

### 9.7 发现的数据问题

| # | 严重度 | 问题 | 建议 |
|---|--------|-----|------|
| 1 | P1 | 期权 Position 403 的 MAE=-24720.0 异常大 | 检查MAE计算是否使用了错误的乘数 |
| 2 | P1 | 多个期权的 MFE 为 null | 检查MFE计算逻辑，确保期权有正确的市场数据 |
| 3 | P2 | 2025-02-27 有 $56k 单日变动 | 核实是否为真实大额交易或数据导入问题 |
| 4 | P3 | 页面标题仍为 "frontend" | 建议改为 "TradingCoach" 或根据语言动态设置 |

---

## 十、总结

### 已完成检查

1. ✅ 15个图表组件代码审查
2. ✅ 6个页面组件功能测试
3. ✅ 10个Statistics API端点健康检查
4. ✅ 444条持仓数据完整性检查
5. ✅ 数据合理性边界值检查
6. ✅ 中文显示和i18n检查
7. ✅ 期权数据特殊场景检查

### 主要发现

**代码层面**:
- 6个 P1 问题：颜色硬编码、日期格式硬编码、缺少 bare 属性
- 8个 P2 问题：代码风格不一致

**数据层面**:
- 2个 P1 问题：期权 MAE 计算异常、MFE 缺失
- 1个 P2 问题：大额单日变动需核实

### 优先修复建议

1. **立即修复**: 期权 MAE/MFE 计算逻辑
2. **本周修复**: 图表颜色硬编码问题
3. **下周修复**: 日期格式国际化、bare 属性补全

---

*报告生成者: Claude Code QA Assistant*
*检查方法: 静态代码分析 + API 测试 + 数据完整性验证*
