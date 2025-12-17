import { isValidElement, cloneElement, type ReactNode, type ReactElement } from 'react';
import clsx from 'clsx';

interface ChartWithInsightProps {
  title?: string;
  chart: ReactNode;
  insight?: string;
  className?: string;
  fullWidth?: boolean;
}

export function ChartWithInsight({ title, chart, insight, className, fullWidth = false }: ChartWithInsightProps) {
  // Clone chart element and pass bare={true} to remove nested card wrapper
  let chartWithBare = chart;
  if (isValidElement(chart)) {
    chartWithBare = cloneElement(chart as ReactElement<{ bare?: boolean }>, { bare: true });
  }

  return (
    <div
      className={clsx(
        'bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800',
        'transition-shadow hover:shadow-sm',
        fullWidth ? 'col-span-2' : '',
        className
      )}
    >
      {/* Chart Title */}
      {title && (
        <div className="px-7 pt-6 pb-3">
          <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
            {title}
          </h3>
        </div>
      )}

      {/* Chart */}
      <div className="px-5 pb-3">
        {chartWithBare}
      </div>

      {/* Insight */}
      {insight && (
        <div className="px-7 pb-6">
          <p className="text-[13px] text-neutral-500 dark:text-neutral-400 leading-relaxed border-l-2 border-neutral-200 dark:border-neutral-700 pl-4 mt-3">
            {insight}
          </p>
        </div>
      )}
    </div>
  );
}
