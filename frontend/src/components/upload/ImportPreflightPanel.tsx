import type { UploadPreflightResponse } from '@/api/client';
import type { TradeImportFileValidation } from '@/utils/importPreflight';
import {
  formatPreflightConfidence,
  getImportPreflightErrorDisplay,
} from '@/utils/importPreflight';
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Table2,
  TriangleAlert,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface ImportPreflightPanelProps {
  selectedFileName: string | null;
  validation: TradeImportFileValidation | null;
  isChecking: boolean;
  result: UploadPreflightResponse | null;
  error?: unknown;
  onRetry?: () => void;
  variant?: 'default' | 'landing';
  className?: string;
}

export function ImportPreflightPanel({
  selectedFileName,
  validation,
  isChecking,
  result,
  error,
  onRetry,
  variant = 'default',
  className = '',
}: ImportPreflightPanelProps) {
  const { t } = useTranslation();
  const errorDisplay = getImportPreflightErrorDisplay(error);
  const hasContent = Boolean(selectedFileName || validation?.valid === false || isChecking || result || errorDisplay);

  if (!hasContent) {
    return null;
  }

  const isLanding = variant === 'landing';
  const shellClass = isLanding
    ? 'bg-white/[0.04] border-white/10 text-white'
    : 'bg-white/80 dark:bg-gray-900/70 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white';
  const mutedClass = isLanding ? 'text-white/55' : 'text-gray-500 dark:text-gray-400';
  const statClass = isLanding
    ? 'bg-black/40 border-white/10'
    : 'bg-gray-50 dark:bg-gray-800/70 border-gray-100 dark:border-gray-700';

  if (validation?.valid === false) {
    return (
      <div
        data-testid="import-preflight-panel"
        className={`rounded-xl border p-4 ${shellClass} ${className}`}
      >
        <div className="flex items-start gap-3">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" />
          <div className="min-w-0">
            <p className="font-semibold">
              {t('importPreflight.unsupportedTitle', 'Unsupported file format')}
            </p>
            <p className={`mt-1 text-sm ${mutedClass}`}>
              {t(
                'importPreflight.csvOnlyMessage',
                'TradingCoach currently supports CSV imports only. Please export a CSV file from your broker.'
              )}
            </p>
            <p className={`mt-2 break-all text-xs ${mutedClass}`}>
              {validation.fileName} ({validation.extension})
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (isChecking) {
    return (
      <div
        data-testid="import-preflight-panel"
        className={`rounded-xl border p-4 ${shellClass} ${className}`}
      >
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 shrink-0 animate-spin text-blue-500" />
          <div>
            <p className="font-semibold">
              {t('importPreflight.checkingTitle', 'Checking import compatibility')}
            </p>
            <p className={`mt-1 text-sm ${mutedClass}`}>
              {t('importPreflight.checkingDesc', 'Detecting broker format without writing data.')}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (errorDisplay) {
    return (
      <div
        data-testid="import-preflight-panel"
        className={`rounded-xl border p-4 ${shellClass} ${className}`}
      >
        <div className="flex items-start gap-3">
          <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
          <div className="min-w-0 flex-1">
            <p className="font-semibold">
              {t(errorDisplay.titleKey, errorDisplay.titleFallback)}
            </p>
            <p className={`mt-1 break-words text-sm ${mutedClass}`}>
              {t(errorDisplay.messageKey, errorDisplay.messageFallback)}
            </p>
            {errorDisplay.detail && (
              <p className={`mt-2 break-words text-xs ${mutedClass}`}>
                {errorDisplay.detail}
              </p>
            )}
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="mt-3 inline-flex items-center gap-2 rounded-lg border border-current px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-950/30"
              >
                <RefreshCw className="h-4 w-4" />
                {t('importPreflight.retry', 'Retry')}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const canImport = result.can_import;
  const messages = [...result.error_messages, ...result.warning_messages];

  return (
    <div
      data-testid="import-preflight-panel"
      className={`rounded-xl border p-4 ${shellClass} ${className}`}
    >
      <div className="flex items-start gap-3">
        {canImport ? (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
        ) : (
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="font-semibold">
              {canImport
                ? t('importPreflight.readyTitle', 'Ready to import')
                : t('importPreflight.blockedTitle', 'File cannot be imported')}
            </p>
            <span className={`break-all text-xs ${mutedClass}`}>{selectedFileName || result.file_name}</span>
          </div>

          {!canImport && (
            <p className={`mt-2 text-sm ${mutedClass}`}>
              {t(
                'importPreflight.blockedHelp',
                "We currently support Futu Securities CSV exports. Try another file, or use “Try Sample Data” above to explore the full experience. Broker not supported? Tell us via the feedback button (bottom-right) and we’ll add it."
              )}
            </p>
          )}

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-4">
            <div className={`rounded-lg border p-3 ${statClass}`}>
              <div className={`flex items-center gap-2 text-xs ${mutedClass}`}>
                <ShieldCheck className="h-4 w-4" />
                {t('importPreflight.broker', 'Broker')}
              </div>
              <p className="mt-1 truncate text-sm font-semibold">
                {result.broker_name || t('importPreflight.unknownBroker', 'Unknown')}
              </p>
            </div>
            <div className={`rounded-lg border p-3 ${statClass}`}>
              <p className={`text-xs ${mutedClass}`}>
                {t('importPreflight.confidence', 'Confidence')}
              </p>
              <p className="mt-1 text-sm font-semibold">
                {formatPreflightConfidence(result.detection_confidence)}
              </p>
            </div>
            <div className={`rounded-lg border p-3 ${statClass}`}>
              <div className={`flex items-center gap-2 text-xs ${mutedClass}`}>
                <Table2 className="h-4 w-4" />
                {t('importPreflight.totalRows', 'Rows')}
              </div>
              <p className="mt-1 text-sm font-semibold">{result.total_rows}</p>
            </div>
            <div className={`rounded-lg border p-3 ${statClass}`}>
              <p className={`text-xs ${mutedClass}`}>
                {t('importPreflight.completedTrades', 'Completed trades')}
              </p>
              <p className="mt-1 text-sm font-semibold">{result.completed_trades}</p>
            </div>
          </div>

          <p className={`mt-3 text-sm ${mutedClass}`}>
            {t('importPreflight.skippedRows', '{{count}} skipped rows', {
              count: result.skipped_rows,
            })}
          </p>

          {canImport && messages.length > 0 && (
            <ul className="mt-3 space-y-1 text-sm text-amber-600 dark:text-amber-400">
              {messages.map((message) => (
                <li key={message}>• {message}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
