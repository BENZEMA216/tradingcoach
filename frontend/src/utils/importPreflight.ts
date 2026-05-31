import type { UploadPreflightResponse } from '@/api/client';

export type TradeImportFileValidation =
  | { valid: true }
  | {
      valid: false;
      code: 'unsupported_extension';
      extension: string;
      fileName: string;
    };

export interface TradeImportReadyInput {
  selectedFile: File | null;
  validation: TradeImportFileValidation | null;
  preflight: UploadPreflightResponse | null;
  isChecking: boolean;
  isSubmitting: boolean;
  isEmailValid: boolean;
}

export interface ImportPreflightErrorDisplay {
  titleKey: string;
  titleFallback: string;
  messageKey: string;
  messageFallback: string;
  detail?: string;
}

interface AxiosLikeError {
  isAxiosError?: boolean;
  code?: string;
  message?: string;
  response?: {
    status?: number;
    data?: unknown;
  };
}

function getFileExtension(fileName: string): string {
  const match = /\.[^./\\]+$/.exec(fileName);
  return match ? match[0].toLowerCase() : '';
}

export function validateTradeImportFile(file: File): TradeImportFileValidation {
  const extension = getFileExtension(file.name);

  if (extension === '.csv') {
    return { valid: true };
  }

  return {
    valid: false,
    code: 'unsupported_extension',
    extension: extension || 'unknown',
    fileName: file.name,
  };
}

export function isTradeImportReady(input: TradeImportReadyInput): boolean {
  return Boolean(
    input.selectedFile &&
      input.validation?.valid &&
      input.preflight?.can_import &&
      !input.isChecking &&
      !input.isSubmitting &&
      input.isEmailValid
  );
}

export function formatPreflightConfidence(confidence: number | null | undefined): string {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) {
    return '--';
  }

  const clamped = Math.min(1, Math.max(0, confidence));
  return `${Math.round(clamped * 100)}%`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function getResponseDetail(data: unknown): string | null {
  if (typeof data === 'string') return data;
  if (!isRecord(data)) return null;

  const detail = data.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => String(item)).join(', ');

  return null;
}

function asAxiosLikeError(error: unknown): AxiosLikeError | null {
  return isRecord(error) ? error : null;
}

export function getImportPreflightErrorDisplay(error: unknown): ImportPreflightErrorDisplay | null {
  if (!error) return null;

  const axiosError = asAxiosLikeError(error);
  const message = axiosError?.message || (error instanceof Error ? error.message : String(error));
  const status = axiosError?.response?.status;
  const detail = getResponseDetail(axiosError?.response?.data);
  const isNetworkFailure =
    axiosError?.code === 'ERR_NETWORK' ||
    message === 'Network Error' ||
    (axiosError?.isAxiosError && !axiosError.response);

  if (isNetworkFailure) {
    return {
      titleKey: 'importPreflight.networkTitle',
      titleFallback: 'Cannot reach import preview service',
      messageKey: 'importPreflight.networkMessage',
      messageFallback:
        'Please confirm the backend service is running, then retry. No trade data was imported.',
      detail: message,
    };
  }

  if (status === 404) {
    return {
      titleKey: 'importPreflight.missingEndpointTitle',
      titleFallback: 'Import preview service is not available',
      messageKey: 'importPreflight.missingEndpointMessage',
      messageFallback:
        'The current backend does not include the import preview endpoint. Restart the backend with the latest code, then retry.',
      detail: detail || message,
    };
  }

  if (status && status >= 500) {
    return {
      titleKey: 'importPreflight.serverTitle',
      titleFallback: 'Import preview service failed',
      messageKey: 'importPreflight.serverMessage',
      messageFallback:
        'The backend returned an error while checking this file. Please retry after the service recovers.',
      detail: detail || message,
    };
  }

  if (detail) {
    return {
      titleKey: 'importPreflight.failedTitle',
      titleFallback: 'Preflight check failed',
      messageKey: 'importPreflight.fileMessage',
      messageFallback: detail,
    };
  }

  return {
    titleKey: 'importPreflight.failedTitle',
    titleFallback: 'Preflight check failed',
    messageKey: 'importPreflight.unknownMessage',
    messageFallback: message || 'Unknown error',
  };
}

export function getImportPreflightErrorMessage(error: unknown): string | null {
  return getImportPreflightErrorDisplay(error)?.messageFallback ?? null;
}
