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
  LabelList,
} from 'recharts';
import type { AssetTypeBreakdownItem } from '@/types';
import { formatCurrency } from '@/utils/format';

interface AssetTypeChartProps {
  data: AssetTypeBreakdownItem[];
  isLoading?: boolean;
  onBarClick?: (assetType: string) => void;
  bare?: boolean;
}

const ASSET_TYPE_COLORS: Record<string, string> = {
  stock: '#3b82f6',
  option: '#8b5cf6',
  crypto: '#f59e0b',
  forex: '#10b981',
  futures: '#ef4444',
};

const ASSET_TYPE_LABELS: Record<string, string> = {
  stock: 'Stock',
  option: 'Option',
  crypto: 'Crypto',
  forex: 'Forex',
  futures: 'Futures',
};

export function AssetTypeChart({ data, isLoading, onBarClick, bare = false }: AssetTypeChartProps) {
  const { t } = useTranslation();

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
          {t('charts.assetTypePerformance')}
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          {t('common.noData')}
        </div>
      </div>
    );
  }

  const chartData = data.map((item) => ({
    type: ASSET_TYPE_LABELS[item.asset_type] || item.asset_type,
    rawType: item.asset_type,
    pnl: item.total_pnl,
    count: item.count,
    winRate: item.win_rate,
    avgPnl: item.avg_pnl,
    avgHolding: item.avg_holding_days,
  }));

  const totalPnL = data.reduce((sum, item) => sum + item.total_pnl, 0);
  const totalTrades = data.reduce((sum, item) => sum + item.count, 0);

  const chartContent = (
    <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 10, right: 60, left: 60, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:stroke-gray-700" horizontal={true} vertical={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
            />
            <YAxis
              type="category"
              dataKey="type"
              tick={{ fontSize: 12, fill: '#6b7280' }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
              width={60}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255,255,255,0.95)',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px 12px',
              }}
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
                      <p className="font-semibold text-gray-900 dark:text-white">{data.type}</p>
                      <div className="mt-1 space-y-0.5 text-sm">
                        <p className={data.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {t('statistics.totalPnl')}: {formatCurrency(data.pnl)}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('charts.tradeCount')}: {data.count}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('common.winRate')}: {data.winRate.toFixed(1)}%
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('charts.avgPnl')}: {formatCurrency(data.avgPnl)}
                        </p>
                        <p className="text-gray-600 dark:text-gray-400">
                          {t('statistics.avgHoldingDays')}: {data.avgHolding.toFixed(1)}
                        </p>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar
              dataKey="pnl"
              radius={[0, 4, 4, 0]}
              onClick={(data: unknown) => {
                const d = data as { rawType?: string };
                if (onBarClick && d?.rawType) {
                  onBarClick(d.rawType);
                }
              }}
              style={{ cursor: onBarClick ? 'pointer' : 'default' }}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={ASSET_TYPE_COLORS[entry.rawType] || '#6b7280'}
                />
              ))}
              <LabelList
                dataKey="pnl"
                position="right"
                formatter={(value) => formatCurrency(Number(value))}
                style={{ fontSize: 11, fill: '#6b7280' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
    </div>
  );

  const legend = (
    <div className="mt-4 flex items-center justify-center gap-4 flex-wrap">
      {chartData.map((item) => (
        <div key={item.rawType} className="flex items-center gap-1.5 text-xs">
          <div
            className="w-3 h-3 rounded"
            style={{ backgroundColor: ASSET_TYPE_COLORS[item.rawType] || '#6b7280' }}
          />
          <span className="text-gray-600 dark:text-gray-300">
            {item.type} ({item.count})
          </span>
        </div>
      ))}
    </div>
  );

  if (bare) {
    return (
      <div>
        <div className="flex items-center justify-between mb-4 text-[13px]">
          <div>
            <span className="text-neutral-400">{t('statistics.totalTrades')}:</span>
            <span className="font-semibold ml-1">{totalTrades}</span>
          </div>
          <div>
            <span className="text-neutral-400">{t('statistics.totalPnl')}:</span>
            <span className={`font-semibold ml-1 ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totalPnL)}
            </span>
          </div>
        </div>
        {chartContent}
        {legend}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {t('charts.assetTypePerformance')}
        </h3>
        <div className="flex items-center gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">{t('statistics.totalTrades')}: </span>
            <span className="font-medium text-gray-900 dark:text-white">{totalTrades}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">{t('statistics.totalPnl')}: </span>
            <span className={`font-medium ${totalPnL >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {formatCurrency(totalPnL)}
            </span>
          </div>
        </div>
      </div>
      {chartContent}
      {legend}
    </div>
  );
}
