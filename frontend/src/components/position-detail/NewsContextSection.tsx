/**
 * NewsContextSection - News context display component
 *
 * input: NewsContext data from position API
 * output: Visual display of news impact on trading
 * pos: Component in position detail page - shows news context with sentiment, scores, categories
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import clsx from 'clsx';
import { ChevronDown, ChevronUp, Newspaper, TrendingUp, TrendingDown, Minus, Shuffle } from 'lucide-react';
import { InfoTooltip } from '@/components/common/InfoTooltip';
import type { NewsContext } from '@/types';

interface NewsContextSectionProps {
  newsContext?: NewsContext | null;
  direction?: string;
  symbol?: string;
}

// Sentiment configuration
const SENTIMENT_CONFIG = {
  bullish: { icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-100 dark:bg-green-900/30', label: 'bullish' },
  bearish: { icon: TrendingDown, color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/30', label: 'bearish' },
  neutral: { icon: Minus, color: 'text-neutral-500', bg: 'bg-neutral-100 dark:bg-neutral-800', label: 'neutral' },
  mixed: { icon: Shuffle, color: 'text-yellow-600', bg: 'bg-yellow-100 dark:bg-yellow-900/30', label: 'mixed' },
};

// Category badge colors
const CATEGORY_COLORS: Record<string, string> = {
  earnings: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  product: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  analyst: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  sector: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
  macro: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  geopolitical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
};

// Score gauge component for news dimensions
function NewsScoreGauge({
  label,
  score,
  weight,
  description,
}: {
  label: string;
  score: number | undefined;
  weight: string;
  description: string;
}) {
  const displayScore = score ?? 0;
  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-600';
    if (s >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getProgressColor = (s: number) => {
    if (s >= 80) return 'bg-green-500';
    if (s >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-neutral-500">{label}</span>
        <span className="text-xs text-neutral-400">({weight})</span>
      </div>
      <div className={clsx('text-2xl font-bold mb-1', getScoreColor(displayScore))}>
        {score !== undefined && score !== null ? score.toFixed(0) : '-'}
      </div>
      {/* Progress bar */}
      <div className="h-1.5 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
        <div
          className={clsx('h-full rounded-full transition-all', getProgressColor(displayScore))}
          style={{ width: `${displayScore}%` }}
        />
      </div>
      <div className="text-[10px] text-neutral-400 mt-1.5 leading-tight">{description}</div>
    </div>
  );
}

// Sentiment indicator component
function SentimentIndicator({
  sentiment,
  score,
  impactLevel,
}: {
  sentiment: 'bullish' | 'bearish' | 'neutral' | 'mixed' | null;
  score: number | null;
  impactLevel: string;
}) {
  const { t } = useTranslation();
  const config = sentiment ? SENTIMENT_CONFIG[sentiment] : SENTIMENT_CONFIG.neutral;
  const Icon = config.icon;

  // Convert -100 to +100 score to percentage for the bar (0-100)
  const barWidth = score !== null ? Math.abs(score) : 0;
  const isPositive = score !== null && score >= 0;

  return (
    <div className={clsx('p-4 rounded-lg', config.bg)}>
      <div className="flex items-center gap-3 mb-3">
        <Icon className={clsx('w-6 h-6', config.color)} />
        <div>
          <div className={clsx('font-semibold', config.color)}>
            {sentiment ? t(`newsContext.sentiment.${sentiment}`) : t('newsContext.sentiment.neutral')}
          </div>
          <div className="text-xs text-neutral-500">
            {t(`newsContext.impact.${impactLevel}`)}
          </div>
        </div>
      </div>

      {/* Sentiment score bar */}
      {score !== null && (
        <div className="relative">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all',
                  isPositive ? 'bg-green-500' : 'bg-red-500'
                )}
                style={{ width: `${barWidth}%` }}
              />
            </div>
            <span className={clsx('text-sm font-medium', config.color)}>
              {score > 0 ? '+' : ''}{score}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// Category badges component
function CategoryBadges({
  hasEarnings,
  hasProduct,
  hasAnalyst,
  hasSector,
  hasMacro,
  hasGeopolitical,
}: {
  hasEarnings: boolean;
  hasProduct: boolean;
  hasAnalyst: boolean;
  hasSector: boolean;
  hasMacro: boolean;
  hasGeopolitical: boolean;
}) {
  const { t } = useTranslation();

  const categories = [
    { key: 'earnings', active: hasEarnings },
    { key: 'product', active: hasProduct },
    { key: 'analyst', active: hasAnalyst },
    { key: 'sector', active: hasSector },
    { key: 'macro', active: hasMacro },
    { key: 'geopolitical', active: hasGeopolitical },
  ].filter((c) => c.active);

  if (categories.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {categories.map((cat) => (
        <span
          key={cat.key}
          className={clsx(
            'px-2.5 py-1 text-xs font-medium rounded-full',
            CATEGORY_COLORS[cat.key]
          )}
        >
          {t(`newsContext.categories.${cat.key}`)}
        </span>
      ))}
    </div>
  );
}

// News list component
function NewsList({
  items,
  expanded,
  onToggle,
}: {
  items: NewsContext['news_items'];
  expanded: boolean;
  onToggle: () => void;
}) {
  const { t } = useTranslation();

  if (!items || items.length === 0) return null;

  const displayItems = expanded ? items : items.slice(0, 3);
  const hasMore = items.length > 3;

  const getSentimentIcon = (sentiment: string) => {
    if (sentiment === 'bullish') return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (sentiment === 'bearish') return <TrendingDown className="w-3 h-3 text-red-500" />;
    return <Minus className="w-3 h-3 text-neutral-400" />;
  };

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">
          {t('newsContext.newsList')}
        </h4>
        <span className="text-xs text-neutral-400">
          {items.length} {t('newsContext.newsCount')}
        </span>
      </div>

      <div className="space-y-2">
        {displayItems.map((item, index) => (
          <div
            key={index}
            className="p-3 rounded-lg bg-neutral-50 dark:bg-neutral-800/50 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            <div className="flex items-start gap-2">
              {getSentimentIcon(item.sentiment)}
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 line-clamp-2">
                  {item.title}
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-neutral-500">
                  <span>{item.source}</span>
                  <span>·</span>
                  <span>{item.date}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {hasMore && (
        <button
          onClick={onToggle}
          className="mt-3 flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              {t('newsContext.collapse')}
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              {t('newsContext.showAll')} ({items.length - 3} more)
            </>
          )}
        </button>
      )}
    </div>
  );
}

export function NewsContextSection({ newsContext }: NewsContextSectionProps) {
  const { t } = useTranslation();
  const [newsExpanded, setNewsExpanded] = useState(false);

  // No news data case
  if (!newsContext || newsContext.news_count === 0) {
    return (
      <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-neutral-400" />
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
            {t('newsContext.title')}
          </h3>
        </div>
        <div className="text-center py-8 text-neutral-500">
          <Newspaper className="w-12 h-12 mx-auto mb-3 text-neutral-300 dark:text-neutral-600" />
          <p>{t('newsContext.noNews')}</p>
        </div>
      </div>
    );
  }

  const breakdown = newsContext.score_breakdown;

  return (
    <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Newspaper className="w-5 h-5 text-neutral-400" />
          <div>
            <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider">
              {t('newsContext.title')}
            </h3>
            <p className="text-xs text-neutral-400">{t('newsContext.subtitle')}</p>
          </div>
        </div>
        {newsContext.news_alignment_score !== null && (
          <div className="text-right">
            <div className="text-xs text-neutral-500 flex items-center gap-1">
              {t('newsContext.alignmentScore')}
              <InfoTooltip termKey="newsAlignmentScore" size="xs" />
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {newsContext.news_alignment_score.toFixed(0)}
            </div>
          </div>
        )}
      </div>

      {/* Sentiment & Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <SentimentIndicator
          sentiment={newsContext.overall_sentiment}
          score={newsContext.sentiment_score}
          impactLevel={newsContext.news_impact_level}
        />
        <div className="flex flex-col justify-center">
          <div className="text-xs text-neutral-500 mb-2">
            {t('newsContext.searchRange')}: ±3 days
          </div>
          <CategoryBadges
            hasEarnings={newsContext.has_earnings}
            hasProduct={newsContext.has_product_news}
            hasAnalyst={newsContext.has_analyst_rating}
            hasSector={newsContext.has_sector_news}
            hasMacro={newsContext.has_macro_news}
            hasGeopolitical={newsContext.has_geopolitical}
          />
        </div>
      </div>

      {/* Score Breakdown - 2x2 grid */}
      {breakdown && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          <NewsScoreGauge
            label={t('newsContext.scores.direction')}
            score={breakdown.direction}
            weight={t('newsContext.scores.directionWeight')}
            description={t('newsContext.scores.directionDesc')}
          />
          <NewsScoreGauge
            label={t('newsContext.scores.timing')}
            score={breakdown.timing}
            weight={t('newsContext.scores.timingWeight')}
            description={t('newsContext.scores.timingDesc')}
          />
          <NewsScoreGauge
            label={t('newsContext.scores.completeness')}
            score={breakdown.completeness}
            weight={t('newsContext.scores.completenessWeight')}
            description={t('newsContext.scores.completenessDesc')}
          />
          <NewsScoreGauge
            label={t('newsContext.scores.risk')}
            score={breakdown.risk}
            weight={t('newsContext.scores.riskWeight')}
            description={t('newsContext.scores.riskDesc')}
          />
        </div>
      )}

      {/* News List */}
      <NewsList
        items={newsContext.news_items}
        expanded={newsExpanded}
        onToggle={() => setNewsExpanded(!newsExpanded)}
      />
    </div>
  );
}
