import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { statisticsApi } from '@/api/client';
import { InsightCard } from './InsightCard';
import {
  SparklesIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import type { TradingInsight, InsightType } from '@/types';
import clsx from 'clsx';

interface AICoachPanelProps {
  dateStart?: string;
  dateEnd?: string;
  limit?: number;
}

interface GroupedInsights {
  problem: TradingInsight[];
  strength: TradingInsight[];
  reminder: TradingInsight[];
}

const GROUP_CONFIG: Record<InsightType, {
  icon: typeof ExclamationTriangleIcon;
  label: { en: string; zh: string };
  emptyLabel: { en: string; zh: string };
  accentColor: string;
  bgColor: string;
}> = {
  problem: {
    icon: ExclamationTriangleIcon,
    label: { en: 'Issues to Address', zh: '待解决问题' },
    emptyLabel: { en: 'No issues detected', zh: '未发现问题' },
    accentColor: 'text-red-500',
    bgColor: 'bg-red-50 dark:bg-red-900/10',
  },
  strength: {
    icon: CheckCircleIcon,
    label: { en: 'Strengths', zh: '优势表现' },
    emptyLabel: { en: 'Keep trading to discover strengths', zh: '继续交易以发现优势' },
    accentColor: 'text-green-500',
    bgColor: 'bg-green-50 dark:bg-green-900/10',
  },
  reminder: {
    icon: InformationCircleIcon,
    label: { en: 'Notes', zh: '注意事项' },
    emptyLabel: { en: 'No notes', zh: '暂无提醒' },
    accentColor: 'text-amber-500',
    bgColor: 'bg-amber-50 dark:bg-amber-900/10',
  },
};

function InsightGroup({
  type,
  insights,
  isZh,
}: {
  type: InsightType;
  insights: TradingInsight[];
  isZh: boolean;
}) {
  const config = GROUP_CONFIG[type];
  const Icon = config.icon;

  if (insights.length === 0) {
    return null;
  }

  return (
    <div>
      {/* Group header */}
      <div className="flex items-center gap-2 mb-2">
        <Icon className={clsx('w-4 h-4', config.accentColor)} />
        <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400 uppercase tracking-wide">
          {isZh ? config.label.zh : config.label.en}
        </span>
        <span className={clsx(
          'ml-auto text-xs font-medium px-1.5 py-0.5 rounded',
          config.bgColor,
          config.accentColor
        )}>
          {insights.length}
        </span>
      </div>

      {/* Insight cards */}
      <div className="space-y-1 -mx-2">
        {insights.map((insight) => (
          <InsightCard key={insight.id} insight={insight} />
        ))}
      </div>
    </div>
  );
}

export function AICoachPanel({ dateStart, dateEnd, limit = 20 }: AICoachPanelProps) {
  const { i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  const { data: insights, isLoading, error } = useQuery({
    queryKey: ['insights', dateStart, dateEnd, limit],
    queryFn: () =>
      statisticsApi.getInsights({
        date_start: dateStart,
        date_end: dateEnd,
        limit,
      }),
  });

  // Group insights by type
  const grouped = useMemo<GroupedInsights>(() => {
    const result: GroupedInsights = {
      problem: [],
      strength: [],
      reminder: [],
    };

    if (!insights) return result;

    for (const insight of insights) {
      if (result[insight.type]) {
        result[insight.type].push(insight);
      }
    }

    return result;
  }, [insights]);

  // Count totals
  const totalCount = insights?.length || 0;
  const problemCount = grouped.problem.length;
  const strengthCount = grouped.strength.length;
  const reminderCount = grouped.reminder.length;

  // Use 2-column layout when we have both problems and strengths
  const use2ColumnLayout = problemCount > 0 && strengthCount > 0;

  return (
    <div className="bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-lg">
            <SparklesIcon className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
              {isZh ? 'AI 教练' : 'AI Coach'}
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">
              {isZh ? '基于您的交易数据智能分析' : 'Smart analysis based on your trading data'}
            </p>
          </div>
        </div>

        {/* Summary badges */}
        {!isLoading && !error && totalCount > 0 && (
          <div className="flex items-center gap-2">
            {problemCount > 0 && (
              <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                {problemCount}
              </span>
            )}
            {strengthCount > 0 && (
              <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                {strengthCount}
              </span>
            )}
            {reminderCount > 0 && (
              <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                {reminderCount}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="px-6 py-5">
        {isLoading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2].map((col) => (
              <div key={col} className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 animate-pulse">
                    <div className="w-2 h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full" />
                    <div className="flex-1">
                      <div className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded w-3/4" />
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-red-600 dark:text-red-400">
            <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm">{isZh ? '加载失败' : 'Failed to load'}</span>
          </div>
        ) : totalCount > 0 ? (
          use2ColumnLayout ? (
            // 2-column layout: Problems left, Strengths right
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left column: Problems */}
              <div className="space-y-5">
                <InsightGroup type="problem" insights={grouped.problem} isZh={isZh} />
                {reminderCount > 0 && (
                  <InsightGroup type="reminder" insights={grouped.reminder} isZh={isZh} />
                )}
              </div>

              {/* Right column: Strengths */}
              <div>
                <InsightGroup type="strength" insights={grouped.strength} isZh={isZh} />
              </div>
            </div>
          ) : (
            // Single column layout when only one type has content
            <div className="space-y-5">
              <InsightGroup type="problem" insights={grouped.problem} isZh={isZh} />
              <InsightGroup type="reminder" insights={grouped.reminder} isZh={isZh} />
              <InsightGroup type="strength" insights={grouped.strength} isZh={isZh} />
            </div>
          )
        ) : (
          <div className="text-center py-8">
            <SparklesIcon className="w-10 h-10 mx-auto mb-2 text-neutral-300 dark:text-neutral-600" />
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              {isZh ? '暂无洞察' : 'No insights yet'}
            </p>
            <p className="text-xs text-neutral-400 dark:text-neutral-500 mt-1">
              {isZh ? '继续交易，AI 教练会帮您发现模式' : 'Keep trading, AI Coach will help you find patterns'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
