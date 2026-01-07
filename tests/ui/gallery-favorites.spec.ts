import { test, expect } from '@playwright/test';
import {
  waitForGlightbox,
  openLightbox,
  closeLightbox,
  getLightboxImage,
} from './fixtures';

/**
 * Photography Favorites Gallery tests.
 * Tests the favorites gallery on the /photography/ list page.
 * Task 2.9: Ensure favorites gallery has same behavior as content page galleries.
 */
test.describe('Photography Favorites Gallery', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the photography list page
    await page.goto('/photography/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);
  });

  test('favorites gallery renders with 4 thumbnails', async ({ page }) => {
    // The favorites gallery should have exactly 4 images
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    const count = await thumbnails.count();
    expect(count).toBe(4);

    // Verify all thumbnails are visible
    await expect(thumbnails.first()).toBeVisible();
    await expect(thumbnails.last()).toBeVisible();
  });

  test('favorites gallery has correct data-gallery attribute', async ({ page }) => {
    const links = page.locator('#gallery-favorites a.glightbox');
    const firstLink = links.first();

    // Verify data-gallery attribute for grouping
    await expect(firstLink).toHaveAttribute('data-gallery', 'favorites');
  });

  test('favorites gallery links have data-type="image" attribute', async ({ page }) => {
    // This test verifies the fix for missing data-type attribute
    const links = page.locator('#gallery-favorites a.glightbox');
    const count = await links.count();

    for (let i = 0; i < count; i++) {
      const link = links.nth(i);
      await expect(link).toHaveAttribute('data-type', 'image');
    }
  });

  test('favorites images use full URLs (not thumbnails)', async ({ page }) => {
    // Favorites gallery uses full images as both thumbnail and lightbox source
    // This is intentional since there are only 4 images
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    const firstThumb = thumbnails.first();

    // Get href (lightbox source)
    const href = await firstThumb.getAttribute('href');

    // Get img src (thumbnail source)
    const img = firstThumb.locator('img');
    const src = await img.getAttribute('src');

    // Both should be full images (not .thumb.jpg)
    expect(href).not.toContain('.thumb.jpg');
    expect(src).not.toContain('.thumb.jpg');

    // They should be the same URL (full image used for both)
    expect(href).toBe(src);
  });

  test('clicking favorite thumbnail opens lightbox', async ({ page }) => {
    // Click the first favorite thumbnail
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    await thumbnails.first().click();
    await page.waitForTimeout(500);

    // Verify lightbox opened
    const overlay = page.locator('.goverlay');
    await expect(overlay).toBeVisible();

    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toBeVisible();
  });

  test('lightbox displays image correctly for favorites', async ({ page }) => {
    // Open lightbox
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    await thumbnails.first().click();
    await page.waitForTimeout(500);

    // Get lightbox image
    const lightboxImg = await getLightboxImage(page);

    // Verify image loaded and has reasonable dimensions
    expect(lightboxImg.src).toBeTruthy();
    expect(lightboxImg.width).toBeGreaterThan(100);
    expect(lightboxImg.height).toBeGreaterThan(100);
  });

  test('favorites lightbox fills viewport properly', async ({ page }) => {
    // Open lightbox
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    await thumbnails.first().click();
    await page.waitForTimeout(500);

    // Get lightbox image dimensions
    const lightboxImg = await getLightboxImage(page);

    // Get viewport dimensions
    const viewportSize = page.viewportSize();
    const viewportWidth = viewportSize?.width || 1280;
    const viewportHeight = viewportSize?.height || 720;

    // Lightbox image should fill at least 80% of viewport in at least one dimension
    const widthRatio = lightboxImg.width / viewportWidth;
    const heightRatio = lightboxImg.height / viewportHeight;
    const maxRatio = Math.max(widthRatio, heightRatio);

    expect(maxRatio).toBeGreaterThan(0.8);
  });

  test('favorites gallery supports keyboard navigation', async ({ page }) => {
    // Open lightbox at first image
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    await thumbnails.first().click();
    await page.waitForTimeout(500);

    // Get first image src
    const firstImage = await getLightboxImage(page);
    const firstSrc = firstImage.src;

    // Press right arrow to navigate
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(400);

    // Get second image src
    const secondImage = await getLightboxImage(page);
    expect(secondImage.src).not.toBe(firstSrc);

    // Press left arrow to go back
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(400);

    // Should be back to first image
    const backToFirst = await getLightboxImage(page);
    expect(backToFirst.src).toBe(firstSrc);
  });

  test('ESC key closes favorites lightbox', async ({ page }) => {
    // Open lightbox
    const thumbnails = page.locator('#gallery-favorites a.glightbox');
    await thumbnails.first().click();
    await page.waitForTimeout(500);

    // Verify lightbox is open
    await expect(page.locator('.goverlay')).toBeVisible();

    // Press ESC
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // Verify lightbox is closed
    await expect(page.locator('.goverlay')).not.toBeVisible();
  });

  test('favorites gallery thumbnails have lazy loading', async ({ page }) => {
    const images = page.locator('#gallery-favorites a.glightbox img');
    const count = await images.count();

    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const loading = await img.getAttribute('loading');
      expect(loading).toBe('lazy');
    }
  });

  test('favorites gallery has data-description for captions', async ({ page }) => {
    // Favorites have data-description for location info
    const links = page.locator('#gallery-favorites a.glightbox');
    const firstLink = links.first();

    const description = await firstLink.getAttribute('data-description');
    expect(description).toBeTruthy();
  });

  test('favorites gallery images have alt text', async ({ page }) => {
    const images = page.locator('#gallery-favorites a.glightbox img');
    const count = await images.count();

    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('favorites gallery uses .gallery-grid class for unified styling', async ({ page }) => {
    // Verify the gallery uses the shared gallery-grid class
    const gallery = page.locator('#gallery-favorites');
    await expect(gallery).toHaveClass(/gallery-grid/);
  });

  test('favorites gallery is contained in favorites-preview wrapper', async ({ page }) => {
    // Verify structure for CSS scoping
    const wrapper = page.locator('.favorites-preview');
    await expect(wrapper).toBeVisible();

    const gallery = wrapper.locator('.gallery-grid');
    await expect(gallery).toBeVisible();
  });
});
