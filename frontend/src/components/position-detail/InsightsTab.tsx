import { useTranslation } from 'react-i18next';
import {
  formatPercent,
  getPnLColorClass,
} from '@/utils/format';
import type { PositionDetail, PositionInsight } from '@/types';
import clsx from 'clsx';
import { TrendingUp, TrendingDown, AlertTriangle, Info, Lightbulb } from 'lucide-react';

interface InsightsTabProps {
  position: PositionDetail;
  insights?: PositionInsight[];
  loading?: boolean;
}

const insightTypeConfig = {
  positive: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    iconBg: 'bg-green-100 dark:bg-green-900/40',
    iconColor: 'text-green-600 dark:text-green-400',
    icon: TrendingUp,
  },
  negative: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 dark:bg-red-900/40',
    iconColor: 'text-red-600 dark:text-red-400',
    icon: TrendingDown,
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    iconBg: 'bg-yellow-100 dark:bg-yellow-900/40',
    iconColor: 'text-yellow-600 dark:text-yellow-400',
    icon: AlertTriangle,
  },
  neutral: {
    bg: 'bg-neutral-50 dark:bg-neutral-800',
    border: 'border-neutral-200 dark:border-neutral-700',
    iconBg: 'bg-neutral-100 dark:bg-neutral-700',
    iconColor: 'text-neutral-600 dark:text-neutral-400',
    icon: Info,
  },
};

function InsightCard({ insight }: { insight: PositionInsight }) {
  const { t } = useTranslation();
  const config = insightTypeConfig[insight.type as keyof typeof insightTypeConfig] || insightTypeConfig.neutral;
  const Icon = config.icon;
  const categoryKey = insight.category as 'entry' | 'exit' | 'risk' | 'behavior' | 'pattern';

  return (
    <div className={clsx('rounded-xl border p-4', config.bg, config.border)}>
      <div className="flex items-start gap-3">
        <div className={clsx('p-2 rounded-lg flex-shrink-0', config.iconBg)}>
          <Icon className={clsx('w-5 h-5', config.iconColor)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300">
              {t(`positionDetail.${categoryKey}`)}
            </span>
          </div>
          <h4 className={clsx('font-semibold mb-1', config.iconColor)}>
            {insight.title}
          </h4>
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            {insight.description}
          </p>
          {insight.suggestion && (
            <div className="mt-3 flex items-start gap-2 p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <Lightbulb className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-600 dark:text-blue-400">
                {insight.suggestion}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function InsightsTab({ position, insights, loading }: InsightsTabProps) {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const hasPostExitData =
    position.post_exit_5d_pct !== null ||
    position.post_exit_10d_pct !== null ||
    position.post_exit_20d_pct !== null;

  const hasInsights = insights && insights.length > 0;

  // If no post-exit data and no insights and not loading, don't render the section
  if (!hasPostExitData && !hasInsights && !loading) {
    return null;
  }

  // Categorize insights
  const positiveInsights = insights?.filter((i) => i.type === 'positive') || [];
  const negativeInsights = insights?.filter((i) => i.type === 'negative') || [];
  const otherInsights = insights?.filter((i) => !['positive', 'negative'].includes(i.type)) || [];

  return (
    <div className="space-y-6">
      {/* Post-Exit Performance */}
      {hasPostExitData && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-4">
            {t('positionDetail.postExitPerformance')}
          </h3>
          <p className="text-sm text-neutral-500 mb-4">
            {isZh
              ? '平仓后标的价格变化，用于评估离场时机'
              : 'Price change after exit, to evaluate exit timing'}
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-2">{t('positionDetail.days5')}</div>
              <div className={clsx('text-2xl font-bold', getPnLColorClass(position.post_exit_5d_pct))}>
                {formatPercent(position.post_exit_5d_pct)}
              </div>
              {position.post_exit_5d_pct !== null && (
                <div className="text-xs text-neutral-400 mt-1">
                  {position.direction === 'long'
                    ? position.post_exit_5d_pct > 0
                      ? (isZh ? '过早离场' : 'Exited too early')
                      : (isZh ? '时机正确' : 'Good timing')
                    : position.post_exit_5d_pct < 0
                      ? (isZh ? '过早离场' : 'Exited too early')
                      : (isZh ? '时机正确' : 'Good timing')}
                </div>
              )}
            </div>
            <div className="text-center p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-2">{t('positionDetail.days10')}</div>
              <div className={clsx('text-2xl font-bold', getPnLColorClass(position.post_exit_10d_pct))}>
                {formatPercent(position.post_exit_10d_pct)}
              </div>
            </div>
            <div className="text-center p-4 rounded-lg bg-neutral-50 dark:bg-neutral-800/50">
              <div className="text-xs text-neutral-500 mb-2">{t('positionDetail.days20')}</div>
              <div className={clsx('text-2xl font-bold', getPnLColorClass(position.post_exit_20d_pct))}>
                {formatPercent(position.post_exit_20d_pct)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Insights - only show when loading or have data */}
      {(loading || hasInsights) && (
        <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800 p-6">
          <h3 className="text-sm font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider mb-4">
            {t('positionDetail.insights')}
          </h3>

          {loading ? (
            <div className="h-48 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-neutral-300 border-t-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Strengths */}
              {positiveInsights.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-green-600 dark:text-green-400 mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    {isZh ? '做得好' : 'What went well'}
                  </h4>
                  <div className="space-y-3">
                    {positiveInsights.map((insight, idx) => (
                      <InsightCard key={idx} insight={insight} />
                    ))}
                  </div>
                </div>
              )}

              {/* Areas for Improvement */}
              {negativeInsights.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                    <TrendingDown className="w-4 h-4" />
                    {isZh ? '需改进' : 'Areas for improvement'}
                  </h4>
                  <div className="space-y-3">
                    {negativeInsights.map((insight, idx) => (
                      <InsightCard key={idx} insight={insight} />
                    ))}
                  </div>
                </div>
              )}

              {/* Other Observations */}
              {otherInsights.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-3 flex items-center gap-2">
                    <Info className="w-4 h-4" />
                    {isZh ? '其他观察' : 'Other observations'}
                  </h4>
                  <div className="space-y-3">
                    {otherInsights.map((insight, idx) => (
                      <InsightCard key={idx} insight={insight} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
