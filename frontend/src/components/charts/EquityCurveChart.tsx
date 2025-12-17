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
import type { EquityCurvePoint } from '@/types';
import { formatCurrency } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  totalPnL: number;
  maxDrawdown?: number | null;
  title?: string;
  bare?: boolean;
  isLoading?: boolean;
}

export function EquityCurveChart({ data, totalPnL, maxDrawdown, title, bare, isLoading }: EquityCurveChartProps) {
  const { t, i18n } = useTranslation();
  const colors = useChartColors();
  const displayTitle = title || t('charts.equityCurve');
  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US';

  if (isLoading) {
    return (
      <div className={bare ? '' : 'bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700'}>
        {!bare && (
          <div className="h-6 w-32 bg-neutral-200 dark:bg-neutral-700 rounded mb-4 animate-pulse" />
        )}
        <div className="h-64 bg-neutral-100 dark:bg-neutral-800 rounded-lg animate-pulse" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={bare ? '' : 'bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700'}>
        {!bare && (
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {displayTitle}
          </h3>
        )}
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
    pnl: point.cumulative_pnl,
    trades: point.trade_count,
  }));

  const lineColor = totalPnL >= 0 ? colors.profit : colors.loss;

  return (
    <div className={bare ? '' : 'bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700'}>
      {!bare && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {displayTitle}
          </h3>
          <div className="flex items-center space-x-4">
            <div className="text-sm">
              <span className="text-gray-500 dark:text-gray-400">Total: </span>
              <span
                className={`font-medium ${totalPnL >= 0 ? 'text-profit' : 'text-loss'}`}
              >
                {formatCurrency(totalPnL)}
              </span>
            </div>
            {maxDrawdown && maxDrawdown > 0 && (
              <div className="text-sm">
                <span className="text-gray-500 dark:text-gray-400">Max DD: </span>
                <span className="font-medium text-loss">
                  {formatCurrency(-maxDrawdown)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
            />
            <YAxis
              tick={{ fontSize: 12, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">{data.date}</p>
                      <p className="text-sm mt-1" style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                        {t('common.pnl')}: {formatCurrency(data.pnl)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={0} stroke={colors.text} strokeDasharray="3 3" />
            <Line
              type="monotone"
              dataKey="pnl"
              stroke={lineColor}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: lineColor }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
