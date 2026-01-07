import { test, expect } from '@playwright/test';

/**
 * Basic smoke test to verify Playwright setup works.
 * This test will be removed or expanded in later phases.
 */
test.describe('Smoke Tests', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/./); // Any title is fine
    await expect(page.locator('body')).toBeVisible();
  });
});
