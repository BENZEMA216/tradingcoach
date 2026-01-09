import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { positionsApi, eventsApi } from '@/api/client';
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
import { NewsContextSection } from '@/components/position-detail/NewsContextSection';
import { InsightsTab } from '@/components/position-detail/InsightsTab';
import { RelatedPositionsTab } from '@/components/position-detail/RelatedPositionsTab';
import { EventTimelineChart } from '@/components/charts';

export function PositionDetail() {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const positionId = parseInt(id || '0', 10);
  const isZh = i18n.language === 'zh' || i18n.language.startsWith('zh-');

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

  // Fetch events for this position
  const { data: positionEvents, isLoading: loadingEvents } = useQuery({
    queryKey: ['position-events', positionId],
    queryFn: () => eventsApi.getForPosition(positionId),
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
            className="p-2 hover:bg-neutral-200 dark:hover:bg-white/10 rounded-sm transition-colors text-neutral-500 dark:text-white/50 hover:text-neutral-900 dark:hover:text-white border border-transparent hover:border-neutral-300 dark:hover:border-white/10"
            aria-label={t('common.back')}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-mono font-bold text-neutral-900 dark:text-white tracking-tight uppercase">
                {position.symbol}
              </h1>
              <span
                className={clsx(
                  'px-2 py-0.5 text-[10px] font-bold rounded-sm uppercase tracking-wider border',
                  position.direction === 'long'
                    ? 'bg-blue-900/30 text-blue-400 border-blue-500/20'
                    : 'bg-purple-900/30 text-purple-400 border-purple-500/20'
                )}
              >
                {position.direction === 'long' ? t('direction.long') : t('direction.short')}
              </span>
              {position.is_option && (
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-sm uppercase tracking-wider bg-white/10 text-white/70 border border-white/20">
                  {isZh ? '期权' : 'OPTION'}
                </span>
              )}
            </div>
            <p className="text-xs font-mono text-neutral-500 dark:text-white/50 mt-1 uppercase tracking-wider">
              {position.symbol_name || position.symbol}
              {position.underlying_symbol && ` // UNDERLYING: ${position.underlying_symbol}`}
            </p>
          </div>
          <div className="text-right">
            <div
              className={clsx(
                'text-3xl font-mono font-bold tracking-tight',
                (position.net_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
              )}
            >
              {formatCurrency(position.net_pnl)}
            </div>
            <div
              className={clsx(
                'text-sm font-mono font-bold tracking-tight',
                (position.net_pnl_pct || 0) >= 0 ? 'text-green-500' : 'text-red-500'
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

        {/* Section 4: News Context */}
        <section>
          <NewsContextSection
            newsContext={position.news_context}
            direction={position.direction}
            symbol={position.symbol}
          />
        </section>

        {/* Section 5: Events During Position */}
        {positionEvents && positionEvents.events && positionEvents.events.length > 0 && (
          <section>
            <div className="bg-white dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-800 p-6">
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white mb-4">
                {t('events.title', '事件复盘')}
              </h2>
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4">
                {t('events.subtitle', '持仓期间的重大市场事件')}
              </p>
              <EventTimelineChart
                events={positionEvents.events}
                isLoading={loadingEvents}
                showPnL={true}
              />
            </div>
          </section>
        )}

        {/* Section 6 (or 5 if no events): AI Insights */}
        <section>
          <InsightsTab
            position={position}
            insights={insights}
            loading={loadingInsights}
          />
        </section>

        {/* Section 6: Related Positions (Option-Stock Bundling) */}
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
