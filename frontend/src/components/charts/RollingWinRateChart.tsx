import { useTranslation } from 'react-i18next';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { RollingMetricsItem } from '@/types';
import { useChartColors } from '@/hooks/useChartColors';

interface RollingWinRateChartProps {
  data: RollingMetricsItem[];
  window?: number;
  isLoading?: boolean;
  bare?: boolean;
}

export function RollingWinRateChart({ data, window = 20, isLoading, bare = false }: RollingWinRateChartProps) {
  const { t, i18n } = useTranslation();
  const colors = useChartColors();
  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US';

  if (isLoading) {
    if (bare) return <div className="h-64 bg-neutral-100 dark:bg-neutral-800 rounded animate-pulse" />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4 animate-pulse" />
        <div className="h-64 bg-gray-100 dark:bg-gray-700/50 rounded animate-pulse" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) return <div className="h-64 flex items-center justify-center text-neutral-500">{t('charts.insufficientData', { count: window })}</div>;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('charts.rollingWinRate')}</h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">{t('charts.insufficientData', { count: window })}</div>
      </div>
    );
  }

  const chartData = data.map((item) => ({
    trade: item.trade_index,
    date: new Date(item.close_date).toLocaleDateString(locale, { month: 'short', day: 'numeric' }),
    winRate: item.rolling_win_rate,
    avgPnl: item.rolling_avg_pnl,
  }));

  const currentWinRate = chartData[chartData.length - 1]?.winRate || 0;
  const firstWinRate = chartData[0]?.winRate || 0;
  const trend = currentWinRate - firstWinRate;

  const chartContent = (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
          <XAxis dataKey="trade" tick={{ fontSize: 11, fill: colors.text }} tickLine={false} axisLine={{ stroke: colors.axis }} />
          <YAxis tick={{ fontSize: 11, fill: colors.text }} tickLine={false} axisLine={{ stroke: colors.axis }} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                    <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                      {t('charts.trade')} #{data.trade}
                    </p>
                    <div className="mt-1 space-y-0.5 text-sm">
                      <p style={{ color: data.winRate >= 50 ? colors.profit : colors.loss }}>
                        {t('common.winRate')}: {data.winRate.toFixed(1)}%
                      </p>
                      <p className="text-neutral-600 dark:text-neutral-400">{data.date}</p>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine y={50} stroke={colors.text} strokeDasharray="3 3" />
          <Line type="monotone" dataKey="winRate" stroke="#8b5cf6" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: '#8b5cf6' }} name="winRate" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          <span className="text-neutral-400">{t('charts.rollingWindow', { count: window })}</span>
          <div className="flex items-center gap-5">
            <div><span className="text-neutral-400">{t('charts.current')}:</span> <span className={`font-semibold ml-1 ${currentWinRate >= 50 ? 'text-green-600' : 'text-red-600'}`}>{currentWinRate.toFixed(1)}%</span></div>
            <div><span className="text-neutral-400">{t('charts.trend')}:</span> <span className={`font-semibold ml-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}%</span></div>
          </div>
        </div>
        {chartContent}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('charts.rollingWinRate')}</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t('charts.rollingWindow', { count: window })}</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div><span className="text-gray-500 dark:text-gray-400">{t('charts.current')}: </span><span className={`font-medium ${currentWinRate >= 50 ? 'text-green-500' : 'text-red-500'}`}>{currentWinRate.toFixed(1)}%</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">{t('charts.trend')}: </span><span className={`font-medium ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`}>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}%</span></div>
        </div>
      </div>
      {chartContent}
    </div>
  );
}
