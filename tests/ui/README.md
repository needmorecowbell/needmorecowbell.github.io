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
- `visual-regression.spec.ts` - Visual screenshot comparison tests
