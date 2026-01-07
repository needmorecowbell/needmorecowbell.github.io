import { test, expect } from '@playwright/test';
import { waitForGlightbox, openLightbox } from './fixtures';

/**
 * Visual regression tests for gallery layouts.
 * These tests capture screenshots and compare against baseline images
 * to detect unintended visual changes.
 *
 * To update baseline screenshots when intentional changes are made:
 *   npm run test:ui:update-snapshots
 *
 * Screenshots are stored in tests/ui/__screenshots__/{projectName}/
 */
test.describe('Visual Regression - Gallery Grid', () => {
  test('gallery grid layout matches baseline screenshot', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Wait for all visible images to load
    await page.waitForTimeout(1000);

    // Capture gallery grid area only (not full page)
    const galleryGrid = page.locator('.gallery-grid');
    await expect(galleryGrid).toBeVisible();

    await expect(galleryGrid).toHaveScreenshot('gallery-grid-layout.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
  });

  test('photography list page layout matches baseline', async ({ page }) => {
    await page.goto('/photography/');
    await page.waitForLoadState('networkidle');

    // Wait for page content to stabilize
    await page.waitForTimeout(500);

    // Capture the main content area
    const mainContent = page.locator('main').first();
    if (await mainContent.count() > 0) {
      await expect(mainContent).toHaveScreenshot('photography-list-layout.png', {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
      });
    } else {
      // Fallback to full page if no main element
      await expect(page).toHaveScreenshot('photography-list-layout.png', {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
        fullPage: false,
      });
    }
  });
});

test.describe('Visual Regression - Lightbox', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);
  });

  test('lightbox overlay appearance matches baseline (light mode)', async ({ page }) => {
    // Ensure light mode (default)
    await page.emulateMedia({ colorScheme: 'light' });

    // Open lightbox
    await openLightbox(page, 0);

    // Wait for lightbox animation and image to load
    await page.waitForTimeout(800);

    // Verify lightbox is fully loaded
    const lightboxImage = page.locator('.gslide.current img.zoomable').first();
    await expect(lightboxImage).toBeVisible();

    // Capture the lightbox overlay
    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toHaveScreenshot('lightbox-overlay-light.png', {
      maxDiffPixelRatio: 0.03, // Slightly higher threshold for lightbox animations
      animations: 'disabled',
    });
  });

  test('lightbox overlay appearance matches baseline (dark mode)', async ({ page }) => {
    // Emulate dark mode
    await page.emulateMedia({ colorScheme: 'dark' });

    // Reload page to apply dark mode styles
    await page.reload();
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);

    // Wait for lightbox animation and image to load
    await page.waitForTimeout(800);

    // Verify lightbox is fully loaded
    const lightboxImage = page.locator('.gslide.current img.zoomable').first();
    await expect(lightboxImage).toBeVisible();

    // Capture the lightbox overlay
    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toHaveScreenshot('lightbox-overlay-dark.png', {
      maxDiffPixelRatio: 0.03,
      animations: 'disabled',
    });
  });
});

test.describe('Visual Regression - Mobile', () => {
  // These tests run on mobile viewports (configured in playwright.config.ts)
  // The mobile-chrome and mobile-safari projects will execute these

  test('mobile gallery grid layout matches baseline', async ({ page }, testInfo) => {
    // Skip if not a mobile project
    const isMobile = testInfo.project.name.includes('mobile');
    if (!isMobile) {
      test.skip();
      return;
    }

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Wait for layout to stabilize
    await page.waitForTimeout(1000);

    // Capture gallery grid on mobile
    const galleryGrid = page.locator('.gallery-grid');
    await expect(galleryGrid).toBeVisible();

    await expect(galleryGrid).toHaveScreenshot('mobile-gallery-grid.png', {
      maxDiffPixelRatio: 0.03,
      animations: 'disabled',
    });
  });

  test('mobile lightbox appearance matches baseline', async ({ page }, testInfo) => {
    // Skip if not a mobile project
    const isMobile = testInfo.project.name.includes('mobile');
    if (!isMobile) {
      test.skip();
      return;
    }

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);

    // Wait for animation and image load
    await page.waitForTimeout(800);

    // Capture lightbox on mobile
    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toHaveScreenshot('mobile-lightbox.png', {
      maxDiffPixelRatio: 0.03,
      animations: 'disabled',
    });
  });
});

test.describe('Visual Regression - Component Details', () => {
  test('thumbnail hover state appearance', async ({ page }, testInfo) => {
    // Skip on mobile (no hover state)
    const isMobile = testInfo.project.name.includes('mobile');
    if (isMobile) {
      test.skip();
      return;
    }

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    const firstThumbnail = page.locator('.gallery-grid a.glightbox').first();
    await expect(firstThumbnail).toBeVisible();

    // Hover over thumbnail
    await firstThumbnail.hover();
    await page.waitForTimeout(300); // Wait for hover transition

    // Screenshot the hovered thumbnail
    await expect(firstThumbnail).toHaveScreenshot('thumbnail-hover-state.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
  });

  test('lightbox navigation controls appearance', async ({ page }, testInfo) => {
    // Skip on mobile (different controls)
    const isMobile = testInfo.project.name.includes('mobile');
    if (isMobile) {
      test.skip();
      return;
    }

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    await openLightbox(page, 0);
    await page.waitForTimeout(500);

    // Move mouse to make controls visible
    await page.mouse.move(100, 300);
    await page.waitForTimeout(200);

    // Screenshot the navigation buttons
    const nextBtn = page.locator('.gnext');
    const prevBtn = page.locator('.gprev');

    if (await nextBtn.isVisible()) {
      await expect(nextBtn).toHaveScreenshot('lightbox-next-button.png', {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
      });
    }

    if (await prevBtn.isVisible()) {
      await expect(prevBtn).toHaveScreenshot('lightbox-prev-button.png', {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
      });
    }
  });

  test('lightbox close button appearance', async ({ page }, testInfo) => {
    // Skip on mobile (different controls)
    const isMobile = testInfo.project.name.includes('mobile');
    if (isMobile) {
      test.skip();
      return;
    }

    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    await openLightbox(page, 0);
    await page.waitForTimeout(500);

    // Screenshot the close button
    const closeBtn = page.locator('.gclose');
    if (await closeBtn.isVisible()) {
      await expect(closeBtn).toHaveScreenshot('lightbox-close-button.png', {
        maxDiffPixelRatio: 0.02,
        animations: 'disabled',
      });
    }
  });
});
