import clsx from 'clsx';

interface ChartSkeletonProps {
  /** Height of the skeleton (default: h-72) */
  height?: string;
  /** Show title skeleton */
  showTitle?: boolean;
  /** Show stats skeleton */
  showStats?: boolean;
  /** Number of stat items to show */
  statsCount?: number;
  /** Custom class name */
  className?: string;
  /** Variant: 'default' for chart, 'table' for table loading */
  variant?: 'default' | 'table' | 'card';
}

/**
 * Unified loading skeleton for charts and data visualizations.
 * Provides consistent loading experience across the app.
 */
export function ChartSkeleton({
  height = 'h-72',
  showTitle = true,
  showStats = true,
  statsCount = 2,
  className,
  variant = 'default',
}: ChartSkeletonProps) {
  if (variant === 'table') {
    return (
      <div className={clsx('animate-pulse', className)}>
        {showTitle && (
          <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-700 rounded mb-4" />
        )}
        <div className="space-y-3">
          {/* Header row */}
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-4 bg-neutral-200 dark:bg-neutral-700 rounded" />
            ))}
          </div>
          {/* Data rows */}
          {[1, 2, 3, 4, 5].map((row) => (
            <div key={row} className="grid grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((col) => (
                <div
                  key={col}
                  className="h-4 bg-neutral-100 dark:bg-neutral-800 rounded"
                  style={{ opacity: 1 - row * 0.15 }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className={clsx('animate-pulse', className)}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-neutral-100 dark:bg-neutral-800 rounded-lg p-4"
            >
              <div className="h-3 w-16 bg-neutral-200 dark:bg-neutral-700 rounded mb-2" />
              <div className="h-6 w-24 bg-neutral-200 dark:bg-neutral-700 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default chart skeleton
  return (
    <div className={clsx('animate-pulse', className)}>
      {/* Title and stats row */}
      {(showTitle || showStats) && (
        <div className="flex items-center justify-between mb-4">
          {showTitle && (
            <div className="h-5 w-32 bg-neutral-200 dark:bg-neutral-700 rounded" />
          )}
          {showStats && (
            <div className="flex items-center gap-4">
              {Array.from({ length: statsCount }).map((_, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="h-3 w-12 bg-neutral-200 dark:bg-neutral-700 rounded" />
                  <div className="h-4 w-16 bg-neutral-200 dark:bg-neutral-700 rounded" />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Chart area with simulated grid lines */}
      <div
        className={clsx(
          height,
          'bg-neutral-100 dark:bg-neutral-800/50 rounded-lg relative overflow-hidden'
        )}
      >
        {/* Simulated horizontal grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between py-4 px-4">
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-full h-px bg-neutral-200 dark:bg-neutral-700"
              style={{ opacity: 0.5 }}
            />
          ))}
        </div>

        {/* Simulated chart line (wave pattern) */}
        <div className="absolute bottom-0 left-0 right-0 h-1/2">
          <svg
            className="w-full h-full"
            viewBox="0 0 100 50"
            preserveAspectRatio="none"
          >
            <path
              d="M0,40 Q10,35 20,30 T40,25 T60,20 T80,25 T100,15"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-neutral-300 dark:text-neutral-600"
            />
          </svg>
        </div>

        {/* Shimmer effect */}
        <div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 dark:via-white/5 to-transparent"
          style={{
            animation: 'shimmer 2s infinite',
          }}
        />
      </div>

      {/* Legend skeleton */}
      <div className="flex items-center justify-center gap-6 mt-3">
        {[1, 2].map((i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="h-3 w-3 bg-neutral-200 dark:bg-neutral-700 rounded" />
            <div className="h-3 w-12 bg-neutral-200 dark:bg-neutral-700 rounded" />
          </div>
        ))}
      </div>

      {/* Add shimmer animation keyframes */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}

/**
 * Mini skeleton for inline loading states
 */
export function InlineSkeleton({
  width = 'w-16',
  height = 'h-4',
  className,
}: {
  width?: string;
  height?: string;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        'bg-neutral-200 dark:bg-neutral-700 rounded animate-pulse',
        width,
        height,
        className
      )}
    />
  );
}

export default ChartSkeleton;
