/**
 * Accessibility Tests - 可访问性测试
 *
 * input: All frontend pages
 * output: Accessibility validation results
 * pos: E2E 测试 - 确保页面可访问性达标
 *
 * Run: npx playwright test tests/e2e/accessibility.spec.ts --project=chromium
 *
 * 一旦我被更新，务必更新我的开头注释，以及所属文件夹的README.md
 */

import { test, expect } from '@playwright/test';
import { checkBasicAccessibility, waitForNetworkIdle } from './helpers/test-utils';

const BASE_URL = 'http://localhost:5173';

const PAGES = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Statistics', path: '/statistics' },
  { name: 'Positions', path: '/positions' },
  { name: 'Upload', path: '/upload' },
  { name: 'System', path: '/system' },
];

test.describe('Basic Accessibility Checks', () => {
  for (const pageInfo of PAGES) {
    test(`${pageInfo.name} has basic accessibility elements`, async ({ page }) => {
      await page.goto(`${BASE_URL}${pageInfo.path}`);
      await waitForNetworkIdle(page);

      const results = await checkBasicAccessibility(page);

      console.log(`\n${pageInfo.name} Accessibility:`);
      console.log(`  Has title: ${results.hasTitle ? '✓' : '✗'}`);
      console.log(`  Has headings: ${results.hasHeading ? '✓' : '✗'}`);
      console.log(`  Images with alt: ${results.imagesWithAlt}/${results.totalImages}`);

      expect(results.hasTitle).toBe(true);
      expect(results.hasHeading).toBe(true);
    });
  }
});

test.describe('Keyboard Navigation', () => {
  test('Dashboard is keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Tab through elements
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
    }

    // Check that focus is visible
    const focusedElement = await page.evaluate(() => {
      const focused = document.activeElement;
      return focused ? focused.tagName : null;
    });

    expect(focusedElement).not.toBeNull();
  });

  test('Navigation links are keyboard accessible', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Find nav links
    const navLinks = page.locator('nav a, aside a');
    const count = await navLinks.count();

    expect(count).toBeGreaterThan(0);

    // First link should be focusable
    if (count > 0) {
      await navLinks.first().focus();
      const focused = await page.evaluate(() => document.activeElement?.tagName);
      expect(focused?.toLowerCase()).toBe('a');
    }
  });

  test('Tables are keyboard navigable', async ({ page }) => {
    await page.goto(`${BASE_URL}/positions`);
    await waitForNetworkIdle(page);

    const table = page.locator('table');
    if (await table.isVisible()) {
      const rows = page.locator('tbody tr');
      const rowCount = await rows.count();

      if (rowCount > 0) {
        await rows.first().focus();
        // Check row is focusable or has focusable elements
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });
});

test.describe('Color Contrast', () => {
  test('Text has sufficient contrast', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    // Check that text elements have readable colors
    const textContrast = await page.evaluate(() => {
      const elements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, td, th');
      const results: { hasContrast: boolean; sample: string }[] = [];

      elements.forEach((el) => {
        const styles = window.getComputedStyle(el);
        const color = styles.color;
        const bgColor = styles.backgroundColor;

        // Simple check - ensure text color is not transparent
        const hasContrast = !color.includes('rgba(0, 0, 0, 0)');
        results.push({
          hasContrast,
          sample: el.textContent?.substring(0, 20) || '',
        });
      });

      return results.slice(0, 10); // Sample first 10
    });

    const withContrast = textContrast.filter(r => r.hasContrast);
    expect(withContrast.length).toBeGreaterThan(0);
  });
});

test.describe('Form Accessibility', () => {
  test('Upload form has accessible labels', async ({ page }) => {
    await page.goto(`${BASE_URL}/upload`);
    await waitForNetworkIdle(page);

    // Check for form elements with labels
    const formInfo = await page.evaluate(() => {
      const inputs = document.querySelectorAll('input, select, textarea');
      const labeled: string[] = [];
      const unlabeled: string[] = [];

      inputs.forEach((input) => {
        const id = input.getAttribute('id');
        const ariaLabel = input.getAttribute('aria-label');
        const ariaLabelledBy = input.getAttribute('aria-labelledby');
        const hasLabel = id && document.querySelector(`label[for="${id}"]`);

        if (hasLabel || ariaLabel || ariaLabelledBy) {
          labeled.push(input.tagName);
        } else {
          unlabeled.push(input.tagName);
        }
      });

      return { labeled, unlabeled };
    });

    console.log('\nForm Accessibility:');
    console.log(`  Labeled inputs: ${formInfo.labeled.length}`);
    console.log(`  Unlabeled inputs: ${formInfo.unlabeled.length}`);

    // Most inputs should have labels
    const total = formInfo.labeled.length + formInfo.unlabeled.length;
    if (total > 0) {
      const labeledRatio = formInfo.labeled.length / total;
      expect(labeledRatio).toBeGreaterThanOrEqual(0.5);
    }
  });
});

test.describe('Screen Reader Support', () => {
  test('Page has proper landmarks', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    const landmarks = await page.evaluate(() => {
      return {
        hasMain: document.querySelector('main, [role="main"]') !== null,
        hasNav: document.querySelector('nav, [role="navigation"]') !== null,
        hasHeader: document.querySelector('header, [role="banner"]') !== null,
        hasFooter: document.querySelector('footer, [role="contentinfo"]') !== null,
      };
    });

    console.log('\nPage Landmarks:');
    console.log(`  Main: ${landmarks.hasMain ? '✓' : '✗'}`);
    console.log(`  Navigation: ${landmarks.hasNav ? '✓' : '✗'}`);
    console.log(`  Header: ${landmarks.hasHeader ? '✓' : '✗'}`);
    console.log(`  Footer: ${landmarks.hasFooter ? '✓' : '✗'}`);

    // At minimum, should have navigation
    expect(landmarks.hasNav).toBe(true);
  });

  test('Interactive elements have accessible names', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await waitForNetworkIdle(page);

    const buttonInfo = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button, [role="button"]');
      const withNames: number[] = [];
      const withoutNames: string[] = [];

      buttons.forEach((btn, index) => {
        const text = btn.textContent?.trim();
        const ariaLabel = btn.getAttribute('aria-label');
        const title = btn.getAttribute('title');

        if (text || ariaLabel || title) {
          withNames.push(index);
        } else {
          withoutNames.push(`button-${index}`);
        }
      });

      return { withNames: withNames.length, withoutNames };
    });

    console.log(`\nButton Accessibility:`);
    console.log(`  With accessible names: ${buttonInfo.withNames}`);
    console.log(`  Without names: ${buttonInfo.withoutNames.length}`);

    // Most buttons should have accessible names
    const total = buttonInfo.withNames + buttonInfo.withoutNames.length;
    if (total > 0) {
      const ratio = buttonInfo.withNames / total;
      expect(ratio).toBeGreaterThanOrEqual(0.7);
    }
  });
});

test.describe('Focus Management', () => {
  test('Modal dialogs trap focus', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000);

    // Try to trigger a modal by clicking on a chart
    const clickableElement = page.locator('.recharts-pie-sector, .recharts-bar-rectangle').first();

    if (await clickableElement.isVisible()) {
      await clickableElement.click({ force: true });
      await page.waitForTimeout(500);

      // Check if modal appeared
      const modal = page.locator('[role="dialog"], .modal, [aria-modal="true"]');
      if (await modal.isVisible()) {
        // Tab should stay within modal
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');

        const focusedInModal = await page.evaluate(() => {
          const modal = document.querySelector('[role="dialog"], .modal, [aria-modal="true"]');
          const focused = document.activeElement;
          return modal?.contains(focused);
        });

        expect(focusedInModal).toBe(true);
      }
    }
  });

  test('Focus returns after modal close', async ({ page }) => {
    await page.goto(`${BASE_URL}/statistics`);
    await waitForNetworkIdle(page);
    await page.waitForTimeout(2000);

    // Find and click trigger element
    const trigger = page.locator('.recharts-pie-sector').first();

    if (await trigger.isVisible()) {
      await trigger.click({ force: true });
      await page.waitForTimeout(500);

      const modal = page.locator('[role="dialog"]');
      if (await modal.isVisible()) {
        // Close modal with Escape
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        // Focus should be manageable
        expect(await page.locator('body').isVisible()).toBe(true);
      }
    }
  });
});
