import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for UI testing the Hugo blog.
 * Requires Hugo dev server running on port 1313.
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests/ui',

  // Run tests in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry failed tests on CI
  retries: process.env.CI ? 2 : 0,

  // Limit parallel workers on CI for stability
  workers: process.env.CI ? 1 : undefined,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  // Shared settings for all projects
  use: {
    // Base URL for the Hugo dev server
    baseURL: 'http://localhost:1313',

    // Collect trace when retrying failed tests
    trace: 'on-first-retry',

    // Capture screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'on-first-retry',

    // Reasonable timeout for actions
    actionTimeout: 10000,
  },

  // Global timeout for each test
  timeout: 30000,

  // Expect timeout
  expect: {
    timeout: 5000,
    // Visual comparison threshold (allow minor anti-aliasing differences)
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
    },
  },

  // Configure projects for major browsers and mobile viewports
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports for responsive testing
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Run Hugo dev server before running tests
  webServer: {
    command: 'hugo server -D --port 1313',
    url: 'http://localhost:1313',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
