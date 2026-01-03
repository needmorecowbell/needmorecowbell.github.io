# Obsidian to Hugo Publishing Tool

A CLI tool for publishing notes from an Obsidian vault to a Hugo blog. It handles frontmatter transformation, Obsidian wikilink conversion, and media embedding.

## Table of Contents

- [Complete Publishing Workflow](#complete-publishing-workflow)
- [Installation](#installation)
- [MinIO Setup (Optional)](#minio-setup-optional)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [How It Works](#how-it-works)
- [Module Overview](#module-overview)
- [Running Tests](#running-tests)
- [Default Paths](#default-paths)

---

## Complete Publishing Workflow

This section provides end-to-end instructions for publishing a blog post from Obsidian to a live Cloudflare Pages site.

### Step 1: Write Your Post in Obsidian

Create a new markdown file in your Obsidian vault (default: `~/Notes/Blog/`). Add YAML frontmatter at the top:

```markdown
---
title: My Amazing Blog Post
date: 2026-01-15
publish: true
draft: false
tags:
  - tutorial
  - python
author: Your Name
description: A brief summary of your post for SEO and previews.
content_type: post
categories:
  - programming
---

# My Amazing Blog Post

Your content here...
```

#### Required Frontmatter Fields

| Field | Description |
|-------|-------------|
| `title` | Post title (or extracted from first H1 heading) |
| `date` | Publication date in YYYY-MM-DD format |
| `publish` | Must be `true` to be discovered by the pipeline |
| `tags` | List of tags for categorization |

#### Optional Frontmatter Fields

| Field | Description |
|-------|-------------|
| `draft` | Set to `true` to mark as draft (won't appear in production) |
| `author` | Author name |
| `description` | SEO description/summary |
| `content_type` | Routing: `post` (default), `photography`, or `project` |
| `categories` | List of categories |
| `series` | Series name for multi-part posts |

#### Content Type-Specific Fields

| Content Type | Additional Fields |
|--------------|-------------------|
| `post` | `author`, `categories`, `series` |
| `photography` | `location`, `camera`, `lens` |
| `project` | `github`, `technologies`, `status` |

### Step 2: Add Media (Images, Videos, Audio)

Embed media using Obsidian's syntax:

```markdown
## Adding Images

![[2026/01/my-photo.jpg]]

## Adding Videos

![[tutorials/demo.mp4]]

## Adding Audio

![[podcasts/episode-01.mp3]]
```

Media files should be in your Media folder (default: `~/Notes/Media/`). Paths are relative to that folder.

### Step 3: Add a Photo Gallery (Optional)

For photography posts or posts with image galleries, add a `## Pictures` section:

```markdown
## Pictures

![[2026/01/gallery/image1.jpg]]
![[2026/01/gallery/image2.png]]
![[2026/01/gallery/image3.webp]]
```

This section is automatically converted to a nanogallery2 photo gallery in the final Hugo output.

### Step 4: Link to Other Posts (Optional)

Use Obsidian wikilinks to reference other posts:

```markdown
Check out my [[Previous Post]] for more context.

You might also like [[Another Article|this related article]].
```

For related content, add an `## Associations` section:

```markdown
## Associations

- [[Getting Started Guide]]
- [[Advanced Tips]]
- [[FAQ]]
```

This section is converted to Hugo internal links and renamed to "## Related" (or can be removed with flags).

### Step 5: Validate Your Post

Before publishing, validate your post to catch issues:

```bash
cd scripts/
python publish.py validate ~/Notes/Blog/my-post.md
```

This checks:
- Required frontmatter fields are present
- Media files exist
- Internal links point to valid posts

### Step 6: Preview the Conversion

Run a dry-run to see the converted output without making changes:

```bash
python publish.py publish ~/Notes/Blog/my-post.md --dry-run
```

This shows:
- The target Hugo path
- Media files that will be uploaded
- Gallery generation status
- A preview of the converted markdown

### Step 7: Publish the Post

When ready, publish the post:

```bash
# With media upload to MinIO
python publish.py publish ~/Notes/Blog/my-post.md

# Skip media upload (use s3cdn shortcode placeholders)
python publish.py publish ~/Notes/Blog/my-post.md --skip-upload

# Auto-confirm without prompts
python publish.py publish ~/Notes/Blog/my-post.md --yes
```

The command will:
1. Validate the post
2. Upload media files to MinIO (if configured)
3. Convert Obsidian syntax to Hugo format
4. Write the Hugo post to the appropriate content directory
5. Record the publish state

### Step 8: Verify with Hugo Build

After publishing, build the Hugo site to verify everything works:

```bash
# From the blog root directory
hugo --environment production

# Or use the Makefile
make build
```

Check for any errors or warnings in the build output.

### Step 9: Preview Locally (Optional)

To preview your post before deploying:

```bash
# Start the Hugo development server
make dev

# Or directly
hugo server -e development --buildDrafts --buildFuture
```

Visit http://localhost:1313 to see your site.

### Step 10: Deploy to Production

Commit and push your changes to trigger a Cloudflare Pages deployment:

```bash
git add content/
git commit -m "Add new blog post: My Amazing Blog Post"
git push origin develop
```

Then create a pull request to merge `develop` into `master`. Cloudflare Pages will automatically build and deploy when changes are merged to `master`.

### Quick Reference: Complete Workflow

```bash
# 1. Validate
python scripts/publish.py validate ~/Notes/Blog/my-post.md

# 2. Preview (dry-run)
python scripts/publish.py publish ~/Notes/Blog/my-post.md --dry-run

# 3. Publish
python scripts/publish.py publish ~/Notes/Blog/my-post.md

# 4. Build Hugo
hugo --environment production

# 5. Commit and push
git add content/
git commit -m "Add: My Amazing Blog Post"
git push origin develop
```

### Makefile Shortcuts

The repository includes a Makefile with common commands:

| Command | Description |
|---------|-------------|
| `make dev` | Start Hugo development server |
| `make build` | Build site for production |
| `make publish-scan` | Scan vault for publishable notes |
| `make publish-list` | Show target paths for all notes |
| `make publish-dry` | Dry-run publish all notes |
| `make test-publish` | Dry-run + Hugo build verification |
| `make test` | Run all tests |
| `make clean` | Remove generated files |

### Bulk Publishing

To publish all notes at once:

```bash
# Preview all publishable notes
python scripts/publish.py publish --all --dry-run

# Publish all notes
python scripts/publish.py publish --all --yes
```

### Troubleshooting

#### Note not discovered by `scan`
- Ensure `publish: true` is in the frontmatter
- Check the file is in the vault directory (`~/Notes/Blog/` by default)
- Verify the YAML frontmatter is valid (between `---` markers)

#### Media files not uploading
- Check MinIO credentials in `scripts/.env`
- Verify media files exist in the Media folder
- Use `python publish.py media <path>` to check references

#### Wikilinks not converting
- Ensure links use the `[[Page Name]]` syntax
- For aliases, use `[[Page Name|Display Text]]`

#### Gallery not generating
- Ensure you have a `## Pictures` section (not `### Pictures`)
- Check images use the `![[path]]` embed syntax
- Use `--no-gallery` to disable if unwanted

---

## Installation

```bash
cd scripts/
pip install -r requirements.txt
```

## MinIO Setup (Optional)

The tool can automatically upload media files (images, videos, audio) to MinIO or any S3-compatible storage. This is optional—without MinIO configured, media embeds will use the `{{<s3cdn>}}` Hugo shortcode.

### 1. Create Environment File

Copy the example environment file and fill in your credentials:

```bash
cp scripts/.env.example scripts/.env
```

Edit `scripts/.env` with your MinIO configuration:

```bash
# MinIO Server Endpoint (without protocol)
MINIO_ENDPOINT=minio.example.com:9000

# Credentials
MINIO_ACCESS_KEY=your-access-key-here
MINIO_SECRET_KEY=your-secret-key-here

# Bucket name (will be created if it doesn't exist)
MINIO_BUCKET=blog-assets

# Use HTTPS (true/false)
MINIO_SECURE=true
```

### 2. Supported Storage Providers

The tool works with any S3-compatible storage:

| Provider | Example Endpoint |
|----------|-----------------|
| Self-hosted MinIO | `minio.example.com:9000` |
| AWS S3 | `s3.amazonaws.com` |
| DigitalOcean Spaces | `nyc3.digitaloceanspaces.com` |
| Backblaze B2 | `s3.us-west-002.backblazeb2.com` |

### 3. Media File Structure

Media files are uploaded preserving their path structure:

```
Local: /home/user/Media/2021/06/photo.jpg
MinIO: bucket/assets/2021/06/photo.jpg
URL:   https://minio.example.com/bucket/assets/2021/06/photo.jpg
```

## Quick Start

```bash
# Scan your vault for publishable notes
python scripts/publish.py scan

# See where notes will be published
python scripts/publish.py list

# Preview media files that would be uploaded
python scripts/publish.py media ~/Notes/Blog/my-post.md

# Convert a specific note (preview first)
python scripts/publish.py convert ~/Notes/Blog/my-post.md --dry-run

# Convert and write the file (with media upload)
python scripts/publish.py convert ~/Notes/Blog/my-post.md

# Convert without uploading media (test mode)
python scripts/publish.py convert ~/Notes/Blog/my-post.md --skip-upload
```

## Commands

### `scan` - Find Publishable Notes

Scans your Obsidian vault for markdown files with `publish: true` in their frontmatter.

```bash
python scripts/publish.py scan

# Use a custom vault location
python scripts/publish.py scan --vault ~/Documents/MyVault
```

**Output example:**
```
Filename                       Title                               Date         Tags
-----------------------------------------------------------------------------------------------
my-first-post.md               My First Blog Post                  2024-01-15   python, tutorial
another-article.md             Another Article                     2024-02-20   hugo, blogging

Found 2 publishable note(s).
```

### `list` - Preview Target Paths

Shows all publishable notes along with their target Hugo output paths.

```bash
python scripts/publish.py list

# Custom vault and output directory
python scripts/publish.py list --vault ~/Notes --output content/english/blog
```

**Output example:**
```
Filename                  Title                          Date         Target Path
---------------------------------------------------------------------------------------------------------
my-first-post.md          My First Blog Post             2024-01-15   content/english/post/2024-01-15-my-first-blog-post.md

Found 1 publishable note(s).
```

### `media` - Preview Media References

Lists all media files (images, videos, audio) referenced in a note without uploading them. Useful for checking what would be uploaded before running `convert`.

```bash
python scripts/publish.py media ~/Notes/Blog/my-post.md
```

**Output example:**
```
Media references in: my-post.md
============================================================

Resolved (3 file(s)):
  2021/06/photo.jpg
    -> /home/user/Media/2021/06/photo.jpg
  2021/06/video.mp4
    -> /home/user/Media/2021/06/video.mp4
  2021/06/diagram.png
    -> /home/user/Media/2021/06/diagram.png

Missing (1 file(s)):
  2021/06/deleted-image.jpg [NOT FOUND]

Summary: 4 reference(s), 3 resolved, 1 missing
```

### `convert` - Convert a Note

Converts a single Obsidian note to Hugo format. When MinIO is configured, media files are automatically uploaded and their URLs are embedded in the converted output.

```bash
# Preview conversion without writing
python scripts/publish.py convert ~/Notes/Blog/my-post.md --dry-run

# Convert and write to Hugo content directory (uploads media to MinIO)
python scripts/publish.py convert ~/Notes/Blog/my-post.md

# Specify custom output directory
python scripts/publish.py convert ~/Notes/Blog/my-post.md --output content/english/blog

# Skip media upload (useful for testing or when MinIO isn't configured)
python scripts/publish.py convert ~/Notes/Blog/my-post.md --skip-upload
```

**Options:**
- `--dry-run`: Preview the conversion without writing files or uploading media
- `--output DIR`: Custom Hugo output directory (default: `content/english/post`)
- `--skip-upload`: Skip uploading media to MinIO (media embeds will use `{{<s3cdn>}}` shortcode)

**With `--dry-run`:**
```
[DRY RUN] Would convert: /home/user/Notes/Blog/my-post.md
[DRY RUN] Target path: content/english/post/2024-01-15-my-post.md
[DRY RUN] Media files found: 3
[DRY RUN] Media files missing: 1

--- Preview of converted content ---

---
title: "My Post"
date: 2024-01-15
draft: false
tags:
  - python
  - tutorial
---

This is my blog post content...
```

**Media Upload Behavior:**
- Existing files in MinIO are skipped (no re-upload)
- Progress bars show upload status when `rich` is installed
- Failed uploads fall back to `{{<s3cdn>}}` shortcode

## How It Works

### Frontmatter Requirements

Notes must have `publish: true` in their YAML frontmatter to be discovered:

```yaml
---
title: My Blog Post
date: 2024-01-15
publish: true
tags:
  - python
  - tutorial
---
```

### Syntax Conversion

The tool automatically converts Obsidian-specific syntax:

| Obsidian Syntax | Hugo Output |
|----------------|-------------|
| `[[Page Name]]` | `[Page Name](/post/page-name/)` |
| `[[Page Name\|Display Text]]` | `[Display Text](/post/page-name/)` |
| `![[image.jpg]]` | `![image]({{<s3cdn>}}/image.jpg)` |
| `![[video.mp4]]` | `<video controls><source src="{{<s3cdn>}}/video.mp4" type="video/mp4"></video>` |
| `![[audio.mp3]]` | `<audio controls><source src="{{<s3cdn>}}/audio.mp3" type="audio/mpeg"></audio>` |

### Frontmatter Transformation

The tool normalizes Obsidian frontmatter to Hugo-compatible format:

- Ensures required Hugo fields: `title`, `date`, `draft`, `tags`
- Normalizes dates to `YYYY-MM-DD` format
- Extracts title from first H1 heading if not in frontmatter
- Removes the `publish` field (Obsidian-specific)
- Preserves optional fields: `author`, `description`, `categories`, `series`, etc.

### Output Filename

Output filenames are generated in Hugo's standard format:
```
YYYY-MM-DD-slug-from-title.md
```

Example: A post titled "My First Blog Post" dated 2024-01-15 becomes:
```
2024-01-15-my-first-blog-post.md
```

## Module Overview

| Module | Purpose |
|--------|---------|
| `publish.py` | Main CLI entry point |
| `obsidian_parser.py` | Parse Obsidian notes and extract frontmatter |
| `syntax_converter.py` | Convert wikilinks, image embeds, and media embeds |
| `frontmatter_transformer.py` | Transform Obsidian frontmatter to Hugo format |
| `hugo_writer.py` | Write formatted Hugo markdown files |
| `media_extractor.py` | Extract and resolve media references from Obsidian syntax |
| `minio_uploader.py` | Upload media files to MinIO/S3-compatible storage |

## Running Tests

```bash
cd scripts/
python -m pytest -v

# Run tests for a specific module
python -m pytest test_obsidian_parser.py -v
python -m pytest test_syntax_converter.py -v
python -m pytest test_frontmatter_transformer.py -v
python -m pytest test_hugo_writer.py -v
python -m pytest test_publish_cli.py -v
python -m pytest test_media_extractor.py -v
python -m pytest test_minio_uploader.py -v
```

## Default Paths

| Setting | Default Value |
|---------|---------------|
| Obsidian vault | `~/Notes` |
| Hugo output directory | `content/english/post` |
| Media folder | `~/Notes/Media` |
| MinIO asset prefix | `assets` |
| Skipped directories | `People` |
