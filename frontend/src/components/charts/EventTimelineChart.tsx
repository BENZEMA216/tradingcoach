import { useTranslation } from 'react-i18next';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
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

// Event type icons/emojis
const EVENT_TYPE_CONFIG: Record<string, { emoji: string; label: string; color: string }> = {
  earnings: { emoji: '📊', label: '财报', color: '#3B82F6' },
  earnings_pre: { emoji: '📊', label: '财报(盘前)', color: '#3B82F6' },
  earnings_post: { emoji: '📊', label: '财报(盘后)', color: '#3B82F6' },
  dividend: { emoji: '💰', label: '分红', color: '#10B981' },
  split: { emoji: '✂️', label: '拆分', color: '#8B5CF6' },
  product: { emoji: '📦', label: '产品', color: '#F59E0B' },
  guidance: { emoji: '🎯', label: '指引', color: '#6366F1' },
  analyst: { emoji: '📝', label: '评级', color: '#EC4899' },
  macro: { emoji: '🌍', label: '宏观', color: '#14B8A6' },
  fed: { emoji: '🏛️', label: '美联储', color: '#EF4444' },
  cpi: { emoji: '📈', label: 'CPI', color: '#F97316' },
  nfp: { emoji: '👷', label: '非农', color: '#84CC16' },
  geopolitical: { emoji: '🌐', label: '地缘', color: '#A855F7' },
  price_anomaly: { emoji: '⚡', label: '价格异动', color: '#EF4444' },
  volume_anomaly: { emoji: '📢', label: '量能异动', color: '#F59E0B' },
  other: { emoji: '📌', label: '其他', color: '#6B7280' },
};

// Impact color mapping
const IMPACT_COLORS: Record<string, string> = {
  positive: '#10B981',
  negative: '#EF4444',
  neutral: '#6B7280',
  mixed: '#F59E0B',
  unknown: '#9CA3AF',
};

export function EventTimelineChart({
  events,
  title,
  showPnL = true,
  isLoading,
}: EventTimelineChartProps) {
  const { t, i18n } = useTranslation();
  const colors = useChartColors();
  const displayTitle = title || t('charts.eventTimeline', '事件时间线');
  const locale = i18n.language === 'zh' ? 'zh-CN' : 'en-US';

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <ChartSkeleton height="h-80" />
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {displayTitle}
        </h3>
        <EmptyState
          icon="event"
          height="h-80"
          title={t('events.noEvents', '暂无事件')}
          description={t('events.noEventsDescription', '该时间段内未检测到重大市场事件')}
          size="md"
        />
      </div>
    );
  }

  // Transform events for chart
  const chartData = events.map((event) => {
    const config = EVENT_TYPE_CONFIG[event.event_type] || EVENT_TYPE_CONFIG.other;
    return {
      date: new Date(event.event_date).toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
      }),
      fullDate: event.event_date,
      title: event.event_title,
      type: event.event_type,
      typeLabel: config.label,
      emoji: config.emoji,
      impact: event.event_impact || 'unknown',
      importance: event.event_importance || 5,
      priceChange: event.price_change_pct,
      volumeSpike: event.volume_spike,
      pnl: event.position_pnl_on_event,
      isKeyEvent: event.is_key_event,
      color: event.event_impact ? IMPACT_COLORS[event.event_impact] : config.color,
    };
  });

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: unknown[] }) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = (payload[0] as { payload: typeof chartData[0] }).payload;
    const impactLabel = {
      positive: t('events.impact.positive', '利好'),
      negative: t('events.impact.negative', '利空'),
      neutral: t('events.impact.neutral', '中性'),
      mixed: t('events.impact.mixed', '混合'),
      unknown: t('events.impact.unknown', '未知'),
    }[data.impact];

    return (
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 max-w-xs">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl">{data.emoji}</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {data.typeLabel}
          </span>
          {data.isKeyEvent && (
            <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-1.5 py-0.5 rounded">
              {t('events.keyEvent', '关键')}
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2 line-clamp-2">
          {data.title}
        </p>
        <div className="text-xs text-gray-500 dark:text-gray-400 space-y-1">
          <div className="flex justify-between">
            <span>{t('events.date', '日期')}:</span>
            <span>{data.fullDate}</span>
          </div>
          <div className="flex justify-between">
            <span>{t('events.impact', '影响')}:</span>
            <span style={{ color: IMPACT_COLORS[data.impact] }}>{impactLabel}</span>
          </div>
          {data.priceChange !== null && (
            <div className="flex justify-between">
              <span>{t('events.priceChange', '价格变动')}:</span>
              <span className={data.priceChange >= 0 ? 'text-green-500' : 'text-red-500'}>
                {data.priceChange >= 0 ? '+' : ''}{data.priceChange.toFixed(1)}%
              </span>
            </div>
          )}
          {data.volumeSpike !== null && data.volumeSpike > 1 && (
            <div className="flex justify-between">
              <span>{t('events.volumeSpike', '成交量')}:</span>
              <span className="text-orange-500">{data.volumeSpike.toFixed(1)}x</span>
            </div>
          )}
          {showPnL && data.pnl !== null && (
            <div className="flex justify-between font-medium">
              <span>{t('events.pnlOnEvent', '当日盈亏')}:</span>
              <span className={data.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                ${data.pnl.toFixed(0)}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {displayTitle}
        </h3>
        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            {t('events.impact.positive', '利好')}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            {t('events.impact.negative', '利空')}
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            {t('events.impact.mixed', '混合')}
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} opacity={0.5} />
          <XAxis
            dataKey="date"
            tick={{ fill: colors.text, fontSize: 11 }}
            tickLine={{ stroke: colors.grid }}
            axisLine={{ stroke: colors.grid }}
            angle={-45}
            textAnchor="end"
            height={60}
          />
          <YAxis
            yAxisId="price"
            orientation="left"
            tick={{ fill: colors.text, fontSize: 11 }}
            tickLine={{ stroke: colors.grid }}
            axisLine={{ stroke: colors.grid }}
            label={{
              value: t('events.priceChange', '价格变动') + ' (%)',
              angle: -90,
              position: 'insideLeft',
              fill: colors.text,
              fontSize: 11,
            }}
          />
          {showPnL && (
            <YAxis
              yAxisId="pnl"
              orientation="right"
              tick={{ fill: colors.text, fontSize: 11 }}
              tickLine={{ stroke: colors.grid }}
              axisLine={{ stroke: colors.grid }}
              label={{
                value: t('events.pnl', '盈亏') + ' ($)',
                angle: 90,
                position: 'insideRight',
                fill: colors.text,
                fontSize: 11,
              }}
            />
          )}
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine yAxisId="price" y={0} stroke={colors.grid} strokeDasharray="3 3" />

          {/* Price change bars */}
          <Bar
            yAxisId="price"
            dataKey="priceChange"
            name={t('events.priceChange', '价格变动')}
            radius={[4, 4, 0, 0]}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.7} />
            ))}
          </Bar>

          {/* PnL line */}
          {showPnL && (
            <Line
              yAxisId="pnl"
              type="monotone"
              dataKey="pnl"
              name={t('events.pnl', '盈亏')}
              stroke={colors.primary}
              strokeWidth={2}
              dot={{
                fill: colors.primary,
                strokeWidth: 2,
                r: 4,
              }}
              activeDot={{
                r: 6,
                fill: colors.primary,
              }}
              connectNulls
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Event type legend */}
      <div className="mt-4 flex flex-wrap gap-2 justify-center">
        {Array.from(new Set(events.map((e) => e.event_type))).map((type) => {
          const config = EVENT_TYPE_CONFIG[type] || EVENT_TYPE_CONFIG.other;
          const count = events.filter((e) => e.event_type === type).length;
          return (
            <span
              key={type}
              className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
            >
              <span>{config.emoji}</span>
              <span>{config.label}</span>
              <span className="text-gray-500 dark:text-gray-400">({count})</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

export default EventTimelineChart;
