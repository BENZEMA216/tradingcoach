import type { ReactNode } from 'react';
import clsx from 'clsx';

interface KPICardProps {
  title: ReactNode;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function KPICard({
  title,
  value,
  subtitle,
  icon,
  trend,
  className,
}: KPICardProps) {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 relative overflow-hidden',
        'transition-all duration-300 ease-out',
        'hover:shadow-lg hover:shadow-neutral-200/50 dark:hover:shadow-neutral-900/50',
        'hover:-translate-y-0.5 hover:border-neutral-200 dark:hover:border-neutral-600',
        className
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
            {title}
          </p>
          <p
            className={clsx(
              'mt-2 text-3xl font-bold truncate transition-colors duration-200',
              trend === 'up' && 'text-profit',
              trend === 'down' && 'text-loss',
              !trend && 'text-gray-900 dark:text-white'
            )}
          >
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 truncate">
              {subtitle}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex-shrink-0 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg transition-transform duration-300 group-hover:scale-110">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
