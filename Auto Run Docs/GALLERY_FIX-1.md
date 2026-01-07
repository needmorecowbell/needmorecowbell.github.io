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

- [x] Create `tests/ui/visual-regression.spec.ts` for screenshot comparisons:
  - Test: Gallery grid layout matches baseline screenshot
  - Test: Lightbox overlay appearance matches baseline (light mode)
  - Test: Lightbox overlay appearance matches baseline (dark mode)
  - Test: Mobile gallery grid layout matches baseline
  - Test: Mobile lightbox appearance matches baseline
- [x] Create `.gitignore` entries for Playwright artifacts (but keep baseline screenshots)
- [x] Document process for updating baseline screenshots

> **Completed:** Created comprehensive `tests/ui/visual-regression.spec.ts` with 9 tests across 4 test suites: Gallery Grid (2 tests), Lightbox (2 tests for light/dark mode), Mobile (2 tests - run only on mobile projects), and Component Details (3 tests for hover state and navigation controls). Updated `.gitignore` to exclude temporary diff/actual comparison images while keeping baseline screenshots committed. Created `tests/ui/README.md` with full documentation on running tests and updating baselines. Generated baseline screenshots for chromium and mobile-chrome projects (16 baseline images total). All tests pass on both desktop and mobile viewports.

### 1.5 Create Photography Section Tests

- [x] Create `tests/ui/photography.spec.ts` for photography-specific tests:
  - Test: Photography list page loads with favorites gallery
  - Test: Favorites gallery thumbnails are clickable
  - Test: Individual photography pages load with their galleries
  - Test: Nova Scotia gallery loads all 19 images from S3CDN
  - Test: Image URLs correctly point to S3CDN (not local paths)
  - Test: Thumbnail URLs use `.thumb.jpg` suffix pattern

> **Completed:** Created comprehensive `tests/ui/photography.spec.ts` with 16 tests across 6 test suites:
> - **Photography List Page (4 tests):** Verifies favorites gallery presence, clickable thumbnails, S3CDN URL patterns, and navigation to individual pages.
> - **Individual Photography Pages (2 tests):** Tests page loading with galleries and verifies Nova Scotia gallery has exactly 19 images.
> - **S3CDN URL Patterns (4 tests):** Validates all image URLs point to S3CDN (not local paths), thumbnails use `.thumb.jpg` suffix, full-resolution images don't have the suffix, and base names match between thumbnails and full images.
> - **Photography Gallery Navigation (2 tests):** Tests keyboard navigation through gallery images and opening specific thumbnails.
> - **Photography Lazy Loading (1 test):** Verifies all thumbnails use `loading="lazy"` attribute.
> - **Photography Accessibility (3 tests):** Tests ARIA attributes, alt text, and aria-labels on gallery elements.
>
> All 16 tests pass on Chromium, Firefox, and mobile-Chrome viewports.

### 1.6 Create Cross-Browser Smoke Tests

- [x] Create `tests/ui/cross-browser.spec.ts` for browser compatibility:
  - Test: Gallery renders in Chromium
  - Test: Gallery renders in Firefox
  - Test: Gallery renders in WebKit (Safari)
  - Test: Lightbox works in mobile viewport (touch simulation)
  - Test: No JavaScript console errors on gallery pages

> **Completed:** Created comprehensive `tests/ui/cross-browser.spec.ts` with 9 tests across 3 test suites:
> - **Cross-Browser Gallery Compatibility (4 tests):** Verifies gallery renders correctly, lightbox opens/displays images, lightbox closes properly, and keyboard navigation works. These tests run across all browser projects to ensure consistent behavior.
> - **Mobile Gallery Support (2 tests):** Tests gallery rendering in mobile viewport and touch/click interaction for opening/closing lightbox. Includes mobile-specific detection for proper test behavior adaptation.
> - **No JavaScript Console Errors (3 tests):** Verifies no application JavaScript errors occur on gallery page load, during lightbox interaction, or on photography list page. Includes filtering for expected third-party CORS/network errors from analytics scripts (Cloudflare Insights) that occur when testing against localhost.
>
> All 27 tests (9 tests × 3 available browser projects) pass on Chromium, Firefox, and mobile-Chrome. WebKit (Safari) and mobile-Safari tests are configured but require system dependencies (`libicu74`, `libxml2`, `libvpx9`, `libflite1`) to be installed via `sudo npx playwright install-deps` - this is an environment setup issue, not a test failure.

### 1.7 Docker Development Environment (Optional but Recommended)

- [x] Create `Dockerfile.test` for consistent test environment:
  - Base: `mcr.microsoft.com/playwright:v1.40.0-jammy`
  - Install Hugo extended version
  - Copy project files
  - Install npm dependencies
- [x] Create `docker-compose.test.yml` for easy test execution:
  - Service: `hugo-server` - runs Hugo dev server
  - Service: `playwright` - runs UI tests against Hugo server
  - Shared network for container communication
- [x] Add npm script `test:ui:docker` to run tests in Docker

> **Completed:** Created Docker development environment for consistent UI test execution:
> - **`Dockerfile.test`:** Based on `mcr.microsoft.com/playwright:v1.50.0-noble` (updated from v1.40.0-jammy for latest Playwright compatibility). Installs Hugo extended v0.140.2, copies project files, and runs `npm ci` for dependency installation.
> - **`docker-compose.test.yml`:** Defines two services:
>   - `hugo-server`: Uses `klakegg/hugo:ext-alpine` to run Hugo dev server on port 1313 with health checks
>   - `playwright`: Builds from Dockerfile.test, depends on hugo-server health, runs tests against `http://hugo-server:1313`
>   - Shared `test-network` bridge for container communication
>   - Volume mounts for test results and reports to persist after container exit
> - **`playwright.docker.config.ts`:** Docker-specific Playwright config that uses container networking (no webServer config since Hugo runs in separate container).
> - **npm scripts:** Added `test:ui:docker` (runs full test suite in Docker) and `test:ui:docker:down` (cleans up containers/volumes).
>
> Configuration validated with `docker-compose config` - all settings correct. Users need Docker group permissions to run (`sudo usermod -aG docker $USER` or use `sudo`).

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
playwright.docker.config.ts    (Docker-specific config)
tests/
  ui/
    fixtures.ts
    gallery.spec.ts
    visual-regression.spec.ts
    photography.spec.ts
    cross-browser.spec.ts
    __screenshots__/        (baseline images)
Dockerfile.test            (created)
docker-compose.test.yml    (created)
.github/workflows/ui-tests.yml
```

---

## Notes

- Playwright was chosen over Cypress for better multi-browser support and faster execution
- Tests require Hugo server running on port 1313 (or configure baseURL)
- Visual regression thresholds should allow minor anti-aliasing differences
- S3CDN URLs may need mocking or the CDN must be accessible during tests
