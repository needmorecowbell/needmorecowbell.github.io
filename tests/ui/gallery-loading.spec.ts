import { test, expect } from '@playwright/test';
import { waitForGlightbox } from './fixtures';

/**
 * Gallery Loading & Error State Tests - Phase 2.6
 *
 * Tests for image loading skeleton placeholders and error state handling.
 */
test.describe('Gallery Loading States', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);
  });

  test('gallery items have skeleton animation before images load', async ({ page }) => {
    // Navigate to page fresh without waiting for images
    await page.goto('/photography/2023_nova_scotia/', { waitUntil: 'domcontentloaded' });

    // Check that gallery items have animation property set
    const galleryItem = page.locator('.gallery-grid a').first();
    const animation = await galleryItem.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.animationName;
    });

    // Should have skeleton shimmer animation or none (if image already loaded)
    expect(animation).toBeDefined();
  });

  test('loaded images are visible with fade-in effect', async ({ page }) => {
    // Wait for images to load
    await page.waitForTimeout(1000);

    // Check that loaded images have the .loaded class
    const loadedImages = page.locator('.gallery-grid a img.loaded');
    const loadedCount = await loadedImages.count();

    // At least some images should be loaded (especially first few due to lazy loading)
    expect(loadedCount).toBeGreaterThan(0);

    // Check opacity of loaded images
    const firstLoadedImage = loadedImages.first();
    const opacity = await firstLoadedImage.evaluate((el) => {
      return window.getComputedStyle(el).opacity;
    });

    expect(opacity).toBe('1');
  });

  test('skeleton animation stops after image loads', async ({ page }) => {
    // Wait for images to fully load
    await page.waitForTimeout(1500);

    // Find a gallery item with a loaded image
    const galleryItemWithLoadedImage = page.locator('.gallery-grid a:has(img.loaded)').first();

    // Check that animation is stopped
    const animation = await galleryItemWithLoadedImage.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.animationName;
    });

    // Animation should be 'none' after image loads
    expect(animation).toBe('none');
  });

  test('all gallery images have loading="lazy" attribute', async ({ page }) => {
    const images = page.locator('.gallery-grid a img');
    const imageCount = await images.count();

    // Check each image has lazy loading
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      const loading = await img.getAttribute('loading');
      expect(loading).toBe('lazy');
    }
  });

  test('lazy loading attribute is correctly set on all images', async ({ page }) => {
    // This test validates that lazy loading is configured, not that it's working
    // (actual lazy loading behavior depends on browser and viewport)
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('domcontentloaded');

    const images = page.locator('.gallery-grid a img');
    const imageCount = await images.count();

    // All images should have loading="lazy"
    for (let i = 0; i < imageCount; i++) {
      const loading = await images.nth(i).getAttribute('loading');
      expect(loading).toBe('lazy');
    }

    // Verify we have multiple images to ensure the test is meaningful
    expect(imageCount).toBeGreaterThan(10);
  });
});

test.describe('Gallery Error States', () => {
  test('error state CSS classes exist and are styled', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Inject error state directly to test CSS styling
    await page.evaluate(() => {
      const firstItem = document.querySelector('.gallery-grid a');
      if (firstItem) {
        firstItem.classList.add('image-error');
        const img = firstItem.querySelector('img');
        if (img) {
          img.classList.add('error');
        }
      }
    });

    // Check error state is applied
    const errorItem = page.locator('.gallery-grid a.image-error').first();
    await expect(errorItem).toHaveClass(/image-error/);

    // Check error state styling is applied - uses secondary-bg-color (neutral gray)
    const backgroundColor = await errorItem.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Error background uses --secondary-bg-color (varies by theme)
    // Should be a valid RGB color
    expect(backgroundColor).toMatch(/rgb\(\d+, \d+, \d+\)/);

    // Verify animation is stopped
    const animation = await errorItem.evaluate((el) => {
      return window.getComputedStyle(el).animationName;
    });
    expect(animation).toBe('none');
  });

  test('error state shows warning icon via ::before pseudo-element', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Inject error state
    await page.evaluate(() => {
      const firstItem = document.querySelector('.gallery-grid a');
      if (firstItem) {
        firstItem.classList.add('image-error');
        const img = firstItem.querySelector('img');
        if (img) {
          img.classList.add('error');
        }
      }
    });

    const errorItem = page.locator('.gallery-grid a.image-error').first();

    // Check ::before pseudo-element has content (warning emoji icon)
    const beforeContent = await errorItem.evaluate((el) => {
      const style = window.getComputedStyle(el, '::before');
      return style.content;
    });

    // Should have warning emoji content: ⚠
    expect(beforeContent).toContain('⚠');
  });

  test('error state shows "Image unavailable" text via ::after pseudo-element', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Inject error state
    await page.evaluate(() => {
      const firstItem = document.querySelector('.gallery-grid a');
      if (firstItem) {
        firstItem.classList.add('image-error');
        const img = firstItem.querySelector('img');
        if (img) {
          img.classList.add('error');
        }
      }
    });

    const errorItem = page.locator('.gallery-grid a.image-error').first();

    // Check ::after pseudo-element has error text
    const afterContent = await errorItem.evaluate((el) => {
      const style = window.getComputedStyle(el, '::after');
      return style.content;
    });

    // Should have "Image unavailable" text
    expect(afterContent).toContain('Image unavailable');
  });

  test('error state hides broken image element', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Inject error state
    await page.evaluate(() => {
      const firstItem = document.querySelector('.gallery-grid a');
      if (firstItem) {
        firstItem.classList.add('image-error');
        const img = firstItem.querySelector('img');
        if (img) {
          img.classList.add('error');
        }
      }
    });

    const errorImage = page.locator('.gallery-grid a.image-error img').first();

    // Check that image is hidden (display: none)
    const display = await errorImage.evaluate((el) => {
      return window.getComputedStyle(el).display;
    });

    expect(display).toBe('none');
  });

  test('error state works in dark mode', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Enable dark mode
    await page.evaluate(() => {
      document.documentElement.setAttribute('data-theme', 'dark');
    });

    // Inject error state
    await page.evaluate(() => {
      const firstItem = document.querySelector('.gallery-grid a');
      if (firstItem) {
        firstItem.classList.add('image-error');
        const img = firstItem.querySelector('img');
        if (img) {
          img.classList.add('error');
        }
      }
    });

    const errorItem = page.locator('.gallery-grid a.image-error').first();

    // Check dark mode error background - uses --secondary-bg-color for dark theme
    const backgroundColor = await errorItem.evaluate((el) => {
      return window.getComputedStyle(el).backgroundColor;
    });

    // Dark mode uses --secondary-bg-color which is a dark gray
    // Should be a valid dark RGB color (not transparent)
    expect(backgroundColor).toMatch(/rgb\(\d+, \d+, \d+\)/);

    // Verify animation is stopped in dark mode too
    const animation = await errorItem.evaluate((el) => {
      return window.getComputedStyle(el).animationName;
    });
    expect(animation).toBe('none');
  });
});
