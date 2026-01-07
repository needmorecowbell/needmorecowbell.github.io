import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for running UI tests in Docker.
 * Uses the Hugo server container as the base URL.
 *
 * This config is used by docker-compose.test.yml and does NOT start
 * a web server (the Hugo container handles that).
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests/ui',

  // Run tests in parallel
  fullyParallel: true,

  // Fail if test.only is left in source code
  forbidOnly: true,

  // Retry failed tests in CI/Docker
  retries: 2,

  // Single worker for stability in container
  workers: 1,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  // Shared settings for all projects
  use: {
    // Base URL points to Hugo container via Docker network
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://hugo-server:1313',

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

  // No webServer config - Docker Compose manages the Hugo server
});
