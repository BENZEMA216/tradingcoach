import clsx from 'clsx';
import { getGradeBadgeClass, isIncompleteGrade } from '@/utils/format';
import { InfoTooltip } from './InfoTooltip';

interface GradeBadgeProps {
  grade: string | null | undefined;
  size?: 'xs' | 'sm' | 'md';
  showIncompleteInfo?: boolean;
  className?: string;
}

const sizeClasses = {
  xs: 'px-1.5 py-0.5 text-[10px]',
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-lg',
};

export function GradeBadge({
  grade,
  size = 'xs',
  showIncompleteInfo = false,
  className,
}: GradeBadgeProps) {
  const incomplete = isIncompleteGrade(grade);

  return (
    <span className="inline-flex items-center justify-center gap-1">
      <span
        className={clsx(
          'font-bold rounded-sm border',
          sizeClasses[size],
          getGradeBadgeClass(grade),
          incomplete && 'border-dashed',
          className
        )}
      >
        {grade || '-'}
      </span>
      {showIncompleteInfo && incomplete && (
        <InfoTooltip termKey="scoreGradeIncomplete" size="xs" />
      )}
    </span>
  );
}
