import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { waitForGlightbox, openLightbox } from './fixtures';

/**
 * Gallery accessibility tests using axe-core.
 * Tests WCAG 2.1 AA compliance for gallery pages.
 */
test.describe('Gallery Accessibility', () => {
  test.describe('Gallery Grid Accessibility', () => {
    test('gallery grid has no critical accessibility violations', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('.gallery-grid')
        .analyze();

      // Filter for critical and serious violations only
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });

    test('all gallery images have alt text', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const images = page.locator('.gallery-grid img');
      const count = await images.count();

      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        expect(alt, `Image ${i} should have alt text`).toBeTruthy();
        expect(alt!.length, `Image ${i} alt should not be empty`).toBeGreaterThan(0);
      }
    });

    test('gallery links have aria-labels', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const links = page.locator('.gallery-grid a.glightbox');
      const count = await links.count();

      for (let i = 0; i < count; i++) {
        const link = links.nth(i);
        const ariaLabel = await link.getAttribute('aria-label');
        expect(ariaLabel, `Link ${i} should have aria-label`).toBeTruthy();
        expect(ariaLabel, `Link ${i} aria-label should describe action`).toContain('image');
      }
    });

    test('gallery has role="region" with accessible name', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const gallery = page.locator('.gallery-grid');
      await expect(gallery).toHaveAttribute('role', 'region');

      const ariaLabel = await gallery.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel!.length).toBeGreaterThan(0);
    });

    test('video items have appropriate aria-labels', async ({ page }) => {
      await page.goto('/post/2023-08-14-sumac-wine-project/');
      await page.waitForLoadState('networkidle');

      const videoLinks = page.locator('.gallery-grid a.video-item');
      const count = await videoLinks.count();

      if (count > 0) {
        for (let i = 0; i < count; i++) {
          const link = videoLinks.nth(i);
          const ariaLabel = await link.getAttribute('aria-label');
          expect(ariaLabel, `Video link ${i} should have aria-label`).toBeTruthy();
          expect(ariaLabel, `Video link ${i} aria-label should describe video action`).toContain('video');
        }
      }
    });
  });

  test.describe('Lightbox Accessibility', () => {
    test('lightbox has role="dialog" when open', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      // Open lightbox
      await openLightbox(page, 0);

      // Check for role="dialog"
      const container = page.locator('.glightbox-container');
      await expect(container).toHaveAttribute('role', 'dialog');
    });

    test('lightbox has aria-modal="true" when open', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      const container = page.locator('.glightbox-container');
      await expect(container).toHaveAttribute('aria-modal', 'true');
    });

    test('lightbox has accessible label', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      const container = page.locator('.glightbox-container');
      const ariaLabel = await container.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    });

    test('close button has aria-label', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      const closeBtn = page.locator('.gclose');
      await expect(closeBtn).toBeVisible();
      const ariaLabel = await closeBtn.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel!.toLowerCase()).toContain('close');
    });

    test('navigation buttons have aria-labels', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      // Check prev button
      const prevBtn = page.locator('.gprev');
      await expect(prevBtn).toBeVisible();
      const prevLabel = await prevBtn.getAttribute('aria-label');
      expect(prevLabel).toBeTruthy();
      expect(prevLabel!.toLowerCase()).toContain('previous');

      // Check next button
      const nextBtn = page.locator('.gnext');
      await expect(nextBtn).toBeVisible();
      const nextLabel = await nextBtn.getAttribute('aria-label');
      expect(nextLabel).toBeTruthy();
      expect(nextLabel!.toLowerCase()).toContain('next');
    });

    test('lightbox has no critical accessibility violations', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      // Wait for lightbox to fully render
      await page.waitForTimeout(500);

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('.glightbox-container')
        .analyze();

      // Filter for critical violations only (ignore minor/moderate)
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical'
      );

      expect(criticalViolations).toEqual([]);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('gallery thumbnails are keyboard focusable', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const firstLink = page.locator('.gallery-grid a.glightbox').first();
      await firstLink.focus();
      await expect(firstLink).toBeFocused();
    });

    test('Enter key opens lightbox', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      const firstLink = page.locator('.gallery-grid a.glightbox').first();
      await firstLink.focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);

      await expect(page.locator('.goverlay')).toBeVisible();
    });

    test('ESC key closes lightbox', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);
      await expect(page.locator('.goverlay')).toBeVisible();

      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      await expect(page.locator('.goverlay')).not.toBeVisible();
    });

    test('Arrow keys navigate between images in lightbox', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');
      await waitForGlightbox(page);

      await openLightbox(page, 0);

      // Get first image src
      const firstImg = page.locator('.gslide.current img.zoomable').first();
      const firstSrc = await firstImg.getAttribute('src');

      // Navigate to next image
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(400);

      // Get second image src
      const secondImg = page.locator('.gslide.current img.zoomable').first();
      const secondSrc = await secondImg.getAttribute('src');

      // Should be different images
      expect(secondSrc).not.toBe(firstSrc);

      // Navigate back
      await page.keyboard.press('ArrowLeft');
      await page.waitForTimeout(400);

      // Should be back to first image
      const backImg = page.locator('.gslide.current img.zoomable').first();
      const backSrc = await backImg.getAttribute('src');
      expect(backSrc).toBe(firstSrc);
    });
  });

  test.describe('Photography Favorites Accessibility', () => {
    test('favorites gallery has no critical a11y violations', async ({ page }) => {
      await page.goto('/photography/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('.favorites-preview')
        .analyze();

      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });

    test('favorites images have descriptive alt text', async ({ page }) => {
      await page.goto('/photography/');
      await page.waitForLoadState('networkidle');

      const images = page.locator('.favorites-preview img');
      const count = await images.count();

      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute('alt');
        expect(alt, `Favorite image ${i} should have alt text`).toBeTruthy();
        // Favorites should have location descriptions
        expect(alt!.length, `Favorite image ${i} alt should be descriptive`).toBeGreaterThan(5);
      }
    });

    test('favorites links have data-type="image" attribute', async ({ page }) => {
      await page.goto('/photography/');
      await page.waitForLoadState('networkidle');

      const links = page.locator('.favorites-preview a.glightbox');
      const count = await links.count();

      for (let i = 0; i < count; i++) {
        const link = links.nth(i);
        await expect(link).toHaveAttribute('data-type', 'image');
      }
    });
  });

  test.describe('Project Gallery Accessibility', () => {
    test('project gallery has no critical a11y violations', async ({ page }) => {
      await page.goto('/projects/stairwell-chandelier/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('.gallery-grid')
        .analyze();

      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });
  });

  test.describe('Full Page Accessibility Audit', () => {
    test('gallery page passes full axe scan (gallery section)', async ({ page }) => {
      await page.goto('/photography/2023_nova_scotia/');
      await page.waitForLoadState('networkidle');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('.gallery-grid')
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      // Log violations for debugging (won't fail test for moderate/minor)
      if (accessibilityScanResults.violations.length > 0) {
        console.log('Accessibility violations found:');
        accessibilityScanResults.violations.forEach((v) => {
          console.log(`- ${v.impact}: ${v.id} - ${v.description}`);
        });
      }

      // Fail only on critical/serious violations
      const criticalViolations = accessibilityScanResults.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious'
      );

      expect(criticalViolations).toEqual([]);
    });
  });
});
