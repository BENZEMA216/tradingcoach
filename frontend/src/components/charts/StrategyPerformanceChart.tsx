import { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from 'recharts';
import type { StrategyBreakdownItem } from '@/types';
import { getPrivacyAwareFormatters } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';
import { useResponsiveChart } from '@/hooks/useResponsiveChart';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

interface StrategyPerformanceChartProps {
  data: StrategyBreakdownItem[];
  isLoading?: boolean;
  onBarClick?: (strategyType: string) => void;
  bare?: boolean;
}

export function StrategyPerformanceChart({ data, isLoading, onBarClick, bare = false }: StrategyPerformanceChartProps) {
  const { t } = useTranslation();
  const colors = useChartColors();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartConfig = useResponsiveChart(containerRef, { layout: 'horizontal' });

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatCurrency: _formatCurrency, formatPnL, formatAxis } = getPrivacyAwareFormatters();

  if (isLoading) {
    if (bare) return <ChartSkeleton height="h-64" showTitle={false} />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <ChartSkeleton height="h-64" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) return <EmptyState icon="chart" height="h-64" size="sm" />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.strategyPerformance')}
        </h3>
        <EmptyState icon="chart" height="h-64" size="sm" />
      </div>
    );
  }

  const chartData = data
    .map((item) => ({
      strategy: item.strategy,
      name: t(`strategy.${item.strategy}`) || item.strategy_name,
      pnl: item.total_pnl,
      count: item.count,
      winRate: item.win_rate,
    }))
    .sort((a, b) => b.pnl - a.pnl);

  const bestStrategy = chartData[0];

  const chartContent = (
    <div ref={containerRef} className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={chartConfig.margin}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} horizontal={true} vertical={false} />
            <XAxis
              type="number"
              tick={{ fontSize: chartConfig.fontSize, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tickFormatter={formatAxis}
            />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: chartConfig.fontSize, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              width={chartConfig.yAxisWidth}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-gray-900 dark:text-white">{data.name}</p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                          {t('statistics.totalPnl')}: {formatPnL(data.pnl)}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('charts.tradeCount')}: {data.count}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('common.winRate')}: {data.winRate.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar
              dataKey="pnl"
              radius={[0, 4, 4, 0]}
              onClick={(data: unknown) => {
                const d = data as { strategy?: string };
                if (onBarClick && d?.strategy) {
                  onBarClick(d.strategy);
                }
              }}
              style={{ cursor: onBarClick ? 'pointer' : 'default' }}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.pnl >= 0 ? colors.profit : colors.loss}
                  fillOpacity={0.8}
                />
              ))}
              {chartConfig.showLabels && (
                <LabelList
                  dataKey="pnl"
                  position="right"
                  formatter={(value) => formatPnL(value as number)}
                  style={{ fontSize: chartConfig.fontSize, fill: colors.text }}
                />
              )}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
    </div>
  );

  const summaryStats = (
    <div className="mt-4 grid grid-cols-3 gap-4 text-center">
      {chartData.slice(0, 3).map((item) => (
        <div key={item.strategy} className="p-2 rounded-lg bg-gray-50 dark:bg-gray-700/50">
          <div className="text-xs text-gray-500 dark:text-gray-400">{item.name}</div>
          <div className={`text-sm font-semibold ${item.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatPnL(item.pnl)}
          </div>
          <div className="text-xs text-gray-400 dark:text-gray-500">
            {item.count} {t('common.trades')} · {item.winRate.toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );

  if (bare) {
    return (
      <div>
        {bestStrategy && (
          <div className="flex items-center justify-end mb-4 text-[13px]">
            <span className="text-neutral-400">{t('charts.bestStrategy')}:</span>
            <span className="font-semibold text-green-600 ml-1">{bestStrategy.name}</span>
          </div>
        )}
        {chartContent}
        {summaryStats}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('charts.strategyPerformance')}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {t('charts.strategyPerformanceHint')}
          </p>
        </div>
        {bestStrategy && (
          <div className="text-sm">
            <span className="text-gray-500 dark:text-gray-400">{t('charts.bestStrategy')}: </span>
            <span className="font-medium text-green-500">{bestStrategy.name}</span>
          </div>
        )}
      </div>
      {chartContent}
      {summaryStats}
    </div>
  );
}
