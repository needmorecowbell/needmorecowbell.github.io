import { test, expect } from '@playwright/test';
import { waitForGlightbox, openLightbox, countGalleryThumbnails } from './fixtures';

/**
 * Photography section specific tests.
 * Tests the photography list page, favorites gallery, individual galleries,
 * and S3CDN URL patterns.
 */

// Expected S3CDN URL pattern
const S3CDN_PATTERN = /^https:\/\/cdn\.414d\.net\/amblog\/assets\//;

test.describe('Photography List Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/photography/');
    await page.waitForLoadState('networkidle');
  });

  test('photography list page loads with favorites gallery', async ({ page }) => {
    // Verify the favorites preview section exists
    const favoritesPreview = page.locator('.favorites-preview');
    await expect(favoritesPreview).toBeVisible();

    // Verify the favorites gallery grid exists
    const favoritesGallery = page.locator('#gallery-favorites');
    await expect(favoritesGallery).toBeVisible();

    // Verify favorites gallery has images
    const favoritesImages = page.locator('#gallery-favorites a.glightbox');
    const count = await favoritesImages.count();
    expect(count).toBeGreaterThan(0);
  });

  test('favorites gallery thumbnails are clickable', async ({ page }) => {
    await waitForGlightbox(page);

    // Get the favorites gallery
    const favoritesGallery = page.locator('#gallery-favorites');
    await expect(favoritesGallery).toBeVisible();

    // Click the first thumbnail in favorites gallery
    const firstThumbnail = page.locator('#gallery-favorites a.glightbox').first();
    await expect(firstThumbnail).toBeVisible();
    await firstThumbnail.click();

    // Verify lightbox opened
    const overlay = page.locator('.goverlay');
    await expect(overlay).toBeVisible();

    // Verify image is displayed in lightbox
    const lightboxImage = page.locator('.gslide.current img.zoomable').first();
    await expect(lightboxImage).toBeVisible();
  });

  test('favorites gallery images point to S3CDN', async ({ page }) => {
    // Check all favorites gallery image URLs
    const favoritesImages = page.locator('#gallery-favorites a.glightbox');
    const count = await favoritesImages.count();

    for (let i = 0; i < count; i++) {
      const link = favoritesImages.nth(i);
      const href = await link.getAttribute('href');

      // Full image URL should point to S3CDN
      expect(href).toMatch(S3CDN_PATTERN);
    }
  });

  test('photography list shows individual photography pages', async ({ page }) => {
    // Verify the list of photography posts exists
    const listItems = page.locator('.listing-item');
    const count = await listItems.count();

    // Should have at least one photography entry
    expect(count).toBeGreaterThan(0);

    // Verify links to individual pages exist
    const firstLink = page.locator('.listing-post a').first();
    await expect(firstLink).toBeVisible();
    const href = await firstLink.getAttribute('href');
    expect(href).toContain('/photography/');
  });
});

test.describe('Individual Photography Pages', () => {
  test('individual photography pages load with their galleries', async ({ page }) => {
    // Navigate to Nova Scotia gallery page
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Verify gallery grid exists
    const galleryGrid = page.locator('.gallery-grid');
    await expect(galleryGrid).toBeVisible();

    // Verify thumbnails are present
    const thumbnailCount = await countGalleryThumbnails(page);
    expect(thumbnailCount).toBeGreaterThan(0);

    // Verify page title is correct
    await expect(page).toHaveTitle(/Nova Scotia/);
  });

  test('Nova Scotia gallery loads all 19 images from S3CDN', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Count thumbnails - should be exactly 19
    const thumbnailCount = await countGalleryThumbnails(page);
    expect(thumbnailCount).toBe(19);

    // Verify all thumbnails are glightbox-enabled
    const glightboxItems = page.locator('.gallery-grid a.glightbox');
    const glightboxCount = await glightboxItems.count();
    expect(glightboxCount).toBe(19);
  });
});

test.describe('S3CDN URL Patterns', () => {
  test('image URLs correctly point to S3CDN (not local paths)', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Check all gallery image href attributes
    const galleryLinks = page.locator('.gallery-grid a.glightbox');
    const count = await galleryLinks.count();

    for (let i = 0; i < count; i++) {
      const link = galleryLinks.nth(i);
      const href = await link.getAttribute('href');

      // Full image URLs should point to S3CDN
      expect(href).toMatch(S3CDN_PATTERN);

      // Should NOT be a local path
      expect(href).not.toMatch(/^\/img\//);
      expect(href).not.toMatch(/^\.\.?\//);
    }
  });

  test('thumbnail URLs use .thumb.jpg suffix pattern', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Check all thumbnail image src attributes
    const thumbnailImages = page.locator('.gallery-grid a.glightbox img');
    const count = await thumbnailImages.count();

    for (let i = 0; i < count; i++) {
      const img = thumbnailImages.nth(i);
      const src = await img.getAttribute('src');

      // Thumbnail URLs should use .thumb.jpg suffix
      expect(src).toMatch(/\.thumb\.jpg$/);

      // Thumbnail URLs should also point to S3CDN
      expect(src).toMatch(S3CDN_PATTERN);
    }
  });

  test('full-resolution images do not have .thumb.jpg suffix', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Open lightbox
    await openLightbox(page, 0);

    // Wait for image to load
    await page.waitForTimeout(500);

    // Get the full-resolution image URL
    const lightboxImage = page.locator('.gslide.current img.zoomable').first();
    await expect(lightboxImage).toBeVisible();

    const src = await lightboxImage.getAttribute('src');

    // Full resolution image should NOT have .thumb.jpg suffix
    expect(src).not.toMatch(/\.thumb\.jpg$/);

    // But should still point to S3CDN
    expect(src).toMatch(S3CDN_PATTERN);
  });

  test('thumbnail and full-resolution have matching base names', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Get thumbnail src
    const firstThumb = page.locator('.gallery-grid a.glightbox').first();
    const thumbImg = firstThumb.locator('img');
    const thumbSrc = await thumbImg.getAttribute('src');

    // Get full image href
    const fullHref = await firstThumb.getAttribute('href');

    // Extract base names (without .thumb.jpg or extension)
    // thumbSrc: .../20230426_092045.thumb.jpg
    // fullHref: .../20230426_092045.jpg
    const thumbBaseName = thumbSrc?.replace(/\.thumb\.jpg$/, '').split('/').pop();
    const fullBaseName = fullHref?.replace(/\.(jpg|jpeg|png|gif)$/i, '').split('/').pop();

    expect(thumbBaseName).toBe(fullBaseName);
  });
});

test.describe('Photography Gallery Navigation', () => {
  test('can navigate through all gallery images', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Open lightbox at first image
    await openLightbox(page, 0);

    // Get first image src
    const firstSrc = await page.locator('.gslide.current img.zoomable').first().getAttribute('src');

    // Navigate to next image
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(400);

    // Verify we're on a different image
    const secondSrc = await page.locator('.gslide.current img.zoomable').first().getAttribute('src');
    expect(secondSrc).not.toBe(firstSrc);

    // Navigate back
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(400);

    // Verify we're back to first image
    const backToFirstSrc = await page.locator('.gslide.current img.zoomable').first().getAttribute('src');
    expect(backToFirstSrc).toBe(firstSrc);
  });

  test('can open specific thumbnail in gallery', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);

    // Get the href of the 5th thumbnail (index 4)
    const fifthThumb = page.locator('.gallery-grid a.glightbox').nth(4);
    const expectedHref = await fifthThumb.getAttribute('href');

    // Open lightbox at 5th image
    await openLightbox(page, 4);

    // Verify the correct image is displayed
    const lightboxSrc = await page.locator('.gslide.current img.zoomable').first().getAttribute('src');

    // Both should point to the same image (lightbox loads full res from href)
    expect(lightboxSrc).toBe(expectedHref);
  });
});

test.describe('Photography Lazy Loading', () => {
  test('gallery thumbnails use lazy loading', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Check all thumbnails have lazy loading attribute
    const thumbnails = page.locator('.gallery-grid a.glightbox img');
    const count = await thumbnails.count();

    for (let i = 0; i < count; i++) {
      const img = thumbnails.nth(i);
      const loading = await img.getAttribute('loading');
      expect(loading).toBe('lazy');
    }
  });
});

test.describe('Photography Accessibility', () => {
  test('gallery has proper accessibility attributes', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Verify gallery has role and aria-label
    const gallery = page.locator('.gallery-grid');
    await expect(gallery).toHaveAttribute('role', 'region');
    await expect(gallery).toHaveAttribute('aria-label', /./);
  });

  test('gallery images have descriptive alt text', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Check that images have non-empty alt text
    const thumbnails = page.locator('.gallery-grid a.glightbox img');
    const count = await thumbnails.count();

    // Check first few images
    for (let i = 0; i < Math.min(5, count); i++) {
      const img = thumbnails.nth(i);
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
      expect(alt!.length).toBeGreaterThan(0);
    }
  });

  test('gallery links have aria-label for screen readers', async ({ page }) => {
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');

    // Check that links have aria-label
    const links = page.locator('.gallery-grid a.glightbox');
    const count = await links.count();

    for (let i = 0; i < Math.min(5, count); i++) {
      const link = links.nth(i);
      const ariaLabel = await link.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toContain('image');
    }
  });
});
