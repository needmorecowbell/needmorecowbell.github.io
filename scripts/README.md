# Obsidian to Hugo Publishing Tool

A CLI tool for publishing notes from an Obsidian vault to a Hugo blog. It handles frontmatter transformation, Obsidian wikilink conversion, and media embedding.

## Installation

```bash
cd scripts/
pip install -r requirements.txt
```

## Quick Start

```bash
# Scan your vault for publishable notes
python scripts/publish.py scan

# See where notes will be published
python scripts/publish.py list

# Convert a specific note (preview first)
python scripts/publish.py convert ~/Notes/Blog/my-post.md --dry-run

# Convert and write the file
python scripts/publish.py convert ~/Notes/Blog/my-post.md
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

### `convert` - Convert a Note

Converts a single Obsidian note to Hugo format.

```bash
# Preview conversion without writing
python scripts/publish.py convert ~/Notes/Blog/my-post.md --dry-run

# Convert and write to Hugo content directory
python scripts/publish.py convert ~/Notes/Blog/my-post.md

# Specify custom output directory
python scripts/publish.py convert ~/Notes/Blog/my-post.md --output content/english/blog
```

**With `--dry-run`:**
```
[DRY RUN] Would convert: /home/user/Notes/Blog/my-post.md
[DRY RUN] Target path: content/english/post/2024-01-15-my-post.md

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
```

## Default Paths

| Setting | Default Value |
|---------|---------------|
| Obsidian vault | `~/Notes` |
| Hugo output directory | `content/english/post` |
| Skipped directories | `People` |
