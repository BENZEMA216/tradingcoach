import { useState } from 'react';
import type { ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface CollapsibleTableProps {
  title: string;
  subtitle?: string;
  defaultCollapsed?: boolean;
  children: ReactNode;
  className?: string;
}

export function CollapsibleTable({
  title,
  subtitle,
  defaultCollapsed = true,
  children,
  className,
}: CollapsibleTableProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div
      className={clsx(
        'bg-white dark:bg-neutral-900 rounded-lg border border-neutral-200 dark:border-neutral-800 overflow-hidden',
        className
      )}
    >
      {/* Header - Clickable */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-neutral-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-neutral-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-neutral-400" />
          )}
          <div className="text-left">
            <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        <span className="text-xs text-neutral-400 dark:text-neutral-500">
          {isCollapsed ? 'Show' : 'Hide'}
        </span>
      </button>

      {/* Content */}
      <div
        className={clsx(
          'transition-all duration-200 ease-in-out overflow-hidden',
          isCollapsed ? 'max-h-0' : 'max-h-[2000px]'
        )}
      >
        <div className="border-t border-neutral-200 dark:border-neutral-800">
          {children}
        </div>
      </div>
    </div>
  );
}
