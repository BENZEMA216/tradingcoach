import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
  SparklesIcon,
  ChartBarIcon,
  LightBulbIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { aiCoachApi } from '@/api/client';
import { AIChat, InsightCard } from '@/components/insights';
import { formatCurrency, formatPercent } from '@/utils/format';
import type { TradingInsight, InsightType, InsightCategory } from '@/types';

// Tab options
type TabType = 'insights' | 'chat';

// Category filter options
const CATEGORY_FILTERS: { value: InsightCategory | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'symbol', label: 'Symbol' },
  { value: 'risk', label: 'Risk' },
  { value: 'holding', label: 'Holding' },
  { value: 'behavior', label: 'Behavior' },
  { value: 'time', label: 'Time' },
  { value: 'fees', label: 'Fees' },
  { value: 'options', label: 'Options' },
];

// Type filter options
const TYPE_FILTERS: { value: InsightType | 'all'; label: string; icon: React.ReactNode }[] = [
  { value: 'all', label: 'All', icon: null },
  { value: 'problem', label: 'Problems', icon: <ExclamationTriangleIcon className="w-4 h-4 text-red-500" /> },
  { value: 'strength', label: 'Strengths', icon: <CheckCircleIcon className="w-4 h-4 text-green-500" /> },
  { value: 'reminder', label: 'Reminders', icon: <InformationCircleIcon className="w-4 h-4 text-yellow-500" /> },
];

export function AICoach() {
  const { t, i18n } = useTranslation();
  const isZh = i18n.language === 'zh';

  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('insights');

  // Filter states
  const [categoryFilter, setCategoryFilter] = useState<InsightCategory | 'all'>('all');
  const [typeFilter, setTypeFilter] = useState<InsightType | 'all'>('all');

  // Fetch proactive insights with AI summary
  const {
    data: proactiveData,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['ai-coach-proactive-insights'],
    queryFn: () => aiCoachApi.getProactiveInsights({ limit: 20 }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch service status
  const { data: status } = useQuery({
    queryKey: ['ai-coach-status'],
    queryFn: () => aiCoachApi.getStatus(),
  });

  // Filter insights
  const filteredInsights = (proactiveData?.insights || []).filter((insight: TradingInsight) => {
    if (categoryFilter !== 'all' && insight.category !== categoryFilter) return false;
    if (typeFilter !== 'all' && insight.type !== typeFilter) return false;
    return true;
  });

  // Count by type
  const typeCounts = {
    problem: proactiveData?.insights?.filter((i: TradingInsight) => i.type === 'problem').length || 0,
    strength: proactiveData?.insights?.filter((i: TradingInsight) => i.type === 'strength').length || 0,
    reminder: proactiveData?.insights?.filter((i: TradingInsight) => i.type === 'reminder').length || 0,
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <SparklesIcon className="w-8 h-8 text-purple-600" />
            {isZh ? 'AI 交易教练' : 'AI Trading Coach'}
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {isZh
              ? '智能分析你的交易表现，提供个性化改进建议'
              : 'Smart analysis of your trading performance with personalized suggestions'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Service Status Badge */}
          <div
            className={`px-3 py-1.5 rounded-full text-xs font-medium flex items-center gap-1.5 ${
              status?.available
                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                status?.available ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            />
            {status?.available
              ? `${status.provider} - ${status.model}`
              : isZh
              ? 'AI 服务不可用'
              : 'AI Unavailable'}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex gap-6">
          <button
            onClick={() => setActiveTab('insights')}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'insights'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <LightBulbIcon className="w-5 h-5" />
            {isZh ? '洞察分析' : 'Insights'}
            {proactiveData?.insights && (
              <span className="ml-1 px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 rounded-full">
                {proactiveData.insights.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'chat'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <ChatBubbleLeftRightIcon className="w-5 h-5" />
            {isZh ? '问答对话' : 'Chat'}
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'insights' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content - Insights */}
          <div className="lg:col-span-2 space-y-6">
            {/* AI Summary Card */}
            {proactiveData?.ai_summary && (
              <div className="bg-gradient-to-br from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-purple-100 dark:border-purple-800">
                <div className="flex items-start gap-3 mb-4">
                  <div className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
                    <SparklesIcon className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {isZh ? 'AI 复盘总结' : 'AI Summary'}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {proactiveData.date_range?.display || 'All time'}
                    </p>
                  </div>
                  <button
                    onClick={() => refetch()}
                    disabled={isFetching}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-white/50 dark:hover:bg-gray-700/50 transition-colors"
                    title={isZh ? '刷新' : 'Refresh'}
                  >
                    <ArrowPathIcon className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
                  </button>
                </div>
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {proactiveData.ai_summary}
                  </p>
                </div>
              </div>
            )}

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-4">
              {/* Type Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {isZh ? '类型' : 'Type'}:
                </span>
                <div className="flex gap-1">
                  {TYPE_FILTERS.map((filter) => (
                    <button
                      key={filter.value}
                      onClick={() => setTypeFilter(filter.value)}
                      className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors flex items-center gap-1 ${
                        typeFilter === filter.value
                          ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {filter.icon}
                      {isZh ? t(`insights.${filter.value}`, filter.label) : filter.label}
                      {filter.value !== 'all' && (
                        <span className="ml-1 text-gray-400">
                          ({typeCounts[filter.value as keyof typeof typeCounts]})
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Category Filter */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {isZh ? '维度' : 'Category'}:
                </span>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value as InsightCategory | 'all')}
                  className="px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 border-0 rounded-lg text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-purple-500"
                >
                  {CATEGORY_FILTERS.map((filter) => (
                    <option key={filter.value} value={filter.value}>
                      {isZh ? t(`insights.category.${filter.value}`, filter.label) : filter.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Insights List */}
            <div className="space-y-3">
              {isLoading ? (
                // Loading skeleton
                Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className="animate-pulse border-l-4 border-gray-300 dark:border-gray-600 rounded-r-lg p-4 bg-gray-50 dark:bg-gray-700/50"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded-full" />
                      <div className="flex-1">
                        <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2" />
                        <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded w-full" />
                      </div>
                    </div>
                  </div>
                ))
              ) : error ? (
                <div className="text-center py-8 text-red-500">
                  {isZh ? '加载失败，请重试' : 'Failed to load. Please try again.'}
                </div>
              ) : filteredInsights.length > 0 ? (
                filteredInsights.map((insight: TradingInsight) => (
                  <InsightCard key={insight.id} insight={insight} />
                ))
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <LightBulbIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>{isZh ? '没有符合筛选条件的洞察' : 'No insights match your filters'}</p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar - Key Metrics */}
          <div className="space-y-6">
            {/* Key Metrics Card */}
            {proactiveData?.key_metrics && Object.keys(proactiveData.key_metrics).length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-2 mb-4">
                  <ChartBarIcon className="w-5 h-5 text-gray-400" />
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {isZh ? '关键指标' : 'Key Metrics'}
                  </h3>
                </div>
                <div className="space-y-4">
                  <MetricItem
                    label={isZh ? '总交易数' : 'Total Trades'}
                    value={String(proactiveData.key_metrics.total_trades || 0)}
                  />
                  <MetricItem
                    label={isZh ? '胜率' : 'Win Rate'}
                    value={formatPercent(proactiveData.key_metrics.win_rate, 1)}
                    highlight={
                      proactiveData.key_metrics.win_rate !== undefined &&
                      proactiveData.key_metrics.win_rate >= 50
                    }
                  />
                  <MetricItem
                    label={isZh ? '总盈亏' : 'Total P&L'}
                    value={formatCurrency(proactiveData.key_metrics.total_pnl)}
                    highlight={
                      proactiveData.key_metrics.total_pnl !== undefined &&
                      proactiveData.key_metrics.total_pnl > 0
                    }
                  />
                  <div className="border-t border-gray-100 dark:border-gray-700 pt-4">
                    <MetricItem
                      label={isZh ? '平均盈利' : 'Avg Win'}
                      value={formatCurrency(proactiveData.key_metrics.avg_win)}
                      small
                    />
                    <MetricItem
                      label={isZh ? '平均亏损' : 'Avg Loss'}
                      value={formatCurrency(proactiveData.key_metrics.avg_loss)}
                      small
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Insight Type Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                {isZh ? '洞察概览' : 'Insights Overview'}
              </h3>
              <div className="space-y-3">
                <TypeSummaryItem
                  icon={<ExclamationTriangleIcon className="w-5 h-5" />}
                  label={isZh ? '待改进' : 'Problems'}
                  count={typeCounts.problem}
                  color="red"
                />
                <TypeSummaryItem
                  icon={<CheckCircleIcon className="w-5 h-5" />}
                  label={isZh ? '优势' : 'Strengths'}
                  count={typeCounts.strength}
                  color="green"
                />
                <TypeSummaryItem
                  icon={<InformationCircleIcon className="w-5 h-5" />}
                  label={isZh ? '提醒' : 'Reminders'}
                  count={typeCounts.reminder}
                  color="yellow"
                />
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Chat Tab */
        <div className="max-w-3xl mx-auto">
          <AIChat className="h-[calc(100vh-280px)]" />
        </div>
      )}
    </div>
  );
}

// Helper Components
function MetricItem({
  label,
  value,
  highlight,
  small,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  small?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between ${small ? 'py-1' : 'py-0'}`}>
      <span className={`text-gray-500 dark:text-gray-400 ${small ? 'text-xs' : 'text-sm'}`}>
        {label}
      </span>
      <span
        className={`font-semibold ${small ? 'text-sm' : 'text-base'} ${
          highlight
            ? 'text-green-600 dark:text-green-400'
            : 'text-gray-900 dark:text-white'
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function TypeSummaryItem({
  icon,
  label,
  count,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
  color: 'red' | 'green' | 'yellow';
}) {
  const colorClasses = {
    red: 'text-red-500 bg-red-50 dark:bg-red-900/20',
    green: 'text-green-500 bg-green-50 dark:bg-green-900/20',
    yellow: 'text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20',
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className={`p-1.5 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      </div>
      <span className="font-semibold text-gray-900 dark:text-white">{count}</span>
    </div>
  );
}
