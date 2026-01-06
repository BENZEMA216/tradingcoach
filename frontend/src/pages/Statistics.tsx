import { useState, useMemo, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { statisticsApi, dashboardApi, eventsApi } from '@/api/client';
import { formatPercent, formatDate, getPrivacyAwareFormatters } from '@/utils/format';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import {
  getEquityCurveInsight,
  getMonthlyInsight,
  getPnLDistributionInsight,
  getHourlyInsight,
  getTradingHeatmapInsight,
  getSymbolRiskInsight,
  getRollingWinRateInsight,
} from '@/utils/insights';
import { DrillDownModal, PrivacyModeToggle } from '@/components/common';
import { AICoachPanel } from '@/components/insights';
import {
  ReportSection,
  ChartWithInsight,
  HeroSummary,
  CollapsibleTable,
} from '@/components/report';
import {
  EquityDrawdownChart,
  MonthlyPerformanceChart,
  PnLDistributionChart,
  RollingWinRateChart,
  DurationPnLChart,
  SymbolRiskQuadrant,
  TradingHeatmap,
  HourlyPerformanceChart,
  AssetTypeChart,
  StrategyPerformanceChart,
  EventTimelineChart,
} from '@/components/charts';
import type { PositionFilters } from '@/types';
import clsx from 'clsx';

type PeriodType = 'all' | 'week' | 'month' | 'quarter' | 'year';

interface DrillDownState {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  filters: PositionFilters;
}

function getDateRange(type: PeriodType, offset: number = 0): { start: Date | null; end: Date | null } {
  if (type === 'all') return { start: null, end: null };

  const now = new Date();
  let start: Date;
  let end: Date;

  switch (type) {
    case 'week': {
      const dayOfWeek = now.getDay();
      start = new Date(now);
      start.setDate(now.getDate() - dayOfWeek - 7 * offset);
      end = new Date(start);
      end.setDate(start.getDate() + 6);
      break;
    }
    case 'month': {
      start = new Date(now.getFullYear(), now.getMonth() - offset, 1);
      end = new Date(now.getFullYear(), now.getMonth() - offset + 1, 0);
      break;
    }
    case 'quarter': {
      const quarterMonth = Math.floor(now.getMonth() / 3) * 3 - offset * 3;
      start = new Date(now.getFullYear(), quarterMonth, 1);
      end = new Date(now.getFullYear(), quarterMonth + 3, 0);
      break;
    }
    case 'year': {
      const year = now.getFullYear() - offset;
      start = new Date(year, 0, 1);
      end = new Date(year, 11, 31);
      break;
    }
  }

  return { start, end };
}

function formatDateForApi(date: Date | null): string | undefined {
  return date ? date.toISOString().split('T')[0] : undefined;
}

function getPeriodLabel(type: PeriodType, offset: number, isZh: boolean): string {
  if (type === 'all') return isZh ? '全部时间' : 'All Time';

  const { start, end } = getDateRange(type, offset);
  if (!start || !end) return '';

  const locale = isZh ? 'zh-CN' : 'en-US';

  switch (type) {
    case 'week':
      return `${start.toLocaleDateString(locale, { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString(locale, { month: 'short', day: 'numeric' })}`;
    case 'month':
      return start.toLocaleDateString(locale, { year: 'numeric', month: 'long' });
    case 'quarter':
      return `${start.getFullYear()} Q${Math.floor(start.getMonth() / 3) + 1}`;
    case 'year':
      return `${start.getFullYear()}`;
  }
}

function calculateOffsetForDate(type: PeriodType, targetDate: Date): number {
  if (type === 'all') return 0;

  const now = new Date();
  let offset = 0;

  switch (type) {
    case 'week': {
      const msPerWeek = 7 * 24 * 60 * 60 * 1000;
      const nowWeekStart = new Date(now);
      nowWeekStart.setDate(now.getDate() - now.getDay());
      nowWeekStart.setHours(0, 0, 0, 0);

      const targetWeekStart = new Date(targetDate);
      targetWeekStart.setDate(targetDate.getDate() - targetDate.getDay());
      targetWeekStart.setHours(0, 0, 0, 0);

      offset = Math.floor((nowWeekStart.getTime() - targetWeekStart.getTime()) / msPerWeek);
      break;
    }
    case 'month': {
      offset = (now.getFullYear() - targetDate.getFullYear()) * 12 + (now.getMonth() - targetDate.getMonth());
      break;
    }
    case 'quarter': {
      const nowQuarter = Math.floor(now.getMonth() / 3);
      const targetQuarter = Math.floor(targetDate.getMonth() / 3);
      offset = (now.getFullYear() - targetDate.getFullYear()) * 4 + (nowQuarter - targetQuarter);
      break;
    }
    case 'year': {
      offset = now.getFullYear() - targetDate.getFullYear();
      break;
    }
  }

  return Math.max(0, offset);
}

// Risk Metric inline display
function RiskMetricInline({
  label,
  value,
  isGood,
}: {
  label: string;
  value: string | number | null | undefined;
  isGood?: boolean | null;
}) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-neutral-100 dark:border-neutral-800 last:border-0">
      <span className="text-[13px] text-neutral-400">{label}</span>
      <span
        className={clsx(
          'text-[13px] font-semibold',
          isGood === true ? 'text-green-600' : isGood === false ? 'text-red-600' : 'text-neutral-900 dark:text-neutral-100'
        )}
      >
        {value ?? '-'}
      </span>
    </div>
  );
}

export function Statistics() {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatCurrency, formatPnL: _formatPnL } = getPrivacyAwareFormatters();

  const [periodType, setPeriodType] = useState<PeriodType>('all');
  const [periodOffset, setPeriodOffset] = useState(0);

  const [drillDown, setDrillDown] = useState<DrillDownState>({
    isOpen: false,
    title: '',
    filters: {},
  });

  // Fetch data date range
  const { data: dateRange } = useQuery({
    queryKey: ['statistics', 'date-range'],
    queryFn: () => statisticsApi.getDateRange(),
  });

  // Auto-adjust to the most recent period with data
  useEffect(() => {
    if (dateRange?.max_date && periodType !== 'all') {
      const maxDate = new Date(dateRange.max_date);
      const newOffset = calculateOffsetForDate(periodType, maxDate);
      setPeriodOffset(newOffset);
    } else if (periodType === 'all') {
      setPeriodOffset(0);
    }
  }, [periodType, dateRange?.max_date]);

  const { start, end } = useMemo(
    () => getDateRange(periodType, periodOffset),
    [periodType, periodOffset]
  );

  const dateParams = useMemo(
    () => ({
      date_start: formatDateForApi(start),
      date_end: formatDateForApi(end),
    }),
    [start, end]
  );

  const openDrillDown = (title: string, filters: PositionFilters, subtitle?: string) => {
    setDrillDown({ isOpen: true, title, subtitle, filters });
  };

  const closeDrillDown = () => {
    setDrillDown({ isOpen: false, title: '', filters: {} });
  };

  // API Queries
  const { data: performance, isLoading } = useQuery({
    queryKey: ['statistics', 'performance', dateParams],
    queryFn: () => statisticsApi.getPerformance(dateParams),
  });

  const { data: riskMetrics } = useQuery({
    queryKey: ['statistics', 'risk-metrics', dateParams],
    queryFn: () => statisticsApi.getRiskMetrics(dateParams),
  });

  const { data: drawdowns } = useQuery({
    queryKey: ['statistics', 'drawdowns', dateParams],
    queryFn: () => statisticsApi.getDrawdowns({ ...dateParams, min_drawdown: 100 }),
  });

  const { data: bySymbol } = useQuery({
    queryKey: ['statistics', 'by-symbol', dateParams],
    queryFn: () => statisticsApi.getBySymbol({ ...dateParams, limit: 10 }),
  });

  const { data: byGrade } = useQuery({
    queryKey: ['statistics', 'by-grade', dateParams],
    queryFn: () => statisticsApi.getByGrade(dateParams),
  });

  const { data: byDirection } = useQuery({
    queryKey: ['statistics', 'by-direction', dateParams],
    queryFn: () => statisticsApi.getByDirectionTyped(dateParams),
  });

  const { data: byHolding } = useQuery({
    queryKey: ['statistics', 'by-holding', dateParams],
    queryFn: () => statisticsApi.getByHoldingPeriodTyped(dateParams),
  });

  const { data: strategyBreakdown } = useQuery({
    queryKey: ['statistics', 'strategy-breakdown', dateParams],
    queryFn: () => dashboardApi.getStrategyBreakdown(dateParams),
  });

  // Chart data queries
  const { data: equityDrawdown, isLoading: loadingEquity } = useQuery({
    queryKey: ['statistics', 'equity-drawdown', dateParams],
    queryFn: () => statisticsApi.getEquityDrawdown(dateParams),
  });

  const { data: monthlyPnL, isLoading: loadingMonthly } = useQuery({
    queryKey: ['statistics', 'monthly-pnl'],
    queryFn: () => statisticsApi.getMonthlyPnL(),
  });

  const { data: pnlDistribution, isLoading: loadingDistribution } = useQuery({
    queryKey: ['statistics', 'pnl-distribution', dateParams],
    queryFn: () => statisticsApi.getPnLDistribution(dateParams),
  });

  const { data: rollingMetrics, isLoading: loadingRolling } = useQuery({
    queryKey: ['statistics', 'rolling-metrics', dateParams],
    queryFn: () => statisticsApi.getRollingMetrics({ ...dateParams, window: 20 }),
  });

  const { data: durationPnL, isLoading: loadingDuration } = useQuery({
    queryKey: ['statistics', 'duration-pnl', dateParams],
    queryFn: () => statisticsApi.getDurationPnL(dateParams),
  });

  const { data: symbolRisk, isLoading: loadingSymbolRisk } = useQuery({
    queryKey: ['statistics', 'symbol-risk', dateParams],
    queryFn: () => statisticsApi.getSymbolRisk({ ...dateParams, min_trades: 2 }),
  });

  const { data: tradingHeatmap, isLoading: loadingHeatmap } = useQuery({
    queryKey: ['statistics', 'trading-heatmap', dateParams],
    queryFn: () => statisticsApi.getTradingHeatmap(dateParams),
  });

  const { data: hourlyPerformance, isLoading: loadingHourly } = useQuery({
    queryKey: ['statistics', 'hourly-performance', dateParams],
    queryFn: () => statisticsApi.getHourlyPerformance(dateParams),
  });

  const { data: byAssetType, isLoading: loadingAssetType } = useQuery({
    queryKey: ['statistics', 'by-asset-type', dateParams],
    queryFn: () => statisticsApi.getByAssetType(dateParams),
  });

  // Events query
  const { data: eventsData, isLoading: loadingEvents } = useQuery({
    queryKey: ['events', 'list', dateParams],
    queryFn: () => eventsApi.list(1, 50, {
      date_start: dateParams.date_start,
      date_end: dateParams.date_end,
    }),
  });

  const periodTabs: { type: PeriodType; label: string }[] = [
    { type: 'all', label: isZh ? '全部' : 'All' },
    { type: 'week', label: isZh ? '周' : 'Week' },
    { type: 'month', label: isZh ? '月' : 'Month' },
    { type: 'quarter', label: isZh ? '季' : 'Quarter' },
    { type: 'year', label: isZh ? '年' : 'Year' },
  ];

  return (
    <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-16 md:space-y-20 pb-16">
      {/* Period Selector - Floating */}
      <div className="sticky top-0 z-10 bg-neutral-50/80 dark:bg-neutral-950/80 backdrop-blur-sm -mx-4 px-4 py-4 border-b border-neutral-200/50 dark:border-neutral-800/50">
        <div className="flex items-center justify-between">
          {/* Period Navigation */}
          {periodType !== 'all' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPeriodOffset((o) => o + 1)}
                className="p-2 hover:bg-neutral-200 dark:hover:bg-neutral-800 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm font-medium min-w-[120px] text-center">
                {getPeriodLabel(periodType, periodOffset, isZh)}
              </span>
              <button
                onClick={() => setPeriodOffset((o) => Math.max(0, o - 1))}
                disabled={periodOffset === 0}
                className="p-2 hover:bg-neutral-200 dark:hover:bg-neutral-800 rounded-lg transition-colors disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
          {periodType === 'all' && <div />}

          {/* Right side: Privacy Toggle + Period Tabs */}
          <div className="flex items-center gap-3">
            <PrivacyModeToggle />
            <div className="flex gap-1 bg-neutral-200 dark:bg-neutral-800 p-1 rounded-lg">
              {periodTabs.map((tab) => (
                <button
                  key={tab.type}
                  onClick={() => setPeriodType(tab.type)}
                  className={clsx(
                    'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
                    periodType === tab.type
                      ? 'bg-white dark:bg-neutral-700 text-neutral-900 dark:text-white shadow-sm'
                      : 'text-neutral-500 hover:text-neutral-700'
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-neutral-300 border-t-neutral-900 dark:border-neutral-700 dark:border-t-neutral-100"></div>
        </div>
      ) : (
        <>
          {/* Hero Summary */}
          <HeroSummary
            period={getPeriodLabel(periodType, periodOffset, isZh)}
            totalPnL={performance?.total_pnl || 0}
            totalTrades={performance?.total_trades || 0}
            winRate={performance?.win_rate || 0}
            profitFactor={performance?.profit_factor || null}
            expectancy={riskMetrics?.expectancy || null}
            isZh={isZh}
          />

          {/* AI Coach Panel */}
          <AICoachPanel dateStart={dateParams.date_start} dateEnd={dateParams.date_end} limit={20} />

          {/* Section 01: Performance */}
          <ReportSection number="01" title="PERFORMANCE" subtitle={isZh ? '业绩表现' : 'Performance Overview'}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartWithInsight
                title={isZh ? '权益曲线' : 'Equity Curve'}
                chart={<EquityDrawdownChart data={equityDrawdown || []} isLoading={loadingEquity} />}
                insight={getEquityCurveInsight(equityDrawdown || [], isZh)}
              />
              <ChartWithInsight
                title={isZh ? '月度盈亏' : 'Monthly P&L'}
                chart={
                  <MonthlyPerformanceChart
                    data={monthlyPnL || []}
                    isLoading={loadingMonthly}
                    onBarClick={(year, month) => {
                      const monthStart = new Date(year, month - 1, 1);
                      const monthEnd = new Date(year, month, 0);
                      openDrillDown(
                        `${year}-${String(month).padStart(2, '0')}`,
                        {
                          date_start: monthStart.toISOString().split('T')[0],
                          date_end: monthEnd.toISOString().split('T')[0],
                        },
                        isZh ? '月度交易' : 'Monthly Trades'
                      );
                    }}
                  />
                }
                insight={getMonthlyInsight(monthlyPnL || [], isZh)}
              />
            </div>
          </ReportSection>

          {/* Section 02: Risk Analysis */}
          <ReportSection number="02" title="RISK ANALYSIS" subtitle={isZh ? '风险分析' : 'Risk Analysis'}>
            {/* Risk Metrics Cards */}
            <div className="bg-white dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-800 p-6 mb-6">
              <h3 className="text-[11px] font-semibold tracking-widest uppercase text-neutral-400 mb-5">
                {isZh ? '核心指标' : 'Key Metrics'}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-x-10">
                <RiskMetricInline
                  label={isZh ? '夏普比率' : 'Sharpe'}
                  value={riskMetrics?.sharpe_ratio?.toFixed(2)}
                  isGood={riskMetrics?.sharpe_ratio ? riskMetrics.sharpe_ratio > 1 : null}
                />
                <RiskMetricInline
                  label={isZh ? '索提诺比率' : 'Sortino'}
                  value={riskMetrics?.sortino_ratio?.toFixed(2)}
                  isGood={riskMetrics?.sortino_ratio ? riskMetrics.sortino_ratio > 1 : null}
                />
                <RiskMetricInline
                  label={isZh ? '卡玛比率' : 'Calmar'}
                  value={riskMetrics?.calmar_ratio?.toFixed(2)}
                  isGood={riskMetrics?.calmar_ratio ? riskMetrics.calmar_ratio > 1 : null}
                />
                <RiskMetricInline
                  label={isZh ? '最大回撤' : 'Max DD'}
                  value={riskMetrics?.max_drawdown ? `${formatCurrency(-riskMetrics.max_drawdown)}` : '-'}
                  isGood={false}
                />
                <RiskMetricInline
                  label={isZh ? '盈亏比' : 'Payoff'}
                  value={riskMetrics?.payoff_ratio?.toFixed(2)}
                  isGood={riskMetrics?.payoff_ratio ? riskMetrics.payoff_ratio > 1 : null}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartWithInsight
                title={isZh ? '盈亏分布' : 'P&L Distribution'}
                chart={<PnLDistributionChart data={pnlDistribution || []} isLoading={loadingDistribution} />}
                insight={getPnLDistributionInsight(
                  pnlDistribution || [],
                  performance?.avg_win || 0,
                  performance?.avg_loss || 0,
                  isZh
                )}
              />
              <ChartWithInsight
                title={isZh ? '滚动胜率' : 'Rolling Win Rate'}
                chart={<RollingWinRateChart data={rollingMetrics || []} window={20} isLoading={loadingRolling} />}
                insight={getRollingWinRateInsight(rollingMetrics || [], isZh)}
              />
            </div>
          </ReportSection>

          {/* Section 03: Trading Behavior */}
          <ReportSection number="03" title="TRADING BEHAVIOR" subtitle={isZh ? '交易行为' : 'Trading Behavior'}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <ChartWithInsight
                title={isZh ? '交易时段热力图' : 'Trading Heatmap'}
                chart={<TradingHeatmap data={tradingHeatmap || []} isLoading={loadingHeatmap} />}
                insight={getTradingHeatmapInsight(tradingHeatmap || [], isZh)}
              />
              <ChartWithInsight
                title={isZh ? '小时表现' : 'Hourly Performance'}
                chart={
                  <HourlyPerformanceChart
                    data={hourlyPerformance || []}
                    isLoading={loadingHourly}
                    onBarClick={(hour) => {
                      openDrillDown(
                        `${hour}:00`,
                        { open_hour: hour },
                        isZh ? '该时段交易' : 'Trades at this hour'
                      );
                    }}
                  />
                }
                insight={getHourlyInsight(hourlyPerformance || [], isZh)}
              />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartWithInsight
                title={isZh ? '持仓时长分析' : 'Duration Analysis'}
                chart={<DurationPnLChart data={durationPnL || []} isLoading={loadingDuration} />}
              />
              {/* Direction Breakdown */}
              {byDirection && byDirection.length > 0 && (
                <div className="bg-white dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
                  <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-4">
                    {isZh ? '多空分布' : 'Direction Breakdown'}
                  </h3>
                  <div className="space-y-4">
                    {byDirection.map((item) => (
                      <div
                        key={item.direction}
                        className={clsx(
                          'p-4 rounded-lg',
                          item.direction === 'long'
                            ? 'bg-green-50 dark:bg-green-900/20'
                            : 'bg-red-50 dark:bg-red-900/20'
                        )}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className={clsx(
                            'font-medium text-sm',
                            item.direction === 'long'
                              ? 'text-green-800 dark:text-green-300'
                              : 'text-red-800 dark:text-red-300'
                          )}>
                            {item.direction === 'long' ? (isZh ? '做多' : 'Long') : (isZh ? '做空' : 'Short')}
                          </span>
                          <span className="text-xs text-neutral-600 dark:text-neutral-400">{item.count} {isZh ? '笔' : 'trades'}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className={clsx(item.total_pnl > 0 ? 'text-green-600' : 'text-red-600')}>
                            {formatCurrency(item.total_pnl)}
                          </span>
                          <span className="text-neutral-500">
                            {isZh ? '胜率' : 'Win'}: {formatPercent(item.win_rate, 1)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </ReportSection>

          {/* Section 04: Portfolio */}
          <ReportSection number="04" title="PORTFOLIO" subtitle={isZh ? '持仓分析' : 'Portfolio Analysis'}>
            <ChartWithInsight
              title={isZh ? '标的风险象限' : 'Symbol Risk Quadrant'}
              chart={
                <SymbolRiskQuadrant
                  data={symbolRisk || []}
                  isLoading={loadingSymbolRisk}
                  onDotClick={(symbol) => {
                    openDrillDown(symbol, { symbol }, isZh ? '标的交易' : 'Symbol Trades');
                  }}
                />
              }
              insight={getSymbolRiskInsight(symbolRisk || [], isZh)}
              fullWidth
            />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <ChartWithInsight
                title={isZh ? '资产类型' : 'Asset Type'}
                chart={
                  <AssetTypeChart
                    data={byAssetType || []}
                    isLoading={loadingAssetType}
                    onBarClick={(assetType) => {
                      openDrillDown(
                        assetType.charAt(0).toUpperCase() + assetType.slice(1),
                        { asset_type: assetType },
                        isZh ? '资产类型交易' : 'Asset Type Trades'
                      );
                    }}
                  />
                }
              />
              {strategyBreakdown && strategyBreakdown.length > 0 && (
                <ChartWithInsight
                  title={isZh ? '策略表现' : 'Strategy Performance'}
                  chart={
                    <StrategyPerformanceChart
                      data={strategyBreakdown}
                      onBarClick={(strategyType) => {
                        openDrillDown(
                          strategyType,
                          { strategy_type: strategyType },
                          isZh ? '策略交易' : 'Strategy Trades'
                        );
                      }}
                    />
                  }
                />
              )}
            </div>
          </ReportSection>

          {/* Section 05: Event Analysis */}
          {eventsData?.items && eventsData.items.length > 0 && (
            <ReportSection number="05" title="EVENT ANALYSIS" subtitle={isZh ? '事件分析' : 'Event Analysis'}>
              <ChartWithInsight
                title={isZh ? '事件时间线' : 'Event Timeline'}
                chart={
                  <EventTimelineChart
                    events={eventsData.items}
                    isLoading={loadingEvents}
                    showPnL={true}
                  />
                }
                insight={
                  eventsData.items.length > 0
                    ? isZh
                      ? `检测到 ${eventsData.items.length} 个事件，其中 ${eventsData.items.filter(e => e.is_key_event).length} 个关键事件`
                      : `Detected ${eventsData.items.length} events, ${eventsData.items.filter(e => e.is_key_event).length} key events`
                    : undefined
                }
                fullWidth
              />
            </ReportSection>
          )}

          {/* Section 06: Detailed Data */}
          <ReportSection number="06" title="DETAILED DATA" subtitle={isZh ? '详细数据' : 'Detailed Data'}>
            {/* By Symbol - Collapsible */}
            <CollapsibleTable
              title={isZh ? 'Top 10 标的' : 'Top 10 Symbols'}
              subtitle={isZh ? '按盈亏排序' : 'Sorted by P&L'}
              defaultCollapsed={false}
            >
              <table className="w-full text-sm">
                <thead className="bg-neutral-50 dark:bg-neutral-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">{t('positions.symbol')}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '次数' : 'Trades'}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{t('positions.pnl')}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '胜率' : 'Win Rate'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                  {bySymbol?.map((item) => (
                    <tr
                      key={item.symbol}
                      onClick={() => openDrillDown(item.symbol, { symbol: item.symbol }, item.symbol_name || undefined)}
                      className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50 cursor-pointer"
                    >
                      <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">{item.symbol}</td>
                      <td className="px-4 py-3 text-right text-neutral-500">{item.count}</td>
                      <td className={clsx('px-4 py-3 text-right font-medium', item.total_pnl > 0 ? 'text-green-600' : 'text-red-600')}>
                        {formatCurrency(item.total_pnl)}
                      </td>
                      <td className="px-4 py-3 text-right text-neutral-500">{formatPercent(item.win_rate, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CollapsibleTable>

            {/* By Grade - Collapsible */}
            <CollapsibleTable
              title={isZh ? '评分分布' : 'Grade Distribution'}
              className="mt-4"
            >
              <table className="w-full text-sm">
                <thead className="bg-neutral-50 dark:bg-neutral-800/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">{t('positions.grade')}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '次数' : 'Trades'}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{t('positions.pnl')}</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '胜率' : 'Win Rate'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                  {byGrade?.map((item) => (
                    <tr
                      key={item.grade}
                      onClick={() => openDrillDown(
                        isZh ? `${item.grade} 级交易` : `Grade ${item.grade} Trades`,
                        { score_grade: item.grade }
                      )}
                      className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50 cursor-pointer"
                    >
                      <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">{item.grade}</td>
                      <td className="px-4 py-3 text-right text-neutral-500">{item.count}</td>
                      <td className={clsx('px-4 py-3 text-right font-medium', item.total_pnl > 0 ? 'text-green-600' : 'text-red-600')}>
                        {formatCurrency(item.total_pnl)}
                      </td>
                      <td className="px-4 py-3 text-right text-neutral-500">{formatPercent(item.win_rate, 1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CollapsibleTable>

            {/* By Holding Period - Collapsible */}
            {byHolding && byHolding.length > 0 && (
              <CollapsibleTable
                title={isZh ? '持仓周期分析' : 'Holding Period Analysis'}
                className="mt-4"
              >
                <table className="w-full text-sm">
                  <thead className="bg-neutral-50 dark:bg-neutral-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">{isZh ? '周期' : 'Period'}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '次数' : 'Trades'}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{t('positions.pnl')}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '胜率' : 'Win Rate'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                    {byHolding.map((item) => (
                      <tr key={item.period_label}>
                        <td className="px-4 py-3 font-medium text-neutral-900 dark:text-neutral-100">{item.period_label}</td>
                        <td className="px-4 py-3 text-right text-neutral-500">{item.count}</td>
                        <td className={clsx('px-4 py-3 text-right font-medium', item.total_pnl > 0 ? 'text-green-600' : 'text-red-600')}>
                          {formatCurrency(item.total_pnl)}
                        </td>
                        <td className="px-4 py-3 text-right text-neutral-500">{formatPercent(item.win_rate, 1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CollapsibleTable>
            )}

            {/* Drawdowns - Collapsible */}
            {drawdowns && drawdowns.length > 0 && (
              <CollapsibleTable
                title={isZh ? '回撤记录' : 'Drawdown History'}
                className="mt-4"
              >
                <table className="w-full text-sm">
                  <thead className="bg-neutral-50 dark:bg-neutral-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">{isZh ? '开始' : 'Start'}</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">{isZh ? '结束' : 'End'}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '回撤' : 'Drawdown'}</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">{isZh ? '天数' : 'Days'}</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-neutral-500 uppercase">{isZh ? '状态' : 'Status'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                    {drawdowns.slice(0, 5).map((dd, idx) => (
                      <tr
                        key={idx}
                        onClick={() => openDrillDown(
                          isZh ? '回撤期间交易' : 'Trades During Drawdown',
                          { date_start: dd.start_date, date_end: dd.end_date || undefined },
                          `${formatDate(dd.start_date)} - ${dd.end_date ? formatDate(dd.end_date) : (isZh ? '至今' : 'Present')}`
                        )}
                        className="hover:bg-neutral-50 dark:hover:bg-neutral-800/50 cursor-pointer"
                      >
                        <td className="px-4 py-3 text-neutral-900 dark:text-neutral-100">{formatDate(dd.start_date)}</td>
                        <td className="px-4 py-3 text-neutral-900 dark:text-neutral-100">{dd.end_date ? formatDate(dd.end_date) : '-'}</td>
                        <td className="px-4 py-3 text-right text-red-600 font-medium">
                          {formatCurrency(-dd.drawdown)}
                        </td>
                        <td className="px-4 py-3 text-right text-neutral-500">
                          {dd.duration_days}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {dd.recovery_date ? (
                            <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                              {isZh ? '已恢复' : 'Recovered'}
                            </span>
                          ) : (
                            <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                              {isZh ? '进行中' : 'Active'}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CollapsibleTable>
            )}
          </ReportSection>

          {/* No Data State */}
          {performance?.total_trades === 0 && (
            <div className="text-center py-12">
              <p className="text-neutral-500 dark:text-neutral-400">
                {isZh ? '该周期内没有交易记录' : 'No trades found for this period.'}
              </p>
            </div>
          )}
        </>
      )}

      {/* Drill-Down Modal */}
      <DrillDownModal
        isOpen={drillDown.isOpen}
        onClose={closeDrillDown}
        title={drillDown.title}
        subtitle={drillDown.subtitle}
        filters={drillDown.filters}
      />
    </div>
  );
}
