import { test as base, expect, Page } from '@playwright/test';

/**
 * Extended test fixture with shared helpers for gallery testing.
 */
export const test = base.extend<{
  galleryPage: Page;
}>({
  galleryPage: async ({ page }, use) => {
    // Navigate to a page with a gallery before each test
    await page.goto('/photography/2023_nova_scotia/');
    await page.waitForLoadState('networkidle');
    await use(page);
  },
});

export { expect };

/**
 * Helper to wait for GLightbox to be fully initialized.
 */
export async function waitForGlightbox(page: Page): Promise<void> {
  // Wait for GLightbox script to load and initialize
  await page.waitForFunction(() => {
    return typeof (window as any).GLightbox !== 'undefined';
  }, { timeout: 10000 });
}

/**
 * Helper to open lightbox by clicking a gallery image.
 */
export async function openLightbox(page: Page, index: number = 0): Promise<void> {
  const galleryItems = page.locator('.glightbox');
  await galleryItems.nth(index).click();
  // Wait for lightbox overlay to appear
  await page.waitForSelector('.goverlay', { state: 'visible', timeout: 5000 });
}

/**
 * Helper to close the lightbox.
 */
export async function closeLightbox(page: Page): Promise<void> {
  // Click the close button - use force to bypass overlay z-index issues
  const closeBtn = page.locator('.gclose');
  if (await closeBtn.isVisible()) {
    await closeBtn.click({ force: true });
  }
  // Wait for overlay to disappear
  await page.waitForSelector('.goverlay', { state: 'hidden', timeout: 5000 });
}

/**
 * Helper to get the current image in the lightbox.
 */
export async function getLightboxImage(page: Page): Promise<{
  src: string;
  width: number;
  height: number;
}> {
  // Wait for slide transition to complete - look for single current slide
  await page.waitForTimeout(100);

  // Use first() to handle case where multiple elements match during transition
  const img = page.locator('.gslide.current img.zoomable').first();
  await img.waitFor({ state: 'visible', timeout: 5000 });

  const src = await img.getAttribute('src') || '';
  const box = await img.boundingBox();

  return {
    src,
    width: box?.width || 0,
    height: box?.height || 0,
  };
}

/**
 * Helper to navigate to next image in lightbox.
 */
export async function lightboxNext(page: Page): Promise<void> {
  const nextBtn = page.locator('.gnext');
  if (await nextBtn.isVisible()) {
    await nextBtn.click({ force: true });
    // Wait for slide transition animation to complete
    await page.waitForTimeout(500);
  }
}

/**
 * Helper to navigate to previous image in lightbox.
 */
export async function lightboxPrev(page: Page): Promise<void> {
  const prevBtn = page.locator('.gprev');
  if (await prevBtn.isVisible()) {
    await prevBtn.click({ force: true });
    // Wait for slide transition animation to complete
    await page.waitForTimeout(500);
  }
}

/**
 * Helper to get gallery counter text (e.g., "3 of 15").
 */
export async function getLightboxCounter(page: Page): Promise<string> {
  const counter = page.locator('.gslide-current_count');
  if (await counter.isVisible()) {
    return await counter.textContent() || '';
  }
  return '';
}

/**
 * Helper to count gallery thumbnails on the page.
 */
export async function countGalleryThumbnails(page: Page): Promise<number> {
  const thumbnails = page.locator('.gallery-grid a.glightbox');
  return await thumbnails.count();
}

/**
 * Helper to check if page has JavaScript console errors.
 */
export async function checkNoConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}
