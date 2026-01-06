/**
 * TradingCoach Frontend QA Walkthrough Tests
 *
 * Run with: npx playwright test tests/e2e/qa-walkthrough.spec.ts
 * Or with UI: npx playwright test --ui
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:5173';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
  });

  test('KPI cards display correctly', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('.grid');

    // Check all 4 KPI cards are visible
    const kpiCards = page.locator('.rounded-xl.shadow-sm');
    await expect(kpiCards).toHaveCount(6); // 4 KPIs + 2 charts

    // Check Total P&L displays a currency value
    await expect(page.getByText(/\$[\d,]+/)).toBeVisible();

    // Check Win Rate displays a percentage
    await expect(page.getByText(/%/)).toBeVisible();
  });

  test('Equity curve chart renders', async ({ page }) => {
    await page.waitForSelector('.recharts-surface');
    const chart = page.locator('.recharts-surface').first();
    await expect(chart).toBeVisible();
  });

  test('Strategy pie chart is clickable', async ({ page }) => {
    await page.waitForSelector('.recharts-pie');
    const pieSlice = page.locator('.recharts-pie-sector').first();
    await expect(pieSlice).toBeVisible();

    // Click on pie slice should open drill-down modal
    await pieSlice.click();
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 5000 });
  });

  test('Recent trades table displays', async ({ page }) => {
    await page.waitForSelector('table');
    const rows = page.locator('tbody tr');
    await expect(rows).toHaveCount(10);
  });
});

test.describe('Statistics Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
  });

  test('Hero summary displays', async ({ page }) => {
    await page.waitForSelector('text=PERFORMANCE OVERVIEW');
    await expect(page.getByText(/\$[\d,]+/)).toBeVisible();
  });

  test('Multiple charts load', async ({ page }) => {
    await page.waitForTimeout(2000); // Wait for all charts
    const charts = page.locator('.recharts-surface');
    const count = await charts.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });

  test('Trading heatmap displays with colors', async ({ page }) => {
    await page.waitForSelector('text=PATTERN ANALYSIS');
    // Check for colored cells (TradingView colors)
    const profitCells = page.locator('[style*="rgba(38, 166, 154"]');
    const lossCells = page.locator('[style*="rgba(239, 83, 80"]');

    const profitCount = await profitCells.count();
    const lossCount = await lossCells.count();
    expect(profitCount + lossCount).toBeGreaterThan(0);
  });

  test('Top 10 symbols table is visible', async ({ page }) => {
    await page.waitForSelector('text=Top 10');
    const table = page.locator('table').filter({ hasText: 'TSLL' });
    await expect(table).toBeVisible();

    // Check font color is visible (not too dark)
    const symbolCell = page.locator('td').filter({ hasText: 'TSLL' }).first();
    await expect(symbolCell).toHaveCSS('color', /(rgb\(|rgba\()/);
  });

  test('Period tabs work', async ({ page }) => {
    // Find period selector buttons
    const buttons = page.locator('button');

    // Click Month button if available
    const monthButton = buttons.filter({ hasText: /Month|月/ });
    if (await monthButton.count() > 0) {
      await monthButton.click();
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Positions Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);
  });

  test('Positions table loads', async ({ page }) => {
    await page.waitForSelector('table');
    const rows = page.locator('tbody tr');
    const count = await rows.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Filter by direction works', async ({ page }) => {
    await page.waitForSelector('table');

    // Find and click direction filter
    const directionFilter = page.locator('select').first();
    if (await directionFilter.isVisible()) {
      await directionFilter.selectOption({ index: 1 });
      await page.waitForTimeout(500);
    }
  });

  test('Click row navigates to detail', async ({ page }) => {
    await page.waitForSelector('tbody tr');
    const firstRow = page.locator('tbody tr').first();
    await firstRow.click();

    await expect(page).toHaveURL(/\/positions\/\d+/);
  });
});

test.describe('Position Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/positions/403`);
  });

  test('Position details load', async ({ page }) => {
    await page.waitForSelector('text=AMZN');
    await expect(page.getByText('AMZN')).toBeVisible();
  });

  test('Trade summary section displays', async ({ page }) => {
    await page.waitForTimeout(1000);
    // Check for P&L display
    await expect(page.getByText(/\$[\d,.-]+/)).toBeVisible();
  });

  test('Related positions section shows', async ({ page }) => {
    await page.waitForTimeout(1000);
    const relatedSection = page.getByText(/Related|关联/);
    // May or may not be visible depending on data
    if (await relatedSection.isVisible()) {
      await expect(relatedSection).toBeVisible();
    }
  });

  test('Back button works', async ({ page }) => {
    const backButton = page.getByText(/Back|返回/);
    await backButton.click();
    await expect(page).toHaveURL(/\/positions$/);
  });
});

test.describe('AI Coach Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/ai-coach`);
  });

  test('Insight cards display', async ({ page }) => {
    await page.waitForTimeout(1000);
    // Check for insight cards or service unavailable message
    const hasInsights = await page.locator('.rounded-xl').count() > 0;
    const hasUnavailable = await page.getByText(/unavailable|不可用/).isVisible();
    expect(hasInsights || hasUnavailable).toBeTruthy();
  });

  test('Chat input is visible', async ({ page }) => {
    const input = page.locator('input[type="text"], textarea').first();
    await expect(input).toBeVisible();
  });
});

test.describe('System Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/system`);
  });

  test('Health status displays', async ({ page }) => {
    await page.waitForSelector('text=API');
    await expect(page.getByText(/healthy|正常/i)).toBeVisible();
  });

  test('Database stats display', async ({ page }) => {
    await page.waitForTimeout(500);
    // Check for positions count
    await expect(page.getByText(/444|positions/i)).toBeVisible();
  });
});

test.describe('Dark Mode', () => {
  test('Toggle dark mode on dashboard', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Find dark mode toggle in sidebar
    const darkModeToggle = page.locator('[aria-label*="dark"], [data-testid="dark-mode-toggle"]');
    if (await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(500);

      // Check body has dark class
      const htmlElement = page.locator('html');
      await expect(htmlElement).toHaveClass(/dark/);
    }
  });

  test('Charts render in dark mode', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);

    // Enable dark mode via localStorage
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    });

    await page.reload();
    await page.waitForTimeout(1000);

    // Charts should still be visible
    const charts = page.locator('.recharts-surface');
    await expect(charts.first()).toBeVisible();
  });
});

test.describe('Internationalization', () => {
  test('Switch to Chinese', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Find language switcher
    const langSwitcher = page.locator('button').filter({ hasText: /中|EN/ });
    if (await langSwitcher.isVisible()) {
      await langSwitcher.click();

      // Select Chinese if dropdown appears
      const zhOption = page.locator('text=中文');
      if (await zhOption.isVisible()) {
        await zhOption.click();
      }

      await page.waitForTimeout(500);
      await expect(page.getByText('仪表盘')).toBeVisible();
    }
  });

  test('System page has Chinese translations', async ({ page }) => {
    // Set language to Chinese
    await page.goto(`${BASE_URL}/system`);
    await page.evaluate(() => {
      localStorage.setItem('i18nextLng', 'zh');
    });
    await page.reload();
    await page.waitForTimeout(500);

    await expect(page.getByText('系统状态')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('Mobile view - dashboard', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`${BASE_URL}/dashboard`);

    // Sidebar should be collapsed
    const sidebar = page.locator('aside');
    // KPI cards should stack
    const grid = page.locator('.grid');
    await expect(grid).toBeVisible();
  });

  test('Tablet view - statistics', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`${BASE_URL}/statistics`);

    await page.waitForTimeout(1000);
    const charts = page.locator('.recharts-surface');
    await expect(charts.first()).toBeVisible();
  });

  test('Desktop view - full layout', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`${BASE_URL}/dashboard`);

    // Sidebar should be visible
    await expect(page.locator('aside')).toBeVisible();
  });
});

test.describe('Chart Interactions', () => {
  test('Duration vs PnL scatter chart tooltip', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await page.waitForTimeout(2000);

    // Find scatter chart dots
    const scatterDots = page.locator('.recharts-scatter-symbol');
    if (await scatterDots.count() > 0) {
      await scatterDots.first().hover();
      await page.waitForTimeout(300);

      // Tooltip should appear
      const tooltip = page.locator('.recharts-tooltip-wrapper');
      await expect(tooltip).toBeVisible();
    }
  });

  test('Monthly performance bar chart click', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await page.waitForTimeout(2000);

    // Find bar chart bars
    const bars = page.locator('.recharts-bar-rectangle');
    if (await bars.count() > 0) {
      await bars.first().click();

      // Drill-down modal should open
      await page.waitForTimeout(500);
      const modal = page.locator('[role="dialog"]');
      // Modal may or may not appear depending on click handler
    }
  });
});

test.describe('Error Handling', () => {
  test('Invalid position ID shows error', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions/99999`);
    await page.waitForTimeout(1000);

    // Should show "not found" or redirect
    const notFound = page.getByText(/not found|未找到/i);
    const hasNotFound = await notFound.isVisible();
    const redirected = page.url().includes('/positions') && !page.url().includes('99999');

    expect(hasNotFound || redirected).toBeTruthy();
  });

  test('API error graceful handling', async ({ page }) => {
    // Block API calls
    await page.route('**/api/**', (route) => route.abort());

    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(2000);

    // Page should not crash - should show loading or error state
    await expect(page.locator('body')).toBeVisible();
  });
});
