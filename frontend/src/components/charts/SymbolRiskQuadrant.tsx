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
                    <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-neutral-900 dark:text-neutral-100">{data.symbol}</p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p style={{ color: colors.profit }}>{t('charts.avgWin')}: {formatCurrency(data.avg_win)}</p>
                        <p style={{ color: colors.loss }}>{t('charts.avgLoss')}: {formatCurrency(data.avg_loss)}</p>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {t('charts.tradeCount')}: {data.trade_count}
                        </p>
                        <p className="text-neutral-600 dark:text-neutral-400">
                          {t('common.winRate')}: {data.win_rate.toFixed(1)}%
                        </p>
                        <p style={{ color: data.total_pnl >= 0 ? colors.profit : colors.loss }}>
                          {t('statistics.totalPnl')}: {formatCurrency(data.total_pnl)}
                        </p>
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
    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
      <div className="text-center p-1 bg-green-50 dark:bg-green-900/20 rounded">
        {t('charts.quadrantHighWinLowLoss')}
      </div>
      <div className="text-center p-1 bg-yellow-50 dark:bg-yellow-900/20 rounded">
        {t('charts.quadrantHighWinHighLoss')}
      </div>
      <div className="text-center p-1 bg-gray-50 dark:bg-gray-700/50 rounded">
        {t('charts.quadrantLowWinLowLoss')}
      </div>
      <div className="text-center p-1 bg-red-50 dark:bg-red-900/20 rounded">
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
