import { useTranslation } from 'react-i18next';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';
import type { EquityDrawdownItem } from '@/types';
import { formatCurrency } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';

interface EquityDrawdownChartProps {
  data: EquityDrawdownItem[];
  isLoading?: boolean;
  bare?: boolean; // When true, render without card wrapper (for use in ChartWithInsight)
}

export function EquityDrawdownChart({ data, isLoading, bare = false }: EquityDrawdownChartProps) {
  const { t, i18n } = useTranslation();
  const colors = useChartColors();
  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US';

  if (isLoading) {
    if (bare) {
      return <div className="h-72 bg-neutral-100 dark:bg-neutral-800 rounded animate-pulse" />;
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4 animate-pulse" />
        <div className="h-64 bg-gray-100 dark:bg-gray-700/50 rounded animate-pulse" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) {
      return (
        <div className="h-72 flex items-center justify-center text-neutral-500 dark:text-neutral-400">
          {t('common.noData')}
        </div>
      );
    }
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.equityDrawdown')}
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          {t('common.noData')}
        </div>
      </div>
    );
  }

  const chartData = data.map((point) => ({
    date: new Date(point.date).toLocaleDateString(locale, {
      month: 'short',
      day: 'numeric',
    }),
    equity: point.cumulative_pnl,
    drawdown: -point.drawdown, // Negative for display below zero
    drawdownPct: point.drawdown_pct,
    peak: point.peak,
  }));

  const maxDrawdown = Math.max(...data.map(d => d.drawdown));
  const currentPnL = data[data.length - 1]?.cumulative_pnl || 0;

  // Header with stats
  const statsHeader = (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
        {t('charts.equityDrawdown')}
      </h3>
      <div className="flex items-center gap-4 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">{t('common.pnl')}: </span>
          <span className={`font-medium ${currentPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {formatCurrency(currentPnL)}
          </span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">{t('statistics.maxDrawdown')}: </span>
          <span className="font-medium text-red-500">
            {formatCurrency(-maxDrawdown)}
          </span>
        </div>
      </div>
    </div>
  );

  // The actual chart content
  const chartContent = (
    <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={colors.loss} stopOpacity={0.3} />
                <stop offset="95%" stopColor={colors.loss} stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
              domain={['auto', 0]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">{data.date}</p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p style={{ color: data.equity >= 0 ? colors.profit : colors.loss }}>
                          {t('common.pnl')}: {formatCurrency(data.equity)}
                        </p>
                        <p style={{ color: colors.loss }}>
                          {t('statistics.drawdown')}: {formatCurrency(data.drawdown)}
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => {
                if (value === 'equity') return t('common.pnl');
                if (value === 'drawdown') return t('statistics.drawdown');
                return value;
              }}
            />
            <ReferenceLine y={0} yAxisId="left" stroke={colors.text} strokeDasharray="3 3" />
            <Area
              yAxisId="right"
              type="monotone"
              dataKey="drawdown"
              stroke={colors.loss}
              strokeWidth={1}
              fill="url(#drawdownGradient)"
              name="drawdown"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="equity"
              stroke={colors.profit}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: colors.profit }}
              name="equity"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
  );

  // Bare mode: just the chart with inline stats
  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          <div>
            <span className="text-neutral-400">{t('common.pnl')}:</span>
            <span className={`font-semibold ml-1 ${currentPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(currentPnL)}
            </span>
          </div>
          <div>
            <span className="text-neutral-400">{t('statistics.maxDrawdown')}:</span>
            <span className="font-semibold ml-1 text-red-600">
              {formatCurrency(-maxDrawdown)}
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
      {statsHeader}
      {chartContent}
    </div>
  );
}
