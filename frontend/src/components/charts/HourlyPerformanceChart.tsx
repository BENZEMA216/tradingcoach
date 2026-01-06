import { useTranslation } from 'react-i18next';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import type { HourlyPerformanceItem } from '@/types';
import { getPrivacyAwareFormatters } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

interface HourlyPerformanceChartProps {
  data: HourlyPerformanceItem[];
  isLoading?: boolean;
  onBarClick?: (hour: number) => void;
  bare?: boolean;
}

export function HourlyPerformanceChart({ data, isLoading, onBarClick, bare = false }: HourlyPerformanceChartProps) {
  const { t } = useTranslation();
  const colors = useChartColors();

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatPnL, formatAxis } = getPrivacyAwareFormatters();

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
          {t('charts.hourlyPerformance')}
        </h3>
        <EmptyState icon="chart" height="h-64" size="sm" />
      </div>
    );
  }

  const chartData = data.map((item) => ({
    hour: `${item.hour}:00`,
    hourNum: item.hour,
    avgPnl: item.avg_pnl,
    totalPnl: item.total_pnl,
    trades: item.trade_count,
    winRate: item.win_rate,
  }));

  // Find best and worst hours
  const sortedByPnl = [...data].sort((a, b) => b.avg_pnl - a.avg_pnl);
  const bestHour = sortedByPnl[0];
  const worstHour = sortedByPnl[sortedByPnl.length - 1];

  const chartContent = (
    <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="hour"
              tick={{ fontSize: 10, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tickFormatter={formatAxis}
            />
            <Tooltip
              cursor={{ fill: 'rgba(0,0,0,0.05)' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">{data.hour}</p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p style={{ color: data.avgPnl >= 0 ? colors.profit : colors.loss }}>
                          {t('charts.avgPnl')}: {formatPnL(data.avgPnl)}
                        </p>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {t('charts.tradeCount')}: {data.trades}
                        </p>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {t('common.winRate')}: {data.winRate.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={0} stroke={colors.text} strokeDasharray="3 3" />
            <Bar
              dataKey="avgPnl"
              radius={[4, 4, 0, 0]}
              onClick={(data: unknown) => {
                const d = data as { hourNum?: number };
                if (onBarClick && d?.hourNum !== undefined) {
                  onBarClick(d.hourNum);
                }
              }}
              style={{ cursor: onBarClick ? 'pointer' : 'default' }}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.avgPnl >= 0 ? colors.profit : colors.loss}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
    </div>
  );

  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          {bestHour && (
            <div>
              <span className="text-neutral-400">{t('charts.bestHour')}:</span>
              <span className="font-semibold text-green-600 ml-1">
                {bestHour.hour}:00 ({formatPnL(bestHour.avg_pnl)})
              </span>
            </div>
          )}
          {worstHour && worstHour.avg_pnl < 0 && (
            <div>
              <span className="text-neutral-400">{t('charts.worstHour')}:</span>
              <span className="font-semibold text-red-600 ml-1">
                {worstHour.hour}:00 ({formatPnL(worstHour.avg_pnl)})
              </span>
            </div>
          )}
        </div>
        {chartContent}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('charts.hourlyPerformance')}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {t('charts.hourlyPerformanceHint')}
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          {bestHour && (
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('charts.bestHour')}: </span>
              <span className="font-medium text-green-500">
                {bestHour.hour}:00 ({formatPnL(bestHour.avg_pnl)})
              </span>
            </div>
          )}
          {worstHour && worstHour.avg_pnl < 0 && (
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('charts.worstHour')}: </span>
              <span className="font-medium text-red-500">
                {worstHour.hour}:00 ({formatPnL(worstHour.avg_pnl)})
              </span>
            </div>
          )}
        </div>
      </div>
      {chartContent}
    </div>
  );
}
