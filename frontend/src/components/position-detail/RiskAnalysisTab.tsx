import { useTranslation } from 'react-i18next';
import {
  formatCurrency,
  formatPercent,
  getPnLColorClass,
} from '@/utils/format';
import { InfoTooltip } from '@/components/common/InfoTooltip';
import { PriceChart } from '@/components/charts/PriceChart';
import type { PositionDetail, PositionMarketData } from '@/types';
import clsx from 'clsx';

interface RiskAnalysisTabProps {
  position: PositionDetail;
  marketData?: PositionMarketData;
  loadingMarketData?: boolean;
}

export function RiskAnalysisTab({ position, marketData, loadingMarketData }: RiskAnalysisTabProps) {
  const { t } = useTranslation();

  // Check if we have any risk metrics data
  const hasRiskMetrics =
    position.risk_metrics.mae !== null ||
    position.risk_metrics.mfe !== null ||
    position.risk_metrics.risk_reward_ratio !== null;

  // Check if we have any data to show at all
  const hasAnyData = hasRiskMetrics || marketData || loadingMarketData;

  // If no data at all, don't render the section
  if (!hasAnyData) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Risk Metrics - only show if we have data */}
      {hasRiskMetrics && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-6">
            {t('positionDetail.riskMetrics')}
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* MAE */}
            <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30">
              <div className="flex items-center gap-2 mb-2">
                <div className="text-sm font-medium text-red-600 dark:text-red-400">
                  {t('positionDetail.mae')}
                </div>
                <InfoTooltip termKey="mae" size="xs" />
              </div>
              <div className={clsx('text-2xl font-bold', getPnLColorClass(position.risk_metrics.mae))}>
                {formatCurrency(position.risk_metrics.mae)}
              </div>
              <div className="text-sm text-neutral-500 mt-1">
                {formatPercent(position.risk_metrics.mae_pct)}
              </div>
              <p className="text-xs text-neutral-400 mt-2">
                {t('positionDetail.maeDescription')}
              </p>
            </div>

            {/* MFE */}
            <div className="p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-900/30">
              <div className="flex items-center gap-2 mb-2">
                <div className="text-sm font-medium text-green-600 dark:text-green-400">
                  {t('positionDetail.mfe')}
                </div>
                <InfoTooltip termKey="mfe" size="xs" />
              </div>
              <div className={clsx('text-2xl font-bold', getPnLColorClass(position.risk_metrics.mfe))}>
                {formatCurrency(position.risk_metrics.mfe)}
              </div>
              <div className="text-sm text-neutral-500 mt-1">
                {formatPercent(position.risk_metrics.mfe_pct)}
              </div>
              <p className="text-xs text-neutral-400 mt-2">
                {t('positionDetail.mfeDescription')}
              </p>
            </div>

            {/* Risk/Reward */}
            <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-900/30">
              <div className="flex items-center gap-2 mb-2">
                <div className="text-sm font-medium text-blue-600 dark:text-blue-400">
                  {t('positionDetail.riskRewardRatio')}
                </div>
                <InfoTooltip termKey="payoffRatio" size="xs" />
              </div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {position.risk_metrics.risk_reward_ratio?.toFixed(2) || '-'}
              </div>
              <div className="text-sm text-neutral-500 mt-1">
                {position.risk_metrics.risk_reward_ratio && position.risk_metrics.risk_reward_ratio >= 1
                  ? t('positionDetail.favorableRisk')
                  : t('positionDetail.unfavorableRisk')}
              </div>
            </div>
          </div>

          {/* Trade Efficiency */}
          {position.risk_metrics.mfe && position.net_pnl != null && position.net_pnl !== 0 && (
            <div className="mt-6 pt-6 border-t border-neutral-100 dark:border-neutral-800">
              <h4 className="text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-4">
                {t('positionDetail.tradeEfficiency')}
              </h4>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="flex justify-between text-xs text-neutral-500 mb-1">
                    <span>{t('positionDetail.capturedProfitRatio')}</span>
                    <span>
                      {position.risk_metrics.mfe > 0
                        ? `${((position.net_pnl / position.risk_metrics.mfe) * 100).toFixed(1)}%`
                        : '-'}
                    </span>
                  </div>
                  <div className="h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        position.net_pnl > 0 ? 'bg-green-500' : 'bg-red-500'
                      )}
                      style={{
                        width: `${Math.min(100, Math.max(0, (position.net_pnl / position.risk_metrics.mfe) * 100))}%`
                      }}
                    />
                  </div>
                </div>
              </div>
              <p className="text-xs text-neutral-400 mt-2">
                {t('positionDetail.efficiencyExplanation')}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Price Chart - only show when loading or when we have data */}
      {(loadingMarketData || marketData) && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800">
          <div className="px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
            <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {t('chart.priceChart')}
            </h3>
          </div>
          <div className="p-4">
            {loadingMarketData ? (
              <div className="h-96 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-neutral-300 border-t-blue-600"></div>
              </div>
            ) : (
              <PriceChart data={marketData!} height={400} showIndicators={true} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
