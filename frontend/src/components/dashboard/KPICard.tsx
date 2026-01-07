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
        'relative overflow-hidden group',
        'bg-white dark:bg-black border border-neutral-200 dark:border-white/10 rounded-sm p-6',
        'hover:border-neutral-300 dark:hover:border-white/20 transition-colors duration-300',
        className
      )}
    >
      <div className="flex items-start justify-between gap-4 relative z-10">
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-mono font-bold text-slate-400 dark:text-white/40 uppercase tracking-[0.2em] mb-2">
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <p
              className={clsx(
                'text-3xl font-mono font-medium tracking-tighter transition-colors duration-200',
                trend === 'up' && 'text-green-600 dark:text-green-500',
                trend === 'down' && 'text-red-600 dark:text-red-500',
                !trend && 'text-slate-900 dark:text-white'
              )}
            >
              {value}
            </p>
          </div>
          {subtitle && (
            <p className="mt-2 text-xs font-mono text-slate-400 dark:text-white/30 truncate flex items-center gap-1">
              {subtitle}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex-shrink-0 p-3 bg-neutral-100 dark:bg-white/5 rounded-sm border border-neutral-200 dark:border-white/5 group-hover:bg-neutral-200 dark:group-hover:bg-white/10 group-hover:border-neutral-300 dark:group-hover:border-white/10 transition-all duration-300">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
