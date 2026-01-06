import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import clsx from 'clsx';

// Icon components (inline SVG for better bundle size)
const icons = {
  chart: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 36V12m6 24V20m6 16v-8m6 8V16m6 20V8m6 28V24" />
    </svg>
  ),
  data: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 24h40M4 12h40M4 36h40" />
      <circle cx="12" cy="24" r="2" fill="currentColor" />
      <circle cx="24" cy="12" r="2" fill="currentColor" />
      <circle cx="36" cy="36" r="2" fill="currentColor" />
    </svg>
  ),
  upload: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M24 32V8m0 0l-8 8m8-8l8 8M6 24v16a2 2 0 002 2h32a2 2 0 002-2V24" />
    </svg>
  ),
  search: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <circle cx="20" cy="20" r="12" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M28 28l12 12" />
    </svg>
  ),
  filter: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12h36M12 24h24M18 36h12" />
    </svg>
  ),
  event: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <rect x="6" y="10" width="36" height="32" rx="2" />
      <path strokeLinecap="round" d="M6 18h36M14 6v8M34 6v8" />
      <path strokeLinecap="round" d="M14 26h8M14 34h20" />
    </svg>
  ),
  insight: (
    <svg className="w-12 h-12" fill="none" viewBox="0 0 48 48" stroke="currentColor" strokeWidth={1.5}>
      <circle cx="24" cy="16" r="10" />
      <path strokeLinecap="round" d="M18 30v8a2 2 0 002 2h8a2 2 0 002-2v-8" />
      <path strokeLinecap="round" d="M24 26v6" />
    </svg>
  ),
};

type IconType = keyof typeof icons;

interface EmptyStateProps {
  /** Icon to display */
  icon?: IconType;
  /** Title text */
  title?: string;
  /** Description text */
  description?: string;
  /** Action button text */
  actionText?: string;
  /** Action link path (uses Link component) */
  actionLink?: string;
  /** Action click handler (uses button) */
  onAction?: () => void;
  /** Additional class names */
  className?: string;
  /** Height of the empty state container */
  height?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Unified empty state component for consistent UX across the app.
 * Provides guidance when no data is available.
 */
export function EmptyState({
  icon = 'data',
  title,
  description,
  actionText,
  actionLink,
  onAction,
  className,
  height = 'h-64',
  size = 'md',
}: EmptyStateProps) {
  const { t } = useTranslation();

  const defaultTitle = t('common.noData', '暂无数据');

  const sizeClasses = {
    sm: {
      container: 'p-4',
      icon: 'scale-75',
      title: 'text-sm',
      description: 'text-xs',
      button: 'text-xs px-3 py-1.5',
    },
    md: {
      container: 'p-6',
      icon: 'scale-100',
      title: 'text-base',
      description: 'text-sm',
      button: 'text-sm px-4 py-2',
    },
    lg: {
      container: 'p-8',
      icon: 'scale-125',
      title: 'text-lg',
      description: 'text-base',
      button: 'text-base px-5 py-2.5',
    },
  };

  const sizes = sizeClasses[size];

  const ActionButton = () => {
    if (!actionText) return null;

    const buttonClasses = clsx(
      sizes.button,
      'font-medium rounded-lg transition-all duration-200',
      'bg-blue-600 hover:bg-blue-700 text-white',
      'hover:shadow-lg hover:shadow-blue-500/25',
      'active:scale-[0.98]'
    );

    if (actionLink) {
      return (
        <Link to={actionLink} className={buttonClasses}>
          {actionText}
        </Link>
      );
    }

    if (onAction) {
      return (
        <button onClick={onAction} className={buttonClasses}>
          {actionText}
        </button>
      );
    }

    return null;
  };

  return (
    <div
      className={clsx(
        height,
        sizes.container,
        'flex flex-col items-center justify-center text-center',
        'rounded-lg',
        className
      )}
    >
      {/* Icon */}
      <div
        className={clsx(
          'text-neutral-300 dark:text-neutral-600 mb-4',
          sizes.icon,
          'transition-transform duration-300'
        )}
      >
        {icons[icon]}
      </div>

      {/* Title */}
      <h3
        className={clsx(
          sizes.title,
          'font-medium text-neutral-700 dark:text-neutral-300 mb-1'
        )}
      >
        {title || defaultTitle}
      </h3>

      {/* Description */}
      {description && (
        <p
          className={clsx(
            sizes.description,
            'text-neutral-500 dark:text-neutral-400 max-w-sm mb-4'
          )}
        >
          {description}
        </p>
      )}

      {/* Action */}
      <ActionButton />
    </div>
  );
}

/**
 * Preset empty states for common scenarios
 */
export const EmptyStatePresets = {
  /** No trades data - guide to upload */
  noTrades: (props?: Partial<EmptyStateProps>) => (
    <EmptyState
      icon="upload"
      title="暂无交易数据"
      description="上传您的交易记录开始分析"
      actionText="上传数据"
      actionLink="/upload"
      {...props}
    />
  ),

  /** No results from filter */
  noResults: (props?: Partial<EmptyStateProps>) => (
    <EmptyState
      icon="filter"
      title="没有找到结果"
      description="尝试调整筛选条件"
      {...props}
    />
  ),

  /** No events detected */
  noEvents: (props?: Partial<EmptyStateProps>) => (
    <EmptyState
      icon="event"
      title="暂无事件"
      description="持仓期间未检测到重大市场事件"
      {...props}
    />
  ),

  /** No insights available */
  noInsights: (props?: Partial<EmptyStateProps>) => (
    <EmptyState
      icon="insight"
      title="暂无洞察"
      description="需要更多交易数据才能生成分析"
      {...props}
    />
  ),

  /** Chart has no data */
  noChartData: (props?: Partial<EmptyStateProps>) => (
    <EmptyState
      icon="chart"
      title="暂无图表数据"
      description="该时间段内没有足够的数据"
      height="h-48"
      size="sm"
      {...props}
    />
  ),
};

export default EmptyState;
