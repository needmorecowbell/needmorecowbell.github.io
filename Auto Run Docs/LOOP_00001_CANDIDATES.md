# Refactoring Candidates

This document tracks refactoring opportunities discovered by executing tactics from the game plan.

---

## Tactic 1: Duplicate Template Files - Executed 2026-01-06 12:00

### Finding 1: Identical projects/single.html and photography/single.html

- **Category:** Duplication
- **Location:** `layouts/photography/single.html:1-116` and `layouts/projects/single.html:1-116`
- **Current State:** Both files are **100% identical** to each other (116 LOC each). They differ from `_default/single.html` only on line 82, using `.Site.DisqusShortname` instead of `site.Config.Services.Disqus.Shortname`.
- **Proposed Change:** Delete both `layouts/photography/single.html` and `layouts/projects/single.html`. Hugo will fall back to `_default/single.html`. If the Disqus shortname access pattern difference matters, standardize on one approach in `_default/single.html`.
- **Code Context:**
  ```html
  {{/* Line 82 in _default/single.html */}}
  {{- if site.Config.Services.Disqus.Shortname -}}

  {{/* Line 82 in photography/single.html and projects/single.html */}}
  {{- if .Site.DisqusShortname -}}
  ```
- **Notes:** Both `.Site.DisqusShortname` and `site.Config.Services.Disqus.Shortname` access the same config value. The `site.Config.Services.Disqus.Shortname` pattern is the modern Hugo approach.

### Finding 2: Identical _default/list.html and projects/list.html

- **Category:** Duplication
- **Location:** `layouts/_default/list.html:1-55` and `layouts/projects/list.html:1-55`
- **Current State:** Both files are **100% identical** (55 LOC each). The `projects/list.html` serves no purpose - Hugo would use `_default/list.html` automatically.
- **Proposed Change:** Delete `layouts/projects/list.html` entirely. Hugo will automatically fall back to `_default/list.html` for the projects section.
- **Code Context:**
  ```html
  {{/* Both files are identical - here's the structure */}}
  {{ define "main" }}
    {{/* Breadcrumbs for nested content navigation */}}
    {{- partial "breadcrumbs.html" . -}}

    <div class="archive {{ with .Site.Params.doNotLoadAnimations }}...">
      <ul class="list-with-title">
        {{ range .Data.Pages.GroupByDate "2006" }}
          <div class="listing-title">{{ .Key }}</div>
          {{ range .Pages }}
            ...
          {{ end }}
        {{ end }}
      </ul>
    </div>
  {{ end }}
  ```
- **Notes:** Both files also contain identical commented-out code (lines 22-28) for category/tag badges. This dead code should be addressed separately (see Tactic 6).

### Finding 3: Single.html differs only in Disqus shortname access pattern

- **Category:** Duplication / Inconsistency
- **Location:** `layouts/_default/single.html:82` vs `layouts/photography/single.html:82` and `layouts/projects/single.html:82`
- **Current State:** The three `single.html` files are functionally identical, differing only in how they access the Disqus shortname configuration.
- **Proposed Change:** Standardize on `site.Config.Services.Disqus.Shortname` (the modern Hugo pattern used in `_default/single.html`) and delete the section-specific templates.
- **Code Context:**
  ```html
  {{/* _default/single.html - modern approach */}}
  {{- if site.Config.Services.Disqus.Shortname -}}

  {{/* photography/single.html & projects/single.html - older approach */}}
  {{- if .Site.DisqusShortname -}}
  ```
- **Notes:** Both patterns work, but mixing them creates maintenance confusion. The modern `site.Config.Services.Disqus.Shortname` is recommended by Hugo documentation for accessing service configurations.

### Tactic Summary

- **Issues Found:** 3 (2 identical file pairs, 1 inconsistency)
- **Files Affected:** 5 files total
  - `layouts/_default/single.html` (reference implementation)
  - `layouts/photography/single.html` (duplicate - can be deleted)
  - `layouts/projects/single.html` (duplicate - can be deleted)
  - `layouts/_default/list.html` (reference implementation)
  - `layouts/projects/list.html` (duplicate - can be deleted)
- **Potential Line Reduction:** ~286 LOC (116 + 116 + 55 = 287 lines in duplicate files)
- **Status:** EXECUTED

---

## Tactic 2: Duplicate baseof.html Templates - Executed 2026-01-06 16:30

### Finding 1: Identical _default/baseof.html and photography/baseof.html

- **Category:** Duplication
- **Location:** `layouts/_default/baseof.html:1-30` and `layouts/photography/baseof.html:1-31`
- **Current State:** Both files are **functionally 100% identical**. The only difference is whitespace: `photography/baseof.html` has an extra blank line (line 28) before the `{{- end -}}` closing tag. This is a trivial whitespace difference with no functional impact.
- **Proposed Change:** Delete `layouts/photography/baseof.html` entirely. Hugo will automatically fall back to `_default/baseof.html` for the photography section. No functionality will change.
- **Code Context:**
  ```html
  {{/* Both files have identical structure */}}
  <!DOCTYPE html>
  <html
    dir="{{ .Site.Language.LanguageDirection | default "ltr" }}"
    lang="{{- site.Language.Lang -}}"
    data-theme="{{- .Site.Params.displayMode -}}"
  >
    {{- partial "head.html" . -}}
    <body>
      <header role="banner">{{ partial "navbar.html" . }}</header>
      <div class="wrapper">
        <aside role="complementary" aria-label="Site information">
          {{- partial "sidebar.html" . -}}
        </aside>
        <main id="main-content" role="main" tabindex="-1">
          <div class="autopagerize_page_element">
            <div class="content">
              {{- block "main" . }}{{- end }}
            </div>
          </div>
        </main>
      </div>

      {{- partial "footer.html" (dict "context" . "footerClassModifier" "base") -}}

      {{- if (eq .Site.Params.simpleAnalytics.enable true) -}}
        {{- partial "analytics/simpleanalytics.html" . -}}
      {{/* photography/baseof.html has one extra blank line here */}}
      {{- end -}}
    </body>
  </html>
  ```
- **Notes:** The photography section does not require any special base template behavior. Hugo's template lookup order means `_default/baseof.html` will be used automatically when the section-specific one is removed.

### Tactic Summary

- **Issues Found:** 1 (identical baseof.html files with only whitespace difference)
- **Files Affected:** 2 files total
  - `layouts/_default/baseof.html` (reference implementation - 30 LOC)
  - `layouts/photography/baseof.html` (duplicate - can be deleted - 31 LOC)
- **Potential Line Reduction:** 31 LOC
- **Status:** EXECUTED
