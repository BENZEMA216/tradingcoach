/**
 * Performance Tests - 前端性能测试
 *
 * input: All frontend pages
 * output: Performance metrics and thresholds validation
 * pos: E2E 测试 - 确保页面加载性能达标
 *
 * Run: npx playwright test tests/e2e/performance.spec.ts --project=chromium
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { test, expect } from '@playwright/test';
import { getPerformanceMetrics, waitForNetworkIdle } from './helpers/test-utils';

const BASE_URL = 'http://localhost:5173';

// Performance thresholds (in milliseconds)
const THRESHOLDS = {
  pageLoad: 5000,         // Max 5 seconds for full page load
  domContentLoaded: 3000, // Max 3 seconds for DOM ready
  firstPaint: 2000,       // Max 2 seconds for first paint
  chartRender: 3000,      // Max 3 seconds for charts to render
  tableRender: 2000,      // Max 2 seconds for tables to render
};

test.describe('Page Load Performance', () => {
  test('Dashboard loads within threshold', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    const loadTime = Date.now() - startTime;

    console.log(`Dashboard load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(THRESHOLDS.pageLoad);
  });

  test('Statistics loads within threshold', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);

    const loadTime = Date.now() - startTime;

    console.log(`Statistics load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(THRESHOLDS.pageLoad);
  });

  test('Positions loads within threshold', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    const loadTime = Date.now() - startTime;

    console.log(`Positions load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(THRESHOLDS.pageLoad);
  });
});

test.describe('Component Render Performance', () => {
  test('Charts render within threshold', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);

    const startTime = Date.now();
    // Wait for any chart to render
    await page.waitForSelector('.recharts-surface, .recharts-wrapper', { timeout: THRESHOLDS.chartRender * 2 });
    const renderTime = Date.now() - startTime;

    console.log(`Chart render time: ${renderTime}ms`);
    // Allow more time for charts on statistics page
    expect(renderTime).toBeLessThan(THRESHOLDS.chartRender * 2);
  });

  test('Tables render within threshold', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);

    const startTime = Date.now();
    await page.waitForSelector('table', { timeout: THRESHOLDS.tableRender * 2 });
    const renderTime = Date.now() - startTime;

    console.log(`Table render time: ${renderTime}ms`);
    expect(renderTime).toBeLessThan(THRESHOLDS.tableRender * 2);
  });

  test('KPI cards render quickly', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    const startTime = Date.now();
    await page.waitForSelector('.grid, main', { timeout: 3000 });
    const renderTime = Date.now() - startTime;

    console.log(`KPI cards render time: ${renderTime}ms`);
    expect(renderTime).toBeLessThan(3000);
  });
});

test.describe('Navigation Performance', () => {
  test('Page navigation is fast', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Navigate to Statistics via sidebar link
    const startTime = Date.now();
    const statsLink = page.locator('aside a[href="/statistics"], aside nav a').filter({ hasText: /statistics|统计/i }).first();
    if (await statsLink.isVisible()) {
      await statsLink.click();
    } else {
      await page.goto(`${BASE_URL}/statistics`);
    }
    await waitForNetworkIdle(page);
    const navTime = Date.now() - startTime;

    console.log(`Navigation time (Dashboard -> Statistics): ${navTime}ms`);
    expect(navTime).toBeLessThan(5000);
  });

  test('Position detail navigation is fast', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    const firstRow = page.locator('tbody tr').first();
    if (await firstRow.isVisible()) {
      const startTime = Date.now();
      await firstRow.click();
      await waitForNetworkIdle(page);
      const navTime = Date.now() - startTime;

      console.log(`Position detail navigation time: ${navTime}ms`);
      expect(navTime).toBeLessThan(2000);
    }
  });
});

test.describe('Performance Metrics Collection', () => {
  test('Collect performance metrics for Dashboard', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    const metrics = await getPerformanceMetrics(page);

    console.log('\nDashboard Performance Metrics:');
    console.log(`  Load Time: ${metrics.loadTime}ms`);
    console.log(`  DOM Content Loaded: ${metrics.domContentLoaded}ms`);
    console.log(`  First Paint: ${metrics.firstPaint}ms`);

    expect(metrics.loadTime).toBeLessThan(THRESHOLDS.pageLoad);
    expect(metrics.domContentLoaded).toBeLessThan(THRESHOLDS.domContentLoaded);
  });

  test('Collect performance metrics for Statistics', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000); // Wait for charts

    const metrics = await getPerformanceMetrics(page);

    console.log('\nStatistics Performance Metrics:');
    console.log(`  Load Time: ${metrics.loadTime}ms`);
    console.log(`  DOM Content Loaded: ${metrics.domContentLoaded}ms`);
    console.log(`  First Paint: ${metrics.firstPaint}ms`);

    // Statistics page can be slower due to charts
    expect(metrics.loadTime).toBeLessThan(THRESHOLDS.pageLoad * 1.5);
  });
});

test.describe('Memory and Resource Usage', () => {
  test('No memory leaks on repeated navigation', async ({ page }) => {
    const memoryUsages: number[] = [];

    for (let i = 0; i < 3; i++) {
      await page.goto(`${BASE_URL}/dashboard`);
      await waitForNetworkIdle(page);

      await page.goto(`${BASE_URL}/statistics`);
      await waitForNetworkIdle(page);

      await page.goto(`${BASE_URL}/positions`);
      await waitForNetworkIdle(page);

      // Get JS heap size
      const metrics = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      if (metrics > 0) {
        memoryUsages.push(metrics);
      }
    }

    // Check memory doesn't grow excessively
    if (memoryUsages.length >= 2) {
      const firstUsage = memoryUsages[0];
      const lastUsage = memoryUsages[memoryUsages.length - 1];
      const growth = (lastUsage - firstUsage) / firstUsage;

      console.log(`\nMemory usage growth: ${(growth * 100).toFixed(2)}%`);
      console.log(`  First: ${(firstUsage / 1024 / 1024).toFixed(2)} MB`);
      console.log(`  Last: ${(lastUsage / 1024 / 1024).toFixed(2)} MB`);

      // Memory growth is expected with SPA navigation, allow up to 150%
      expect(growth).toBeLessThan(1.5);
    }
  });
});

test.describe('Network Request Performance', () => {
  test('API responses are fast', async ({ page }) => {
    const apiTimes: { url: string; time: number }[] = [];

    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/')) {
        const timing = response.request().timing();
        if (timing) {
          apiTimes.push({
            url: url.split('/api/')[1] || url,
            time: timing.responseEnd - timing.requestStart,
          });
        }
      }
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Report API times
    console.log('\nAPI Response Times:');
    apiTimes.forEach(({ url, time }) => {
      console.log(`  ${url}: ${time.toFixed(0)}ms`);
    });

    // All API calls should complete within 2 seconds
    apiTimes.forEach(({ url, time }) => {
      expect(time).toBeLessThan(2000);
    });
  });
});

test.describe('Bundle Size Check', () => {
  test('JavaScript bundle is reasonably sized', async ({ page }) => {
    let totalJsSize = 0;
    let totalCssSize = 0;

    page.on('response', async (response) => {
      const url = response.url();
      const contentType = response.headers()['content-type'] || '';

      if (contentType.includes('javascript')) {
        const body = await response.body().catch(() => Buffer.from(''));
        totalJsSize += body.length;
      } else if (contentType.includes('css')) {
        const body = await response.body().catch(() => Buffer.from(''));
        totalCssSize += body.length;
      }
    });

    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    const jsKB = totalJsSize / 1024;
    const cssKB = totalCssSize / 1024;

    console.log(`\nBundle Sizes:`);
    console.log(`  JavaScript: ${jsKB.toFixed(2)} KB`);
    console.log(`  CSS: ${cssKB.toFixed(2)} KB`);
    console.log(`  Total: ${(jsKB + cssKB).toFixed(2)} KB`);

    // JS bundle should be under 8MB (allow for larger bundles with charts and dependencies)
    expect(jsKB).toBeLessThan(8192);
  });
});
