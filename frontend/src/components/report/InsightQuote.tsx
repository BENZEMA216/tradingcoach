import type { ReactNode } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Info, Lightbulb } from 'lucide-react';
import clsx from 'clsx';

export type InsightType = 'positive' | 'negative' | 'warning' | 'info' | 'tip';

interface InsightQuoteProps {
  text: string;
  type?: InsightType;
  icon?: ReactNode;
  className?: string;
}

const typeConfig: Record<InsightType, { icon: ReactNode; bgClass: string; iconClass: string }> = {
  positive: {
    icon: <TrendingUp className="w-4 h-4" />,
    bgClass: 'bg-green-50 dark:bg-green-950/30',
    iconClass: 'text-green-600 dark:text-green-400',
  },
  negative: {
    icon: <TrendingDown className="w-4 h-4" />,
    bgClass: 'bg-red-50 dark:bg-red-950/30',
    iconClass: 'text-red-600 dark:text-red-400',
  },
  warning: {
    icon: <AlertTriangle className="w-4 h-4" />,
    bgClass: 'bg-amber-50 dark:bg-amber-950/30',
    iconClass: 'text-amber-600 dark:text-amber-400',
  },
  info: {
    icon: <Info className="w-4 h-4" />,
    bgClass: 'bg-neutral-50 dark:bg-neutral-800/50',
    iconClass: 'text-neutral-500 dark:text-neutral-400',
  },
  tip: {
    icon: <Lightbulb className="w-4 h-4" />,
    bgClass: 'bg-blue-50 dark:bg-blue-950/30',
    iconClass: 'text-blue-600 dark:text-blue-400',
  },
};

/**
 * Highlight numbers and percentages in the text
 */
function highlightText(text: string): ReactNode[] {
  // Match numbers with optional $ prefix and % suffix
  const regex = /(\$?[\d,]+\.?\d*%?)/g;
  const parts = text.split(regex);

  return parts.map((part, index) => {
    if (regex.test(part)) {
      return (
        <span key={index} className="font-semibold text-neutral-900 dark:text-neutral-100 not-italic">
          {part}
        </span>
      );
    }
    return part;
  });
}

export function InsightQuote({ text, type = 'info', icon, className }: InsightQuoteProps) {
  const config = typeConfig[type];
  const displayIcon = icon || config.icon;

  return (
    <div
      className={clsx(
        'flex items-start gap-3 rounded-lg p-4 mt-4',
        'text-sm text-neutral-600 dark:text-neutral-400 italic',
        config.bgClass,
        className
      )}
    >
      <span className={clsx('flex-shrink-0 mt-0.5', config.iconClass)}>
        {displayIcon}
      </span>
      <p className="leading-relaxed">
        {highlightText(text)}
      </p>
    </div>
  );
}

/**
 * Simple insight text without icon/background
 * Uses the insight-text CSS class
 */
export function InsightText({ text, className }: { text: string; className?: string }) {
  return (
    <p className={clsx('insight-text', className)}>
      {highlightText(text)}
    </p>
  );
}
