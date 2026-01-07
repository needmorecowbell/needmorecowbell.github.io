import { test, expect } from '@playwright/test';
import { waitForGlightbox, openLightbox } from './fixtures';

/**
 * Dark mode gallery tests - Phase 2.5
 * Tests gallery-specific dark mode styling and behavior.
 */
test.describe('Gallery Dark Mode', () => {
  test.beforeEach(async ({ page }) => {
    // Set dark mode
    await page.emulateMedia({ colorScheme: 'dark' });
    // Navigate to gallery page
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    // Click the theme toggle to enable dark mode in the site's theme system
    const themeToggle = page.locator('.theme-switch');
    if (await themeToggle.count() > 0) {
      // Check if dark mode is already active
      const htmlTheme = await page.getAttribute('html', 'data-theme');
      if (htmlTheme !== 'dark') {
        await themeToggle.click();
        await page.waitForTimeout(300);
      }
    }
    await waitForGlightbox(page);
  });

  test('gallery grid has correct dark mode background', async ({ page }) => {
    // Check gallery grid item background (placeholder before image loads)
    const galleryItem = page.locator('.gallery-grid a').first();
    await expect(galleryItem).toBeVisible();

    // Get computed background color
    const bgColor = await galleryItem.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Should be using dark mode secondary background color (not light mode)
    // Dark mode secondary-bg-color is #161b22 = rgb(22, 27, 34)
    // Light mode secondary-bg-color is #f3f4f6 = rgb(243, 244, 246)
    // Allow for some variation in case of CSS variable fallbacks
    expect(bgColor).not.toBe('rgb(243, 244, 246)'); // Should NOT be light mode color
    expect(bgColor).not.toBe('rgb(238, 238, 238)'); // Should NOT be old fallback color
    console.log('Gallery item background color:', bgColor);
  });

  test('GLightbox overlay has appropriate dark background', async ({ page }) => {
    // Open lightbox
    await openLightbox(page, 0);
    await page.waitForTimeout(500);

    // Check overlay background
    const overlay = page.locator('.goverlay');
    await expect(overlay).toBeVisible();

    const overlayBg = await overlay.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // GLightbox default is a dark overlay (rgba(0, 0, 0, ~0.9))
    // Check it's dark enough (not light colored)
    console.log('Lightbox overlay background:', overlayBg);

    // Parse RGB values to verify it's dark
    const rgbMatch = overlayBg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (rgbMatch) {
      const [_, r, g, b] = rgbMatch.map(Number);
      // All RGB values should be low (dark)
      expect(r).toBeLessThan(50);
      expect(g).toBeLessThan(50);
      expect(b).toBeLessThan(50);
    }
  });

  test('lightbox controls are visible against dark overlay', async ({ page }) => {
    // Open lightbox
    await openLightbox(page, 0);
    await page.waitForTimeout(500);

    // Verify close button is visible
    const closeBtn = page.locator('.gclose');
    await expect(closeBtn).toBeVisible();

    // Verify navigation buttons are visible
    const nextBtn = page.locator('.gnext');
    const prevBtn = page.locator('.gprev');
    await expect(nextBtn).toBeVisible();
    await expect(prevBtn).toBeVisible();
  });

  test('lightbox image is clearly visible in dark mode', async ({ page }) => {
    // Open lightbox
    await openLightbox(page, 0);
    await page.waitForTimeout(500);

    // Verify image is loaded and visible
    const lightboxImage = page.locator('.gslide.current img.zoomable').first();
    await expect(lightboxImage).toBeVisible();

    // Get image dimensions to ensure it's displayed properly
    const box = await lightboxImage.boundingBox();
    expect(box?.width).toBeGreaterThan(100);
    expect(box?.height).toBeGreaterThan(100);
  });

  test('gallery thumbnail images display correctly in dark mode', async ({ page }) => {
    // Check that thumbnails are visible and properly styled
    const thumbnails = page.locator('.gallery-grid a.glightbox');
    const count = await thumbnails.count();
    expect(count).toBeGreaterThan(0);

    // Check first few thumbnails have images that loaded
    for (let i = 0; i < Math.min(3, count); i++) {
      const img = thumbnails.nth(i).locator('img');
      await expect(img).toBeVisible();

      // Verify image has dimensions (loaded successfully)
      const box = await img.boundingBox();
      expect(box?.width).toBeGreaterThan(50);
      expect(box?.height).toBeGreaterThan(50);
    }
  });

  test('hover effect works on thumbnails in dark mode', async ({ page }, testInfo) => {
    // Skip on mobile (no hover)
    if (testInfo.project.name.includes('mobile')) {
      test.skip();
      return;
    }

    const firstThumb = page.locator('.gallery-grid a.glightbox').first();
    await expect(firstThumb).toBeVisible();

    // Get initial transform
    const initialTransform = await firstThumb.locator('img').evaluate((el) => {
      return window.getComputedStyle(el).transform;
    });

    // Hover over thumbnail
    await firstThumb.hover();
    await page.waitForTimeout(400); // Wait for transition

    // Get hover transform
    const hoverTransform = await firstThumb.locator('img').evaluate((el) => {
      return window.getComputedStyle(el).transform;
    });

    // Hover should apply scale transform
    console.log('Initial transform:', initialTransform);
    console.log('Hover transform:', hoverTransform);

    // The hover state should either have a different transform or be scaled
    // The CSS has: transform: scale(1.05)
    if (initialTransform === 'none' || initialTransform === 'matrix(1, 0, 0, 1, 0, 0)') {
      // On hover, should be scaled (matrix with values > 1)
      expect(hoverTransform).not.toBe('none');
      expect(hoverTransform).toContain('matrix');
    }
  });
});

/**
 * Visual regression for dark mode gallery
 */
test.describe('Gallery Dark Mode Visual Regression', () => {
  test('gallery grid dark mode matches baseline', async ({ page }, testInfo) => {
    // Skip on mobile for this test
    if (testInfo.project.name.includes('mobile')) {
      test.skip();
      return;
    }

    // Set dark mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Ensure dark theme is active
    const themeToggle = page.locator('.theme-switch');
    if (await themeToggle.count() > 0) {
      const htmlTheme = await page.getAttribute('html', 'data-theme');
      if (htmlTheme !== 'dark') {
        await themeToggle.click();
        await page.waitForTimeout(300);
      }
    }

    await waitForGlightbox(page);
    await page.waitForTimeout(500);

    // Capture gallery grid
    const galleryGrid = page.locator('.gallery-grid');
    await expect(galleryGrid).toBeVisible();

    await expect(galleryGrid).toHaveScreenshot('gallery-grid-dark-mode.png', {
      maxDiffPixelRatio: 0.03,
      animations: 'disabled',
    });
  });
});
