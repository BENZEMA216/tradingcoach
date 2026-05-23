import { describe, expect, it } from 'vitest';
import {
  formatPreflightConfidence,
  getImportPreflightErrorDisplay,
  isTradeImportReady,
  validateTradeImportFile,
} from './importPreflight';

function makeFile(name: string, size = 128): File {
  return new File(['x'.repeat(size)], name, { type: 'text/csv' });
}

describe('trade import preflight utilities', () => {
  it('accepts csv files case-insensitively', () => {
    expect(validateTradeImportFile(makeFile('orders.csv'))).toEqual({ valid: true });
    expect(validateTradeImportFile(makeFile('orders.CSV'))).toEqual({ valid: true });
  });

  it('blocks spreadsheet files until backend parsing supports them', () => {
    expect(validateTradeImportFile(makeFile('orders.xlsx'))).toMatchObject({
      valid: false,
      code: 'unsupported_extension',
      extension: '.xlsx',
      fileName: 'orders.xlsx',
    });
    expect(validateTradeImportFile(makeFile('orders.xls'))).toMatchObject({
      valid: false,
      code: 'unsupported_extension',
      extension: '.xls',
      fileName: 'orders.xls',
    });
  });

  it('requires a successful preflight before import can start', () => {
    expect(
      isTradeImportReady({
        selectedFile: makeFile('orders.csv'),
        validation: { valid: true },
        preflight: {
          can_import: true,
          file_name: 'orders.csv',
          file_hash: 'abc',
          broker_id: 'futu_cn',
          broker_name: 'Futu Securities',
          detection_confidence: 0.92,
          total_rows: 10,
          completed_trades: 8,
          skipped_rows: 2,
          detected_columns: [],
          error_messages: [],
          warning_messages: [],
        },
        isChecking: false,
        isSubmitting: false,
        isEmailValid: true,
      })
    ).toBe(true);

    expect(
      isTradeImportReady({
        selectedFile: makeFile('orders.csv'),
        validation: { valid: true },
        preflight: null,
        isChecking: false,
        isSubmitting: false,
        isEmailValid: true,
      })
    ).toBe(false);
  });

  it('formats broker detection confidence as a percentage', () => {
    expect(formatPreflightConfidence(0.923)).toBe('92%');
    expect(formatPreflightConfidence(1)).toBe('100%');
  });

  it('turns network failures into actionable preflight guidance', () => {
    const display = getImportPreflightErrorDisplay({
      isAxiosError: true,
      code: 'ERR_NETWORK',
      message: 'Network Error',
    });

    expect(display.titleFallback).toBe('Cannot reach import preview service');
    expect(display.messageFallback).toContain('backend service is running');
  });

  it('explains stale backends that do not expose the preflight endpoint', () => {
    const display = getImportPreflightErrorDisplay({
      isAxiosError: true,
      message: 'Request failed with status code 404',
      response: {
        status: 404,
        data: { detail: 'Not Found' },
      },
    });

    expect(display.titleFallback).toBe('Import preview service is not available');
    expect(display.messageFallback).toContain('current backend does not include');
  });
});
