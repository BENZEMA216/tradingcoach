/**
 * Visual Regression Tests - 视觉回归测试
 *
 * input: Frontend pages and components
 * output: Screenshot comparisons and visual validation
 * pos: E2E 测试 - 确保 UI 视觉一致性
 *
 * Run: npx playwright test tests/e2e/visual-regression/ --project=chromium
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { test, expect } from '@playwright/test';
import {
  ConsoleErrorCollector,
  waitForNetworkIdle,
  waitForChartLoad,
  assertNoConsoleErrors,
  VIEWPORTS,
} from '../helpers/test-utils';

const BASE_URL = 'http://localhost:5173';

test.describe('Visual Regression - Dashboard', () => {
  test('Dashboard page screenshot - Desktop', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.setViewportSize(VIEWPORTS.desktop);
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);
    await waitForChartLoad(page);

    // Take full page screenshot
    await expect(page).toHaveScreenshot('dashboard-desktop.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });

    // Check for console errors
    await assertNoConsoleErrors(consoleCollector);
  });

  test('Dashboard page screenshot - Mobile', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.mobile);
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('Dashboard page screenshot - Tablet', async ({ page }) => {
    await page.setViewportSize(VIEWPORTS.tablet);
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    await expect(page).toHaveScreenshot('dashboard-tablet.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('Dashboard KPI cards visual consistency', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Capture KPI section
    const kpiSection = page.locator('.grid').first();
    await expect(kpiSection).toHaveScreenshot('dashboard-kpi-cards.png', {
      maxDiffPixels: 50,
    });
  });
});

test.describe('Visual Regression - Statistics', () => {
  test('Statistics page screenshot - Desktop', async ({ page }) => {
    const consoleCollector = new ConsoleErrorCollector(page);

    await page.setViewportSize(VIEWPORTS.desktop);
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000); // Wait for all charts

    await expect(page).toHaveScreenshot('statistics-desktop.png', {
      fullPage: true,
      maxDiffPixels: 200, // Charts may have minor variations
    });

    await assertNoConsoleErrors(consoleCollector);
  });

  test('Statistics Hero Summary visual', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);

    const heroSection = page.locator('section').first();
    await expect(heroSection).toHaveScreenshot('statistics-hero.png', {
      maxDiffPixels: 100,
    });
  });

  test('Statistics charts render correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000);

    // Verify charts are visible
    const charts = page.locator('.recharts-surface');
    const chartCount = await charts.count();
    expect(chartCount).toBeGreaterThanOrEqual(4);

    // Take screenshot of first chart
    if (chartCount > 0) {
      await expect(charts.first()).toHaveScreenshot('statistics-chart-1.png', {
        maxDiffPixels: 100,
      });
    }
  });
});

test.describe('Visual Regression - Positions', () => {
  test('Positions list page screenshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    await expect(page).toHaveScreenshot('positions-list.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('Positions table visual', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    const table = page.locator('table');
    await expect(table).toHaveScreenshot('positions-table.png', {
      maxDiffPixels: 50,
    });
  });

  test('Position detail page screenshot', async ({ page }) => {
    // Navigate to positions list first
    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    // Click first row to go to detail
    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await waitForNetworkIdle(page);

      await expect(page).toHaveScreenshot('position-detail.png', {
        fullPage: true,
        maxDiffPixels: 100,
      });
    }
  });
});

test.describe('Visual Regression - Dark Mode', () => {
  test('Dashboard dark mode screenshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Enable dark mode
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    });

    await page.reload();
    await waitForNetworkIdle(page);
    await waitForChartLoad(page);

    await expect(page).toHaveScreenshot('dashboard-dark-mode.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });

  test('Statistics dark mode screenshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);

    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    });

    await page.reload();
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000);

    await expect(page).toHaveScreenshot('statistics-dark-mode.png', {
      fullPage: true,
      maxDiffPixels: 200,
    });
  });
});

test.describe('Visual Regression - System Page', () => {
  test('System page screenshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/system`);
    await waitForNetworkIdle(page);

    await expect(page).toHaveScreenshot('system-page.png', {
      fullPage: true,
      maxDiffPixels: 100,
    });
  });
});

test.describe('Visual Regression - Upload Page', () => {
  test('Upload page screenshot', async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);
    await waitForNetworkIdle(page);

    await expect(page).toHaveScreenshot('upload-page.png', {
      fullPage: true,
      maxDiffPixels: 50,
    });
  });
});

test.describe('Visual Regression - Cross Browser', () => {
  test('Dashboard consistency across viewports', async ({ page }) => {
    const viewports = ['mobile', 'tablet', 'desktop'] as const;

    for (const viewport of viewports) {
      await page.setViewportSize(VIEWPORTS[viewport]);
      await page.goto(`${BASE_URL}/dashboard`);
      await waitForNetworkIdle(page);

      await expect(page).toHaveScreenshot(`dashboard-${viewport}-responsive.png`, {
        fullPage: true,
        maxDiffPixels: 100,
      });
    }
  });
});
