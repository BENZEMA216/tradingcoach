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
} from 'recharts';
import type { PnLDistributionBin } from '@/types';
import { formatCurrency } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';

interface PnLDistributionChartProps {
  data: PnLDistributionBin[];
  isLoading?: boolean;
  bare?: boolean;
}

export function PnLDistributionChart({ data, isLoading, bare = false }: PnLDistributionChartProps) {
  const { t } = useTranslation();
  const colors = useChartColors();

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
    if (bare) return <div className="h-64 flex items-center justify-center text-neutral-500">{t('common.noData')}</div>;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{t('charts.pnlDistribution')}</h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">{t('common.noData')}</div>
      </div>
    );
  }

  const chartData = data.map((bin) => ({
    range: `$${bin.min_value.toFixed(0)}`,
    count: bin.count,
    isProfit: bin.is_profit,
    min: bin.min_value,
    max: bin.max_value,
  }));

  const profitBins = data.filter(b => b.is_profit);
  const lossBins = data.filter(b => !b.is_profit);
  const profitCount = profitBins.reduce((sum, bin) => sum + bin.count, 0);
  const lossCount = lossBins.reduce((sum, bin) => sum + bin.count, 0);

  const chartContent = (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
          <XAxis dataKey="range" tick={{ fontSize: 10, fill: colors.text }} tickLine={false} axisLine={{ stroke: colors.axis }} interval={Math.floor(chartData.length / 6)} />
          <YAxis tick={{ fontSize: 11, fill: colors.text }} tickLine={false} axisLine={{ stroke: colors.axis }} />
          <Tooltip
            cursor={{ fill: 'rgba(0,0,0,0.05)' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                    <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                      {formatCurrency(data.min)} ~ {formatCurrency(data.max)}
                    </p>
                    <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                      {t('charts.tradeCount')}: {data.count}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Bar dataKey="count" radius={[2, 2, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.isProfit ? colors.profit : colors.loss} fillOpacity={0.8} />
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
          <div><span className="text-neutral-400">{t('reports.winners')}:</span> <span className="font-semibold text-green-600 ml-1">{profitCount}</span></div>
          <div><span className="text-neutral-400">{t('reports.losers')}:</span> <span className="font-semibold text-red-600 ml-1">{lossCount}</span></div>
        </div>
        {chartContent}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{t('charts.pnlDistribution')}</h3>
        <div className="flex items-center gap-4 text-sm">
          <div><span className="text-gray-500 dark:text-gray-400">{t('reports.winners')}: </span><span className="font-medium text-green-500">{profitCount}</span></div>
          <div><span className="text-gray-500 dark:text-gray-400">{t('reports.losers')}: </span><span className="font-medium text-red-500">{lossCount}</span></div>
        </div>
      </div>
      {chartContent}
    </div>
  );
}
