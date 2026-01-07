import { useTranslation } from 'react-i18next';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { EquityCurvePoint } from '@/types';
import { getPrivacyAwareFormatters } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

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

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatPnL, formatAxis } = getPrivacyAwareFormatters();

  if (isLoading) {
    if (bare) {
      return <ChartSkeleton height="h-64" showTitle={false} />;
    }
    return (
      <div className="bg-white dark:bg-black rounded-sm p-6 shadow-sm border border-neutral-200 dark:border-white/10 transition-colors">
        <ChartSkeleton height="h-64" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) {
      return <EmptyState icon="chart" height="h-64" size="sm" />;
    }
    return (
      <div className="bg-white dark:bg-black rounded-sm p-6 shadow-sm border border-neutral-200 dark:border-white/10 transition-colors">
        <h3 className="text-lg font-mono font-bold text-slate-900 dark:text-white mb-4 uppercase tracking-widest text-xs">
          {displayTitle}
        </h3>
        <EmptyState icon="chart" height="h-64" size="sm" />
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
    <div className={bare ? '' : 'bg-white dark:bg-black rounded-sm p-6 shadow-sm dark:shadow-none border border-neutral-200 dark:border-white/10 transition-colors'}>
      {!bare && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em]">
            {displayTitle}
          </h3>
          <div className="flex items-center space-x-4">
            <div className="text-sm">
              <span className="text-gray-500 dark:text-gray-400">Total: </span>
              <span
                className={`font-mono font-medium ${totalPnL >= 0 ? 'text-profit' : 'text-loss'}`}
              >
                {formatPnL(totalPnL)}
              </span>
            </div>
            {maxDrawdown && maxDrawdown > 0 && (
              <div className="text-sm">
                <span className="text-gray-500 dark:text-gray-400">Max DD: </span>
                <span className="font-mono font-medium text-loss">
                  {formatPnL(-maxDrawdown)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="equityCurveGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={lineColor} stopOpacity={0.4} />
                <stop offset="95%" stopColor={lineColor} stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke={colors.grid}
              strokeOpacity={0.5}
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={{ stroke: colors.axis, strokeOpacity: 0.5 }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 11, fill: colors.text }}
              tickLine={false}
              axisLine={false}
              tickFormatter={formatAxis}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-black border border-neutral-200 dark:border-white/20 rounded-sm p-3 shadow-xl backdrop-blur-sm">
                      <p className="font-mono font-bold text-slate-900 dark:text-white text-xs">{data.date}</p>
                      <p className="text-xs mt-1.5 font-mono" style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                        {t('common.pnl')}: {formatPnL(data.pnl)}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <ReferenceLine y={0} stroke={colors.zeroline} strokeDasharray="4 4" strokeOpacity={0.7} />
            <Area
              type="monotone"
              dataKey="pnl"
              stroke={lineColor}
              strokeWidth={2}
              fill="url(#equityCurveGradient)"
              dot={false}
              activeDot={{
                r: 5,
                fill: lineColor,
                stroke: colors.background,
                strokeWidth: 2,
              }}
              animationDuration={1000}
              animationEasing="ease-out"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
