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
      <ResponsiveContainer width="100%" height="100%">
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
                  <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 shadow-lg">
                    <p className="font-medium text-neutral-900 dark:text-neutral-100">{data.name}</p>
                    <div className="text-sm mt-1 space-y-0.5">
                      <p className="text-neutral-600 dark:text-neutral-400">{t('common.trades')}: {data.value}</p>
                      <p style={{ color: data.pnl >= 0 ? colors.profit : colors.loss }}>
                        {t('common.pnl')}: {formatCurrency(data.pnl)}
                      </p>
                      <p className="text-neutral-600 dark:text-neutral-400">{t('common.winRate')}: {data.winRate.toFixed(1)}%</p>
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
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {displayTitle}
      </h3>
      {chartContent}
    </div>
  );
}
