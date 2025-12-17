import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { positionsApi } from '@/api/client';
import {
  formatCurrency,
  formatPercent,
  getPnLColorClass,
} from '@/utils/format';
import clsx from 'clsx';
import { ChevronLeft } from 'lucide-react';

// Import all sections directly (no lazy loading for single page)
import { TradeSummaryTab } from '@/components/position-detail/TradeSummaryTab';
import { RiskAnalysisTab } from '@/components/position-detail/RiskAnalysisTab';
import { ExecutionTab } from '@/components/position-detail/ExecutionTab';
import { InsightsTab } from '@/components/position-detail/InsightsTab';
import { RelatedPositionsTab } from '@/components/position-detail/RelatedPositionsTab';

export function PositionDetail() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const positionId = parseInt(id || '0', 10);

  // Fetch position detail
  const { data: position, isLoading: loadingPosition } = useQuery({
    queryKey: ['position', positionId],
    queryFn: () => positionsApi.getDetail(positionId),
    enabled: positionId > 0,
  });

  // Fetch trades
  const { data: trades, isLoading: loadingTrades } = useQuery({
    queryKey: ['position-trades', positionId],
    queryFn: () => positionsApi.getTrades(positionId),
    enabled: positionId > 0,
  });

  // Fetch insights
  const { data: insights, isLoading: loadingInsights } = useQuery({
    queryKey: ['position-insights', positionId],
    queryFn: () => positionsApi.getInsights(positionId),
    enabled: positionId > 0,
  });

  // Fetch market data for chart
  const { data: marketData, isLoading: loadingMarketData } = useQuery({
    queryKey: ['position-market-data', positionId],
    queryFn: () => positionsApi.getMarketData(positionId),
    enabled: positionId > 0,
  });

  // Fetch related positions (option-stock bundling)
  const { data: relatedPositions, isLoading: loadingRelated } = useQuery({
    queryKey: ['position-related', positionId],
    queryFn: () => positionsApi.getRelated(positionId),
    enabled: positionId > 0,
  });

  if (loadingPosition) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-neutral-300 border-t-blue-600"></div>
      </div>
    );
  }

  if (!position) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-neutral-900 dark:text-white">
          {t('positionDetail.positionNotFound')}
        </h2>
        <button
          onClick={() => navigate('/positions')}
          className="mt-4 text-blue-600 hover:underline"
        >
          {t('positionDetail.backToPositions')}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/positions')}
            className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-lg transition-colors"
            aria-label="Back"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
                {position.symbol}
              </h1>
              <span
                className={clsx(
                  'px-2 py-1 text-sm font-medium rounded',
                  position.direction === 'long'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                    : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                )}
              >
                {t(`direction.${position.direction}`)}
              </span>
              {position.is_option && (
                <span className="px-2 py-1 text-sm font-medium rounded bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                  {t('positionDetail.option')}
                </span>
              )}
            </div>
            <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
              {position.symbol_name || position.symbol}
              {position.underlying_symbol && ` (${t('positionDetail.underlying')}: ${position.underlying_symbol})`}
            </p>
          </div>
          <div className="text-right">
            <div
              className={clsx(
                'text-2xl font-bold',
                getPnLColorClass(position.net_pnl)
              )}
            >
              {formatCurrency(position.net_pnl)}
            </div>
            <div
              className={clsx(
                'text-sm',
                getPnLColorClass(position.net_pnl_pct)
              )}
            >
              {formatPercent(position.net_pnl_pct)}
            </div>
          </div>
        </div>
      </div>

      {/* All Sections in Single Page Layout */}
      <div className="space-y-8">
        {/* Section 1: Trade Summary */}
        <section>
          <TradeSummaryTab position={position} />
        </section>

        {/* Section 2: Risk Analysis & Price Chart */}
        <section>
          <RiskAnalysisTab
            position={position}
            marketData={marketData}
            loadingMarketData={loadingMarketData}
          />
        </section>

        {/* Section 3: Trade Executions */}
        <section>
          <ExecutionTab trades={trades} loading={loadingTrades} />
        </section>

        {/* Section 4: AI Insights */}
        <section>
          <InsightsTab
            position={position}
            insights={insights}
            loading={loadingInsights}
          />
        </section>

        {/* Section 5: Related Positions (Option-Stock Bundling) */}
        <section>
          <RelatedPositionsTab
            relatedPositions={relatedPositions}
            loading={loadingRelated}
            currentSymbol={position.symbol}
            isOption={position.is_option}
            underlyingSymbol={position.underlying_symbol}
          />
        </section>
      </div>
    </div>
  );
}
