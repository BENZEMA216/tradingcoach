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
        'bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 transition-colors',
        'transition-colors duration-300',
        'hover:border-neutral-300 dark:hover:border-white/20',
        fullWidth ? 'col-span-2' : '',
        className
      )}
    >
      {/* Chart Title */}
      {title && (
        <div className="px-6 pt-5 pb-2 border-b border-neutral-100 dark:border-white/5 mb-4">
          <h3 className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-widest">
            {title}
          </h3>
        </div>
      )}

      {/* Chart */}
      <div className="px-5 pb-5">
        {chartWithBare}
      </div>

      {/* Insight */}
      {insight && (
        <div className="px-6 pb-6 pt-2 border-t border-neutral-100 dark:border-white/5">
          <p className="text-xs font-mono text-slate-500 dark:text-white/50 leading-relaxed pl-2 border-l border-neutral-300 dark:border-white/20">
            {insight}
          </p>
        </div>
      )}
    </div>
  );
}
