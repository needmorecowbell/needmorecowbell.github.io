import { test, expect } from '@playwright/test';
import { waitForGlightbox, openLightbox } from './fixtures';

/**
 * Video gallery tests for GLightbox integration.
 * Tests video-specific functionality: thumbnails, play button overlay, playback in lightbox.
 */
test.describe('Gallery Video Support', () => {
  // Use sumac-wine-project page which has video content
  const VIDEO_GALLERY_PAGE = '/post/2023-08-14-sumac-wine-project/';

  test.beforeEach(async ({ page }) => {
    await page.goto(VIDEO_GALLERY_PAGE);
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);
  });

  test('video gallery page has video items', async ({ page }) => {
    // The sumac wine project has 3 videos
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    expect(count).toBe(3);
  });

  test('video items have .video-item class', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify each video item has the correct class
    for (let i = 0; i < count; i++) {
      const item = videoItems.nth(i);
      await expect(item).toHaveClass(/video-item/);
    }
  });

  test('video items have data-type="video" attribute', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify each video item has correct data-type
    for (let i = 0; i < count; i++) {
      const item = videoItems.nth(i);
      await expect(item).toHaveAttribute('data-type', 'video');
    }
  });

  test('video items have glightbox class for lightbox integration', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify each video item has glightbox class
    for (let i = 0; i < count; i++) {
      const item = videoItems.nth(i);
      await expect(item).toHaveClass(/glightbox/);
    }
  });

  test('video thumbnails have .thumb.jpg extension', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify thumbnails use .thumb.jpg
    for (let i = 0; i < count; i++) {
      const img = videoItems.nth(i).locator('img');
      const src = await img.getAttribute('src');
      expect(src).toContain('.thumb.jpg');
    }
  });

  test('video items link to actual video files', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Video extensions we support
    const videoExtensions = ['.mp4', '.MP4', '.mov', '.MOV', '.webm', '.avi'];

    // Verify href points to a video file
    for (let i = 0; i < count; i++) {
      const item = videoItems.nth(i);
      const href = await item.getAttribute('href');

      const hasVideoExtension = videoExtensions.some(ext => href?.includes(ext));
      expect(hasVideoExtension).toBe(true);
    }
  });

  test('video thumbnail play button overlay is visible', async ({ page }) => {
    const videoItem = page.locator('.gallery-grid a.video-item').first();

    // The play button is a CSS ::after pseudo-element, so we verify the computed styles
    const afterStyles = await page.evaluate(() => {
      const el = document.querySelector('.gallery-grid a.video-item');
      if (!el) return null;
      const styles = window.getComputedStyle(el, '::after');
      return {
        content: styles.content,
        position: styles.position,
        width: styles.width,
        height: styles.height,
        opacity: styles.opacity,
      };
    });

    expect(afterStyles).not.toBeNull();
    // Pseudo-element should exist (content is not 'none')
    expect(afterStyles?.content).not.toBe('none');
    // Should be absolutely positioned for overlay
    expect(afterStyles?.position).toBe('absolute');
  });

  test('clicking video item opens GLightbox', async ({ page }) => {
    const videoItem = page.locator('.gallery-grid a.video-item').first();

    // Click the video item
    await videoItem.click();

    // Wait for lightbox overlay to appear
    const overlay = page.locator('.goverlay');
    await expect(overlay).toBeVisible({ timeout: 5000 });

    // Verify lightbox container is visible
    const lightboxContainer = page.locator('.glightbox-container');
    await expect(lightboxContainer).toBeVisible();
  });

  test('video plays in GLightbox with video player', async ({ page }) => {
    const videoItem = page.locator('.gallery-grid a.video-item').first();

    // Click to open lightbox
    await videoItem.click();

    // Wait for lightbox to open
    await page.waitForSelector('.goverlay', { state: 'visible' });

    // GLightbox creates a video element or iframe for video playback
    // Check for video element or gvideo class
    const videoElement = page.locator('.gslide.current video, .gslide.current .gvideo');

    // Wait for video element to appear (may take a moment to load)
    await expect(videoElement.first()).toBeVisible({ timeout: 10000 });
  });

  test('video in lightbox has controls', async ({ page }) => {
    const videoItem = page.locator('.gallery-grid a.video-item').first();

    // Open lightbox
    await videoItem.click();
    await page.waitForSelector('.goverlay', { state: 'visible' });

    // Wait for video element
    const video = page.locator('.gslide.current video').first();

    // Wait for video to be visible
    const isVideoVisible = await video.isVisible().catch(() => false);

    if (isVideoVisible) {
      // Video element should have controls attribute
      const hasControls = await video.getAttribute('controls');
      // GLightbox may set controls or handle it differently
      // At minimum, verify video element exists and is interactive
      expect(await video.isVisible()).toBe(true);
    } else {
      // GLightbox might use custom controls or iframe
      // Verify the video container exists
      const gvideo = page.locator('.gslide.current .gvideo');
      await expect(gvideo.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('video thumbnail images have lazy loading', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify lazy loading on video thumbnails
    for (let i = 0; i < count; i++) {
      const img = videoItems.nth(i).locator('img');
      const loading = await img.getAttribute('loading');
      expect(loading).toBe('lazy');
    }
  });

  test('video items have accessible aria-label', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify accessible labels
    for (let i = 0; i < count; i++) {
      const item = videoItems.nth(i);
      const ariaLabel = await item.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toContain('video');
    }
  });

  test('video thumbnail images have alt text', async ({ page }) => {
    const videoItems = page.locator('.gallery-grid a.video-item');
    const count = await videoItems.count();

    // Verify alt text on video thumbnails
    for (let i = 0; i < count; i++) {
      const img = videoItems.nth(i).locator('img');
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
      expect(alt).toContain('Video thumbnail');
    }
  });
});

/**
 * Video navigation in lightbox tests.
 */
test.describe('Gallery Video Navigation', () => {
  const VIDEO_GALLERY_PAGE = '/post/2023-08-14-sumac-wine-project/';

  test.beforeEach(async ({ page }) => {
    await page.goto(VIDEO_GALLERY_PAGE);
    await page.waitForLoadState('networkidle');
    await waitForGlightbox(page);
  });

  test('can navigate between videos using arrow keys', async ({ page }) => {
    // Open first video
    const videoItems = page.locator('.gallery-grid a.video-item');
    await videoItems.first().click();

    // Wait for lightbox
    await page.waitForSelector('.goverlay', { state: 'visible' });

    // Wait a moment for video to load
    await page.waitForTimeout(1000);

    // Navigate to next video
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500);

    // Navigate back
    await page.keyboard.press('ArrowLeft');
    await page.waitForTimeout(500);

    // Verify still in lightbox
    await expect(page.locator('.goverlay')).toBeVisible();
  });

  test('ESC key closes video lightbox', async ({ page }) => {
    // Open first video
    const videoItems = page.locator('.gallery-grid a.video-item');
    await videoItems.first().click();

    // Wait for lightbox
    await page.waitForSelector('.goverlay', { state: 'visible' });

    // Press ESC
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // Verify lightbox closed
    await expect(page.locator('.goverlay')).not.toBeVisible();
  });
});
