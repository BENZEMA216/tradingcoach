import { test, expect } from '@playwright/test';

test.describe('TradingCoach V2 Scoring Walkthrough', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard loads with KPI cards', async ({ page }) => {
    // Check dashboard loads
    await expect(page.locator('h1, h2').first()).toBeVisible();

    // Take a screenshot
    await page.screenshot({ path: 'screenshots/01-dashboard.png', fullPage: true });
    console.log('✓ Dashboard loaded successfully');
  });

  test('Positions page shows scores', async ({ page }) => {
    // Navigate to Positions page
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');

    // Wait for the table to load
    await page.waitForTimeout(1000);

    // Take a screenshot
    await page.screenshot({ path: 'screenshots/02-positions.png', fullPage: true });
    console.log('✓ Positions page loaded');

    // Check for score columns or badges (Grade column)
    const gradeElements = await page.locator('text=/B\\+|B\\-|B|C\\+|C\\-|C|A\\+|A\\-|A/').count();
    console.log(`  Found ${gradeElements} grade elements`);
  });

  test('Position detail page shows V2 scores', async ({ page }) => {
    // Navigate to Positions page
    await page.click('text=Positions');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click on first position row to view details
    const firstRow = page.locator('table tbody tr').first();
    if (await firstRow.isVisible()) {
      await firstRow.click();
      await page.waitForTimeout(1000);
      await page.screenshot({ path: 'screenshots/03-position-detail.png', fullPage: true });
      console.log('✓ Position detail accessed');
    }
  });

  test('Statistics page loads', async ({ page }) => {
    // Navigate to Statistics page
    await page.click('text=Statistics');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Take a screenshot
    await page.screenshot({ path: 'screenshots/04-statistics.png', fullPage: true });
    console.log('✓ Statistics page loaded');
  });
});
