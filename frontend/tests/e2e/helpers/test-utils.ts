/**
 * E2E Test Utilities
 *
 * input: Playwright test context
 * output: Helper functions for robust E2E testing
 * pos: 测试基础设施 - 提供可复用的测试工具函数
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { Page, expect, Locator } from '@playwright/test';

export interface ConsoleMessage {
  type: string;
  text: string;
  location: string;
}

export interface TestResult {
  passed: boolean;
  errors: string[];
  warnings: string[];
  screenshots: string[];
}

/**
 * Console Error Collector - 收集页面控制台错误
 */
export class ConsoleErrorCollector {
  private errors: ConsoleMessage[] = [];
  private warnings: ConsoleMessage[] = [];
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.setupListeners();
  }

  private setupListeners(): void {
    this.page.on('console', (msg) => {
      const type = msg.type();
      const text = msg.text();
      const location = msg.location().url || '';

      if (type === 'error') {
        this.errors.push({ type, text, location });
      } else if (type === 'warning') {
        this.warnings.push({ type, text, location });
      }
    });

    this.page.on('pageerror', (error) => {
      this.errors.push({
        type: 'pageerror',
        text: error.message,
        location: error.stack || '',
      });
    });
  }

  getErrors(): ConsoleMessage[] {
    return this.errors;
  }

  getWarnings(): ConsoleMessage[] {
    return this.warnings;
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  clear(): void {
    this.errors = [];
    this.warnings = [];
  }

  getReport(): string {
    let report = '';
    if (this.errors.length > 0) {
      report += `\n❌ Console Errors (${this.errors.length}):\n`;
      this.errors.forEach((e, i) => {
        report += `  ${i + 1}. ${e.text}\n`;
      });
    }
    if (this.warnings.length > 0) {
      report += `\n⚠️ Console Warnings (${this.warnings.length}):\n`;
      this.warnings.forEach((w, i) => {
        report += `  ${i + 1}. ${w.text}\n`;
      });
    }
    return report || '✅ No console errors or warnings';
  }
}

/**
 * Visual Regression Helper - 视觉回归测试辅助
 */
export class VisualRegressionHelper {
  private page: Page;
  private screenshotDir: string;

  constructor(page: Page, screenshotDir: string = 'screenshots') {
    this.page = page;
    this.screenshotDir = screenshotDir;
  }

  async captureFullPage(name: string): Promise<string> {
    const path = `${this.screenshotDir}/${name}-${Date.now()}.png`;
    await this.page.screenshot({ path, fullPage: true });
    return path;
  }

  async captureElement(locator: Locator, name: string): Promise<string> {
    const path = `${this.screenshotDir}/${name}-${Date.now()}.png`;
    await locator.screenshot({ path });
    return path;
  }

  async captureViewport(name: string): Promise<string> {
    const path = `${this.screenshotDir}/${name}-${Date.now()}.png`;
    await this.page.screenshot({ path });
    return path;
  }
}

/**
 * Wait Helpers - 等待辅助函数
 */
export async function waitForNetworkIdle(page: Page, timeout: number = 5000): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout });
}

export async function waitForChartLoad(page: Page, timeout: number = 10000): Promise<void> {
  await page.waitForSelector('.recharts-surface', { timeout });
  // Additional wait for chart animations to complete
  await page.waitForTimeout(500);
}

export async function waitForTableLoad(page: Page, timeout: number = 10000): Promise<void> {
  await page.waitForSelector('table tbody tr', { timeout });
}

/**
 * Assertion Helpers - 断言辅助函数
 */
export async function assertNoConsoleErrors(collector: ConsoleErrorCollector): Promise<void> {
  const errors = collector.getErrors().filter(e =>
    // Filter out known benign errors
    !e.text.includes('ResizeObserver') &&
    !e.text.includes('favicon.ico')
  );

  if (errors.length > 0) {
    throw new Error(`Console errors detected:\n${errors.map(e => e.text).join('\n')}`);
  }
}

export async function assertElementVisible(page: Page, selector: string, timeout: number = 5000): Promise<void> {
  await expect(page.locator(selector)).toBeVisible({ timeout });
}

export async function assertElementCount(page: Page, selector: string, minCount: number): Promise<void> {
  const count = await page.locator(selector).count();
  expect(count).toBeGreaterThanOrEqual(minCount);
}

/**
 * Navigation Helpers - 导航辅助函数
 */
export async function navigateAndWait(page: Page, url: string): Promise<void> {
  await page.goto(url);
  await waitForNetworkIdle(page);
}

export async function clickAndWait(page: Page, locator: Locator): Promise<void> {
  await locator.click();
  await waitForNetworkIdle(page);
}

/**
 * Responsive Testing Helper - 响应式测试辅助
 */
export const VIEWPORTS = {
  mobile: { width: 375, height: 667 },
  tablet: { width: 768, height: 1024 },
  desktop: { width: 1920, height: 1080 },
  laptop: { width: 1366, height: 768 },
};

export async function testResponsive(
  page: Page,
  url: string,
  testFn: (viewport: string) => Promise<void>
): Promise<void> {
  for (const [name, size] of Object.entries(VIEWPORTS)) {
    await page.setViewportSize(size);
    await page.goto(url);
    await waitForNetworkIdle(page);
    await testFn(name);
  }
}

/**
 * API Mock Helper - API 模拟辅助
 */
export async function mockApiResponse(
  page: Page,
  urlPattern: string,
  response: object,
  status: number = 200
): Promise<void> {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status,
      contentType: 'application/json',
      body: JSON.stringify(response),
    });
  });
}

export async function blockApiCalls(page: Page, urlPattern: string = '**/api/**'): Promise<void> {
  await page.route(urlPattern, (route) => route.abort());
}

/**
 * Performance Metrics Helper - 性能指标辅助
 */
export async function getPerformanceMetrics(page: Page): Promise<{
  loadTime: number;
  domContentLoaded: number;
  firstPaint: number;
}> {
  const metrics = await page.evaluate(() => {
    const timing = performance.timing;
    const paintEntries = performance.getEntriesByType('paint');
    const firstPaint = paintEntries.find(e => e.name === 'first-paint');

    return {
      loadTime: timing.loadEventEnd - timing.navigationStart,
      domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
      firstPaint: firstPaint ? firstPaint.startTime : 0,
    };
  });

  return metrics;
}

/**
 * Accessibility Helper - 可访问性辅助
 */
export async function checkBasicAccessibility(page: Page): Promise<{
  hasTitle: boolean;
  hasHeading: boolean;
  imagesWithAlt: number;
  totalImages: number;
}> {
  const results = await page.evaluate(() => {
    const title = document.title;
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const images = document.querySelectorAll('img');
    const imagesWithAlt = Array.from(images).filter(img => img.alt).length;

    return {
      hasTitle: title.length > 0,
      hasHeading: headings.length > 0,
      imagesWithAlt,
      totalImages: images.length,
    };
  });

  return results;
}
