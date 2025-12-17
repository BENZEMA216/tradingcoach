import clsx from 'clsx';

export interface TooltipItem {
  label: string;
  value: string | number;
  color?: string;
  prefix?: string;
  suffix?: string;
}

interface ChartTooltipProps {
  active?: boolean;
  title?: string;
  items?: TooltipItem[];
  footer?: string;
  className?: string;
}

/**
 * Unified tooltip component for Recharts
 * Use as a custom content renderer for Recharts Tooltip
 */
export function ChartTooltip({
  active,
  title,
  items = [],
  footer,
  className,
}: ChartTooltipProps) {
  if (!active || items.length === 0) {
    return null;
  }

  return (
    <div
      className={clsx(
        'bg-white dark:bg-neutral-800 rounded-lg shadow-lg',
        'border border-neutral-200 dark:border-neutral-700',
        'px-3 py-2.5 text-sm',
        className
      )}
    >
      {/* Title */}
      {title && (
        <p className="font-medium text-neutral-900 dark:text-neutral-100 mb-1.5 text-xs uppercase tracking-wide">
          {title}
        </p>
      )}

      {/* Items */}
      <div className="space-y-1">
        {items.map((item, index) => (
          <div key={index} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {item.color && (
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: item.color }}
                />
              )}
              <span className="text-neutral-600 dark:text-neutral-400">
                {item.label}
              </span>
            </div>
            <span className="font-medium text-neutral-900 dark:text-neutral-100 tabular-nums">
              {item.prefix}
              {typeof item.value === 'number' ? item.value.toLocaleString() : item.value}
              {item.suffix}
            </span>
          </div>
        ))}
      </div>

      {/* Footer */}
      {footer && (
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-2 pt-2 border-t border-neutral-200 dark:border-neutral-700">
          {footer}
        </p>
      )}
    </div>
  );
}

/**
 * Helper to create a Recharts-compatible custom tooltip renderer
 */
export function createTooltipRenderer(
  formatter: (payload: unknown[], label: string) => {
    title?: string;
    items: TooltipItem[];
    footer?: string;
  }
) {
  return function CustomTooltip({
    active,
    payload,
    label,
  }: {
    active?: boolean;
    payload?: unknown[];
    label?: string;
  }) {
    if (!active || !payload || payload.length === 0) {
      return null;
    }

    const { title, items, footer } = formatter(payload, label || '');

    return (
      <ChartTooltip
        active={active}
        title={title}
        items={items}
        footer={footer}
      />
    );
  };
}

/**
 * Pre-built formatter for simple value tooltips
 */
export function simpleTooltipFormatter(
  labelKey: string,
  valueKey: string,
  options?: {
    color?: string;
    prefix?: string;
    suffix?: string;
    formatValue?: (value: number) => string;
  }
) {
  return (payload: unknown[]) => {
    const data = (payload[0] as { payload?: Record<string, unknown> })?.payload;
    if (!data) return { items: [] };

    const value = data[valueKey] as number;
    const label = data[labelKey] as string;

    return {
      title: label,
      items: [
        {
          label: valueKey,
          value: options?.formatValue ? options.formatValue(value) : value,
          color: options?.color,
          prefix: options?.prefix,
          suffix: options?.suffix,
        },
      ],
    };
  };
}
