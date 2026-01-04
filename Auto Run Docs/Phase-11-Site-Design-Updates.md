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

- [ ] Remove or replace Bootstrap
  - Check what Bootstrap features are actually used
  - Replace with minimal custom CSS if needed
  - Test all pages after removal

- [ ] Update Font Awesome to 6.x
  - Update CDN links
  - Check icon names for breaking changes
  - Test all icon displays

### Phase 11.2: Gallery Modernization

- [ ] Evaluate gallery alternatives
  - Option A: CSS Grid gallery with native `<dialog>` lightbox
  - Option B: Lighter library (GLightbox, Parvus)
  - Option C: Keep nanogallery2 but optimize loading
  - Document decision and rationale

- [ ] Implement chosen gallery solution
  - Update gallery shortcode
  - Ensure video thumbnail support preserved
  - Test all gallery pages
  - Verify mobile experience

- [ ] Remove jQuery if no longer needed
  - Check side_collapse.js can be converted to vanilla JS
  - Update any remaining jQuery code
  - Remove jQuery CDN reference

### Phase 11.3: Layout Refinements

- [ ] Review sidebar design
  - Profile picture sizing and shape
  - Social icon styling
  - Navigation clarity
  - Mobile collapse behavior

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
