import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { eventsApi } from '@/api/client';
import { EventTimelineChart } from '@/components/charts/EventTimelineChart';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';
import { formatCurrency, formatPercent } from '@/utils/format';
import {
  Calendar,
  TrendingUp,
  TrendingDown,
  Activity,
  Filter,
  Target,
  AlertCircle,
  DollarSign,
  BarChart2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

// Event type filter options
// Note: News-based events (analyst, sector, product) are unreliable for historical data
// Only price_anomaly, volume_anomaly, and earnings have correct historical dates
const EVENT_TYPES = [
  { key: 'all', labelKey: 'events.filterAll' },
  { key: 'price_anomaly', labelKey: 'events.filterPriceAnomaly' },
  { key: 'volume_anomaly', labelKey: 'events.filterVolumeAnomaly' },
  { key: 'earnings', labelKey: 'events.filterEarnings' },
];

export function EventAnalysis() {
  const { t } = useTranslation();
  const [eventTypeFilter, setEventTypeFilter] = useState('price_anomaly');
  const [expandedSection, setExpandedSection] = useState<string | null>('timeline');

  // Fetch all events for complete timeline visualization
  // Performance: 3000 events = ~44ms backend, ~860KB transfer - acceptable
  const { data: eventsData, isLoading: eventsLoading } = useQuery({
    queryKey: ['events', 'list', eventTypeFilter],
    queryFn: () =>
      eventsApi.list(1, 5000, {
        event_type: eventTypeFilter === 'all' ? undefined : eventTypeFilter,
        sort_order: 'asc', // Chronological order for timeline visualization
      }),
  });

  // Fetch event statistics
  const { data: eventStats, isLoading: statsLoading } = useQuery({
    queryKey: ['events', 'statistics'],
    queryFn: () => eventsApi.getStatistics(),
  });

  // Fetch performance by event type
  const { data: performanceByType } = useQuery({
    queryKey: ['events', 'performance-by-type'],
    queryFn: () => eventsApi.getPerformanceByType(),
  });

  const events = eventsData?.items || [];
  const isLoading = eventsLoading || statsLoading;

  // Calculate summary stats
  const totalEvents = eventStats?.total_events || events.length;
  const keyEventsCount = eventStats?.high_impact_count || events.filter(e => e.is_key_event).length;
  const totalPnL = events.reduce((sum, e) => sum + (e.position_pnl_on_event || 0), 0);
  const avgPriceChange = events.length > 0
    ? events.reduce((sum, e) => sum + (e.price_change_pct || 0), 0) / events.length
    : 0;

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
            {t('events.title', '事件分析')}
          </h1>
          <p className="text-neutral-500 dark:text-neutral-400">
            {t('events.subtitle', '分析市场事件对交易收益的影响')}
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-black rounded-sm p-5 border border-neutral-200 dark:border-white/10 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-neutral-500 dark:text-white/40 font-mono uppercase tracking-wider">
              {t('events.totalEvents', '总事件数')}
            </span>
            <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-500" />
          </div>
          <p className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {isLoading ? '-' : totalEvents}
          </p>
        </div>

        <div className="bg-white dark:bg-black rounded-sm p-5 border border-neutral-200 dark:border-white/10 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-neutral-500 dark:text-white/40 font-mono uppercase tracking-wider">
              {t('events.keyEvents', '关键事件')}
            </span>
            <Target className="w-5 h-5 text-amber-500" />
          </div>
          <p className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {isLoading ? '-' : keyEventsCount}
          </p>
        </div>

        <div className="bg-white dark:bg-black rounded-sm p-5 border border-neutral-200 dark:border-white/10 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-neutral-500 dark:text-white/40 font-mono uppercase tracking-wider">
              {t('events.eventPnL', '事件盈亏')}
            </span>
            <DollarSign className={`w-5 h-5 ${totalPnL >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`} />
          </div>
          <p className={`text-2xl font-mono font-bold ${totalPnL >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
            {isLoading ? '-' : formatCurrency(totalPnL)}
          </p>
        </div>

        <div className="bg-white dark:bg-black rounded-sm p-5 border border-neutral-200 dark:border-white/10 transition-colors">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-neutral-500 dark:text-white/40 font-mono uppercase tracking-wider">
              {t('events.avgPriceChange', '平均价格变动')}
            </span>
            {avgPriceChange >= 0 ? (
              <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-500" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-500" />
            )}
          </div>
          <p className={`text-2xl font-mono font-bold ${avgPriceChange >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
            {isLoading ? '-' : formatPercent(avgPriceChange / 100)}
          </p>
        </div>
      </div>

      {/* Event Type Filter */}
      <div className="bg-white dark:bg-black rounded-sm p-4 border border-neutral-200 dark:border-white/10 transition-colors">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 text-neutral-500 dark:text-white/40">
            <Filter className="w-4 h-4" />
            <span className="text-sm font-mono font-medium uppercase">{t('events.filterBy', '筛选')}:</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {EVENT_TYPES.map((type) => (
              <button
                key={type.key}
                onClick={() => setEventTypeFilter(type.key)}
                className={`px-3 py-1.5 text-xs font-mono uppercase rounded-sm transition-colors ${eventTypeFilter === type.key
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-neutral-100 dark:bg-white/5 text-slate-700 dark:text-white/60 hover:bg-neutral-200 dark:hover:bg-white/10'
                  }`}
              >
                {t(type.labelKey, type.key)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Event Timeline Section */}
      <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors">
        <button
          onClick={() => toggleSection('timeline')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-blue-600 dark:text-blue-500" />
            <h2 className="text-lg font-mono font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              {t('events.timeline', '事件时间线')}
            </h2>
            <span className="text-xs font-mono text-slate-500 dark:text-white/40 group-hover:text-slate-900 dark:group-hover:text-white/60">
              ({events.length} {t('events.events', '事件')})
            </span>
          </div>
          {expandedSection === 'timeline' ? (
            <ChevronUp className="w-5 h-5 text-slate-400 dark:text-white/40" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400 dark:text-white/40" />
          )}
        </button>
        {expandedSection === 'timeline' && (
          <div className="px-6 pb-6">
            <EventTimelineChart
              events={events}
              showPnL={true}
              isLoading={eventsLoading}
            />
          </div>
        )}
      </div>

      {/* Event List Section */}
      <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors">
        <button
          onClick={() => toggleSection('list')}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors"
        >
          <div className="flex items-center gap-3">
            <BarChart2 className="w-5 h-5 text-purple-600 dark:text-purple-500" />
            <h2 className="text-lg font-mono font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              {t('events.eventList', '事件列表')}
            </h2>
          </div>
          {expandedSection === 'list' ? (
            <ChevronUp className="w-5 h-5 text-slate-400 dark:text-white/40" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400 dark:text-white/40" />
          )}
        </button>
        {expandedSection === 'list' && (
          <div className="px-6 pb-6">
            {eventsLoading ? (
              <ChartSkeleton height="h-64" />
            ) : events.length === 0 ? (
              <EmptyState
                icon="event"
                height="h-64"
                title={t('events.noEvents', '暂无事件')}
                description={t('events.noEventsDescription', '该时间段内未检测到重大市场事件')}
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs font-mono font-medium text-slate-500 dark:text-white/40 uppercase tracking-wider border-b border-neutral-200 dark:border-white/10">
                      <th className="pb-3 pr-4">{t('events.date', '日期')}</th>
                      <th className="pb-3 pr-4">{t('events.type', '类型')}</th>
                      <th className="pb-3 pr-4">{t('events.event', '事件')}</th>
                      <th className="pb-3 pr-4">{t('events.symbol', '标的')}</th>
                      <th className="pb-3 pr-4 text-right">{t('events.priceChange', '价格变动')}</th>
                      <th className="pb-3 text-right">{t('events.pnl', '盈亏')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 dark:divide-white/5">
                    {events.slice(0, 20).map((event) => (
                      <tr key={event.id} className="text-sm hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors">
                        <td className="py-3 pr-4 text-slate-500 dark:text-white/60 whitespace-nowrap font-mono">
                          {new Date(event.event_date).toLocaleDateString()}
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`px-2 py-1 text-xs font-mono rounded-sm ${event.event_type === 'earnings'
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                            : event.event_type === 'macro' || event.event_type === 'fed'
                              ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                              : event.event_type === 'price_anomaly'
                                ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                                : 'bg-neutral-100 text-neutral-700 dark:bg-white/10 dark:text-white/60'
                            }`}>
                            {event.event_type}
                          </span>
                          {event.is_key_event && (
                            <span className="ml-1 text-amber-500">★</span>
                          )}
                        </td>
                        <td className="py-3 pr-4 text-slate-900 dark:text-white max-w-[200px] truncate font-medium">
                          {event.event_title}
                        </td>
                        <td className="py-3 pr-4 font-mono font-medium text-slate-900 dark:text-white">
                          {event.symbol}
                        </td>
                        <td className={`py-3 pr-4 text-right font-mono font-bold ${(event.price_change_pct || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                          }`}>
                          {event.price_change_pct !== null
                            ? `${event.price_change_pct >= 0 ? '+' : ''}${event.price_change_pct.toFixed(1)}%`
                            : '-'}
                        </td>
                        <td className={`py-3 text-right font-mono font-bold ${(event.position_pnl_on_event || 0) >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                          }`}>
                          {event.position_pnl_on_event !== null
                            ? formatCurrency(event.position_pnl_on_event)
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {events.length > 20 && (
                  <p className="mt-4 text-center text-xs font-mono text-slate-500 dark:text-white/40">
                    {t('events.showingFirst', '显示前 20 条，共')} {events.length} {t('events.records', '条记录')}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Performance by Event Type Section */}
      {performanceByType && performanceByType.length > 0 && (
        <div className="bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors">
          <button
            onClick={() => toggleSection('performance')}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <h2 className="text-lg font-mono font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                {t('events.performanceByType', '按事件类型统计')}
              </h2>
            </div>
            {expandedSection === 'performance' ? (
              <ChevronUp className="w-5 h-5 text-slate-400 dark:text-white/40" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400 dark:text-white/40" />
            )}
          </button>
          {expandedSection === 'performance' && (
            <div className="px-6 pb-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {performanceByType.map((perf) => {
                  const avgChange = perf.avg_price_change ?? 0;
                  return (
                    <div
                      key={perf.event_type}
                      className="p-4 bg-neutral-50 dark:bg-white/5 rounded-sm"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-mono font-medium text-slate-900 dark:text-white capitalize">
                          {perf.event_type}
                        </span>
                        <span className="text-sm font-mono text-slate-500 dark:text-white/40">
                          {perf.event_count} {t('events.times', '次')}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500 dark:text-white/40">{t('events.totalPnL', '总盈亏')}</span>
                        <span className={`font-mono font-medium ${perf.total_pnl >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
                          {formatCurrency(perf.total_pnl)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm mt-1">
                        <span className="text-slate-500 dark:text-white/40">{t('events.avgChange', '平均变动')}</span>
                        <span className={`font-mono font-medium ${avgChange >= 0 ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'}`}>
                          {avgChange >= 0 ? '+' : ''}{avgChange.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
