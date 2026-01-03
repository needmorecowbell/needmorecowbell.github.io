# Content Creation Guide

This guide explains how to create posts, projects, photography galleries, and other content for the blog.

## Table of Contents

- [Content Types](#content-types)
- [Creating a Blog Post](#creating-a-blog-post)
- [Creating a Project](#creating-a-project)
- [Creating a Photography Gallery](#creating-a-photography-gallery)
- [Shortcodes Reference](#shortcodes-reference)
- [Publishing from Obsidian](#publishing-from-obsidian)
  - [Obsidian Note Structure](#obsidian-note-structure)
  - [Required Frontmatter Fields](#required-frontmatter-fields)
  - [Publishing Commands](#publishing-commands)
  - [Troubleshooting](#troubleshooting)

---

## Content Types

| Type | Directory | Description |
|------|-----------|-------------|
| Post | `content/english/post/` | Blog posts, tutorials, articles |
| Project | `content/english/projects/` | Maker projects, builds, crafts |
| Photography | `content/english/photography/` | Photo galleries from trips/events |

---

## Creating a Blog Post

### File Location

Create a new file in `content/english/post/` with the naming convention:
```
YYYY-MM-DD-slug-title.md
```

Example: `2026-01-15-building-a-weather-station.md`

### Frontmatter Template

```yaml
---
layout: post
title: "Your Post Title"
date: "2026-01-15"
headerimg: "/img/post-bg-09.png"
tags: ["tag1", "tag2"]
description: "A brief description for SEO"
draft: false
---
```

#### Required Fields

| Field | Description |
|-------|-------------|
| `title` | Post title |
| `date` | Publication date (YYYY-MM-DD) |

#### Optional Fields

| Field | Description |
|-------|-------------|
| `layout` | Use `post` for standard posts |
| `headerimg` | Header background image path |
| `tags` | List of tags for categorization |
| `description` | SEO meta description |
| `draft` | Set `true` to hide from production |

### Example Post

```markdown
---
layout: post
title: "Building a Weather Station"
date: "2026-01-15"
tags: ["raspberry-pi", "iot", "python"]
---

Introduction paragraph here...

## Section Heading

Content with **bold** and *italic* text.

### Code Examples

```python
print("Hello, World!")
```

## Adding Images

![Alt text](https://example.com/image.jpg)

## Embedding Videos from S3

<video width="700" controls>
  <source src="{{</* s3cdn */>}}/videos/demo.mp4" type="video/mp4">
</video>
```

---

## Creating a Project

### File Location

Create a new file in `content/english/projects/`:
```
project-name.md
```

Example: `laser-engraved-coasters.md`

### Frontmatter Template

```yaml
---
title: "Project Title"
date: 2026-01-15
draft: false
tags: ["woodwork", "laser", "crafts"]
description: "Brief project description"
---
```

### Project with Gallery (Using Shortcode)

```markdown
---
title: "Laser Engraved Coasters"
date: 2026-01-15
draft: false
tags: ["woodwork", "laser"]
---

Description of your project...

{{</* gallery path="projects/coasters" maxRows="1" images="img1.jpg, img2.jpg, img3.jpg" /*/>}}
```

### Project with Gallery (Raw HTML - Legacy)

For more control or captions, use raw nanogallery2 HTML:

```markdown
---
title: "Quarter Rings"
date: 2019-04-05
draft: false
---

Smashing quarters into rings

<div ID="gallery" data-nanogallery2='{
    "itemsBaseURL": "{{</*s3cdn*/>}}/projects/quarter_rings/",
    "thumbnailWidth": "250",
    "thumbnailHeight": "250",
    "thumbnailBorderVertical": 1,
    "thumbnailBorderHorizontal": 1,
    "thumbnailLabel": {
        "position": "overImageOnBottom",
        "displayDescription": true
    },
    "thumbnailHoverEffect2": "labelAppear75|descriptionSlideUp",
    "galleryDisplayMode": "pagination",
    "galleryMaxRows": 1,
    "thumbnailAlignment": "center",
    "thumbnailOpenImage": true,
    "viewerTools": {
        "topLeft": "pageCounter, label",
        "topRight": "playPauseButton, rotateLeft, rotateRight, fullscreenButton, closeButton"
    }
}'>
    <a href="ring_01.jpg" data-ngthumb="ring_01.jpg" data-ngdesc="Caption here"></a>
    <a href="ring_02.jpg" data-ngthumb="ring_02.jpg" data-ngdesc="Another caption"></a>
</div>
```

---

## Creating a Photography Gallery

### File Location

Create a new file in `content/english/photography/`:
```
YYYY_location_or_event.md
```

Example: `2026_iceland_trip.md`

### Frontmatter Template

```yaml
---
title: "Iceland Trip"
date: 2026-06-15
draft: false
tags: ["Iceland", "Travel", "Landscape"]
---
```

### Photography Gallery Example

```markdown
---
title: "Iceland Trip"
date: 2026-06-15
draft: false
tags: ["Iceland", "Travel"]
---

## Iceland Trip 2026

<div ID="gallery-iceland" data-nanogallery2='{
    "itemsBaseURL": "{{</*s3cdn*/>}}/img/gallery/travel/iceland_2026/",
    "thumbnailWidth": "250",
    "thumbnailHeight": "250",
    "thumbnailBorderVertical": 1,
    "thumbnailBorderHorizontal": 1,
    "thumbnailLabel": {
        "position": "overImageOnBottom",
        "displayDescription": true
    },
    "thumbnailHoverEffect2": "labelAppear75|descriptionSlideUp",
    "galleryDisplayMode": "pagination",
    "galleryMaxRows": 1,
    "thumbnailAlignment": "center",
    "thumbnailOpenImage": true,
    "viewerTools": {
        "topLeft": "pageCounter, label",
        "topRight": "playPauseButton, rotateLeft, rotateRight, fullscreenButton, closeButton"
    }
}'>
    <a href="photo_01.jpg" data-ngthumb="photo_01.jpg" data-ngdesc="Reykjavik Harbor">Reykjavik</a>
    <a href="photo_02.jpg" data-ngthumb="photo_02.jpg" data-ngdesc="Northern Lights">Aurora</a>
</div>
```

---

## Shortcodes Reference

### `{{</* s3cdn */>}}` - S3 CDN Base URL

Returns the S3 CDN base URL configured in `config/*/params.toml`.

**Usage:**
```markdown
![Image]({{</*s3cdn*/>}}/path/to/image.jpg)
```

**With path parameter:**
```markdown
![Image]({{</*s3cdn "projects/myproject/photo.jpg"*/>}})
```

### `{{</* gallery */>}}` - Photo Gallery

Creates a nanogallery2 photo gallery.

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | `""` | S3 CDN subdirectory for images |
| `id` | `"gallery"` | HTML element ID |
| `maxRows` | `2` | Rows per page |
| `thumbnailWidth` | `"250"` | Thumbnail width in pixels |
| `thumbnailHeight` | `"250"` | Thumbnail height in pixels |
| `images` | `""` | Comma-separated list of image filenames |

**Usage with `images` parameter (recommended):**
```markdown
{{</* gallery path="projects/2014_uke" maxRows="1" images="photo1.jpg, photo2.jpg, photo3.jpg" /*/>}}
```

**Usage with inner content (for captions):**
```markdown
{{</* gallery path="projects/myproject" maxRows="2" */>}}
<a href="photo1.jpg" data-ngthumb="photo1.jpg" data-ngdesc="Caption 1"></a>
<a href="photo2.jpg" data-ngthumb="photo2.jpg" data-ngdesc="Caption 2"></a>
{{</* /gallery */>}}
```

### `{{</* video */>}}` - Video Player

Embeds a video with optional controls.

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `path` | (required) | Video path (relative to S3CDN or absolute URL) |
| `poster` | `""` | Poster image path |
| `autoplay` | `false` | Auto-play on load |
| `loop` | `false` | Loop video |
| `muted` | `false` | Mute audio |
| `controls` | `true` | Show playback controls |
| `class` | `"video-player"` | CSS class |

**Usage:**
```markdown
{{</* video path="videos/demo.mp4" /*/>}}

{{</* video path="videos/demo.mp4" poster="videos/demo-poster.jpg" autoplay="true" loop="true" muted="true" /*/>}}
```

---

## Publishing from Obsidian

The blog supports a complete Obsidian-to-Hugo publishing pipeline. Use the conversion script to transform Obsidian notes into Hugo-compatible markdown with automatic media handling.

### Obsidian Note Structure

The conversion script expects notes to follow this structure:

```markdown
---
tags: ['note', 'project', 'cooking']
aliases: []
publish: false
content_type: post
---

# Project Name
**Created**:: MM-DD-YYYY
**Author**:: [[Adam Musciano]]
**Description**:: Brief description of your project

****
## Content

Your main content goes here. Write freely using Obsidian features.

## Associations
- [[related note]]

---------
## Collaborators
-

---------
## Pictures
- [[path/to/image.jpg]]
- ![[another-image.png]]
- [[video.mp4]]

---------
## References
1. https://example.com
```

### Required Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `tags` | No | Obsidian tags (will be converted to Hugo format) |
| `publish` | No | Set to `true` when ready to publish |
| `content_type` | Yes | One of: `post`, `project`, `photography` |

### Body Metadata Fields

These fields are extracted from the note body (not frontmatter):

| Field | Format | Description |
|-------|--------|-------------|
| `**Created**::` | `MM-DD-YYYY` | Date created (converted to `YYYY-MM-DD`) |
| `**Description**::` | Text | Brief description for SEO |
| `**Author**::` | `[[Name]]` | Optional author attribution |

### Pictures Section

The `## Pictures` section supports both wikilink formats:

- `[[path/to/image.jpg]]` - Standard wikilink
- `![[path/to/image.jpg]]` - Embed syntax

Media paths are resolved relative to `~/Notes/Media/` by default.

**Supported formats:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.mp4`, `.mov`, `.webm`, `.avi`

### Content Type Routing

The `content_type` field determines the output location:

| Content Type | Hugo Directory | S3 Path |
|--------------|----------------|---------|
| `post` | `content/english/post/` | `img/posts/<slug>/` |
| `project` | `content/english/projects/` | `projects/<slug>/` |
| `photography` | `content/english/photography/` | `img/gallery/<slug>/` |

### Publishing Commands

Use `scripts/obsidian_to_hugo.py` for conversion:

```bash
# Preview conversion (no files written)
python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --dry-run

# Convert with media upload
python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md"

# Skip media upload (local testing)
python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --skip-upload

# Override content type
python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --type project

# Custom Hugo root directory
python scripts/obsidian_to_hugo.py "~/Notes/Blog/Post.md" --hugo-root /path/to/hugo

# Custom media base directory
python scripts/obsidian_to_hugo.py "~/Notes/Blog/Post.md" --media-base ~/Media
```

### Command Options

| Option | Description |
|--------|-------------|
| `--dry-run`, `-n` | Preview changes without writing files or uploading |
| `--type`, `-t` | Override content type (`post`, `project`, `photography`) |
| `--hugo-root` | Hugo site root directory (default: parent of scripts/) |
| `--media-base` | Base path for media files (default: `~/Notes/Media`) |
| `--skip-upload` | Skip uploading media to MinIO |
| `--skip-video-thumbs` | Skip video thumbnail generation |

### Complete Publishing Workflow

1. **Write in Obsidian** using the Blog Post template
2. **Add media** to `## Pictures` section using wikilinks
3. **Set `publish: true`** in frontmatter when ready
4. **Preview conversion:**
   ```bash
   python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --dry-run
   ```
5. **Convert and upload:**
   ```bash
   python scripts/obsidian_to_hugo.py "~/Notes/Projects/My Project.md"
   ```
6. **Preview locally:**
   ```bash
   hugo server -e development --buildDrafts
   ```
7. **Commit and push:**
   ```bash
   git add . && git commit -m "Add new content" && git push
   ```

### What Gets Converted

The conversion script performs these transformations:

| Obsidian | Hugo |
|----------|------|
| `[[wikilink]]` | Removed (text preserved) |
| `![[image.jpg]]` | Gallery shortcode |
| `**Created**:: MM-DD-YYYY` | `date: YYYY-MM-DD` |
| `**Description**::` | `description:` frontmatter |
| `tags: ['a','b']` | `tags: ["a", "b"]` |
| `## Pictures` section | `{{< gallery />}}` shortcode |
| `## Associations` section | Removed |
| `## Collaborators` section | Removed (if empty) |
| `## References` section | Removed (if empty) |
| Duplicate H1 title | Removed (uses frontmatter) |
| Spaces in filenames | Replaced with underscores |

### Troubleshooting

#### Media files not found

**Symptom:** Warning messages like "Media file not found: path/to/image.jpg"

**Cause:** The script can't locate the referenced media file.

**Solutions:**
1. Verify the file exists in `~/Notes/Media/`
2. Check the exact path in your wikilink matches the file location
3. Use `--media-base` to specify a different media directory:
   ```bash
   python scripts/obsidian_to_hugo.py note.md --media-base ~/Media
   ```

#### rclone not configured

**Symptom:** Upload errors or "rclone: command not found"

**Solutions:**
1. Install rclone: `sudo pacman -S rclone` (Arch) or `brew install rclone` (macOS)
2. Configure remote: `rclone config`
3. Set environment variable if using non-default remote:
   ```bash
   export RCLONE_REMOTE="myremote:bucket/path"
   ```

#### ffmpeg not found (video thumbnails)

**Symptom:** "ffmpeg not found, skipping thumbnail generation"

**Solutions:**
1. Install ffmpeg: `sudo pacman -S ffmpeg` (Arch) or `brew install ffmpeg` (macOS)
2. Or skip thumbnails: `--skip-video-thumbs`

#### Date parsing issues

**Symptom:** Missing or incorrect date in output

**Cause:** Date format doesn't match expected `MM-DD-YYYY`

**Solutions:**
1. Use the correct format in your note: `**Created**:: 01-15-2026`
2. Or add `date:` directly to frontmatter

#### Gallery not rendering

**Symptom:** Gallery shortcode appears as raw text

**Solutions:**
1. Verify Hugo server is running with correct environment
2. Check that `layouts/shortcodes/gallery.html` exists
3. Ensure media was uploaded (check MinIO/S3)
4. Run with `--dry-run` to see generated shortcode

#### Content type detection

**Symptom:** Post ends up in wrong directory

**Solutions:**
1. Explicitly set `content_type: project` (or `post`, `photography`) in frontmatter
2. Or use `--type` flag:
   ```bash
   python scripts/obsidian_to_hugo.py note.md --type project
   ```

#### Python dependencies

**Symptom:** Import errors when running script

**Solutions:**
1. Install dependencies:
   ```bash
   pip install python-dotenv rich pyyaml
   ```
2. Or use a virtual environment:
   ```bash
   cd scripts && python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```

### Environment Variables

The script supports these environment variables (can also be set in `scripts/.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `RCLONE_REMOTE` | `homes3:amblog/assets` | rclone remote and bucket path |

---

## Media Hosting

All media (images, videos) are hosted on S3-compatible storage (MinIO). The `S3CDN` parameter in config provides the base URL.

### Uploading Media

Use the upload script:
```bash
./scripts/upload_media.sh /path/to/local/file.jpg destination/path/file.jpg
```

Or upload through the publish pipeline when publishing from Obsidian.

### S3 Path Conventions

| Content Type | S3 Path |
|--------------|---------|
| Post images | `img/posts/<slug>/` |
| Project images | `projects/<project-name>/` |
| Photography | `img/gallery/travel/<trip>/` |
| Videos | `videos/` |

---

## Video Thumbnails

When including videos in galleries, thumbnails must be generated separately. The gallery shortcode automatically looks for `.thumb.jpg` files for video thumbnails.

### Generating Video Thumbnails

Use the thumbnail generation script:

```bash
# Generate thumbnails for videos already uploaded to S3
./scripts/generate_video_thumbnails.sh --s3 img/gallery/travel/my_trip

# Generate thumbnails from local files and upload
./scripts/generate_video_thumbnails.sh ~/Media/my_videos img/gallery/travel/my_trip
```

### How It Works

1. For each video file (`.mp4`, `.mov`, `.webm`, `.avi`), the script extracts a frame at the 1-second mark
2. The thumbnail is saved as `<video_name>.thumb.jpg` (e.g., `video.mp4` → `video.thumb.jpg`)
3. The gallery shortcode automatically uses the `.thumb.jpg` file for video thumbnails

### Example Gallery with Videos

```markdown
{{</* gallery path="img/gallery/travel/my_trip" images="photo1.jpg, photo2.jpg, clip.mp4, photo3.jpg" /*/>}}
```

The shortcode will automatically use:
- `photo1.jpg` as thumbnail for `photo1.jpg`
- `clip.thumb.jpg` as thumbnail for `clip.mp4`

### Workflow for Publishing Content with Videos

1. Upload videos to S3
2. Generate thumbnails: `./scripts/generate_video_thumbnails.sh --s3 <s3_path>`
3. Add videos to gallery shortcode `images` parameter
4. Build and preview

---

## Building and Previewing

### Local Development

```bash
# Start dev server with drafts
hugo server -e development --buildDrafts --buildFuture

# Or use Makefile
make dev
```

Visit http://localhost:1313

### Production Build

```bash
hugo --environment production

# Or use Makefile
make build
```

### Deployment

The site deploys automatically to Cloudflare Pages when changes are merged to `master`.

```bash
git checkout develop
git add .
git commit -m "Add new content"
git push origin develop
# Create PR to merge develop → master
```
