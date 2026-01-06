import { useEffect, useCallback, cloneElement, isValidElement } from 'react';
import type { ReactNode, ReactElement } from 'react';
import { X, Download } from 'lucide-react';
import clsx from 'clsx';

interface FullscreenModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  children: ReactNode;
  onExport?: () => void;
}

/**
 * Fullscreen modal for displaying charts in expanded view
 * Automatically resizes chart children to fill the modal
 */
export function FullscreenModal({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  onExport,
}: FullscreenModalProps) {
  // Handle ESC key
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
      };
    }
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  // Clone children to pass fullscreen dimensions if they accept width/height
  const enhancedChildren = isValidElement(children)
    ? cloneElement(children as ReactElement<{ width?: number | string; height?: number | string }>, {
        width: '100%',
        height: '100%',
      })
    : children;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 z-40 transition-opacity backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
        <div
          className={clsx(
            'bg-white dark:bg-neutral-900 rounded-xl shadow-2xl',
            'w-full h-full max-w-[95vw] max-h-[90vh]',
            'flex flex-col',
            'animate-in fade-in zoom-in-95 duration-200'
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-800 flex-shrink-0">
            <div>
              <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                {title}
              </h2>
              {subtitle && (
                <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
                  {subtitle}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {onExport && (
                <button
                  onClick={onExport}
                  className={clsx(
                    'flex items-center gap-2 px-3 py-2',
                    'text-sm text-neutral-600 dark:text-neutral-300',
                    'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                    'rounded-lg transition-colors'
                  )}
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Export</span>
                </button>
              )}
              <button
                onClick={onClose}
                className={clsx(
                  'p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300',
                  'hover:bg-neutral-100 dark:hover:bg-neutral-800',
                  'rounded-lg transition-colors'
                )}
                aria-label="Close fullscreen"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Content - Chart Area */}
          <div className="flex-1 p-6 overflow-hidden">
            <div className="w-full h-full">
              {enhancedChildren}
            </div>
          </div>

          {/* Footer with ESC hint */}
          <div className="px-6 py-3 border-t border-neutral-200 dark:border-neutral-800 flex-shrink-0">
            <p className="text-xs text-neutral-400 dark:text-neutral-500 text-center">
              Press <kbd className="px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 font-mono text-xs">ESC</kbd> to close
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
