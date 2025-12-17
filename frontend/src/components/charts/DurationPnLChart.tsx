import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ZAxis,
} from 'recharts';
import type { DurationPnLItem } from '@/types';
import { formatCurrency } from '@/utils/format';

interface DurationPnLChartProps {
  data: DurationPnLItem[];
  isLoading?: boolean;
  bare?: boolean;
}

// TradingView colors
const PROFIT_COLOR = '#26a69a';
const LOSS_COLOR = '#ef5350';

export function DurationPnLChart({ data, isLoading, bare = false }: DurationPnLChartProps) {
  const { t } = useTranslation();

  // Calculate optimal visualization settings based on data density
  const { processedData, dotSize, dotOpacity, xAxisScale } = useMemo(() => {
    if (!data || data.length === 0) {
      return { processedData: [], dotSize: 40, dotOpacity: 0.6, xAxisScale: 'linear' };
    }

    const count = data.length;

    // Adjust dot size and opacity based on data count
    let size: number;
    let opacity: number;

    if (count > 300) {
      size = 15;
      opacity = 0.4;
    } else if (count > 150) {
      size = 25;
      opacity = 0.5;
    } else if (count > 50) {
      size = 35;
      opacity = 0.6;
    } else {
      size = 50;
      opacity = 0.7;
    }

    // Transform data: use sqrt scale for X-axis to spread out dense areas
    // Add a transformed x value for better distribution
    const processed = data.map(d => ({
      ...d,
      // Use sqrt to spread out lower values (most trades are short-term)
      holding_days_display: Math.sqrt(d.holding_days) * 10,
      original_days: d.holding_days,
    }));

    return {
      processedData: processed,
      dotSize: size,
      dotOpacity: opacity,
      xAxisScale: 'sqrt' as const,
    };
  }, [data]);

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
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.durationVsPnl')}
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          {t('common.noData')}
        </div>
      </div>
    );
  }

  const winners = processedData.filter(d => d.is_winner);
  const losers = processedData.filter(d => !d.is_winner);

  // Calculate average holding days using original data
  const avgDaysWinners = winners.length > 0
    ? winners.reduce((sum, d) => sum + d.original_days, 0) / winners.length
    : 0;
  const avgDaysLosers = losers.length > 0
    ? losers.reduce((sum, d) => sum + d.original_days, 0) / losers.length
    : 0;

  // Custom tick formatter to show original days from sqrt-transformed values
  const formatXAxisTick = (value: number) => {
    const originalDays = Math.round((value / 10) ** 2);
    return originalDays.toString();
  };

  const chartContent = (
    <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis
              type="number"
              dataKey="holding_days_display"
              name="days"
              tick={{ fontSize: 11, fill: '#9ca3af' }}
              tickLine={false}
              axisLine={{ stroke: '#4b5563' }}
              tickFormatter={formatXAxisTick}
              domain={['dataMin - 5', 'dataMax + 5']}
              label={{
                value: t('charts.holdingDays'),
                position: 'insideBottom',
                offset: -10,
                style: { fontSize: 11, fill: '#9ca3af' },
              }}
            />
            <YAxis
              type="number"
              dataKey="pnl"
              name="pnl"
              tick={{ fontSize: 11, fill: '#9ca3af' }}
              tickLine={false}
              axisLine={{ stroke: '#4b5563' }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            />
            <ZAxis range={[dotSize, dotSize]} />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">
                        {d.symbol} ({d.direction === 'long' ? t('direction.long') : t('direction.short')})
                      </p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p style={{ color: d.pnl >= 0 ? PROFIT_COLOR : LOSS_COLOR }}>
                          {t('common.pnl')}: {formatCurrency(d.pnl)}
                        </p>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {t('charts.holdingDays')}: {d.original_days} {t('common.days')}
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
            <Scatter
              name="Winners"
              data={winners}
              fill={PROFIT_COLOR}
              fillOpacity={dotOpacity}
            />
            <Scatter
              name="Losers"
              data={losers}
              fill={LOSS_COLOR}
              fillOpacity={dotOpacity}
            />
          </ScatterChart>
        </ResponsiveContainer>
    </div>
  );

  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PROFIT_COLOR }} />
            <span className="text-neutral-400">
              {t('reports.winners')} ({avgDaysWinners.toFixed(1)} {t('common.days')})
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: LOSS_COLOR }} />
            <span className="text-neutral-400">
              {t('reports.losers')} ({avgDaysLosers.toFixed(1)} {t('common.days')})
            </span>
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
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('charts.durationVsPnl')}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {t('charts.durationVsPnlHint')}
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PROFIT_COLOR }} />
            <span className="text-gray-600 dark:text-gray-300">
              {t('reports.winners')} ({avgDaysWinners.toFixed(1)} {t('common.days')})
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: LOSS_COLOR }} />
            <span className="text-gray-600 dark:text-gray-300">
              {t('reports.losers')} ({avgDaysLosers.toFixed(1)} {t('common.days')})
            </span>
          </div>
        </div>
      </div>
      {chartContent}
    </div>
  );
}
