import { useState, useRef } from 'react';
import type { ReactNode, RefObject } from 'react';
import { Download, Maximize2, ExternalLink, MoreHorizontal } from 'lucide-react';
import clsx from 'clsx';

export type ChartAction = 'export' | 'fullscreen' | 'drilldown';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onDrillDown?: () => void;
  onExport?: (ref: RefObject<HTMLDivElement | null>) => void;
  onFullscreen?: (ref: RefObject<HTMLDivElement | null>) => void;
  loading?: boolean;
  actions?: ChartAction[];
  className?: string;
  height?: string;
  insight?: string;
}

export function ChartContainer({
  title,
  subtitle,
  children,
  onDrillDown,
  onExport,
  onFullscreen,
  loading = false,
  actions = [],
  className,
  height = 'h-64',
  insight,
}: ChartContainerProps) {
  const [showActions, setShowActions] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  const hasActions = actions.length > 0;

  const handleExport = () => {
    if (onExport) {
      onExport(chartRef);
    }
  };

  const handleFullscreen = () => {
    if (onFullscreen) {
      onFullscreen(chartRef);
    }
  };

  return (
    <div
      className={clsx(
        'bg-white dark:bg-neutral-900 rounded-xl border border-neutral-200 dark:border-neutral-800',
        'transition-shadow hover:shadow-sm',
        className
      )}
    >
      {/* Header */}
      <div className="px-6 pt-5 pb-3 flex items-start justify-between">
        <div>
          <h3 className="text-[13px] font-semibold text-neutral-800 dark:text-neutral-200 tracking-wide">
            {title}
          </h3>
          {subtitle && (
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
              {subtitle}
            </p>
          )}
        </div>

        {/* Actions */}
        {hasActions && (
          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-1.5 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md transition-colors"
              aria-label="Chart actions"
            >
              <MoreHorizontal className="w-4 h-4 text-neutral-400" />
            </button>

            {showActions && (
              <>
                {/* Backdrop */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowActions(false)}
                />
                {/* Dropdown */}
                <div className="absolute right-0 top-full mt-1 z-20 bg-white dark:bg-neutral-800 rounded-lg shadow-lg border border-neutral-200 dark:border-neutral-700 py-1 min-w-[140px]">
                  {actions.includes('export') && (
                    <button
                      onClick={() => {
                        handleExport();
                        setShowActions(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Export PNG
                    </button>
                  )}
                  {actions.includes('fullscreen') && (
                    <button
                      onClick={() => {
                        handleFullscreen();
                        setShowActions(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2"
                    >
                      <Maximize2 className="w-4 h-4" />
                      Fullscreen
                    </button>
                  )}
                  {actions.includes('drilldown') && onDrillDown && (
                    <button
                      onClick={() => {
                        onDrillDown();
                        setShowActions(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 flex items-center gap-2"
                    >
                      <ExternalLink className="w-4 h-4" />
                      View Details
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Chart Area */}
      <div ref={chartRef} className={clsx('px-4 pb-4', height)}>
        {loading ? (
          <div className="w-full h-full flex items-center justify-center">
            <div className="animate-pulse flex flex-col items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-neutral-200 dark:bg-neutral-700" />
              <div className="w-24 h-2 rounded bg-neutral-200 dark:bg-neutral-700" />
            </div>
          </div>
        ) : (
          children
        )}
      </div>

      {/* Insight */}
      {insight && (
        <div className="px-6 pb-5 border-t border-neutral-100 dark:border-neutral-800">
          <p className="insight-text mt-4">
            {insight}
          </p>
        </div>
      )}
    </div>
  );
}
