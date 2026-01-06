# Refactoring Plan - Loop 00001

## Summary
- **Total Candidates:** 4
- **PENDING (auto-implement):** 0
- **IMPLEMENTED:** 2
- **PENDING - MANUAL REVIEW:** 0
- **WON'T DO:** 0

## Status Matrix

| # | Candidate | Risk | Benefit | Status |
|---|-----------|------|---------|--------|
| 1 | Identical projects/single.html and photography/single.html | LOW | HIGH | IMPLEMENTED |
| 2 | Identical _default/list.html and projects/list.html | LOW | HIGH | IMPLEMENTED |

## Detailed Evaluations

### 1. Identical projects/single.html and photography/single.html
- **Location:** `layouts/photography/single.html:1-116` and `layouts/projects/single.html:1-116`
- **Category:** Duplication
- **Risk:** LOW
- **Benefit:** HIGH
- **Status:** IMPLEMENTED
- **Risk Rationale:**
  - Internal-only change affecting template files
  - No API changes or exported interfaces
  - Hugo's template fallback system is well-documented and predictable
  - Both files are 100% identical to each other
  - The only difference from `_default/single.html` is line 82, where `.Site.DisqusShortname` is used instead of `site.Config.Services.Disqus.Shortname` - both access the same configuration value
  - Hugo will automatically fall back to `_default/single.html` when section-specific templates are removed
  - Easy to verify by running `hugo serve` and checking photography/projects pages
  - No side effects expected since the templates are functionally identical
- **Benefit Rationale:**
  - Removes 232 lines of duplicate code (2 x 116 LOC)
  - Eliminates maintenance burden of keeping three templates in sync
  - Standardizes on the modern Hugo pattern for Disqus configuration access
  - Reduces confusion about which template is the "source of truth"
  - Makes future template updates simpler (only one file to modify)
- **Refactoring Approach:**
  1. Verify that `_default/single.html` is the canonical implementation
  2. Delete `layouts/photography/single.html`
  3. Delete `layouts/projects/single.html`
  4. Run `hugo serve` and verify photography and projects pages render correctly
  5. Test Disqus integration if configured (the `site.Config.Services.Disqus.Shortname` pattern in `_default/single.html` is the modern approach and will work correctly)

### 2. Identical _default/list.html and projects/list.html
- **Location:** `layouts/_default/list.html:1-55` and `layouts/projects/list.html:1-55`
- **Category:** Duplication
- **Risk:** LOW
- **Benefit:** HIGH
- **Status:** IMPLEMENTED
- **Risk Rationale:**
  - Internal-only change affecting template files
  - No API changes or exported interfaces
  - Hugo's template fallback system is well-documented and predictable
  - Both files are **100% byte-for-byte identical** (verified via direct comparison)
  - Hugo will automatically fall back to `_default/list.html` when section-specific template is removed
  - Easy to verify by running `hugo serve` and checking the projects listing page
  - No side effects expected since the templates are completely identical
  - Single file deletion with no dependencies
- **Benefit Rationale:**
  - Removes 55 lines of completely duplicate code
  - Eliminates maintenance burden of keeping two identical templates in sync
  - Reduces confusion about which template is the "source of truth" for list layouts
  - Makes future list template updates simpler (only one file to modify)
  - Follows Hugo best practices of using `_default/` templates for shared layouts
- **Refactoring Approach:**
  1. Verify that `_default/list.html` exists and is the canonical implementation
  2. Delete `layouts/projects/list.html`
  3. Run `hugo serve` and verify the projects listing page renders correctly
  4. Confirm no visual or functional differences in the projects section list view
