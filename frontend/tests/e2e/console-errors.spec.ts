/**
 * Console Error Monitoring Tests - 控制台错误监控测试
 *
 * input: All frontend pages
 * output: Console error detection and reporting
 * pos: E2E 测试 - 确保页面无 JavaScript 错误
 *
 * Run: npx playwright test tests/e2e/console-errors.spec.ts --project=chromium
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { test, expect } from '@playwright/test';
import { ConsoleErrorCollector, waitForNetworkIdle } from './helpers/test-utils';

const BASE_URL = 'http://localhost:5173';

// Pages to test
const PAGES = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Statistics', path: '/statistics' },
  { name: 'Positions', path: '/positions' },
  { name: 'Upload', path: '/upload' },
  { name: 'System', path: '/system' },
  { name: 'AI Coach', path: '/ai-coach' },
];

// Known benign errors to filter out
const IGNORED_ERRORS = [
  'ResizeObserver loop',
  'favicon.ico',
  'net::ERR_FAILED',
  'Failed to load resource',
  // Add more patterns as needed
];

function isIgnoredError(errorText: string): boolean {
  return IGNORED_ERRORS.some(pattern => errorText.includes(pattern));
}

test.describe('Console Error Monitoring', () => {
  for (const pageInfo of PAGES) {
    test(`${pageInfo.name} page has no console errors`, async ({ page }) => {
      const consoleCollector = new ConsoleErrorCollector(page);

      await page.goto(`${BASE_URL}${pageInfo.path}`);
      await waitForNetworkIdle(page);

      // Wait additional time for async operations
      await page.waitForTimeout(2000);

      // Filter errors
      const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));

      // Report
      if (errors.length > 0) {
        console.log(`\n❌ Errors on ${pageInfo.name}:`);
        errors.forEach((e, i) => {
          console.log(`  ${i + 1}. ${e.text}`);
        });
      }

      expect(errors.length).toBe(0);
    });
  }
});

test.describe('Console Error Monitoring - User Interactions', () => {
  test('Dashboard interactions produce no errors', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Interact with the page
    // Click on navigation items
    const navLinks = page.locator('nav a, aside a');
    const navCount = await navLinks.count();

    if (navCount > 0) {
      await navLinks.first().click();
      await waitForNetworkIdle(page);
    }

    const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));
    expect(errors.length).toBe(0);
  });

  test('Statistics chart interactions produce no errors', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000);

    // Hover over charts
    const charts = page.locator('.recharts-surface');
    const chartCount = await charts.count();

    for (let i = 0; i < Math.min(chartCount, 3); i++) {
      await charts.nth(i).hover();
      await page.waitForTimeout(300);
    }

    const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));
    expect(errors.length).toBe(0);
  });

  test('Positions table interactions produce no errors', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    // Click on table rows
    const rows = page.locator('tbody tr');
    const rowCount = await rows.count();

    if (rowCount > 0) {
      await rows.first().click();
      await waitForNetworkIdle(page);

      // Go back
      const backButton = page.getByText(/Back|返回/);
      if (await backButton.isVisible()) {
        await backButton.click();
        await waitForNetworkIdle(page);
      }
    }

    const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));
    expect(errors.length).toBe(0);
  });

  test('Dark mode toggle produces no errors', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Toggle dark mode via localStorage
    await page.evaluate(() => {
      const currentTheme = localStorage.getItem('theme');
      localStorage.setItem('theme', currentTheme === 'dark' ? 'light' : 'dark');
    });

    await page.reload();
    await waitForNetworkIdle(page);

    const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));
    expect(errors.length).toBe(0);
  });

  test('Language switch produces no errors', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Switch language
    await page.evaluate(() => {
      const currentLang = localStorage.getItem('i18nextLng') || 'en';
      localStorage.setItem('i18nextLng', currentLang === 'en' ? 'zh' : 'en');
    });

    await page.reload();
    await waitForNetworkIdle(page);

    const errors = consoleCollector.getErrors().filter(e => !isIgnoredError(e.text));
    expect(errors.length).toBe(0);
  });
});

test.describe('Console Error Monitoring - API Failures', () => {
  test('Handles API timeout gracefully', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    // Slow down API responses
    await page.route('**/api/**', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 5000));
      await route.continue();
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(2000);

    // Should not crash - check for unhandled errors
    const criticalErrors = consoleCollector.getErrors().filter(e =>
      e.text.includes('Uncaught') || e.text.includes('Unhandled')
    );

    expect(criticalErrors.length).toBe(0);
  });

  test('Handles API 500 error gracefully', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    // Mock API to return 500
    await page.route('**/api/v1/dashboard/**', (route) => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal Server Error' }),
      });
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Page should not crash
    await expect(page.locator('body')).toBeVisible();

    // Check for unhandled errors
    const criticalErrors = consoleCollector.getErrors().filter(e =>
      e.text.includes('Uncaught') || e.text.includes('Unhandled')
    );

    expect(criticalErrors.length).toBe(0);
  });
});

test.describe('Console Warning Analysis', () => {
  test('Collect and report all warnings across pages', async ({ page }) => {
    const allWarnings: { page: string; warning: string }[] = [];

    for (const pageInfo of PAGES) {
      const consoleCollector = new ConsoleErrorCollector(page);

      await page.goto(`${BASE_URL}${pageInfo.path}`);
      await waitForNetworkIdle(page);
      await page.waitForTimeout(1000);

      const warnings = consoleCollector.getWarnings();
      warnings.forEach(w => {
        allWarnings.push({ page: pageInfo.name, warning: w.text });
      });
    }

    // Report warnings (don't fail, just log)
    if (allWarnings.length > 0) {
      console.log('\n⚠️ Console Warnings Summary:');
      allWarnings.forEach((w, i) => {
        console.log(`  ${i + 1}. [${w.page}] ${w.warning.substring(0, 100)}`);
      });
    }

    // This test always passes - it's for reporting only
    expect(true).toBe(true);
  });
});
