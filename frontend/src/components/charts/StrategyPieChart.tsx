import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useTranslation } from 'react-i18next';
import type { StrategyBreakdownItem } from '@/types';
import { formatCurrency } from '@/utils/format';
import { useChartColors } from '@/hooks/useChartColors';

interface StrategyPieChartProps {
  data: StrategyBreakdownItem[];
  title?: string;
  onDrillDown?: (strategyType: string, strategyName: string) => void;
  bare?: boolean;
  isLoading?: boolean;
}

const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#ef4444', '#8b5cf6', '#6b7280'];

interface ChartDataItem {
  name: string;
  strategyKey: string;
  strategyType: string;
  value: number;
  pnl: number;
  winRate: number;
  [key: string]: string | number;
}

export function StrategyPieChart({ data, title, onDrillDown, bare = false, isLoading = false }: StrategyPieChartProps) {
  const { t } = useTranslation();
  const colors = useChartColors();
  const displayTitle = title || t('dashboard.strategyBreakdown');

  // Helper to translate strategy name
  const translateStrategy = (strategy: string): string => {
    const key = strategy.toLowerCase().replace(/\s+/g, '_');
    return t(`strategy.${key}`, { defaultValue: strategy });
  };

  if (isLoading) {
    return (
      <div className={bare ? '' : 'bg-white dark:bg-black rounded-sm p-6 shadow-sm border border-neutral-200 dark:border-white/10 transition-colors'}>
        {!bare && (
          <div className="h-6 w-32 bg-neutral-200 dark:bg-white/10 rounded-sm mb-4 animate-pulse" />
        )}
        <div className="h-64 bg-neutral-100 dark:bg-white/5 rounded-sm animate-pulse" />
      </div>
    );
  }

  // Treat "all unclassified" the same as no data — pie chart of 100% one slice is noise
  const isAllUnclassified =
    data && data.length === 1 &&
    (data[0].strategy_name === 'Unclassified' || data[0].strategy === 'unclassified');

  if (!data || data.length === 0 || isAllUnclassified) {
    return (
      <div className={bare ? '' : 'bg-white dark:bg-black rounded-sm p-6 shadow-sm border border-neutral-200 dark:border-white/10 transition-colors'}>
        {!bare && (
          <h3 className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em] mb-4">
            {displayTitle}
          </h3>
        )}
        <div className="h-64 flex flex-col items-center justify-center text-slate-400 dark:text-white/30 font-mono text-xs gap-2">
          <div>{t('strategy.allUnclassifiedTitle', '暂未分类策略')}</div>
          <div className="text-[10px] text-slate-300 dark:text-white/20">
            {t('strategy.allUnclassifiedHint', '策略自动分类正在开发中')}
          </div>
        </div>
      </div>
    );
  }

  const chartData: ChartDataItem[] = data.map((item) => ({
    name: translateStrategy(item.strategy_name),
    strategyKey: item.strategy_name,
    strategyType: item.strategy,
    value: item.count,
    pnl: item.total_pnl,
    winRate: item.win_rate,
  }));

  // Handle pie slice click
  const handlePieClick = (data: ChartDataItem) => {
    if (onDrillDown) {
      onDrillDown(data.strategyType, data.name);
    }
  };

  const chartContent = (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%" minHeight={200}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
            label={({ name, percent }) =>
              `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
            }
            labelLine={{ stroke: colors.text, strokeWidth: 1 }}
            onClick={(_, index) => handlePieClick(chartData[index])}
            style={{ cursor: onDrillDown ? 'pointer' : 'default' }}
          >
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length > 0) {
                const data = payload[0].payload as ChartDataItem;
                return (
                  <div className="bg-white dark:bg-black border border-neutral-200 dark:border-white/20 rounded-sm p-3 shadow-xl backdrop-blur-sm">
                    <p className="font-mono font-bold text-slate-900 dark:text-white text-xs">{data.name}</p>
                    <div className="text-xs mt-1 space-y-0.5 font-mono">
                      <p className="text-slate-500 dark:text-white/60">{t('common.trades')}: {data.value}</p>
                      <p style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                        {t('common.pnl')}: {formatCurrency(data.pnl)}
                      </p>
                      <p className="text-slate-500 dark:text-white/60">{t('common.winRate')}: {data.winRate.toFixed(1)}%</p>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );

  if (bare) {
    return chartContent;
  }

  return (
    <div className="bg-white dark:bg-black rounded-sm p-6 shadow-sm border border-neutral-200 dark:border-white/10 transition-colors">
      <h3 className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em] mb-4">
        {displayTitle}
      </h3>
      {chartContent}
    </div>
  );
}
