/**
 * Insight generation utilities for charts and data
 * Generates human-readable insights based on trading data
 */

import type {
  EquityDrawdownItem,
  PnLDistributionBin,
  RollingMetricsItem,
  HourlyPerformanceItem,
  TradingHeatmapCell,
  SymbolRiskItem,
  MonthlyPnLItem,
  RiskMetrics,
} from '@/types';

// Helper to format currency
const formatUSD = (value: number) => {
  const sign = value >= 0 ? '' : '-';
  return `${sign}$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
};

/**
 * Generate insight for equity curve
 */
export function getEquityCurveInsight(
  data: EquityDrawdownItem[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  const last = data[data.length - 1];
  const maxDrawdown = Math.min(...data.map(d => d.drawdown_pct ?? 0));

  if (isZh) {
    return `累计收益 ${formatUSD(last.cumulative_pnl)}，期间最大回撤 ${Math.abs(maxDrawdown).toFixed(1)}%。`;
  }
  return `Cumulative P&L of ${formatUSD(last.cumulative_pnl)} with maximum drawdown of ${Math.abs(maxDrawdown).toFixed(1)}%.`;
}

/**
 * Generate insight for monthly performance
 */
export function getMonthlyInsight(
  data: MonthlyPnLItem[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  const profitable = data.filter(d => d.pnl > 0);
  const best = data.reduce((a, b) => a.pnl > b.pnl ? a : b);

  const bestMonth = new Date(best.year, best.month - 1).toLocaleDateString(
    isZh ? 'zh-CN' : 'en-US',
    { year: 'numeric', month: 'short' }
  );

  if (isZh) {
    return `${data.length} 个月中 ${profitable.length} 个盈利月。最佳: ${bestMonth} (${formatUSD(best.pnl)})。`;
  }
  return `${profitable.length} profitable months out of ${data.length}. Best: ${bestMonth} (${formatUSD(best.pnl)}).`;
}

/**
 * Generate insight for P&L distribution
 */
export function getPnLDistributionInsight(
  data: PnLDistributionBin[],
  avgWin: number,
  avgLoss: number,
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  // Check if distribution is right-skewed (good) or left-skewed (bad)
  const skewDirection = avgWin > Math.abs(avgLoss) ? 'positive' : 'negative';

  if (isZh) {
    if (skewDirection === 'positive') {
      return `盈亏分布呈右偏态，平均盈利 ${formatUSD(avgWin)} 大于平均亏损 ${formatUSD(Math.abs(avgLoss))}，具备正期望。`;
    }
    return `平均盈利 ${formatUSD(avgWin)} 小于平均亏损 ${formatUSD(Math.abs(avgLoss))}，需要提高盈亏比。`;
  }

  if (skewDirection === 'positive') {
    return `Right-skewed distribution with avg win ${formatUSD(avgWin)} exceeding avg loss ${formatUSD(Math.abs(avgLoss))}. Positive expectancy.`;
  }
  return `Avg win ${formatUSD(avgWin)} is less than avg loss ${formatUSD(Math.abs(avgLoss))}. Consider improving risk/reward ratio.`;
}

/**
 * Generate insight for hourly performance
 */
export function getHourlyInsight(
  data: HourlyPerformanceItem[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  // Find best and worst hours
  const bestHour = data.reduce((a, b) => a.avg_pnl > b.avg_pnl ? a : b);
  const mostActive = data.reduce((a, b) => a.trade_count > b.trade_count ? a : b);

  const formatHour = (hour: number) => {
    const suffix = hour >= 12 ? 'PM' : 'AM';
    const h = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${h}${suffix}`;
  };

  if (isZh) {
    return `最佳交易时段: ${formatHour(bestHour.hour)}-${formatHour(bestHour.hour + 1)}。最活跃时段: ${formatHour(mostActive.hour)} (${mostActive.trade_count} 笔)。`;
  }
  return `Best trading hour: ${formatHour(bestHour.hour)}-${formatHour(bestHour.hour + 1)}. Most active: ${formatHour(mostActive.hour)} (${mostActive.trade_count} trades).`;
}

/**
 * Generate insight for trading heatmap
 */
export function getTradingHeatmapInsight(
  data: TradingHeatmapCell[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  // Backend uses Python weekday(): 0=Monday, 6=Sunday
  const dayNames = isZh
    ? ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  // Group by day of week
  const byDay = new Map<number, { count: number; pnl: number }>();
  data.forEach(cell => {
    const existing = byDay.get(cell.day_of_week) || { count: 0, pnl: 0 };
    byDay.set(cell.day_of_week, {
      count: existing.count + cell.trade_count,
      pnl: existing.pnl + cell.total_pnl,
    });
  });

  // Find most active and most profitable day
  let mostActiveDay = 0;
  let maxCount = 0;
  let mostProfitableDay = 0;
  let maxPnl = -Infinity;

  byDay.forEach((stats, day) => {
    if (stats.count > maxCount) {
      maxCount = stats.count;
      mostActiveDay = day;
    }
    if (stats.pnl > maxPnl) {
      maxPnl = stats.pnl;
      mostProfitableDay = day;
    }
  });

  if (isZh) {
    return `最活跃: ${dayNames[mostActiveDay]}。最盈利: ${dayNames[mostProfitableDay]} (${formatUSD(maxPnl)})。`;
  }
  return `Most active: ${dayNames[mostActiveDay]}. Most profitable: ${dayNames[mostProfitableDay]} (${formatUSD(maxPnl)}).`;
}

/**
 * Generate insight for symbol risk quadrant
 */
export function getSymbolRiskInsight(
  data: SymbolRiskItem[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  // Calculate average P&L per trade for each symbol
  const symbolsWithAvgPnl = data.map(d => ({
    ...d,
    avgPnl: d.total_pnl / d.trade_count,
    // Use risk_reward_ratio as a proxy for volatility/risk
    riskScore: d.risk_reward_ratio ? Math.abs(d.avg_loss) / (d.avg_win || 1) : 1,
  }));

  const avgPnl = symbolsWithAvgPnl.reduce((sum, d) => sum + d.avgPnl, 0) / symbolsWithAvgPnl.length;
  const avgRisk = symbolsWithAvgPnl.reduce((sum, d) => sum + d.riskScore, 0) / symbolsWithAvgPnl.length;

  const highProfitLowRisk = symbolsWithAvgPnl.filter(d => d.avgPnl > avgPnl && d.riskScore < avgRisk);
  const highRisk = symbolsWithAvgPnl.filter(d => d.riskScore > avgRisk * 1.5);

  const topPerformers = highProfitLowRisk.slice(0, 3).map(d => d.symbol).join(', ');
  const riskyCalls = highRisk.slice(0, 2).map(d => d.symbol).join(', ');

  if (isZh) {
    let insight = '';
    if (topPerformers) insight += `优质标的: ${topPerformers}。`;
    if (riskyCalls) insight += ` 高波动标的: ${riskyCalls}。`;
    return insight || '标的表现均衡。';
  }

  let insight = '';
  if (topPerformers) insight += `Top performers: ${topPerformers}.`;
  if (riskyCalls) insight += ` High volatility: ${riskyCalls}.`;
  return insight || 'Balanced performance across symbols.';
}

/**
 * Generate insight for rolling win rate
 */
export function getRollingWinRateInsight(
  data: RollingMetricsItem[],
  isZh: boolean
): string {
  if (!data || data.length === 0) return '';

  const recent = data.slice(-10);
  const avgRecent = recent.reduce((sum, d) => sum + d.rolling_win_rate, 0) / recent.length;
  const overall = data.reduce((sum, d) => sum + d.rolling_win_rate, 0) / data.length;

  const trend = avgRecent > overall ? 'improving' : avgRecent < overall ? 'declining' : 'stable';

  if (isZh) {
    const trendText = trend === 'improving' ? '上升趋势' : trend === 'declining' ? '下降趋势' : '保持稳定';
    return `近期胜率 ${avgRecent.toFixed(1)}%，${trendText}。`;
  }
  return `Recent win rate ${avgRecent.toFixed(1)}%, ${trend} trend.`;
}

/**
 * Generate overall risk summary
 */
export function getRiskSummaryInsight(
  metrics: RiskMetrics | undefined,
  isZh: boolean
): string {
  if (!metrics) return '';

  const sharpe = metrics.sharpe_ratio;
  const maxDD = metrics.max_drawdown_pct;

  let riskLevel = 'moderate';
  if (sharpe && sharpe > 1.5 && maxDD && maxDD < 20) riskLevel = 'low';
  else if (maxDD && maxDD > 40) riskLevel = 'high';

  if (isZh) {
    const riskText = riskLevel === 'low' ? '风险可控' : riskLevel === 'high' ? '风险较高' : '风险中等';
    return `夏普比率 ${sharpe?.toFixed(2) || '-'}，最大回撤 ${maxDD?.toFixed(1) || '-'}%，${riskText}。`;
  }
  return `Sharpe ${sharpe?.toFixed(2) || '-'}, max drawdown ${maxDD?.toFixed(1) || '-'}%. ${riskLevel.charAt(0).toUpperCase() + riskLevel.slice(1)} risk profile.`;
}
