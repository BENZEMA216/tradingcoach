import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import type { NeedsReviewItem } from '@/types';
import { GradeBadge } from '@/components/common';
import { formatCurrency, formatDate, getPnLColorClass } from '@/utils/format';

interface NeedsReviewPanelProps {
  items: NeedsReviewItem[];
  isLoading?: boolean;
}

function translateReason(reason: string, isZh: boolean) {
  if (!isZh) return reason;
  if (reason === 'Large loss') return '大额亏损';
  if (reason.startsWith('Low score')) return reason.replace('Low score', '低评分');
  return reason;
}

export function NeedsReviewPanel({ items, isLoading }: NeedsReviewPanelProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  return (
    <div className="bg-white dark:bg-black border border-neutral-200 dark:border-white/10 rounded-sm overflow-hidden transition-colors">
      <div className="px-6 py-4 border-b border-neutral-200 dark:border-white/10 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xs font-mono font-bold text-slate-700 dark:text-white uppercase tracking-[0.2em]">
            {isZh ? '待复盘交易' : 'Needs Review'}
          </h3>
          <p className="mt-1 text-xs text-slate-500 dark:text-white/40">
            {isZh ? '未复盘的大亏损或低评分交易' : 'Unreviewed large losses or low-grade trades'}
          </p>
        </div>
        <AlertTriangle className="w-4 h-4 text-amber-500" />
      </div>

      {isLoading ? (
        <div className="p-4 space-y-2">
          {[1, 2, 3].map((idx) => (
            <div key={idx} className="h-12 rounded-sm bg-neutral-100 dark:bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="px-6 py-8 text-center text-sm text-slate-500 dark:text-white/40">
          {isZh ? '当前没有待复盘候选' : 'No review candidates right now'}
        </div>
      ) : (
        <div className="divide-y divide-neutral-100 dark:divide-white/5">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/positions/${item.id}`}
              className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 px-6 py-3 hover:bg-neutral-50 dark:hover:bg-white/5 focus:bg-neutral-50 dark:focus:bg-white/5 focus:outline-none transition-colors"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-sm text-slate-900 dark:text-white truncate">
                    {item.symbol}
                  </span>
                  <GradeBadge grade={item.grade} showIncompleteInfo />
                </div>
                <div className="mt-1 text-xs text-slate-500 dark:text-white/40">
                  {formatDate(item.close_date)} · {translateReason(item.reason, isZh)}
                </div>
              </div>
              <div className={clsx('font-mono text-sm font-bold text-right', getPnLColorClass(item.net_pnl))}>
                {formatCurrency(item.net_pnl, item.currency || 'USD')}
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="px-6 py-3 border-t border-neutral-100 dark:border-white/5">
        <Link
          to="/positions?is_reviewed=false"
          className="text-xs font-mono text-blue-600 dark:text-blue-400 hover:underline"
        >
          {t('dashboard.viewAllNeedsReview', isZh ? '查看全部未复盘交易' : 'View all unreviewed trades')}
        </Link>
      </div>
    </div>
  );
}
