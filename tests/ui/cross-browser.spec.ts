import { test, expect } from '@playwright/test';
import {
  waitForGlightbox,
  openLightbox,
  closeLightbox,
  getLightboxImage,
  countGalleryThumbnails,
} from './fixtures';

/**
 * Helper to filter out expected third-party CORS/network errors from console errors.
 * Cloudflare Insights and other analytics scripts cause CORS errors when
 * running locally that are not actual application errors.
 * Also filters generic network failures from blocked third-party requests.
 */
function filterThirdPartyErrors(errors: string[]): string[] {
  const ignoredPatterns = [
    /cloudflareinsights\.com/i,
    /CORS/i,
    /Access-Control-Allow-Origin/i,
    /Cross-Origin Request Blocked/i,
    /cdn-cgi\/rum/i,
    // Generic network errors from blocked third-party requests
    /Failed to load resource: net::ERR_FAILED/i,
    /net::ERR_BLOCKED_BY_CLIENT/i,
  ];

  return errors.filter((error) => {
    return !ignoredPatterns.some((pattern) => pattern.test(error));
  });
}

/**
 * Cross-browser smoke tests for gallery functionality.
 * These tests verify basic gallery operations work consistently across
 * Chromium, Firefox, WebKit (Safari), and mobile viewports.
 *
 * The tests are designed to be run across all browser projects configured
 * in playwright.config.ts to ensure cross-browser compatibility.
 */
test.describe('Cross-Browser Gallery Compatibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
  });

  test('gallery renders correctly', async ({ page, browserName }) => {
    // Wait for GLightbox to initialize
    await waitForGlightbox(page);

    // Verify gallery grid exists and has content
    const gallery = page.locator('.gallery-grid');
    await expect(gallery).toBeVisible();

    // Verify thumbnails are present
    const thumbnailCount = await countGalleryThumbnails(page);
    expect(thumbnailCount).toBeGreaterThan(0);

    // Log browser for debugging
    console.log(`Gallery renders correctly in ${browserName}: ${thumbnailCount} thumbnails`);
  });

  test('lightbox opens and displays image', async ({ page, browserName }) => {
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);

    // Verify overlay is visible
    const overlay = page.locator('.goverlay');
    await expect(overlay).toBeVisible();

    // Verify lightbox container is visible
    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toBeVisible();

    // Verify image is displayed
    const lightboxImg = await getLightboxImage(page);
    expect(lightboxImg.src).toBeTruthy();
    expect(lightboxImg.width).toBeGreaterThan(0);
    expect(lightboxImg.height).toBeGreaterThan(0);

    console.log(`Lightbox opens correctly in ${browserName}`);
  });

  test('lightbox closes properly', async ({ page, browserName }, testInfo) => {
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);
    await expect(page.locator('.goverlay')).toBeVisible();

    // Close using ESC key (most reliable across browsers)
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // Verify lightbox is closed
    await expect(page.locator('.goverlay')).not.toBeVisible();

    console.log(`Lightbox closes correctly in ${browserName}`);
  });

  test('keyboard navigation works', async ({ page, browserName }) => {
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);

    // Get first image
    const firstImage = await getLightboxImage(page);
    const firstSrc = firstImage.src;

    // Navigate to next image with arrow key
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(400);

    // Verify navigation worked (different image)
    const secondImage = await getLightboxImage(page);
    expect(secondImage.src).not.toBe(firstSrc);

    // Navigate back
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(400);

    // Verify we're back to first image
    const backToFirst = await getLightboxImage(page);
    expect(backToFirst.src).toBe(firstSrc);

    console.log(`Keyboard navigation works correctly in ${browserName}`);
  });
});

/**
 * Mobile-specific tests for touch simulation and responsive behavior.
 * These tests only run on mobile viewport projects.
 */
test.describe('Mobile Gallery Support', () => {
  test('gallery renders in mobile viewport', async ({ page, browserName }, testInfo) => {
    // This test is meaningful for all browsers, but especially mobile projects
    const isMobile = testInfo.project.name.includes('mobile');

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Verify gallery is visible
    const gallery = page.locator('.gallery-grid');
    await expect(gallery).toBeVisible();

    // Verify thumbnails are accessible
    const thumbnails = page.locator('.gallery-grid a.glightbox');
    const count = await thumbnails.count();
    expect(count).toBeGreaterThan(0);

    // Verify first thumbnail is visible and clickable
    await expect(thumbnails.first()).toBeVisible();

    console.log(`Mobile gallery renders in ${browserName} (mobile: ${isMobile}): ${count} thumbnails`);
  });

  test('lightbox works with touch/click on mobile viewport', async ({ page, browserName }, testInfo) => {
    const isMobile = testInfo.project.name.includes('mobile');

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Open lightbox (click simulates tap on mobile)
    await openLightbox(page, 0);

    // Verify lightbox opened
    await expect(page.locator('.goverlay')).toBeVisible();

    // Verify image is displayed
    const currentSlide = page.locator('.gslide.current');
    await expect(currentSlide).toBeVisible();

    // Close with ESC (works universally)
    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);

    // Verify closed
    await expect(page.locator('.goverlay')).not.toBeVisible();

    console.log(`Touch/click lightbox works in ${browserName} (mobile: ${isMobile})`);
  });
});

/**
 * JavaScript console error detection tests.
 * Ensures no JavaScript errors are thrown on gallery pages.
 * Note: Third-party analytics CORS errors are filtered out as they
 * are expected when running locally against a dev server.
 */
test.describe('No JavaScript Console Errors', () => {
  test('no console errors on gallery page load', async ({ page, browserName }) => {
    const errors: string[] = [];

    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Also capture page errors (uncaught exceptions)
    page.on('pageerror', (error) => {
      errors.push(`Page error: ${error.message}`);
    });

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Give time for any deferred scripts to execute
    await page.waitForTimeout(500);

    // Filter out expected third-party CORS errors
    const relevantErrors = filterThirdPartyErrors(errors);

    // Log any errors found (for debugging)
    if (relevantErrors.length > 0) {
      console.log(`Console errors in ${browserName}:`, relevantErrors);
    }

    // No application errors should be present
    expect(relevantErrors.length).toBe(0);
  });

  test('no console errors during lightbox interaction', async ({ page, browserName }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', (error) => {
      errors.push(`Page error: ${error.message}`);
    });

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Interact with lightbox
    await openLightbox(page, 0);
    await page.waitForTimeout(300);

    // Navigate through a few images
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(300);

    // Close lightbox
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // Filter out expected third-party CORS errors
    const relevantErrors = filterThirdPartyErrors(errors);

    // Log any errors found
    if (relevantErrors.length > 0) {
      console.log(`Console errors during interaction in ${browserName}:`, relevantErrors);
    }

    expect(relevantErrors.length).toBe(0);
  });

  test('no console errors on photography list page', async ({ page, browserName }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', (error) => {
      errors.push(`Page error: ${error.message}`);
    });

    await page.goto('/photography/');
    await page.waitForLoadState('networkidle');

    // Wait for any scripts to initialize
    await page.waitForTimeout(500);

    // Filter out expected third-party CORS errors
    const relevantErrors = filterThirdPartyErrors(errors);

    if (relevantErrors.length > 0) {
      console.log(`Console errors on photography list in ${browserName}:`, relevantErrors);
    }

    expect(relevantErrors.length).toBe(0);
  });
});
