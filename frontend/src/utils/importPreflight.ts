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

export function getImportPreflightErrorMessage(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof Error) return error.message;
  return String(error);
}
