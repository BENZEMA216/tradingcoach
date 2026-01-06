import type { ReactNode } from 'react';
import clsx from 'clsx';

interface ReportSectionProps {
  number: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  className?: string;
}

export function ReportSection({ number, title, subtitle, children, className }: ReportSectionProps) {
  return (
    <section className={clsx('report-section animate-fade-in', className)}>
      {/* Section Header */}
      <div className="mb-10">
        <div className="flex items-baseline gap-3 mb-2">
          <span className="text-[11px] font-medium tracking-[0.2em] text-neutral-400 dark:text-neutral-500 transition-colors duration-200">
            {number}
          </span>
          <span className="text-[11px] font-medium tracking-widest text-neutral-300 dark:text-neutral-600">
            /
          </span>
          <span className="text-[11px] font-semibold tracking-[0.15em] uppercase text-neutral-800 dark:text-neutral-200 transition-colors duration-200">
            {title}
          </span>
        </div>
        <h2 className="text-lg font-medium text-neutral-600 dark:text-neutral-400">
          {subtitle}
        </h2>
        <div className="mt-4 h-[0.5px] bg-neutral-200/70 dark:bg-neutral-700/50 transition-all duration-500" />
      </div>

      {/* Section Content */}
      <div className="space-y-8">
        {children}
      </div>
    </section>
  );
}
