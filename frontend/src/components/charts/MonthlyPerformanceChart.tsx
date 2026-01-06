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
import type { MonthlyPnLItem } from '@/types';
import { getPrivacyAwareFormatters } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

interface MonthlyPerformanceChartProps {
  data: MonthlyPnLItem[];
  isLoading?: boolean;
  onBarClick?: (year: number, month: number) => void;
  bare?: boolean;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function MonthlyPerformanceChart({ data, isLoading, onBarClick, bare = false }: MonthlyPerformanceChartProps) {
  const { t } = useTranslation();
  const colors = useChartColors();

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatPnL, formatAxis } = getPrivacyAwareFormatters();

  if (isLoading) {
    if (bare) {
      return <ChartSkeleton height="h-64" showTitle={false} />;
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <ChartSkeleton height="h-64" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) {
      return <EmptyState icon="chart" height="h-64" size="sm" />;
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.monthlyPerformance')}
        </h3>
        <EmptyState icon="chart" height="h-64" size="sm" />
      </div>
    );
  }

  const chartData = data.map((item) => ({
    month: `${item.year}-${MONTHS[item.month - 1]}`,
    year: item.year,
    monthNum: item.month,
    pnl: item.pnl,
    trades: item.trade_count,
    winRate: item.win_rate,
  }));

  const totalPnL = data.reduce((sum, item) => sum + item.pnl, 0);
  const avgMonthlyPnL = totalPnL / data.length;

  const chartContent = (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fill: colors.text }}
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
                    <p className="font-semibold text-neutral-900 dark:text-neutral-100">{data.month}</p>
                    <div className="mt-1 space-y-0.5 text-sm">
                      <p style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                        {t('common.pnl')}: {formatPnL(data.pnl)}
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
            dataKey="pnl"
            radius={[4, 4, 0, 0]}
            onClick={(data: unknown) => {
              const d = data as { year?: number; monthNum?: number };
              if (onBarClick && d?.year && d?.monthNum) {
                onBarClick(d.year, d.monthNum);
              }
            }}
            style={{ cursor: onBarClick ? 'pointer' : 'default' }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.pnl >= 0 ? colors.profit : colors.loss}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );

  // Bare mode
  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          <div>
            <span className="text-neutral-400">{t('statistics.totalPnl')}:</span>
            <span className={`font-semibold ml-1 ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPnL(totalPnL)}
            </span>
          </div>
          <div>
            <span className="text-neutral-400">{t('charts.avgMonthly')}:</span>
            <span className={`font-semibold ml-1 ${avgMonthlyPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPnL(avgMonthlyPnL)}
            </span>
          </div>
        </div>
        {chartContent}
      </div>
    );
  }

  // Full card mode
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('charts.monthlyPerformance')}
        </h3>
        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">{t('statistics.totalPnl')}: </span>
            <span className={`font-medium ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {formatPnL(totalPnL)}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">{t('charts.avgMonthly')}: </span>
            <span className={`font-medium ${avgMonthlyPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {formatPnL(avgMonthlyPnL)}
            </span>
          </div>
        </div>
      </div>
      {chartContent}
    </div>
  );
}
