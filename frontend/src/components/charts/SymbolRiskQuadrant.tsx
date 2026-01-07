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
  Cell,
} from 'recharts';
import type { SymbolRiskItem } from '@/types';
import { getPrivacyAwareFormatters } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';
import { usePrivacyStore } from '@/store/usePrivacyStore';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

interface SymbolRiskQuadrantProps {
  data: SymbolRiskItem[];
  isLoading?: boolean;
  onDotClick?: (symbol: string) => void;
  bare?: boolean;
}

export function SymbolRiskQuadrant({ data, isLoading, onDotClick, bare = false }: SymbolRiskQuadrantProps) {
  const { t } = useTranslation();
  const colors = useChartColors();

  // Subscribe to privacy state for re-renders
  const { isPrivacyMode: _isPrivacyMode } = usePrivacyStore();
  const { formatCurrency, formatAxis } = getPrivacyAwareFormatters();

  if (isLoading) {
    if (bare) return <ChartSkeleton height="h-72" showTitle={false} />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <ChartSkeleton height="h-72" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) return <EmptyState icon="chart" height="h-72" size="sm" />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.symbolRiskQuadrant')}
        </h3>
        <EmptyState icon="chart" height="h-64" size="sm" />
      </div>
    );
  }

  const chartData = data.map((item) => ({
    ...item,
    x: Math.abs(item.avg_loss), // X-axis: avg loss (absolute)
    y: item.avg_win,           // Y-axis: avg win
    z: item.trade_count,       // Bubble size
  }));

  // Calculate averages for quadrant lines
  const avgLoss = chartData.reduce((sum, d) => sum + d.x, 0) / chartData.length;
  const avgWin = chartData.reduce((sum, d) => sum + d.y, 0) / chartData.length;

  // Color based on total P&L
  const getColor = (pnl: number) => {
    if (pnl > 0) return colors.profit;
    if (pnl < 0) return colors.loss;
    return colors.text;
  };

  const chartContent = (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
          <XAxis
            type="number"
            dataKey="x"
            name="avgLoss"
            tick={{ fontSize: 11, fill: colors.text }}
            tickLine={false}
            axisLine={{ stroke: colors.axis }}
            tickFormatter={formatAxis}
            label={{
              value: t('charts.avgLoss'),
              position: 'insideBottom',
              offset: -10,
              style: { fontSize: 11, fill: colors.text },
            }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="avgWin"
            tick={{ fontSize: 11, fill: colors.text }}
            tickLine={false}
            axisLine={{ stroke: colors.axis }}
            tickFormatter={formatAxis}
            label={{
              value: t('charts.avgWin'),
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 11, fill: colors.text },
            }}
          />
          <ZAxis type="number" dataKey="z" range={[60, 400]} />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-black border border-white/20 rounded-sm p-3 shadow-xl backdrop-blur-md">
                    <p className="font-mono font-bold text-white mb-2 pb-2 border-b border-white/10">{data.symbol}</p>
                    <div className="space-y-1 text-xs font-mono">
                      <p style={{ color: colors.profit }}>{t('charts.avgWin')}: {formatCurrency(data.avg_win)}</p>
                      <p style={{ color: colors.loss }}>{t('charts.avgLoss')}: {formatCurrency(data.avg_loss)}</p>
                      <div className="flex justify-between gap-4 text-white/60">
                        <span>{t('charts.tradeCount')}:</span>
                        <span className="text-white">{data.trade_count}</span>
                      </div>
                      <div className="flex justify-between gap-4 text-white/60">
                        <span>{t('common.winRate')}:</span>
                        <span className="text-white">{data.win_rate.toFixed(1)}%</span>
                      </div>
                      <div className="pt-2 mt-1 border-t border-white/10 flex justify-between gap-4">
                        <span className="text-white/60">{t('statistics.totalPnl')}:</span>
                        <span style={{ color: data.total_pnl >= 0 ? colors.profit : colors.loss }}>
                          {formatCurrency(data.total_pnl)}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <ReferenceLine x={avgLoss} stroke={colors.text} strokeDasharray="3 3" />
          <ReferenceLine y={avgWin} stroke={colors.text} strokeDasharray="3 3" />
          <Scatter
            name="Symbols"
            data={chartData}
            onClick={(data: unknown) => {
              const d = data as { symbol?: string };
              if (onDotClick && d?.symbol) {
                onDotClick(d.symbol);
              }
            }}
            style={{ cursor: onDotClick ? 'pointer' : 'default' }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getColor(entry.total_pnl)}
                fillOpacity={0.7}
                stroke={getColor(entry.total_pnl)}
                strokeWidth={1}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );

  const quadrantLegend = (
    <div className="mt-4 grid grid-cols-2 gap-2 text-[10px] font-mono uppercase tracking-wider">
      <div className="text-center p-2 bg-green-500/10 border border-green-500/20 text-green-500 rounded-sm">
        {t('charts.quadrantHighWinLowLoss')}
      </div>
      <div className="text-center p-2 bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 rounded-sm">
        {t('charts.quadrantHighWinHighLoss')}
      </div>
      <div className="text-center p-2 bg-white/5 border border-white/10 text-white/40 rounded-sm">
        {t('charts.quadrantLowWinLowLoss')}
      </div>
      <div className="text-center p-2 bg-red-500/10 border border-red-500/20 text-red-500 rounded-sm">
        {t('charts.quadrantLowWinHighLoss')}
      </div>
    </div>
  );

  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-end mb-3 text-[13px] text-neutral-400">
          {t('charts.bubbleSize')}: {t('charts.tradeCount')}
        </div>
        {chartContent}
        {quadrantLegend}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t('charts.symbolRiskQuadrant')}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {t('charts.symbolRiskQuadrantHint')}
          </p>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {t('charts.bubbleSize')}: {t('charts.tradeCount')}
        </div>
      </div>
      {chartContent}
      {quadrantLegend}
    </div>
  );
}
