# Pull Request

## Summary

<!-- Provide a brief description of what this PR does -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Blog content (new posts, updates to existing posts)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have tested my changes locally
- [ ] I have updated documentation if needed
- [ ] All tests pass (`make test`)
- [ ] Hugo build completes without errors (`hugo --environment production`)

---

## Publishing Workflow Reference

This repository uses an Obsidian to Hugo publishing pipeline. Below is a reference for the workflow.

### Quick Start

```bash
# From the scripts/ directory
cd scripts/

# 1. Scan vault for publishable notes (notes with `publish: true`)
python publish.py scan

# 2. Preview where notes will be published
python publish.py list

# 3. Check media references in a note
python publish.py media ~/Notes/Blog/my-post.md

# 4. Validate a note before publishing
python publish.py validate ~/Notes/Blog/my-post.md

# 5. Preview conversion (dry-run)
python publish.py convert ~/Notes/Blog/my-post.md --dry-run

# 6. Convert and publish (with media upload to MinIO)
python publish.py convert ~/Notes/Blog/my-post.md

# 7. Build Hugo site
hugo --environment production
```

### Obsidian Note Requirements

Notes must have `publish: true` in their YAML frontmatter:

```yaml
---
title: My Blog Post
date: 2024-01-15
publish: true
tags:
  - python
  - tutorial
content_type: post  # Optional: post, photography, project
---
```

### Supported Content Types

| Content Type | Hugo Section | Optional Fields |
|--------------|--------------|-----------------|
| `post` (default) | `content/english/post/` | author, categories, series |
| `photography` | `content/english/photography/` | location, camera, lens |
| `project` | `content/english/project/` | github, technologies, status |

### Syntax Conversions

The publishing pipeline automatically converts:

| Obsidian Syntax | Hugo Output |
|----------------|-------------|
| `[[Page Name]]` | `[Page Name](/post/page-name/)` |
| `[[Page Name\|Display Text]]` | `[Display Text](/post/page-name/)` |
| `![[image.jpg]]` | `![image]({{<s3cdn>}}/image.jpg)` |
| `![[video.mp4]]` | HTML5 `<video>` element |
| `![[audio.mp3]]` | HTML5 `<audio>` element |

### Special Sections

- **Pictures Section**: A `## Pictures` section with embedded images is converted to a nanogallery2 photo gallery
- **Associations Section**: A `## Associations` section with wikilinks is converted to Hugo internal links

### Media Upload

Media files (images, videos, audio) can be automatically uploaded to MinIO/S3-compatible storage:

1. Configure `scripts/.env` with MinIO credentials
2. Run `python publish.py convert <path>` (uploads automatically)
3. Use `--skip-upload` to skip media upload during testing

### Running Tests

```bash
# Run all tests
make test

# Or from scripts directory
cd scripts/ && python -m pytest -v
```

### CLI Commands Reference

| Command | Description |
|---------|-------------|
| `scan` | Find all notes with `publish: true` |
| `list` | Show target Hugo paths for publishable notes |
| `media <path>` | List media references in a note |
| `validate <path>` | Validate note before publishing |
| `convert <path>` | Convert note to Hugo format |
| `publish` | Interactive publishing workflow |

For detailed documentation, see `scripts/README.md`.
