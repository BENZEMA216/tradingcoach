import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Info, X } from 'lucide-react';

interface InfoTooltipProps {
  termKey: string;
  size?: 'xs' | 'sm' | 'md';
}

export function InfoTooltip({ termKey, size = 'sm' }: InfoTooltipProps) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Get glossary term data
  const term = t(`glossary.${termKey}.term`, { defaultValue: termKey });
  const fullName = t(`glossary.${termKey}.fullName`, { defaultValue: '' });
  const description = t(`glossary.${termKey}.description`, { defaultValue: '' });

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Don't render if no description available
  if (!description) {
    return null;
  }

  const iconSize = size === 'xs' ? 'w-3 h-3' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  return (
    <span className="relative inline-flex items-center ml-1">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center justify-center
                   text-gray-400 hover:text-blue-500
                   dark:text-gray-500 dark:hover:text-blue-400
                   transition-colors rounded-full
                   hover:bg-gray-100 dark:hover:bg-gray-700
                   p-0.5`}
        aria-label={t('common.infoAbout', { term, defaultValue: `Info about ${term}` })}
      >
        <Info className={iconSize} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop for mobile */}
          <div
            className="fixed inset-0 bg-black/20 z-40 md:hidden"
            onClick={() => setIsOpen(false)}
          />

          {/* Tooltip content */}
          <div
            ref={tooltipRef}
            className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2
                       w-72 md:w-80
                       bg-white dark:bg-gray-800
                       rounded-lg shadow-xl
                       border border-gray-200 dark:border-gray-700
                       animate-in fade-in zoom-in-95 duration-200"
          >
            {/* Arrow */}
            <div className="absolute left-1/2 -translate-x-1/2 -bottom-2
                           w-4 h-4 rotate-45
                           bg-white dark:bg-gray-800
                           border-r border-b border-gray-200 dark:border-gray-700" />

            {/* Content */}
            <div className="relative p-4">
              {/* Close button */}
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-2 right-2 p-1
                         text-gray-400 hover:text-gray-600
                         dark:text-gray-500 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>

              {/* Term and full name */}
              <div className="pr-6">
                <h4 className="font-semibold text-gray-900 dark:text-white">
                  {term}
                </h4>
                {fullName && fullName !== term && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {fullName}
                  </p>
                )}
              </div>

              {/* Description */}
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {description}
              </p>
            </div>
          </div>
        </>
      )}
    </span>
  );
}

// Component that renders a term with its info tooltip
interface TermWithInfoProps {
  termKey: string;
  children?: React.ReactNode;
  className?: string;
}

export function TermWithInfo({ termKey, children, className = '' }: TermWithInfoProps) {
  const { t } = useTranslation();
  const term = t(`glossary.${termKey}.term`, { defaultValue: termKey });

  return (
    <span className={`inline-flex items-center ${className}`}>
      <span>{children || term}</span>
      <InfoTooltip termKey={termKey} />
    </span>
  );
}
