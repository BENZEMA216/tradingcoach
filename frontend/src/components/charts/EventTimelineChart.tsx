import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { EventListItem } from '@/types';
import { useChartColors } from '@/hooks/useChartColors';
import { ChartSkeleton } from '@/components/common/ChartSkeleton';
import { EmptyState } from '@/components/common/EmptyState';

interface EventTimelineChartProps {
  events: EventListItem[];
  title?: string;
  showPnL?: boolean;
  isLoading?: boolean;
}

// Event type configuration
const EVENT_TYPE_CONFIG: Record<string, { emoji: string; label: string; labelEn: string; color: string }> = {
  price_anomaly: { emoji: '⚡', label: '价格异动', labelEn: 'Price', color: '#EF4444' },
  volume_anomaly: { emoji: '📊', label: '量能异动', labelEn: 'Volume', color: '#F59E0B' },
  earnings: { emoji: '📈', label: '财报', labelEn: 'Earnings', color: '#3B82F6' },
  analyst: { emoji: '📝', label: '评级', labelEn: 'Analyst', color: '#EC4899' },
  product: { emoji: '📦', label: '产品', labelEn: 'Product', color: '#8B5CF6' },
  sector: { emoji: '🏭', label: '行业', labelEn: 'Sector', color: '#6366F1' },
  geopolitical: { emoji: '🌐', label: '地缘', labelEn: 'Geo', color: '#14B8A6' },
  regulatory: { emoji: '⚖️', label: '监管', labelEn: 'Regulatory', color: '#0EA5E9' },
  management: { emoji: '👔', label: '管理层', labelEn: 'Mgmt', color: '#A855F7' },
  macro: { emoji: '🌍', label: '宏观', labelEn: 'Macro', color: '#10B981' },
  fda: { emoji: '💊', label: 'FDA', labelEn: 'FDA', color: '#DC2626' },
  other: { emoji: '📌', label: '其他', labelEn: 'Other', color: '#6B7280' },
};

// Impact colors
const IMPACT_COLORS = {
  positive: '#10B981',
  negative: '#EF4444',
  mixed: '#F59E0B',
  neutral: '#64748B',
};

interface TimelineTooltipPayload {
  dateLabel: string;
  positive: number;
  negative: number;
  neutral: number;
  mixed: number;
  total: number;
}

function TimelineTooltip({
  active,
  payload,
  isZh,
}: {
  active?: boolean;
  payload?: unknown[];
  isZh: boolean;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const data = (payload[0] as { payload: TimelineTooltipPayload }).payload;

  return (
    <div className="bg-white dark:bg-neutral-900 px-3 py-2 rounded-sm shadow-lg border border-neutral-200 dark:border-white/10 text-xs font-mono">
      <div className="font-bold text-slate-900 dark:text-white mb-1.5">{data.dateLabel}</div>
      <div className="space-y-0.5">
        {data.positive > 0 && (
          <div className="flex items-center justify-between gap-4">
            <span className="text-green-600 dark:text-green-500">▲ {isZh ? '利好' : 'Bullish'}</span>
            <span className="text-slate-900 dark:text-white">{data.positive}</span>
          </div>
        )}
        {data.negative > 0 && (
          <div className="flex items-center justify-between gap-4">
            <span className="text-red-600 dark:text-red-500">▼ {isZh ? '利空' : 'Bearish'}</span>
            <span className="text-slate-900 dark:text-white">{data.negative}</span>
          </div>
        )}
        {data.mixed > 0 && (
          <div className="flex items-center justify-between gap-4">
            <span className="text-amber-600 dark:text-amber-500">◆ {isZh ? '混合' : 'Mixed'}</span>
            <span className="text-slate-900 dark:text-white">{data.mixed}</span>
          </div>
        )}
        {data.neutral > 0 && (
          <div className="flex items-center justify-between gap-4">
            <span className="text-slate-500 dark:text-slate-400">○ {isZh ? '中性' : 'Neutral'}</span>
            <span className="text-slate-900 dark:text-white">{data.neutral}</span>
          </div>
        )}
        <div className="border-t border-neutral-200 dark:border-white/10 pt-1 mt-1 flex items-center justify-between">
          <span className="text-slate-500 dark:text-white/40">{isZh ? '合计' : 'Total'}</span>
          <span className="font-bold text-slate-900 dark:text-white">{data.total}</span>
        </div>
      </div>
    </div>
  );
}

export function EventTimelineChart({
  events,
  isLoading,
}: EventTimelineChartProps) {
  const { t, i18n } = useTranslation();
  const colors = useChartColors();
  const isZh = i18n.language === 'zh';

  // Use events directly - filtering should be done at API level
  const validEvents = useMemo(() => {
    if (!events || events.length === 0) return [];
    return events;
  }, [events]);

  // Aggregate events by date for timeline
  const timelineData = useMemo(() => {
    if (!validEvents || validEvents.length === 0) return [];

    const dateMap = new Map<string, {
      date: string;
      dateLabel: string;
      positive: number;
      negative: number;
      neutral: number;
      mixed: number;
      total: number;
      negativeDisplay: number; // For display below x-axis
    }>();

    validEvents.forEach((event) => {
      const dateStr = event.event_date.split('T')[0];

      if (!dateMap.has(dateStr)) {
        const d = new Date(dateStr);
        dateMap.set(dateStr, {
          date: dateStr,
          dateLabel: d.toLocaleDateString(isZh ? 'zh-CN' : 'en-US', {
            month: 'short',
            day: 'numeric'
          }),
          positive: 0,
          negative: 0,
          neutral: 0,
          mixed: 0,
          total: 0,
          negativeDisplay: 0,
        });
      }

      const entry = dateMap.get(dateStr)!;
      entry.total += 1;

      const impact = event.event_impact || 'neutral';
      if (impact === 'positive') entry.positive += 1;
      else if (impact === 'negative') {
        entry.negative += 1;
        entry.negativeDisplay -= 1; // Negative for display below axis
      }
      else if (impact === 'mixed') entry.mixed += 1;
      else entry.neutral += 1;
    });

    return Array.from(dateMap.values())
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [validEvents, isZh]);

  // Event type summary
  const typeSummary = useMemo(() => {
    if (!validEvents || validEvents.length === 0) return [];

    const typeMap = new Map<string, number>();
    validEvents.forEach((event) => {
      const type = event.event_type || 'other';
      typeMap.set(type, (typeMap.get(type) || 0) + 1);
    });

    return Array.from(typeMap.entries())
      .map(([type, count]) => {
        const config = EVENT_TYPE_CONFIG[type] || EVENT_TYPE_CONFIG.other;
        return {
          type,
          count,
          label: isZh ? config.label : config.labelEn,
          emoji: config.emoji,
          color: config.color,
          percent: ((count / validEvents.length) * 100).toFixed(0),
        };
      })
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [validEvents, isZh]);

  // Impact summary
  const impactSummary = useMemo(() => {
    if (!validEvents || validEvents.length === 0) return { positive: 0, negative: 0, neutral: 0, mixed: 0 };

    const counts = { positive: 0, negative: 0, neutral: 0, mixed: 0 };
    validEvents.forEach((event) => {
      const impact = event.event_impact || 'neutral';
      if (impact in counts) counts[impact as keyof typeof counts]++;
      else counts.neutral++;
    });

    return counts;
  }, [validEvents]);

  if (isLoading) {
    return <ChartSkeleton height="h-80" />;
  }

  if (!validEvents || validEvents.length === 0) {
    return (
      <EmptyState
        icon="event"
        height="h-64"
        title={t('events.noEvents', '暂无事件')}
        description={t('events.noEventsDescription', '该时间段内未检测到重大市场事件')}
        size="md"
      />
    );
  }

  const totalPositive = impactSummary.positive;
  const totalNegative = impactSummary.negative;
  const totalNeutralMixed = impactSummary.neutral + impactSummary.mixed;

  return (
    <div className="space-y-6">
      {/* Summary Stats Row */}
      <div className="grid grid-cols-4 gap-3">
        <div className="text-center">
          <div className="text-2xl font-mono font-bold text-slate-900 dark:text-white">
            {validEvents.length}
          </div>
          <div className="text-[10px] font-mono text-slate-400 dark:text-white/30 uppercase tracking-wider">
            {t('events.total', 'Total')}
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-mono font-bold text-green-600 dark:text-green-500">
            {totalPositive}
          </div>
          <div className="text-[10px] font-mono text-slate-400 dark:text-white/30 uppercase tracking-wider">
            {isZh ? '利好' : 'Bullish'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-mono font-bold text-red-600 dark:text-red-500">
            {totalNegative}
          </div>
          <div className="text-[10px] font-mono text-slate-400 dark:text-white/30 uppercase tracking-wider">
            {isZh ? '利空' : 'Bearish'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-mono font-bold text-slate-500 dark:text-slate-400">
            {totalNeutralMixed}
          </div>
          <div className="text-[10px] font-mono text-slate-400 dark:text-white/30 uppercase tracking-wider">
            {isZh ? '中性/混合' : 'Other'}
          </div>
        </div>
      </div>

      {/* Main Timeline Chart - Diverging Bar Chart */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-mono font-medium text-slate-400 dark:text-white/30 uppercase tracking-widest">
            {t('events.timelineByImpact', '影响时间线')}
          </h4>
          <div className="flex items-center gap-3 text-[10px] font-mono">
            <span className="flex items-center gap-1 text-green-600 dark:text-green-500">
              <span className="w-2 h-2 rounded-sm bg-green-500" />
              {isZh ? '利好' : 'Bullish'}
            </span>
            <span className="flex items-center gap-1 text-red-600 dark:text-red-500">
              <span className="w-2 h-2 rounded-sm bg-red-500" />
              {isZh ? '利空' : 'Bearish'}
            </span>
            <span className="flex items-center gap-1 text-slate-400">
              <span className="w-2 h-2 rounded-sm bg-slate-400" />
              {isZh ? '其他' : 'Other'}
            </span>
          </div>
        </div>

        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%" minHeight={200}>
            <ComposedChart
              data={timelineData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              stackOffset="sign"
            >
              <XAxis
                dataKey="dateLabel"
                tick={{ fill: colors.text, fontSize: 9, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: colors.grid, strokeOpacity: 0.3 }}
                interval="preserveStartEnd"
                minTickGap={30}
              />
              <YAxis
                tick={{ fill: colors.text, fontSize: 9, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={false}
                width={25}
                tickFormatter={(v) => Math.abs(v).toString()}
              />
              <Tooltip content={<TimelineTooltip isZh={isZh} />} />
              <ReferenceLine y={0} stroke={colors.grid} strokeOpacity={0.5} />

              {/* Positive events - above axis */}
              <Bar
                dataKey="positive"
                stackId="stack"
                fill={IMPACT_COLORS.positive}
                radius={[2, 2, 0, 0]}
              />

              {/* Neutral + Mixed - above axis, stacked */}
              <Bar
                dataKey="neutral"
                stackId="stack"
                fill={IMPACT_COLORS.neutral}
                fillOpacity={0.6}
              />
              <Bar
                dataKey="mixed"
                stackId="stack"
                fill={IMPACT_COLORS.mixed}
                fillOpacity={0.6}
              />

              {/* Negative events - below axis */}
              <Bar
                dataKey="negativeDisplay"
                fill={IMPACT_COLORS.negative}
                radius={[0, 0, 2, 2]}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Type Distribution - Compact Horizontal */}
      <div className="space-y-2">
        <h4 className="text-xs font-mono font-medium text-slate-400 dark:text-white/30 uppercase tracking-widest">
          {t('events.typeBreakdown', '类型构成')}
        </h4>

        <div className="flex flex-wrap gap-2">
          {typeSummary.map((item) => (
            <div
              key={item.type}
              className="flex items-center gap-1.5 px-2 py-1 rounded-sm bg-neutral-50 dark:bg-white/5"
            >
              <span className="text-sm">{item.emoji}</span>
              <span className="text-xs font-mono text-slate-600 dark:text-white/60">
                {item.label}
              </span>
              <span className="text-xs font-mono font-bold text-slate-900 dark:text-white">
                {item.count}
              </span>
              <span className="text-[10px] font-mono text-slate-400 dark:text-white/30">
                ({item.percent}%)
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Impact Distribution Bar */}
      <div className="space-y-2">
        <h4 className="text-xs font-mono font-medium text-slate-400 dark:text-white/30 uppercase tracking-widest">
          {t('events.impactDistribution', '影响分布')}
        </h4>

        <div className="h-3 rounded-full overflow-hidden flex bg-neutral-100 dark:bg-white/5">
          {impactSummary.positive > 0 && (
            <div
              className="h-full bg-green-500 transition-all"
              style={{ width: `${(impactSummary.positive / validEvents.length) * 100}%` }}
              title={`${isZh ? '利好' : 'Bullish'}: ${impactSummary.positive}`}
            />
          )}
          {impactSummary.mixed > 0 && (
            <div
              className="h-full bg-amber-500 transition-all"
              style={{ width: `${(impactSummary.mixed / validEvents.length) * 100}%` }}
              title={`${isZh ? '混合' : 'Mixed'}: ${impactSummary.mixed}`}
            />
          )}
          {impactSummary.neutral > 0 && (
            <div
              className="h-full bg-slate-400 transition-all"
              style={{ width: `${(impactSummary.neutral / validEvents.length) * 100}%` }}
              title={`${isZh ? '中性' : 'Neutral'}: ${impactSummary.neutral}`}
            />
          )}
          {impactSummary.negative > 0 && (
            <div
              className="h-full bg-red-500 transition-all"
              style={{ width: `${(impactSummary.negative / validEvents.length) * 100}%` }}
              title={`${isZh ? '利空' : 'Bearish'}: ${impactSummary.negative}`}
            />
          )}
        </div>

        <div className="flex justify-between text-[10px] font-mono text-slate-400 dark:text-white/30">
          <span>{((impactSummary.positive / validEvents.length) * 100).toFixed(0)}% {isZh ? '利好' : 'Bullish'}</span>
          <span>{((impactSummary.negative / validEvents.length) * 100).toFixed(0)}% {isZh ? '利空' : 'Bearish'}</span>
        </div>
      </div>
    </div>
  );
}

export default EventTimelineChart;
