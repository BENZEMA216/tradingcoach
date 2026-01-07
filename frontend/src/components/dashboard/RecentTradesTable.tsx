import { useTranslation } from 'react-i18next';
import type { RecentTradeItem } from '@/types';
import { formatCurrency, formatPercent, formatDate, getPnLColorClass, getGradeBadgeClass } from '@/utils/format';
import clsx from 'clsx';

interface RecentTradesTableProps {
  trades: RecentTradeItem[];
  isLoading?: boolean;
  title?: string;
}

export function RecentTradesTable({ trades, isLoading, title }: RecentTradesTableProps) {
  const { t } = useTranslation();
  const displayTitle = title || t('dashboard.recentTrades');

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-black border border-neutral-200 dark:border-white/10 rounded-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-200 dark:bg-white/10 rounded w-1/4 mb-4"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-neutral-100 dark:bg-white/5 rounded mb-2"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-black border border-neutral-200 dark:border-white/10 rounded-sm overflow-hidden transition-colors">
      <div className="px-6 py-4 border-b border-neutral-200 dark:border-white/10">
        <h3 className="text-xs font-mono font-bold text-slate-700 dark:text-white uppercase tracking-[0.2em]">
          {displayTitle}
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-neutral-50 dark:bg-black border-b border-neutral-200 dark:border-white/10">
            <tr>
              <th className="px-6 py-3 text-left text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
                {t('positions.symbol')}
              </th>
              <th className="px-6 py-3 text-left text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
                {t('positions.closeDate')}
              </th>
              <th className="px-6 py-3 text-right text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
                {t('positions.pnl')}
              </th>
              <th className="px-6 py-3 text-right text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
                {t('positions.pnlPct')}
              </th>
              <th className="px-6 py-3 text-center text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
                {t('positions.grade')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100 dark:divide-white/5">
            {trades.map((trade) => (
              <tr
                key={trade.id}
                className="group transition-colors duration-200 hover:bg-neutral-50 dark:hover:bg-white/5 cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-sm font-mono font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {trade.symbol}
                    </span>
                    <span
                      className={clsx(
                        'ml-2 px-1 py-0.5 text-[9px] font-bold rounded-sm uppercase tracking-wider',
                        trade.direction === 'long'
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20'
                          : 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-500/20'
                      )}
                    >
                      {trade.direction === 'long' ? 'L' : 'S'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-slate-500 dark:text-white/50">
                  {formatDate(trade.close_date)}
                </td>
                <td
                  className={clsx(
                    'px-6 py-4 whitespace-nowrap text-sm font-bold text-right font-mono tracking-tight',
                    (trade.net_pnl || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                  )}
                >
                  {formatCurrency(trade.net_pnl)}
                </td>
                <td
                  className={clsx(
                    'px-6 py-4 whitespace-nowrap text-sm font-bold text-right font-mono tracking-tight',
                    (trade.net_pnl_pct || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                  )}
                >
                  {formatPercent(trade.net_pnl_pct)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-center">
                  <span
                    className={clsx(
                      'px-2 py-1 text-[10px] font-bold rounded-sm border',
                      // Dual-mode industrial badges
                      trade.grade === 'A' || trade.grade === 'A+' ? 'bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400 border-green-200 dark:border-green-500/30' :
                        trade.grade === 'B' ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/30' :
                          trade.grade === 'C' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-500/30' :
                            'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-500/30'
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
