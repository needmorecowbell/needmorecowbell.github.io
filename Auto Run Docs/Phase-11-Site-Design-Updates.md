# Phase 11: Site Design Updates

This phase modernizes the blog's visual design while preserving its minimalist simplicity. The current Anatole theme provides a solid foundation, but the dependencies are dated and the layout could be refreshed.

## Current State Assessment

| Aspect | Current | Notes |
|--------|---------|-------|
| Theme | Anatole | Two-column layout, CSS variables, dark mode |
| jQuery | 3.6.1 | Required by nanogallery2, could be removed |
| Bootstrap | 5.2.2 | Minimally used, mostly for JS utilities |
| Font Awesome | 5.15.1 | Outdated, should be 6.x |
| Gallery | nanogallery2 | Heavy jQuery dependency |
| Layout | Fixed sidebar + content | Good structure, responsive |
| CSS | CSS Variables | Modern, easy to customize |

## Design Goals

1. **Maintain simplicity** - Clean, content-focused design
2. **Remove jQuery dependency** - Use vanilla JS where possible
3. **Modernize typography** - Better font choices and spacing
4. **Improve navigation** - Clearer hierarchy and mobile experience
5. **Refresh color scheme** - Subtle updates while keeping professional look
6. **Optimize performance** - Fewer external dependencies

## Tasks

### Phase 11.1: Dependency Cleanup

- [x] Audit current external dependencies
  - List all CDN resources in head.html
  - Identify which are actually used
  - Document removal candidates

  **AUDIT COMPLETED (2026-01-04):**

  ### CDN Resources in `layouts/partials/head.html`:

  | Resource | CDN URL | Version | Size Est. |
  |----------|---------|---------|-----------|
  | Font Awesome CSS | cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css | 5.15.1 | ~90KB |
  | Bootstrap JS | cdnjs.cloudflare.com/ajax/libs/bootstrap/5.2.2/js/bootstrap.min.js | 5.2.2 | ~60KB |
  | jQuery (cdnjs) | cdnjs.cloudflare.com/ajax/libs/jquery/3.6.1/jquery.min.js | 3.6.1 | ~90KB |
  | jQuery (jsdelivr) | cdn.jsdelivr.net/npm/jquery@3.3.1/dist/jquery.min.js | 3.3.1 | ~90KB |
  | nanogallery2 CSS | cdn.jsdelivr.net/npm/nanogallery2@3/dist/css/nanogallery2.min.css | 3.x | ~30KB |
  | nanogallery2 JS | cdn.jsdelivr.net/npm/nanogallery2@3/dist/jquery.nanogallery2.min.js | 3.x | ~200KB |
  | Cloudflare Analytics | static.cloudflareinsights.com/beacon.min.js | - | ~5KB |

  **NOTE:** jQuery is loaded TWICE from different CDNs (cdnjs 3.6.1 + jsdelivr 3.3.1) - this is redundant.

  ### Usage Analysis:

  **Font Awesome (ACTIVELY USED):**
  - Social icons in sidebar: `fab fa-github`, `fab fa-twitter`, `fab fa-linkedin`, `fas fa-envelope`
  - Date icons: `fas fa-calendar-day` (multiple layouts)
  - Reading time: `fas fa-stopwatch` (single.html layouts)
  - Theme toggle: `fas fa-adjust` (navbar.html)
  - Pagination: `fa fa-angle-left`, `fa fa-angle-right`
  - Sidebar collapse (commented out): `fas fa-chevron-left/right`

  **Bootstrap JS (NOT USED):**
  - Zero Bootstrap classes detected in HTML templates
  - No `data-bs-*` attributes found
  - No Bootstrap JS components (dropdown, modal, collapse, etc.) being used
  - Custom CSS handles the language dropdown in navbar

  **jQuery (USED BY):**
  - nanogallery2 (required dependency)
  - `static/js/side_collapse.js` (13 lines, easily converted to vanilla JS)
  - NOTE: sidebar_collapse toggle is currently **commented out** in sidebar.html

  **nanogallery2 (ACTIVELY USED):**
  - Gallery shortcode relies on it for all photography galleries
  - Provides lightbox, pagination, thumbnail generation

  ### Removal Candidates:

  | Resource | Recommendation | Reason |
  |----------|----------------|--------|
  | **Bootstrap JS** | **REMOVE** | Zero usage detected - not a single Bootstrap feature is used |
  | **jQuery (duplicate)** | **REMOVE ONE** | Only one jQuery instance needed |
  | **jQuery (cdnjs)** | Keep (for now) | Required by nanogallery2 |
  | **Font Awesome** | Keep but **UPDATE to 6.x** | Actively used, but version 5.15.1 is outdated |
  | **nanogallery2** | Evaluate | Heavy (~200KB + jQuery dependency), consider alternatives |

  ### Estimated Savings:
  - Removing Bootstrap JS: **~60KB**
  - Removing duplicate jQuery: **~90KB**
  - **Total immediate savings: ~150KB**

- [x] Remove or replace Bootstrap
  - Check what Bootstrap features are actually used
  - Replace with minimal custom CSS if needed
  - Test all pages after removal

  **COMPLETED (2026-01-04):**
  - Removed Bootstrap JS (5.2.2) from `layouts/partials/head.html` - confirmed zero usage
  - Also removed duplicate jQuery reference (3.3.1 from jsdelivr) - was loading jQuery twice
  - Kept jQuery 3.6.1 from cdnjs (required by nanogallery2)
  - Site builds successfully (209 pages in 87ms)
  - Verified no Bootstrap references in output HTML
  - Verified only one jQuery reference in output HTML
  - **Savings: ~150KB** (60KB Bootstrap + 90KB duplicate jQuery)

- [x] Update Font Awesome to 6.x
  - Update CDN links
  - Check icon names for breaking changes
  - Test all icon displays

  **COMPLETED (2026-01-04):**
  - Updated Font Awesome CDN from 5.15.1 to 6.7.2 in `layouts/partials/head.html`
  - New CDN URL: `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css`
  - SRI hash: `sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==`
  - Icons verified working (FA6 has backward compatibility for FA5 icon names):
    - Social icons: `fab fa-github`, `fab fa-twitter`, `fab fa-linkedin`, `fas fa-envelope`
    - Date icons: `fas fa-calendar-day`
    - Reading time: `fas fa-stopwatch`
    - Theme toggle: `fas fa-adjust`
    - Pagination: `fa fa-angle-left`, `fa fa-angle-right`
  - Site builds successfully (209 pages)

### Phase 11.2: Gallery Modernization

- [x] Evaluate gallery alternatives
  - Option A: CSS Grid gallery with native `<dialog>` lightbox
  - Option B: Lighter library (GLightbox, Parvus)
  - Option C: Keep nanogallery2 but optimize loading
  - Document decision and rationale

  **EVALUATION COMPLETED (2026-01-04):**

  ### Current State: nanogallery2
  - **Bundle Size:** ~200KB JS + ~30KB CSS + jQuery (~90KB) = **~320KB total**
  - **Pros:** Full-featured, handles videos, thumbnails, pagination, lightbox
  - **Cons:** Heavy, requires jQuery, actively maintained but complex

  ### Option A: CSS Grid + Native `<dialog>` (Custom Implementation)
  | Aspect | Assessment |
  |--------|------------|
  | Bundle Size | ~5-10KB (custom JS + CSS) |
  | jQuery Required | No |
  | Video Support | Would need custom implementation |
  | Accessibility | Native `<dialog>` is accessible by default |
  | Maintenance | High - must maintain custom code |
  | Features | Must build: navigation, zoom, gestures, thumbnails |

  **Verdict:** Most lightweight, but significant development effort. Would need to implement video player integration, keyboard navigation, touch gestures, and gallery pagination from scratch. Risk of bugs and maintenance burden.

  ### Option B: GLightbox (Recommended)
  | Aspect | Assessment |
  |--------|------------|
  | Bundle Size | ~11KB gzipped (JS only) |
  | jQuery Required | **No** - pure JavaScript |
  | Video Support | **Yes** - YouTube, Vimeo, self-hosted with autoplay |
  | Accessibility | Keyboard and touch navigation |
  | Community | 2.4k GitHub stars, 6,300+ dependents |
  | Features | Zoom, drag, galleries, responsive, touch-friendly |

  **Additional research:**
  - GitHub: https://github.com/biati-digital/glightbox
  - Demo: https://biati-digital.github.io/glightbox/
  - CDN available via jsDelivr

  ### Option B Alternative: Parvus
  | Aspect | Assessment |
  |--------|------------|
  | Bundle Size | ~6KB gzipped |
  | jQuery Required | No |
  | Video Support | **No** - images only |
  | Accessibility | Core design goal, uses native `<dialog>` |
  | Features | Galleries, srcset support, swipe gestures |

  **Verdict:** Excellent for images but **lacks video support** which is required for this site (see `galleries/*.gallery.yaml` with .mp4 files).

  ### Option C: Keep nanogallery2 + Optimize
  | Aspect | Assessment |
  |--------|------------|
  | Optimization Options | Lazy load script, conditional load only on gallery pages |
  | Savings Potential | Moderate - could defer ~320KB |
  | jQuery Removal | Not possible - nanogallery2 requires it |

  **Verdict:** Still requires jQuery, limits future modernization.

  ### Recommendation: **GLightbox (Option B)**

  **Rationale:**
  1. **11KB vs 320KB** - ~97% reduction in gallery-related JavaScript
  2. **Removes jQuery dependency** - enables removal of ~90KB jQuery from entire site
  3. **Video support** - critical for existing galleries with .mp4 files
  4. **Pure JavaScript** - aligns with Phase 11 goal of removing jQuery
  5. **Active maintenance** - well-supported, large community
  6. **Feature parity** - provides lightbox, galleries, responsive design, touch support
  7. **CDN available** - easy integration via jsDelivr

  **What will change:**
  - Gallery shortcode will need rewrite for GLightbox's simpler API
  - Will use CSS Grid for thumbnail layout (more control, simpler markup)
  - Video thumbnails (`.thumb.jpg`) already exist - can continue using these
  - Pagination handled by CSS Grid rows or infinite scroll

  **Estimated total savings after implementation:**
  - Remove jQuery: ~90KB
  - Remove nanogallery2: ~230KB
  - Add GLightbox: +11KB
  - **Net savings: ~309KB**

- [x] Implement chosen gallery solution
  - Update gallery shortcode
  - Ensure video thumbnail support preserved
  - Test all gallery pages
  - Verify mobile experience

  **COMPLETED (2026-01-04):**

  ### Implementation Details:

  **Replaced nanogallery2 with GLightbox:**
  - Added GLightbox 3.3.1 from jsDelivr CDN to `layouts/partials/head.html`
  - Removed jQuery 3.6.1, nanogallery2 CSS/JS from head.html
  - Removed unused `static/js/side_collapse.js` (was jQuery-dependent, sidebar collapse is already commented out)

  **Rewrote gallery shortcode (`layouts/shortcodes/gallery.html`):**
  - Uses CSS Grid for responsive thumbnail layout (auto-fill, minmax 250px)
  - Native `loading="lazy"` for all images
  - Video support preserved: detects .mp4/.mov/.webm/.avi and uses `.thumb.jpg` thumbnails
  - Play button overlay via CSS pseudo-element for video items
  - GLightbox initialized per-gallery with keyboard/touch navigation, loop enabled
  - Data attributes: `data-gallery` for grouping, `data-type="video"` for videos

  **Files Modified:**
  - `layouts/partials/head.html` - Replaced jQuery+nanogallery2 with GLightbox
  - `layouts/shortcodes/gallery.html` - Complete rewrite for GLightbox + CSS Grid

  **Files Removed:**
  - `static/js/side_collapse.js` - No longer needed (was jQuery, sidebar collapse commented out)

  **Tested Gallery Pages:**
  - `/projects/vertical_rotisserie/` - 7 items (3 images + 4 videos) ✓
  - `/photography/2023_nova_scotia/` - 20 images ✓
  - `/gallery/` - Multiple galleries ✓
  - Build successful: 209 pages in 86ms

  **Bundle Size Savings:**
  - Removed jQuery 3.6.1: ~90KB
  - Removed nanogallery2: ~230KB (JS + CSS)
  - Added GLightbox 3.3.1: ~11KB (JS) + ~15KB (CSS)
  - **Net savings: ~294KB** (representing a 92% reduction in gallery-related dependencies)

- [x] Remove jQuery if no longer needed
  - Check side_collapse.js can be converted to vanilla JS
  - Update any remaining jQuery code
  - Remove jQuery CDN reference

  **COMPLETED (2026-01-04):**
  - jQuery removed as part of GLightbox implementation above
  - `side_collapse.js` deleted (was only jQuery usage, sidebar collapse feature commented out)
  - No remaining jQuery dependencies in the codebase
  - Site is now fully jQuery-free

### Phase 11.3: Layout Refinements

- [x] Review sidebar design
  - Profile picture sizing and shape
  - Social icon styling
  - Navigation clarity
  - Mobile collapse behavior

  **COMPLETED (2026-01-04):**

  ### Sidebar Design Improvements:

  Created `assets/css/custom.css` with comprehensive sidebar enhancements:

  **Profile Picture:**
  - Increased size from 127px to 140px (desktop: 150px)
  - Added subtle border (3px solid, using theme border-color variable)
  - Added box-shadow for depth (0 4px 12px rgba(0,0,0,0.1))
  - Added hover effect: scale(1.02) + enhanced shadow
  - Dark mode compatible with adjusted shadow intensity

  **Social Icons:**
  - Redesigned as circular bordered buttons (42px circles)
  - Added smooth hover transitions (color, border, background, transform)
  - Hover effect: lift animation (-2px translateY), link color highlight
  - Improved spacing between icons (8px padding)
  - Dark mode compatible with adjusted hover backgrounds

  **Navigation Clarity:**
  - Added underline animation on nav link hover (width 0 to 100%)
  - Current page indicator uses link color with persistent underline
  - Improved mobile navigation with border separators between items
  - Theme toggle button gets hover background for better visibility

  **Mobile Improvements (< 960px):**
  - Reduced profile picture to 120px for better proportions
  - Adjusted description font size and margins
  - Larger touch targets for social icons (44px)
  - Navigation items have border separators for clarity
  - Rounded bottom corners on mobile dropdown menu

  **Files Modified:**
  - `assets/css/custom.css` (NEW) - Custom CSS overrides
  - `config/_default/params.toml` - Enabled customCss parameter

  **Build Status:** 209 pages in 91ms

- [ ] Improve content area
  - Reading width optimization
  - Post list styling
  - Date/metadata display
  - Tag styling

- [ ] Enhance navigation
  - Active state visibility
  - Mobile menu improvements
  - Breadcrumbs for nested content (optional)

### Phase 11.4: Typography & Color Updates

- [ ] Select modern font stack
  - Consider: Inter, Source Sans Pro, or system fonts
  - Ensure good readability at all sizes
  - Test with actual content

- [ ] Update CSS color variables
  - Subtle refinements to current scheme
  - Improve contrast where needed
  - Ensure dark mode consistency

- [ ] Refine spacing and rhythm
  - Consistent margins/padding
  - Better heading hierarchy
  - Improved list styling

### Phase 11.5: Performance Optimization

- [ ] Audit page load performance
  - Run Lighthouse audit
  - Identify largest render-blocking resources
  - Document baseline metrics

- [ ] Implement lazy loading
  - Images below the fold
  - Gallery thumbnails
  - Consider native loading="lazy"

- [ ] Optimize CSS delivery
  - Inline critical CSS (optional)
  - Remove unused styles
  - Minify custom CSS

### Phase 11.6: Testing & Polish

- [ ] Cross-browser testing
  - Chrome, Firefox, Safari
  - Mobile Safari, Chrome Android
  - Document any issues

- [ ] Accessibility review
  - Color contrast
  - Focus states
  - Screen reader testing
  - Keyboard navigation

- [ ] Final visual polish
  - Hover states
  - Transitions
  - Loading states
  - Error states

## Reference: CSS Variables to Update

Current variables in `themes/anatole/assets/css/style.css`:

```css
:root {
  --bg-color: #fff;
  --secondary-bg-color: #eeeeee;
  --heading-color: #464646;
  --body-color: rgba(0, 0, 0, 0.7);
  --post-color: rgba(0, 0, 0, 0.44);
  --border-color: rgba(0, 0, 0, 0.15);
  --link-color: #0366d7;
  --pre-bg-color: #f9f9fd;
  --nav-text-color: #5a5a5a;
  --tag-color: #424242;
  --content-ratio: 0.8;
}
```

## Reference: Files Likely to Modify

| File | Purpose |
|------|---------|
| `layouts/partials/head.html` | CDN dependencies, custom CSS |
| `layouts/shortcodes/gallery.html` | Gallery implementation |
| `layouts/partials/sidebar.html` | Sidebar design |
| `layouts/partials/footer.html` | Footer design |
| `static/js/side_collapse.js` | Sidebar toggle (convert to vanilla JS) |
| `static/css/custom.css` (new) | Site-specific style overrides |
| `config/_default/params.toml` | Font settings, content ratio |

## Notes

- The Anatole theme is installed as a git submodule - avoid modifying theme files directly
- All customizations should go in the site-level `layouts/` and `static/` directories
- CSS variables can be overridden in a custom stylesheet
- Test thoroughly on localhost before deploying
- Keep the existing dark mode toggle functionality
- Preserve all current shortcode functionality (gallery, s3cdn, video)
