import type { RecentTradeItem } from '@/types';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass } from '@/utils/format';
import clsx from 'clsx';

interface RecentTradesTableProps {
  trades: RecentTradeItem[];
  isLoading?: boolean;
}

export function RecentTradesTable({ trades, isLoading }: RecentTradesTableProps) {
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-gray-100 dark:bg-gray-700 rounded mb-2"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Recent Trades
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Symbol
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                P&L
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Return
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Grade
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {trades.map((trade) => (
              <tr
                key={trade.id}
                className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {trade.symbol}
                    </span>
                    <span
                      className={clsx(
                        'ml-2 px-2 py-0.5 text-xs rounded',
                        trade.direction === 'long'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200'
                      )}
                    >
                      {trade.direction === 'long' ? 'L' : 'S'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(trade.close_date)}
                </td>
                <td
                  className={clsx(
                    'px-6 py-4 whitespace-nowrap text-sm font-medium text-right',
                    getPnLColorClass(trade.net_pnl)
                  )}
                >
                  {formatCurrency(trade.net_pnl)}
                </td>
                <td
                  className={clsx(
                    'px-6 py-4 whitespace-nowrap text-sm font-medium text-right',
                    getPnLColorClass(trade.net_pnl_pct)
                  )}
                >
                  {formatPercent(trade.net_pnl_pct)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span
                    className={clsx(
                      'px-2 py-1 text-xs font-medium rounded',
                      getGradeBadgeClass(trade.grade)
                    )}
                  >
                    {trade.grade || '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
