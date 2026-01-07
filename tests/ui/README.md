# UI Tests

This directory contains Playwright browser tests for the blog's gallery functionality.

## Running Tests

```bash
# Run all UI tests
npm run test:ui

# Run tests with visible browser window
npm run test:ui:headed

# Run tests in debug mode
npm run test:ui:debug

# View HTML test report
npm run test:ui:report
```

## Visual Regression Tests

Visual regression tests (`visual-regression.spec.ts`) capture screenshots and compare them against baseline images to detect unintended visual changes.

### How It Works

1. **First run**: Playwright captures screenshots and saves them as baselines in `tests/ui/visual-regression.spec.ts-snapshots/`
2. **Subsequent runs**: New screenshots are compared against baselines
3. **Failures**: If screenshots differ beyond the threshold (2-3%), the test fails

### Updating Baseline Screenshots

When you make **intentional** visual changes (new styles, layout updates, etc.):

```bash
# Update all baseline screenshots
npm run test:ui:update-snapshots

# Update specific test file's snapshots
npx playwright test visual-regression.spec.ts --update-snapshots

# Update snapshots for specific browser only
npx playwright test visual-regression.spec.ts --update-snapshots --project=chromium
```

### Important Notes

- **Always commit baseline screenshots** - They are stored in `*.spec.ts-snapshots/` directories
- **Review changes before committing** - Use `git diff` to see what screenshots changed
- **Different browsers have different baselines** - Each project (chromium, firefox, webkit, mobile-chrome, mobile-safari) has its own snapshot directory
- **Diff images are not committed** - Files ending in `-diff.png` and `-actual.png` are gitignored

### Screenshot Storage Structure

```
tests/ui/
  visual-regression.spec.ts              # Test file
  visual-regression.spec.ts-snapshots/   # Baseline screenshots
    chromium/
      gallery-grid-layout.png
      lightbox-overlay-light.png
      ...
    firefox/
      ...
    webkit/
      ...
    mobile-chrome/
      ...
    mobile-safari/
      ...
```

### Threshold Configuration

Visual comparison thresholds are configured in `playwright.config.ts`:

```typescript
expect: {
  toHaveScreenshot: {
    maxDiffPixelRatio: 0.02,  // Allow 2% pixel difference
  },
}
```

Individual tests can override this:

```typescript
await expect(element).toHaveScreenshot('name.png', {
  maxDiffPixelRatio: 0.03,  // Allow 3% for this test
});
```

## Test Files

- `fixtures.ts` - Shared test helpers and fixtures
- `smoke.spec.ts` - Basic smoke tests
- `gallery.spec.ts` - Gallery functionality tests
- `photography.spec.ts` - Photography section tests
- `visual-regression.spec.ts` - Visual screenshot comparison tests
- `cross-browser.spec.ts` - Cross-browser compatibility tests

## CI Integration

The UI tests are automatically run via GitHub Actions on:
- Push to `develop` or `main` branches
- Pull requests targeting `develop` or `main`

### GitHub Actions Workflow

The workflow file (`.github/workflows/ui-tests.yml`) runs two jobs:

1. **UI Tests** - Runs the full Playwright test suite on Chromium and Firefox
2. **Visual Regression** - Runs visual comparison tests separately for clearer reporting

### Artifacts

On failure, the following artifacts are uploaded:
- `playwright-report/` - HTML test report (always uploaded)
- `test-results/` - Screenshots and videos from failed tests
- Visual diff images showing expected vs actual screenshots

### Manual CI Setup

If GitHub Actions is not already configured for your repository:

1. **Enable Actions**: Go to repository Settings > Actions > General, ensure "Allow all actions" is selected

2. **Check workflow permissions**: Settings > Actions > General > Workflow permissions should be "Read and write permissions"

3. **Verify workflow file**: Ensure `.github/workflows/ui-tests.yml` exists and is committed

4. **First run setup**: The first workflow run will:
   - Install Hugo extended v0.140.2
   - Install Playwright browsers (Chromium, Firefox)
   - Run all UI tests

### Running Tests Locally (CI Simulation)

To simulate CI behavior locally:

```bash
# Run with CI environment variable (single worker, stricter mode)
CI=true npm run test:ui

# Or use Docker for a clean environment
npm run test:ui:docker
```

### Troubleshooting CI Failures

1. **Screenshot comparison failures**:
   - Download the `visual-regression-diffs` artifact
   - Compare expected vs actual images
   - If changes are intentional, update baselines locally and push

2. **Timeout failures**:
   - Check Hugo server startup in workflow logs
   - Increase timeout in `playwright.config.ts` if needed

3. **Browser-specific failures**:
   - Some tests may behave differently across browsers
   - Check which browser failed in the workflow logs
   - Run locally with that specific browser: `npx playwright test --project=firefox`

### Required Secrets/Variables

The current workflow doesn't require any secrets. If your tests need to access:
- **S3CDN content**: Tests currently use live S3CDN URLs; no credentials needed for read-only access
- **Other services**: Add secrets via Settings > Secrets and variables > Actions
