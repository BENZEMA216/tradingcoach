import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ImportPreflightPanel } from './ImportPreflightPanel';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (_key: string, fallback: string, params?: Record<string, string | number>) =>
      fallback.replace('{{count}}', String(params?.count ?? '')),
  }),
}));

describe('ImportPreflightPanel', () => {
  it('shows broker match and import counts for a supported csv', () => {
    render(
      <ImportPreflightPanel
        selectedFileName="orders.csv"
        validation={{ valid: true }}
        isChecking={false}
        result={{
          can_import: true,
          file_name: 'orders.csv',
          file_hash: 'abc',
          broker_id: 'futu_cn',
          broker_name: 'Futu Securities',
          detection_confidence: 0.95,
          total_rows: 12,
          completed_trades: 10,
          skipped_rows: 2,
          detected_columns: ['股票代码', '成交数量'],
          error_messages: [],
          warning_messages: ['2 rows skipped'],
        }}
      />
    );

    expect(screen.getByTestId('import-preflight-panel')).toBeInTheDocument();
    expect(screen.getByText('Futu Securities')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByTestId('import-preflight-panel')).toHaveTextContent('2 rows skipped');
  });

  it('shows a blocking message for xlsx files', () => {
    render(
      <ImportPreflightPanel
        selectedFileName={null}
        validation={{
          valid: false,
          code: 'unsupported_extension',
          extension: '.xlsx',
          fileName: 'orders.xlsx',
        }}
        isChecking={false}
        result={null}
      />
    );

    expect(screen.getByTestId('import-preflight-panel')).toBeInTheDocument();
    expect(screen.getByText(/CSV/)).toBeInTheDocument();
    expect(screen.getByTestId('import-preflight-panel')).toHaveTextContent('orders.xlsx');
  });

  it('shows actionable copy when the preview service cannot be reached', () => {
    render(
      <ImportPreflightPanel
        selectedFileName="orders.csv"
        validation={{ valid: true }}
        isChecking={false}
        result={null}
        error={{
          isAxiosError: true,
          code: 'ERR_NETWORK',
          message: 'Network Error',
        }}
      />
    );

    expect(screen.getByTestId('import-preflight-panel')).toHaveTextContent(
      'Cannot reach import preview service'
    );
    expect(screen.getByTestId('import-preflight-panel')).toHaveTextContent(
      'backend service is running'
    );
  });
});
