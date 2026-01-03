# Phase 7: Obsidian Publishing Infrastructure

This phase creates the scripts and templates needed to publish from Obsidian to Hugo seamlessly, building on the existing publishing pipeline from Phase 1-6.

## Tasks

- [x] Create `scripts/obsidian_to_hugo.py` conversion script
  - Parse Obsidian frontmatter and convert to Hugo format
  - Extract images from `## Pictures` section
  - Handle wikilink removal/conversion
  - Upload images to MinIO with proper naming (spaces → underscores)
  - Generate video thumbnails for .mp4/.mov files using `scripts/generate_video_thumbnails.sh`
  - Create gallery shortcode from Pictures section
  - Output Hugo markdown to correct directory based on content_type

  **Completed:** Created standalone CLI script that wraps existing publishing modules. Features:
  - Extracts `**Created**::`, `**Description**::` metadata from body
  - Handles both `[[...]]` wikilinks and `![[...]]` embeds in Pictures section
  - Uses rclone for MinIO uploads, ffmpeg for video thumbnails
  - Generates `{{< gallery />}}` shortcode with sanitized filenames
  - Supports `--dry-run`, `--skip-upload`, `--type` options
  - Cleans up Obsidian-specific sections (Associations, Collaborators, References)

- [ ] Create Obsidian blog template at `~/Notes/Templates/Blog Post.md`
  - Include Hugo-compatible frontmatter fields
  - Add `publish: false` by default
  - Include `content_type: post|project|photography` field
  - Add placeholder sections for content

- [ ] Test pipeline with existing project notes
  - Test with `~/Notes/Projects/Slab Computer Desk.md` (18 photos)
  - Test with `~/Notes/Projects/Wood Zippo Lighter.md`
  - Verify images upload correctly to MinIO
  - Verify video thumbnails are generated
  - Verify Hugo renders properly

- [ ] Update CONTENT_GUIDE.md with Obsidian workflow documentation
  - Document the Obsidian note structure
  - Document required frontmatter fields
  - Document the publishing command
  - Add troubleshooting section

## Reference: Current Obsidian Note Structure

```markdown
---
tags: ['note','project','cooking']
aliases: []
---

# Project Name
**Created**:: MM-DD-YYYY
**Author**:: [[Adam Musciano]]
**Description**:: Brief description

## Associations
- [[related note]]

## Collaborators
-

## Pictures
- [[path/to/image.jpg]]

## References
1.
```

## Reference: Target Hugo Structure

```markdown
---
title: "Project Name"
date: YYYY-MM-DD
draft: false
tags: ["cooking", "DIY", "project"]
description: "Brief description"
---

Content here...

{{< gallery path="projects/project_name" images="img1.jpg, img2.jpg" />}}
```

## Reference: Required Conversions

| Obsidian | Hugo |
|----------|------|
| `[[wikilink]]` | Remove or convert to text |
| `![[image.jpg]]` | `{{<s3cdn>}}/path/image.jpg` or gallery |
| `tags: ['a','b']` | `tags: ["a", "b"]` |
| `## Pictures` section | `{{< gallery />}}` shortcode |
| `## Associations` | Remove or convert to related posts |
| `**Created**:: MM-DD-YYYY` | `date: YYYY-MM-DD` |
| `**Description**::` | `description:` in frontmatter |
