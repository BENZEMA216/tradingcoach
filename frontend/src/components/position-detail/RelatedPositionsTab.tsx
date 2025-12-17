import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import {
  formatCurrency,
  formatPercent,
  formatDate,
  getPnLColorClass,
  getGradeBadgeClass,
} from '@/utils/format';
import type { RelatedPosition } from '@/types';
import clsx from 'clsx';
import { ArrowRight, TrendingUp, TrendingDown } from 'lucide-react';

interface RelatedPositionsTabProps {
  relatedPositions?: RelatedPosition[];
  loading?: boolean;
  currentSymbol: string;
  isOption: boolean;
  underlyingSymbol?: string | null;
}

export function RelatedPositionsTab({
  relatedPositions,
  loading,
  currentSymbol,
  isOption,
  underlyingSymbol,
}: RelatedPositionsTabProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Don't render if no related positions and not loading
  if (!loading && (!relatedPositions || relatedPositions.length === 0)) {
    return null;
  }

  // Group by stock vs options
  const stockPositions = relatedPositions?.filter((p) => !p.is_option) || [];
  const optionPositions = relatedPositions?.filter((p) => p.is_option) || [];

  // Calculate totals
  const totalPnL = relatedPositions?.reduce((sum, p) => sum + (p.net_pnl || 0), 0) || 0;

  return (
    <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {t('positionDetail.relatedPositions')}
          </h3>
          <p className="text-xs text-neutral-400 mt-1">
            {isOption
              ? isZh
                ? `与标的 ${underlyingSymbol} 相关的其他交易`
                : `Other trades related to underlying ${underlyingSymbol}`
              : isZh
                ? `${currentSymbol} 的期权交易`
                : `Option trades on ${currentSymbol}`}
          </p>
        </div>
        {relatedPositions && relatedPositions.length > 0 && (
          <div className="text-right">
            <div className="text-xs text-neutral-500">
              {isZh ? '关联交易总盈亏' : 'Total Related P&L'}
            </div>
            <div className={clsx('text-lg font-bold', getPnLColorClass(totalPnL))}>
              {formatCurrency(totalPnL)}
            </div>
          </div>
        )}
      </div>

      {loading ? (
        <div className="h-32 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-neutral-300 border-t-blue-600"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Stock Positions */}
          {stockPositions.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                {isZh ? '正股交易' : 'Stock Trades'}
                <span className="text-neutral-400">({stockPositions.length})</span>
              </h4>
              <div className="space-y-2">
                {stockPositions.map((position) => (
                  <PositionCard key={position.id} position={position} />
                ))}
              </div>
            </div>
          )}

          {/* Option Positions */}
          {optionPositions.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-neutral-500 mb-2 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                {isZh ? '期权交易' : 'Option Trades'}
                <span className="text-neutral-400">({optionPositions.length})</span>
              </h4>
              <div className="space-y-2">
                {optionPositions.map((position) => (
                  <PositionCard key={position.id} position={position} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PositionCard({ position }: { position: RelatedPosition }) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';
  const isProfit = (position.net_pnl || 0) > 0;

  return (
    <Link
      to={`/positions/${position.id}`}
      className="block p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors border border-transparent hover:border-neutral-200 dark:hover:border-neutral-700"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center',
              isProfit
                ? 'bg-green-100 dark:bg-green-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            )}
          >
            {isProfit ? (
              <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-neutral-900 dark:text-white">
                {position.symbol}
              </span>
              <span
                className={clsx(
                  'px-1.5 py-0.5 text-xs font-medium rounded',
                  position.direction === 'long'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                )}
              >
                {t(`direction.${position.direction}`)}
              </span>
              {position.score_grade && (
                <span
                  className={clsx(
                    'px-1.5 py-0.5 text-xs font-medium rounded',
                    getGradeBadgeClass(position.score_grade)
                  )}
                >
                  {position.score_grade}
                </span>
              )}
            </div>
            <div className="text-xs text-neutral-500 mt-0.5">
              {formatDate(position.open_date)} → {formatDate(position.close_date)}
              {position.holding_period_days !== null && (
                <span className="ml-2">
                  ({position.holding_period_days}{isZh ? '天' : 'd'})
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className={clsx('font-semibold', getPnLColorClass(position.net_pnl))}>
              {formatCurrency(position.net_pnl)}
            </div>
            <div className={clsx('text-xs', getPnLColorClass(position.net_pnl_pct))}>
              {formatPercent(position.net_pnl_pct)}
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-neutral-400" />
        </div>
      </div>
    </Link>
  );
}
