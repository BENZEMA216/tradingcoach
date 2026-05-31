import { expect, test } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173';
const CURRENT_DIR = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE_CSV = path.resolve(CURRENT_DIR, '../../../tests/fixtures/test_trades.csv');

async function mockSharedApi(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/system/stats', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        database: {
          positions: { count: 0 },
          trades: { count: 0 },
        },
      }),
    });
  });

  await page.route('**/api/v1/upload/history**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    });
  });
}

async function mockSuccessfulPreflight(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/upload/trades/preview', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        can_import: true,
        file_name: 'test_trades.csv',
        file_hash: 'abc',
        broker_id: 'futu_cn',
        broker_name: 'Futu Securities',
        detection_confidence: 1,
        total_rows: 8,
        completed_trades: 7,
        skipped_rows: 1,
        detected_columns: ['股票代码', '成交数量'],
        error_messages: [],
        warning_messages: [],
      }),
    });
  });
}

test.describe('Upload preflight', () => {
  test('Landing gates analysis until csv preflight succeeds', async ({ page }) => {
    await mockSharedApi(page);
    await mockSuccessfulPreflight(page);
    await page.goto(`${BASE_URL}/`);

    const startButton = page.getByTestId('start-analysis-button');
    await expect(startButton).toBeDisabled();

    await page.getByTestId('trade-file-input').setInputFiles(FIXTURE_CSV);
    await expect(page.getByTestId('import-preflight-panel')).toContainText('Futu Securities');
    await expect(page.getByTestId('import-preflight-panel')).toContainText('100%');
    await expect(startButton).toBeEnabled();
  });

  test('Landing blocks spreadsheet uploads with a clear csv-only message', async ({ page }) => {
    await mockSharedApi(page);
    await page.goto(`${BASE_URL}/`);

    const spreadsheet = {
      name: 'orders.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('not a csv'),
    };

    await page.getByTestId('trade-file-input').setInputFiles(spreadsheet);
    await expect(page.getByTestId('import-preflight-panel')).toContainText('orders.xlsx');
    await expect(page.getByTestId('import-preflight-panel')).toContainText(/CSV/i);
    await expect(page.getByTestId('start-analysis-button')).toBeDisabled();
  });

  test('/upload exposes the full upload page and uses the same preflight gate', async ({ page }) => {
    await mockSharedApi(page);
    await mockSuccessfulPreflight(page);
    await page.goto(`${BASE_URL}/upload`);

    await expect(page).toHaveURL(/\/upload$/);
    const startButton = page.getByTestId('start-analysis-button');
    await expect(startButton).toBeDisabled();

    await page.getByTestId('trade-file-input').setInputFiles(FIXTURE_CSV);
    await expect(page.getByTestId('import-preflight-panel')).toContainText('Futu Securities');
    await expect(startButton).toBeEnabled();
  });
});
