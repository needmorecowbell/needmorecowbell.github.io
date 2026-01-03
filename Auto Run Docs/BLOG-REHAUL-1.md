# Phase 1: Stylistic Shift - From Dev Log to Personal Blog

The site is currently branded as "Adam's Dev Log" with a tech-focused description. Since the blog will now include craft projects, cooking, family-friendly content, and personal projects, we need to rebrand for a broader audience.

## Tasks

- [x] Update site title from "Adam's Dev Log" to a more inclusive name (e.g., "Adam Musciano" or "Adam's Corner")
    - Changed to "Adam Musciano" in: config/_default/config.toml, config/_default/languages.toml, config/_default/params.toml
    - Also updated README.md header to match
- [x] Update site description from "A Developer's Ramblings" to something broader (e.g., "Projects, crafts, code, and everything in between")
    - Changed to "Projects, crafts, code, and everything in between" in config/_default/params.toml
- [x] Fix typo in menu: "Photgraphy" → "Photography"
    - Fixed in config/_default/menus.en.toml line 20
- [x] Consider adding a "Crafts" or "Making" section to the menu, or consolidate under "Projects"
    - **Decision: Keep consolidated under "Projects"** - The existing Projects section already serves as a versatile hub containing woodwork, stained glass, tech projects, cooking/DIY, gardening, and jewelry making (13 total projects). Adding a separate "Crafts" menu would fragment content unnecessarily and create categorization confusion. Tags (e.g., `woodwork`, `stained glass`, `cooking`, `DIY`) already provide filtering. No changes needed.
- [ ] Review social icons - Twitter may be outdated, consider removing or updating
- [ ] Update profile picture URL to use production S3CDN path (currently hardcoded to local IP)
