# Refactoring Game Plan

## Codebase Profile
- **Total Files:** ~70 source files (excluding themes, node_modules, public, venv)
- **Key Directories:**
  - `layouts/` - Hugo templates (24 HTML files, 1660 LOC total)
  - `scripts/` - Python publishing pipeline (16 main scripts, 8008 LOC)
  - `assets/css/` - Stylesheets (custom.css: 2868 LOC)
  - `config/` - Hugo configuration (TOML files)
  - `content/` - Markdown content (posts, projects, photography)

- **Largest Files:**
  1. `scripts/publish.py` - 2538 LOC (main CLI entry point)
  2. `assets/css/custom.css` - 2868 LOC (monolithic stylesheet)
  3. `scripts/obsidian_to_hugo.py` - 728 LOC
  4. `scripts/gallery_generator.py` - 612 LOC
  5. `scripts/minio_uploader.py` - 568 LOC
  6. `scripts/validators.py` - 472 LOC
  7. `layouts/partials/head.html` - 258 LOC

- **Existing Patterns:**
  - Hugo partial templates for reusable components
  - Section-based organization in CSS with comment headers
  - Modular Python scripts with separate concerns (media, gallery, frontmatter, etc.)
  - Test files alongside main scripts

## Investigation Tactics

Each tactic is a specific, actionable search pattern for finding refactoring opportunities.

### [EXECUTED] Tactic 1: Duplicate Template Files
- **Target:** Nearly identical Hugo template files that should be consolidated
- **Search Pattern:** Compare `layouts/*/single.html` and `layouts/*/list.html` files
- **Files to Check:**
  - `layouts/_default/single.html` (115 LOC)
  - `layouts/photography/single.html` (115 LOC)
  - `layouts/projects/single.html` (115 LOC)
  - `layouts/_default/list.html` (54 LOC)
  - `layouts/projects/list.html` (54 LOC)
- **Why It Matters:** All three `single.html` files are nearly identical (only 1 line difference: `site.Config.Services.Disqus.Shortname` vs `.Site.DisqusShortname`). The `_default/list.html` and `projects/list.html` are 100% identical. This creates maintenance burden and inconsistency risk.
- **Recommendation:** Delete redundant section-specific files and rely on `_default/` templates, or extract common logic into a partial.

### [EXECUTED] Tactic 2: Duplicate baseof.html Templates
- **Target:** Identical base template files
- **Search Pattern:** Compare `layouts/*/baseof.html` files
- **Files to Check:**
  - `layouts/_default/baseof.html` (30 LOC)
  - `layouts/photography/baseof.html` (31 LOC)
- **Why It Matters:** These files are 99% identical (only whitespace differences). Photography section doesn't need its own baseof.html.
- **Recommendation:** Delete `layouts/photography/baseof.html` - Hugo will fall back to `_default/baseof.html`.

### Tactic 3: Inline CSS in Templates
- **Target:** CSS embedded directly in HTML templates instead of external stylesheets
- **Search Pattern:** `<style>` tags in HTML files
- **Files to Check:**
  - `layouts/shortcodes/gallery.html` (lines 14-72 contain 58 lines of CSS)
  - `layouts/photography/list.html` (lines 15-38 contain gallery CSS)
- **Why It Matters:** Inline CSS creates duplication (gallery grid styles appear in both files), prevents caching, and makes styling inconsistent. The gallery shortcode has its own grid styles that partially duplicate what's in custom.css.
- **Recommendation:** Move all gallery-related CSS to `custom.css` and remove inline `<style>` blocks.

### Tactic 4: Monolithic CSS File
- **Target:** Large CSS file that could benefit from modular organization
- **Search Pattern:** Section headers in `assets/css/custom.css`
- **Files to Check:**
  - `assets/css/custom.css` (2868 LOC with 12 major sections)
- **Why It Matters:** While the file is well-organized with section comments, 2800+ lines in a single file can be unwieldy. However, Hugo's asset pipeline handles this well, so this is lower priority than code duplication.
- **Recommendation:** Consider if splitting makes sense, but may not be worth the effort given Hugo's build process.

### Tactic 5: Large Python Entry Point
- **Target:** Oversized main script that could be broken into modules
- **Search Pattern:** Functions and classes in `scripts/publish.py`
- **Files to Check:**
  - `scripts/publish.py` (2538 LOC)
- **Why It Matters:** At 2500+ lines, this file likely handles too many concerns. However, the project already has good modularization (gallery_generator, minio_uploader, etc.), so this may be intentional as the CLI coordinator.
- **Recommendation:** Review if any logic can be extracted to existing modules. Lower priority since the architecture is already modular.

### Tactic 6: Commented-Out Code in Templates
- **Target:** Dead code left in templates
- **Search Pattern:** `{{/*` comment blocks containing actual code
- **Files to Check:**
  - `layouts/_default/list.html` (lines 22-28 have commented-out category/tag code)
  - `layouts/projects/list.html` (same commented-out code)
  - `layouts/photography/list.html` (same commented-out code)
- **Why It Matters:** Commented code is noise that obscures actual functionality and may confuse future maintainers about whether features are active.
- **Recommendation:** Either remove the dead code or implement the feature properly.

### Tactic 7: Hardcoded Values in Templates
- **Target:** Magic strings and hardcoded URLs that should be configuration
- **Search Pattern:** `http://`, `https://` in HTML files
- **Files to Check:**
  - `layouts/partials/head.html` - Contains hardcoded CDN URLs and Cloudflare token
  - `layouts/photography/list.html` - Hardcoded favorite photo paths
- **Why It Matters:** Hardcoded values make the site less portable and updates more error-prone.
- **Recommendation:** Move CDN references and tokens to config files where possible.

## Priority Order

1. **High Impact, Low Effort:**
   - Tactic 1: Delete duplicate single.html files (photography, projects)
   - Tactic 2: Delete duplicate baseof.html
   - Tactic 6: Remove commented-out code

2. **Medium Impact, Medium Effort:**
   - Tactic 3: Consolidate inline CSS to custom.css

3. **Lower Priority:**
   - Tactic 4: CSS file organization (already well-structured)
   - Tactic 5: Python publish.py review (architecture is already modular)
   - Tactic 7: Hardcoded values (requires careful testing)

## Summary

The most impactful refactoring opportunities are in the Hugo templates:
- 3 nearly-identical `single.html` files can become 1
- 2 identical `list.html` files can become 1
- 2 identical `baseof.html` files can become 1
- Inline CSS duplication can be consolidated

These changes would reduce template maintenance burden significantly while making the codebase more consistent.
