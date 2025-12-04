import { useQuery } from '@tanstack/react-query';
import { statisticsApi } from '@/api/client';
import { formatCurrency, formatPercent } from '@/utils/format';
import clsx from 'clsx';

export function Statistics() {
  const { data: performance, isLoading } = useQuery({
    queryKey: ['statistics', 'performance'],
    queryFn: () => statisticsApi.getPerformance(),
  });

  const { data: bySymbol } = useQuery({
    queryKey: ['statistics', 'by-symbol'],
    queryFn: () => statisticsApi.getBySymbol({ limit: 10 }),
  });

  const { data: byGrade } = useQuery({
    queryKey: ['statistics', 'by-grade'],
    queryFn: () => statisticsApi.getByGrade(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Statistics
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Detailed performance analysis
        </p>
      </div>

      {/* Performance Overview */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Performance Overview
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-gray-500">Total P&L</p>
            <p
              className={clsx(
                'text-2xl font-bold',
                performance?.total_pnl && performance.total_pnl > 0
                  ? 'text-profit'
                  : 'text-loss'
              )}
            >
              {formatCurrency(performance?.total_pnl)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Win Rate</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {formatPercent(performance?.win_rate, 1)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Profit Factor</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {performance?.profit_factor?.toFixed(2) || '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Max Drawdown</p>
            <p className="text-2xl font-bold text-loss">
              {formatCurrency(performance?.max_drawdown ? -performance.max_drawdown : 0)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Average Win</p>
            <p className="text-2xl font-bold text-profit">
              {formatCurrency(performance?.avg_win)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Average Loss</p>
            <p className="text-2xl font-bold text-loss">
              {formatCurrency(performance?.avg_loss)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Total Trades</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {performance?.total_trades}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Avg Holding Days</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {performance?.avg_holding_days?.toFixed(1)}
            </p>
          </div>
        </div>
      </div>

      {/* Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Symbol */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              By Symbol (Top 10)
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Symbol
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Trades
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    P&L
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Win Rate
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {bySymbol?.map((item) => (
                  <tr key={item.symbol}>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                      {item.symbol}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {item.count}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-right font-medium',
                        item.total_pnl > 0 ? 'text-profit' : 'text-loss'
                      )}
                    >
                      {formatCurrency(item.total_pnl)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {formatPercent(item.win_rate, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* By Grade */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              By Grade
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Grade
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Trades
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    P&L
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Win Rate
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {byGrade?.map((item) => (
                  <tr key={item.grade}>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                      {item.grade}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {item.count}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-right font-medium',
                        item.total_pnl > 0 ? 'text-profit' : 'text-loss'
                      )}
                    >
                      {formatCurrency(item.total_pnl)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {formatPercent(item.win_rate, 1)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
