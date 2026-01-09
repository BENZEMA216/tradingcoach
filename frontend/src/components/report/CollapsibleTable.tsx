import { useState } from 'react';
import type { ReactNode } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div
      className={clsx(
        'bg-white dark:bg-black rounded-sm border border-neutral-200 dark:border-white/10 overflow-hidden transition-colors',
        className
      )}
    >
      {/* Header - Clickable */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-white/5 transition-colors group"
      >
        <div className="flex items-center gap-3">
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4 text-slate-400 dark:text-white/40 group-hover:text-slate-600 dark:group-hover:text-white" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400 dark:text-white/40 group-hover:text-slate-600 dark:group-hover:text-white" />
          )}
          <div className="text-left">
            <h3 className="text-[10px] font-mono font-bold tracking-[0.2em] uppercase text-slate-700 dark:text-white/80 group-hover:text-slate-900 dark:group-hover:text-white">
              {title}
            </h3>
            {subtitle && (
              <p className="text-[10px] font-mono text-slate-400 dark:text-white/40 mt-1 uppercase tracking-wider">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        <span className="text-[9px] font-mono text-slate-300 dark:text-white/20 uppercase tracking-widest group-hover:text-slate-500 dark:group-hover:text-white/60">
          {isCollapsed ? `[ ${t('common.show', 'SHOW')} ]` : `[ ${t('common.hide', 'HIDE')} ]`}
        </span>
      </button>

      {/* Content */}
      <div
        className={clsx(
          'transition-all duration-200 ease-in-out overflow-hidden',
          isCollapsed ? 'max-h-0' : 'max-h-[2000px]'
        )}
      >
        <div className="border-t border-neutral-200 dark:border-white/10">
          {children}
        </div>
      </div>
    </div>
  );
}
