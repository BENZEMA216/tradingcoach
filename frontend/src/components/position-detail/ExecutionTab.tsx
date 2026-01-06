import { useTranslation } from 'react-i18next';
import {
  formatCurrency,
  formatDateTime,
  getPnLColorClass,
} from '@/utils/format';
import type { PositionTrade } from '@/types';
import clsx from 'clsx';

interface ExecutionTabProps {
  trades?: PositionTrade[];
  loading?: boolean;
}

export function ExecutionTab({ trades, loading }: ExecutionTabProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Calculate slippage summary
  const slippageSummary = trades?.reduce(
    (acc, trade) => {
      if (trade.slippage !== null) {
        acc.total += trade.slippage;
        acc.count++;
        if (trade.slippage > acc.worst) acc.worst = trade.slippage;
        if (trade.slippage < acc.best) acc.best = trade.slippage;
      }
      return acc;
    },
    { total: 0, count: 0, best: Infinity, worst: -Infinity }
  );

  const avgSlippage = slippageSummary && slippageSummary.count > 0
    ? slippageSummary.total / slippageSummary.count
    : null;

  // Calculate fees summary
  const feesSummary = trades?.reduce(
    (acc, trade) => {
      acc.total += trade.total_fees;
      return acc;
    },
    { total: 0 }
  );

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Trades */}
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
          <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
            {t('positionDetail.totalExecutions')}
          </div>
          <div className="text-2xl font-bold">
            {trades?.length || 0}
          </div>
        </div>

        {/* Total Fees */}
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
          <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
            {t('positionDetail.totalFees')}
          </div>
          <div className="text-2xl font-bold text-red-600">
            -{formatCurrency(feesSummary?.total || 0)}
          </div>
        </div>

        {/* Avg Slippage */}
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
          <div className="text-xs text-neutral-500 uppercase tracking-wider mb-1">
            {t('positionDetail.avgSlippage')}
          </div>
          <div className={clsx('text-2xl font-bold', avgSlippage !== null ? getPnLColorClass(-avgSlippage) : '')}>
            {avgSlippage !== null ? formatCurrency(avgSlippage) : '-'}
          </div>
        </div>
      </div>

      {/* Trade Executions Table */}
      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {t('positionDetail.tradeExecutions')}
          </h3>
        </div>

        {loading ? (
          <div className="h-48 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-neutral-300 border-t-blue-600"></div>
          </div>
        ) : trades && trades.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 dark:bg-neutral-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.time')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.direction')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.price')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.quantity')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.amount')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.fees')}
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-neutral-500 uppercase">
                    {t('positionDetail.slippage')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 dark:divide-neutral-800">
                {trades.map((trade) => (
                  <tr key={trade.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/30">
                    <td className="px-4 py-3 text-neutral-600 dark:text-neutral-300">
                      {formatDateTime(trade.filled_time)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'px-2 py-1 text-xs font-medium rounded',
                          trade.direction === 'buy'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        )}
                      >
                        {t(`direction.${trade.direction}`)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      {formatCurrency(trade.filled_price)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {trade.filled_quantity}
                    </td>
                    <td className="px-4 py-3 text-right font-medium">
                      {formatCurrency(trade.filled_amount)}
                    </td>
                    <td className="px-4 py-3 text-right text-red-600">
                      -{formatCurrency(trade.total_fees)}
                    </td>
                    <td className={clsx(
                      'px-4 py-3 text-right font-medium',
                      trade.slippage !== null ? getPnLColorClass(-trade.slippage) : 'text-neutral-400'
                    )}>
                      {trade.slippage !== null ? formatCurrency(trade.slippage) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-neutral-500">
            {t('positionDetail.noLinkedTrades')}
          </div>
        )}
      </div>

      {/* Slippage Analysis */}
      {slippageSummary && slippageSummary.count > 0 && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-4">
            {t('positionDetail.slippageAnalysis')}
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-1">{isZh ? '总滑点' : 'Total Slippage'}</div>
              <div className={clsx('text-lg font-bold', getPnLColorClass(-slippageSummary.total))}>
                {formatCurrency(slippageSummary.total)}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
              <div className="text-xs text-neutral-500 mb-1">{isZh ? '最佳滑点' : 'Best Slippage'}</div>
              <div className="text-lg font-bold text-green-600">
                {slippageSummary.best !== Infinity ? formatCurrency(slippageSummary.best) : '-'}
              </div>
            </div>
            <div className="text-center p-3 rounded-lg bg-red-50 dark:bg-red-900/20">
              <div className="text-xs text-neutral-500 mb-1">{isZh ? '最差滑点' : 'Worst Slippage'}</div>
              <div className="text-lg font-bold text-red-600">
                {slippageSummary.worst !== -Infinity ? formatCurrency(slippageSummary.worst) : '-'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
