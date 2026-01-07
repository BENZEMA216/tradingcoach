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
        'bg-white dark:bg-black rounded-sm shadow-sm dark:shadow-none',
        'border border-neutral-200 dark:border-white/20',
        'px-3 py-2 text-xs font-mono transition-colors',
        className
      )}
    >
      {/* Title */}
      {title && (
        <p className="font-bold text-slate-900 dark:text-white mb-2 text-[10px] uppercase tracking-widest border-b border-neutral-100 dark:border-white/10 pb-1">
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
                  className="w-1.5 h-1.5 rounded-none flex-shrink-0"
                  style={{ backgroundColor: item.color }}
                />
              )}
              <span className="text-slate-500 dark:text-white/60 uppercase tracking-wider text-[10px]">
                {item.label}
              </span>
            </div>
            <span className="font-bold text-slate-900 dark:text-white tabular-nums tracking-tight">
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
