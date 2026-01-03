# Adam Musciano

Personal blog built with Hugo, featuring an Obsidian-to-Hugo publishing pipeline and S3-compatible media storage.

**Live site:** [adammusciano.com](https://adammusciano.com)

## Quick Start

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Start development server
make dev

# Build for production
make build
```

## Project Structure

```
├── config/                 # Hugo configuration
│   ├── _default/          # Base config (production)
│   └── development/       # Development overrides (local MinIO)
├── content/english/       # Site content
│   ├── post/              # Blog posts
│   ├── projects/          # Project writeups
│   ├── photography/       # Photo galleries
│   └── gallery.md         # Main gallery page
├── layouts/               # Custom Hugo templates
│   ├── photography/       # Photography section layouts
│   ├── projects/          # Project section layouts
│   └── shortcodes/        # Custom shortcodes (s3cdn, etc.)
├── scripts/               # Obsidian publishing tools
├── static/                # Static assets (JS, favicons)
└── themes/anatole/        # Hugo theme (submodule)
```

## Content Sections

| Section | Path | Description |
|---------|------|-------------|
| Posts | `content/english/post/` | Technical blog posts |
| Projects | `content/english/projects/` | Maker and DIY project documentation |
| Photography | `content/english/photography/` | Photo galleries with nanogallery2 |
| Gallery | `content/english/gallery.md` | Main photography index |

## Publishing from Obsidian

This blog includes a CLI tool for publishing notes directly from an Obsidian vault. Notes with `publish: true` in their frontmatter are converted to Hugo format with automatic:

- Wikilink conversion to Hugo internal links
- Media embedding via S3CDN shortcode
- Frontmatter transformation
- Photo gallery generation

### Commands

```bash
# Check publishing status
python scripts/publish.py status

# Scan vault for publishable notes
python scripts/publish.py scan

# Preview where notes will be published
python scripts/publish.py list

# Validate a note before publishing
python scripts/publish.py validate ~/Notes/Blog/my-post.md

# Convert a single note (dry-run)
python scripts/publish.py convert ~/Notes/Blog/my-post.md --dry-run

# Publish a note (converts + uploads media)
python scripts/publish.py publish ~/Notes/Blog/my-post.md

# Publish all pending notes
python scripts/publish.py publish --all

# Preview a post locally before publishing
python scripts/publish.py preview ~/Notes/Blog/my-post.md
```

See [scripts/README.md](scripts/README.md) for full documentation.

## Make Targets

```bash
make dev           # Start Hugo dev server (localhost:1313)
make build         # Build site for production
make publish-dry   # Dry-run publish all pending notes
make publish-scan  # Scan vault for publishable notes
make test-publish  # Dry-run + Hugo build verification
make test          # Run publishing script tests
make clean         # Remove generated files
make help          # Show all targets
```

## Media Storage

Media files (images, videos, audio) are stored in S3-compatible storage (MinIO). The `{{< s3cdn >}}` shortcode generates URLs:

```markdown
{{< s3cdn "2024/01/photo.jpg" >}}
<!-- Outputs: https://s3cdn.617a.net/amblog/assets/2024/01/photo.jpg -->
```

### Environment Configuration

Development uses local MinIO, production uses the CDN. Copy the example config:

```bash
cp scripts/.env.example scripts/.env
```

Configure your MinIO/S3 credentials in `scripts/.env`:

```bash
MINIO_ENDPOINT=minio.example.com:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=blog-assets
MINIO_SECURE=true
```

## Development

### Prerequisites

- Hugo (extended version recommended)
- Python 3.8+
- MinIO/S3 storage (optional, for media uploads)

### Running Tests

```bash
cd scripts
python -m pytest -v
```

### Theme

The site uses the [Anatole theme](https://github.com/lxndrblz/anatole) as a git submodule with custom layout overrides in `/layouts/`.

## Deployment

The site deploys automatically via Cloudflare Pages when changes are pushed to the `master` branch.

## License

Content is copyright Adam Musciano. Theme is MIT licensed.
