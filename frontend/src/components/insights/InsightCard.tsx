import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDownIcon, ChevronRightIcon, LightBulbIcon } from '@heroicons/react/24/outline';
import type { TradingInsight, InsightType } from '@/types';
import clsx from 'clsx';

interface InsightCardProps {
  insight: TradingInsight;
  compact?: boolean;
}

const TYPE_CONFIG: Record<InsightType, {
  label: { en: string; zh: string };
  dotColor: string;
  textColor: string;
  hoverBg: string;
}> = {
  problem: {
    label: { en: 'Issue', zh: '问题' },
    dotColor: 'bg-red-500',
    textColor: 'text-red-600 dark:text-red-400',
    hoverBg: 'hover:bg-red-50 dark:hover:bg-red-900/10',
  },
  strength: {
    label: { en: 'Strength', zh: '优势' },
    dotColor: 'bg-green-500',
    textColor: 'text-green-600 dark:text-green-400',
    hoverBg: 'hover:bg-green-50 dark:hover:bg-green-900/10',
  },
  reminder: {
    label: { en: 'Note', zh: '提醒' },
    dotColor: 'bg-amber-500',
    textColor: 'text-amber-600 dark:text-amber-400',
    hoverBg: 'hover:bg-amber-50 dark:hover:bg-amber-900/10',
  },
};

export function InsightCard({ insight, compact = false }: InsightCardProps) {
  const { i18n } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const config = TYPE_CONFIG[insight.type];
  const isZh = i18n.language === 'zh';

  const formatDataPoint = (key: string, value: unknown): string => {
    if (typeof value === 'number') {
      if (key.includes('rate') || key.includes('pct') || key.includes('percentage')) {
        return `${value.toFixed(1)}%`;
      }
      if (key.includes('pnl') || key.includes('loss') || key.includes('win') || key.includes('fees')) {
        return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
      }
      if (key.includes('days') || key.includes('holding')) {
        return `${value.toFixed(1)}d`;
      }
      if (Number.isInteger(value)) {
        return String(value);
      }
      return value.toFixed(1);
    }
    return String(value);
  };

  // Extract key metrics from data_points for inline display
  const keyMetrics = Object.entries(insight.data_points)
    .slice(0, 2)
    .map(([key, value]) => ({
      label: key.replace(/_/g, ' '),
      value: formatDataPoint(key, value),
    }));

  if (compact) {
    // Compact mode: single line with hover expansion
    return (
      <div
        className={clsx(
          'group flex items-center gap-3 px-3 py-2 rounded-lg transition-colors cursor-pointer',
          config.hoverBg
        )}
        onClick={() => setExpanded(!expanded)}
      >
        <span className={clsx('w-2 h-2 rounded-full flex-shrink-0', config.dotColor)} />
        <span className="text-sm text-neutral-900 dark:text-neutral-100 truncate flex-1">
          {insight.title}
        </span>
        {keyMetrics.length > 0 && (
          <span className="text-xs text-neutral-500 dark:text-neutral-400 hidden sm:inline">
            {keyMetrics.map(m => m.value).join(' · ')}
          </span>
        )}
        <ChevronRightIcon
          className={clsx(
            'w-4 h-4 text-neutral-400 transition-transform',
            expanded && 'rotate-90'
          )}
        />
      </div>
    );
  }

  // Standard mode: More detailed card
  return (
    <div className="group">
      <div
        className={clsx(
          'flex items-start gap-3 px-4 py-3 rounded-lg transition-colors cursor-pointer',
          config.hoverBg
        )}
        onClick={() => setExpanded(!expanded)}
      >
        {/* Type indicator */}
        <div className="flex flex-col items-center gap-1 pt-0.5">
          <span className={clsx('w-2.5 h-2.5 rounded-full', config.dotColor)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Title row */}
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className={clsx('text-xs font-medium uppercase tracking-wide', config.textColor)}>
              {isZh ? config.label.zh : config.label.en}
            </span>
            <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {insight.title}
            </span>
            {/* Inline metrics */}
            {keyMetrics.length > 0 && !expanded && (
              <span className="text-xs text-neutral-400 dark:text-neutral-500 ml-auto">
                {keyMetrics.map(m => m.value).join(' · ')}
              </span>
            )}
          </div>

          {/* Description - truncated when collapsed */}
          <p className={clsx(
            'text-sm text-neutral-500 dark:text-neutral-400 mt-1',
            !expanded && 'line-clamp-1'
          )}>
            {insight.description}
          </p>

          {/* Expanded content */}
          {expanded && (
            <div className="mt-3 space-y-3">
              {/* Suggestion */}
              <div className="flex items-start gap-2 p-2.5 bg-neutral-100 dark:bg-neutral-800 rounded-md">
                <LightBulbIcon className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-neutral-600 dark:text-neutral-300">
                  {insight.suggestion}
                </p>
              </div>

              {/* Data points */}
              {Object.keys(insight.data_points).length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Object.entries(insight.data_points).map(([key, value]) => (
                    <span
                      key={key}
                      className="inline-flex items-center gap-1.5 px-2 py-1 bg-neutral-100 dark:bg-neutral-800 rounded text-xs"
                    >
                      <span className="text-neutral-400">{key.replace(/_/g, ' ')}:</span>
                      <span className="font-medium text-neutral-700 dark:text-neutral-200">
                        {formatDataPoint(key, value)}
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Expand indicator */}
        <ChevronDownIcon
          className={clsx(
            'w-4 h-4 text-neutral-400 transition-transform flex-shrink-0',
            expanded && 'rotate-180'
          )}
        />
      </div>
    </div>
  );
}
