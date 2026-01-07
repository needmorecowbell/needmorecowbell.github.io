# Phase 01: Implement UI Testing Framework

**Effort:** GALLERY_FIX
**Phase:** 1 of 2
**Goal:** Establish automated visual/UI testing infrastructure to catch regressions and validate gallery functionality in a real browser environment.

---

## Context

The blog uses GLightbox for image galleries, but we have no automated way to verify:
- Images actually expand to full-screen when clicked
- Gallery navigation (prev/next) works correctly
- Lightbox overlay renders properly
- Mobile touch gestures function
- Dark mode doesn't break gallery display

Manual testing is error-prone and changes can silently break functionality. We need real browser testing.

---

## Phase 1 Tasks

### 1.1 Set Up Node.js Project & Playwright

- [x] Create `package.json` with project metadata and scripts for UI testing
- [x] Install Playwright as the browser automation framework (`npm install -D @playwright/test`)
- [x] Run `npx playwright install` to download browser binaries (Chromium, Firefox, WebKit)
- [x] Create `playwright.config.ts` with configuration for:
  - Base URL pointing to local Hugo dev server
  - Test directory structure (`tests/ui/`)
  - Screenshot and video capture on failure
  - Multiple browser projects (chromium, firefox, webkit, mobile-chrome, mobile-safari)
  - Reasonable timeouts

> **Completed:** Created `package.json` at project root with Playwright v1.57.0 installed. Configured `playwright.config.ts` with 5 browser projects (chromium, firefox, webkit, mobile-chrome, mobile-safari), automatic Hugo server startup via webServer config, screenshot/video capture on failure, and visual regression thresholds. Also created `tests/ui/fixtures.ts` with helper functions for gallery testing and a smoke test (`tests/ui/smoke.spec.ts`) that verified the setup works. Updated `.gitignore` to exclude node_modules and Playwright artifacts.

### 1.2 Create Test Infrastructure Scripts

- [x] Add npm script `test:ui` to run Playwright tests
- [x] Add npm script `test:ui:headed` to run tests in visible browser mode for debugging
- [x] Add npm script `test:ui:report` to view HTML test reports
- [x] Add npm script `dev` to start Hugo dev server (port 1313)
- [x] Create `tests/ui/fixtures.ts` with shared test fixtures (page setup, navigation helpers)

> **Completed:** All infrastructure scripts were created during phase 1.1 setup. The `package.json` includes: `test:ui` (runs `playwright test`), `test:ui:headed` (runs tests with `--headed` flag), `test:ui:report` (runs `playwright show-report`), and `dev` (runs Hugo server on port 1313). Additionally includes `test:ui:debug` for debugging and `test:ui:update-snapshots` for updating baseline screenshots. The `tests/ui/fixtures.ts` file contains comprehensive helpers: `waitForGlightbox()`, `openLightbox()`, `closeLightbox()`, `getLightboxImage()`, `lightboxNext()`, `lightboxPrev()`, `getLightboxCounter()`, `countGalleryThumbnails()`, and `checkNoConsoleErrors()`.

### 1.3 Create Gallery Test Suite

- [x] Create `tests/ui/gallery.spec.ts` with core gallery functionality tests:
  - Test: Gallery grid renders with expected number of thumbnails
  - Test: Clicking thumbnail opens GLightbox overlay
  - Test: Lightbox displays full-resolution image (not thumbnail)
  - Test: Image dimensions in lightbox are larger than thumbnail dimensions
  - Test: Close button dismisses lightbox
  - Test: Clicking outside image closes lightbox
  - Test: ESC key closes lightbox
  - Test: Arrow keys navigate between images
  - Test: Gallery counter shows correct position (e.g., "3 of 15")
  - Test: Video items show play button overlay on thumbnails
  - Test: Video items play in lightbox when clicked

> **Completed:** Created comprehensive `tests/ui/gallery.spec.ts` with 18 tests covering core functionality (10 tests), video support (2 tests - skipped when no video content), accessibility (4 tests), and image loading (2 tests). Tests pass on Chromium, Firefox, and mobile-Chrome viewports. Key features tested: thumbnail grid rendering, lightbox opening/closing (button, ESC, click-outside), full-resolution image display, keyboard navigation (arrow keys), navigation buttons, gallery counter, accessibility attributes (ARIA roles, labels, alt text), lazy loading, and video item detection. Fixed `fixtures.ts` to use correct `.gallery-grid` selector and added `force: true` for GLightbox button clicks to handle overlay z-index. Added mobile-specific test handling for viewport-constrained scenarios.

### 1.4 Create Visual Regression Tests

- [ ] Create `tests/ui/visual-regression.spec.ts` for screenshot comparisons:
  - Test: Gallery grid layout matches baseline screenshot
  - Test: Lightbox overlay appearance matches baseline (light mode)
  - Test: Lightbox overlay appearance matches baseline (dark mode)
  - Test: Mobile gallery grid layout matches baseline
  - Test: Mobile lightbox appearance matches baseline
- [ ] Create `.gitignore` entries for Playwright artifacts (but keep baseline screenshots)
- [ ] Document process for updating baseline screenshots when intentional changes are made

### 1.5 Create Photography Section Tests

- [ ] Create `tests/ui/photography.spec.ts` for photography-specific tests:
  - Test: Photography list page loads with favorites gallery
  - Test: Favorites gallery thumbnails are clickable
  - Test: Individual photography pages load with their galleries
  - Test: Nova Scotia gallery loads all 19 images from S3CDN
  - Test: Image URLs correctly point to S3CDN (not local paths)
  - Test: Thumbnail URLs use `.thumb.jpg` suffix pattern

### 1.6 Create Cross-Browser Smoke Tests

- [ ] Create `tests/ui/cross-browser.spec.ts` for browser compatibility:
  - Test: Gallery renders in Chromium
  - Test: Gallery renders in Firefox
  - Test: Gallery renders in WebKit (Safari)
  - Test: Lightbox works in mobile viewport (touch simulation)
  - Test: No JavaScript console errors on gallery pages

### 1.7 Docker Development Environment (Optional but Recommended)

- [ ] Create `Dockerfile.test` for consistent test environment:
  - Base: `mcr.microsoft.com/playwright:v1.40.0-jammy`
  - Install Hugo extended version
  - Copy project files
  - Install npm dependencies
- [ ] Create `docker-compose.test.yml` for easy test execution:
  - Service: `hugo-server` - runs Hugo dev server
  - Service: `playwright` - runs UI tests against Hugo server
  - Shared network for container communication
- [ ] Add npm script `test:ui:docker` to run tests in Docker

### 1.8 CI Integration Preparation

- [ ] Create `.github/workflows/ui-tests.yml` workflow file (template):
  - Trigger on push to develop/main
  - Trigger on pull requests
  - Install dependencies
  - Start Hugo server in background
  - Run Playwright tests
  - Upload test artifacts (screenshots, videos) on failure
  - Upload HTML report as artifact
- [ ] Document manual CI setup steps if GitHub Actions not already configured

---

## Success Criteria

1. Running `npm run test:ui` executes browser tests against local Hugo server
2. Tests detect when GLightbox fails to initialize
3. Tests detect when images don't expand to full-screen
4. Visual regression tests catch unintended layout changes
5. Tests run in multiple browsers to catch compatibility issues
6. Failed tests produce screenshots/videos for debugging

---

## Files Created

```
package.json
playwright.config.ts
tests/
  ui/
    fixtures.ts
    gallery.spec.ts
    visual-regression.spec.ts
    photography.spec.ts
    cross-browser.spec.ts
    __screenshots__/        (baseline images)
Dockerfile.test            (optional)
docker-compose.test.yml    (optional)
.github/workflows/ui-tests.yml
```

---

## Notes

- Playwright was chosen over Cypress for better multi-browser support and faster execution
- Tests require Hugo server running on port 1313 (or configure baseURL)
- Visual regression thresholds should allow minor anti-aliasing differences
- S3CDN URLs may need mocking or the CDN must be accessible during tests
