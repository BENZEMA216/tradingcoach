import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { positionsApi } from '@/api/client';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass, formatHoldingDays } from '@/utils/format';
import clsx from 'clsx';

export function Positions() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const { data, isLoading } = useQuery({
    queryKey: ['positions', page, pageSize],
    queryFn: () => positionsApi.list(page, pageSize),
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Positions
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            {data?.total || 0} total positions
          </p>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Symbol
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Direction
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Open Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Close Date
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Quantity
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  P&L
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Return
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Grade
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Holding
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {isLoading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={9} className="px-4 py-4">
                      <div className="h-4 bg-gray-100 dark:bg-gray-700 rounded animate-pulse"></div>
                    </td>
                  </tr>
                ))
              ) : (
                data?.items.map((position) => (
                  <tr
                    key={position.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-3">
                      <div>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {position.symbol}
                        </span>
                        {position.symbol_name && (
                          <span className="block text-xs text-gray-500">
                            {position.symbol_name}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'px-2 py-1 text-xs rounded',
                          position.direction === 'long'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        )}
                      >
                        {position.direction === 'long' ? 'Long' : 'Short'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(position.open_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(position.close_date)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-900 dark:text-white">
                      {position.quantity}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm text-right font-medium',
                        getPnLColorClass(position.net_pnl)
                      )}
                    >
                      {formatCurrency(position.net_pnl)}
                    </td>
                    <td
                      className={clsx(
                        'px-4 py-3 text-sm text-right font-medium',
                        getPnLColorClass(position.net_pnl_pct)
                      )}
                    >
                      {formatPercent(position.net_pnl_pct)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={clsx(
                          'px-2 py-1 text-xs font-medium rounded',
                          getGradeBadgeClass(position.score_grade)
                        )}
                      >
                        {position.score_grade || '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-500">
                      {formatHoldingDays(position.holding_period_days)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && (
          <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Showing {(page - 1) * pageSize + 1} to{' '}
              {Math.min(page * pageSize, data.total)} of {data.total}
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
                className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
