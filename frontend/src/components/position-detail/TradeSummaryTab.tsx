import { useTranslation } from 'react-i18next';
import {
  formatCurrency,
  formatPercent,
  formatDateTime,
  getPnLColorClass,
  getGradeBadgeClass,
  formatHoldingDays,
} from '@/utils/format';
import { InfoTooltip } from '@/components/common/InfoTooltip';
import type { PositionDetail } from '@/types';
import clsx from 'clsx';

interface TradeSummaryTabProps {
  position: PositionDetail;
}

interface ScoreGaugeProps {
  label: string;
  score: number | null;
  termKey?: string;
}

function ScoreGauge({ label, score, termKey }: ScoreGaugeProps) {
  const displayScore = score ?? 0;
  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-600';
    if (s >= 60) return 'text-blue-600';
    if (s >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="text-center p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
      <div className={clsx('text-2xl font-bold', getScoreColor(displayScore))}>
        {score !== null ? score.toFixed(0) : '-'}
      </div>
      <div className="text-xs text-neutral-500 flex items-center justify-center gap-1 mt-1">
        {label}
        {termKey && <InfoTooltip termKey={termKey} size="xs" />}
      </div>
    </div>
  );
}

export function TradeSummaryTab({ position }: TradeSummaryTabProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  return (
    <div className="space-y-6">
      {/* Key P&L Metrics */}
      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {t('positionDetail.tradeSummary')}
          </h3>
          <span
            className={clsx(
              'px-3 py-1 text-lg font-bold rounded-lg',
              getGradeBadgeClass(position.score_grade)
            )}
          >
            {position.score_grade || '-'}
          </span>
        </div>

        {/* Hero P&L */}
        <div className="text-center mb-6 pb-6 border-b border-neutral-100 dark:border-neutral-800">
          <div
            className={clsx(
              'text-4xl font-bold mb-1',
              getPnLColorClass(position.net_pnl)
            )}
          >
            {formatCurrency(position.net_pnl)}
          </div>
          <div
            className={clsx(
              'text-lg',
              getPnLColorClass(position.net_pnl_pct)
            )}
          >
            {formatPercent(position.net_pnl_pct)}
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.openPrice')}</div>
            <div className="text-lg font-semibold">{formatCurrency(position.open_price)}</div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.closePrice')}</div>
            <div className="text-lg font-semibold">{formatCurrency(position.close_price)}</div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.quantity')}</div>
            <div className="text-lg font-semibold">{position.quantity}</div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1 flex items-center gap-1">
              {t('positionDetail.holdingPeriod')}
              <InfoTooltip termKey="holdingPeriod" size="xs" />
            </div>
            <div className="text-lg font-semibold">{formatHoldingDays(position.holding_period_days, isZh)}</div>
          </div>
        </div>

        {/* Time & Fees */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-800">
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.openTime')}</div>
            <div className="text-sm">{formatDateTime(position.open_time)}</div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.closeTime')}</div>
            <div className="text-sm">{formatDateTime(position.close_time)}</div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1 flex items-center gap-1">
              {t('positionDetail.grossPnl')}
              <InfoTooltip termKey="pnl" size="xs" />
            </div>
            <div className={clsx('text-sm font-medium', getPnLColorClass(position.realized_pnl))}>
              {formatCurrency(position.realized_pnl)}
            </div>
          </div>
          <div>
            <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.totalFees')}</div>
            <div className="text-sm font-medium text-red-600">
              -{formatCurrency(position.total_fees)}
            </div>
          </div>
        </div>
      </div>

      {/* Score Card - only show if we have any scores */}
      {(position.scores.entry_quality_score !== null ||
        position.scores.exit_quality_score !== null ||
        position.scores.trend_quality_score !== null ||
        position.scores.risk_mgmt_score !== null ||
        position.scores.overall_score !== null) && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-4">
            {t('positionDetail.scores')}
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <ScoreGauge label={t('positionDetail.entryScore')} score={position.scores.entry_quality_score} termKey="entryScore" />
            <ScoreGauge label={t('positionDetail.exitScore')} score={position.scores.exit_quality_score} termKey="exitScore" />
            <ScoreGauge label={t('positionDetail.trendScore')} score={position.scores.trend_quality_score} termKey="trendScore" />
            <ScoreGauge label={t('positionDetail.riskMgmtScore')} score={position.scores.risk_mgmt_score} termKey="riskMgmtScore" />
          </div>

          <div className="mt-4 pt-4 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-center gap-8">
            <div className="text-center">
              <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.overallScore')}</div>
              <div className="text-3xl font-bold text-blue-600">
                {position.scores.overall_score?.toFixed(0) || '-'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Strategy - only show if we have strategy data */}
      {position.strategy_type && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-4">
            {t('positionDetail.strategyAnalysis')}
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.strategyType')}</div>
              <div className="font-semibold capitalize">
                {position.strategy_type.replace('_', ' ')}
              </div>
            </div>
            <div className="p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-1">{t('positionDetail.confidence')}</div>
              <div className="font-semibold">
                {position.strategy_confidence ? `${(position.strategy_confidence * 100).toFixed(0)}%` : '-'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
