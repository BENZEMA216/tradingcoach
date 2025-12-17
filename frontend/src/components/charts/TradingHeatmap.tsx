import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import type { TradingHeatmapCell } from '@/types';
import { formatCurrency } from '@/utils/format';

interface TradingHeatmapProps {
  data: TradingHeatmapCell[];
  isLoading?: boolean;
  bare?: boolean;
}

const DAYS_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAYS_ZH = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

// Get user's timezone offset in hours
const getTimezoneOffset = () => {
  return -new Date().getTimezoneOffset() / 60; // e.g., +8 for Beijing
};

// Convert UTC hour to local hour
const utcToLocal = (utcHour: number, offset: number): number => {
  let localHour = (utcHour + offset) % 24;
  if (localHour < 0) localHour += 24;
  return localHour;
};

// Convert local hour to UTC hour
const localToUtc = (localHour: number, offset: number): number => {
  let utcHour = (localHour - offset) % 24;
  if (utcHour < 0) utcHour += 24;
  return utcHour;
};

export function TradingHeatmap({ data, isLoading, bare = false }: TradingHeatmapProps) {
  const { t } = useTranslation();

  // ALL hooks must be called unconditionally at the top - before any returns
  const timezoneOffset = useMemo(() => getTimezoneOffset(), []);

  // Format timezone label
  const tzLabel = useMemo(() => {
    const sign = timezoneOffset >= 0 ? '+' : '';
    return `UTC${sign}${timezoneOffset}`;
  }, [timezoneOffset]);

  // Determine which LOCAL hours have trading data
  const { tradingHours, dataMap, maxAvgPnl } = useMemo(() => {
    if (!data || data.length === 0) {
      return { tradingHours: [], dataMap: new Map<string, TradingHeatmapCell>(), maxAvgPnl: 0 };
    }

    // Create a lookup map using UTC hours (as stored in backend)
    const map = new Map<string, TradingHeatmapCell>();
    data.forEach((cell) => {
      map.set(`${cell.day_of_week}-${cell.hour}`, cell);
    });

    // Find max values for color scaling
    const maxPnl = Math.max(...data.map(d => Math.abs(d.avg_pnl)));

    // Convert UTC hours to local hours and find the range
    const localHoursWithData = new Set<number>();
    data.forEach(d => {
      const localHour = utcToLocal(d.hour, timezoneOffset);
      localHoursWithData.add(localHour);
    });

    if (localHoursWithData.size === 0) {
      return { tradingHours: [], dataMap: map, maxAvgPnl: maxPnl };
    }

    // Find min and max local hours with some padding
    const sortedHours = Array.from(localHoursWithData).sort((a, b) => a - b);

    // Group hours into contiguous ranges to find main trading periods
    // For simplicity, show all hours from min-1 to max+1 (with bounds)
    const min = Math.max(0, sortedHours[0] - 1);
    const max = Math.min(23, sortedHours[sortedHours.length - 1] + 1);

    // Generate hour range
    const hours: number[] = [];
    for (let h = min; h <= max; h++) {
      hours.push(h);
    }

    return { tradingHours: hours, dataMap: map, maxAvgPnl: maxPnl };
  }, [data, timezoneOffset]);

  // Derived values (not hooks, just computed)
  const isZh = t('common.noData') === '暂无数据';
  const DAYS = isZh ? DAYS_ZH : DAYS_EN;

  // Create a lookup that maps local hour -> UTC hour for data retrieval
  const getDataForLocalHour = (dayIndex: number, localHour: number) => {
    const utcHour = localToUtc(localHour, timezoneOffset);
    return dataMap.get(`${dayIndex}-${utcHour}`);
  };

  // TradingView-style colors for dark mode
  // Profit: #26a69a (teal) -> varies from 20% to 100% opacity
  // Loss: #ef5350 (coral red) -> varies from 20% to 100% opacity
  const getCellStyle = (cell: TradingHeatmapCell | undefined): React.CSSProperties => {
    if (!cell || cell.trade_count === 0) {
      return {};
    }
    const intensity = Math.min(Math.abs(cell.avg_pnl) / (maxAvgPnl || 1), 1);
    const alpha = 0.2 + intensity * 0.8; // Range from 0.2 to 1.0

    if (cell.avg_pnl > 0) {
      // TradingView profit teal: #26a69a
      return { backgroundColor: `rgba(38, 166, 154, ${alpha})` };
    } else {
      // TradingView loss coral: #ef5350
      return { backgroundColor: `rgba(239, 83, 80, ${alpha})` };
    }
  };

  const getEmptyCellClass = () => 'bg-neutral-200/50 dark:bg-neutral-700/30';

  const getTextColor = (cell: TradingHeatmapCell | undefined) => {
    if (!cell || cell.trade_count === 0) return 'text-neutral-400 dark:text-neutral-500';
    const intensity = Math.min(Math.abs(cell.avg_pnl) / (maxAvgPnl || 1), 1);
    if (intensity > 0.5) return 'text-white';
    return 'text-neutral-800 dark:text-white';
  };

  // Early returns AFTER all hooks
  if (isLoading) {
    if (bare) return <div className="h-48 bg-neutral-100 dark:bg-neutral-800 rounded animate-pulse" />;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4 animate-pulse" />
        <div className="h-48 bg-gray-100 dark:bg-gray-700/50 rounded animate-pulse" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    if (bare) return <div className="h-48 flex items-center justify-center text-neutral-500">{t('common.noData')}</div>;
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          {t('charts.tradingHeatmap')}
        </h3>
        <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
          {t('common.noData')}
        </div>
      </div>
    );
  }

  const heatmapContent = (
    <>
      {/* Timezone indicator */}
      <div className="text-[11px] text-neutral-400 dark:text-neutral-500 mb-3">
        {isZh ? '本地时间' : 'Local time'} ({tzLabel})
      </div>

      <div className="overflow-x-auto">
          <div className="inline-flex gap-1">
            {/* Day labels column */}
          <div className="flex flex-col">
            <div className="h-6" /> {/* Header spacer */}
            {DAYS.slice(0, 5).map((day) => (
              <div
                key={day}
                className="h-8 flex items-center text-xs text-gray-500 dark:text-gray-400 font-medium pr-2"
              >
                {day}
              </div>
            ))}
          </div>

          {/* Hour columns */}
          {tradingHours.map((localHour) => (
            <div key={localHour} className="flex flex-col items-center">
              {/* Hour header */}
              <div className="h-6 flex items-center justify-center text-[10px] text-gray-500 dark:text-gray-400">
                {localHour}
              </div>

              {/* Day cells for this hour */}
              {DAYS.slice(0, 5).map((day, dayIndex) => {
                const cell = getDataForLocalHour(dayIndex, localHour);
                const hasData = cell && cell.trade_count > 0;
                // Bottom rows (Thu=3, Fri=4) show tooltip above, others show below
                const showTooltipAbove = dayIndex >= 3;
                return (
                  <div key={`${dayIndex}-${localHour}`} className="p-0.5">
                    <div
                      className={`
                        w-7 h-7 rounded-sm flex items-center justify-center
                        cursor-pointer transition-all hover:ring-2 hover:ring-offset-1 hover:ring-neutral-400 dark:hover:ring-neutral-500
                        ${!hasData ? getEmptyCellClass() : ''}
                        group relative
                      `}
                      style={getCellStyle(cell)}
                    >
                      <span className={`text-[10px] font-medium ${getTextColor(cell)}`}>
                        {cell?.trade_count || ''}
                      </span>

                      {/* Tooltip - position based on row to avoid clipping */}
                      {cell && cell.trade_count > 0 && (
                        <div className={`absolute left-1/2 -translate-x-1/2 hidden group-hover:block z-50 pointer-events-none ${
                          showTooltipAbove ? 'bottom-full mb-2' : 'top-full mt-2'
                        }`}>
                          <div className="bg-gray-900 dark:bg-gray-700 text-white text-xs rounded-lg p-2.5 shadow-xl whitespace-nowrap border border-gray-700 dark:border-gray-600">
                            <div className="font-semibold">{day} {localHour}:00</div>
                            <div className="mt-1.5 space-y-1">
                              <div>{t('charts.tradeCount')}: {cell.trade_count}</div>
                              <div>{t('common.winRate')}: {cell.win_rate.toFixed(1)}%</div>
                              <div className={cell.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                                {t('charts.avgPnl')}: {formatCurrency(cell.avg_pnl)}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-center gap-4 text-[11px] text-neutral-400">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-neutral-200/50 dark:bg-neutral-700/30 rounded border border-neutral-300 dark:border-neutral-600" />
          <span>{t('charts.noTrades')}</span>
        </div>
        <div className="flex items-center gap-0.5">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(239, 83, 80, 0.3)' }} />
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(239, 83, 80, 0.6)' }} />
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(239, 83, 80, 1)' }} />
          <span className="ml-1">{t('charts.moreLoss')}</span>
        </div>
        <div className="flex items-center gap-0.5">
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(38, 166, 154, 0.3)' }} />
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(38, 166, 154, 0.6)' }} />
          <div className="w-3 h-3 rounded" style={{ backgroundColor: 'rgba(38, 166, 154, 1)' }} />
          <span className="ml-1">{t('charts.moreProfit')}</span>
        </div>
      </div>
    </>
  );

  if (bare) {
    return heatmapContent;
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {t('charts.tradingHeatmap')}
      </h3>
      {heatmapContent}
    </div>
  );
}
