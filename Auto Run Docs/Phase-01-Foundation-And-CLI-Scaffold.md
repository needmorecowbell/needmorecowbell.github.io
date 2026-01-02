# Phase 1: Foundation and CLI Scaffold

This phase establishes the development environment and builds a working CLI tool that can scan your Obsidian vault for publishable notes. By the end of this phase, you'll have a `publish` command that finds notes marked with `publish: true` in their frontmatter, displays them in a formatted list, and demonstrates the core Obsidian-to-Hugo syntax conversion. The tool will run end-to-end, proving the concept works before we add media handling in later phases.

## Tasks

- [x] Create a `develop` branch from master to isolate all development work from the live site
  - Branch created and pushed to origin on 2026-01-02

- [x] Create a `scripts/` directory in the blog root for the publishing tools
  - Created `/home/adam/Dev/blog/needmorecowbell.github.io/scripts/` on 2026-01-02

- [x] Create `scripts/publish.py` as the main CLI entry point with argparse supporting these subcommands: `scan` (find publishable notes), `convert` (process a single note), and `list` (show what would be published)
  - Created CLI scaffold with `scan`, `list`, and `convert` subcommands on 2026-01-02
  - Includes `--dry-run` flag for convert, proper error handling, and helpful usage examples

- [x] Create `scripts/obsidian_parser.py` module that reads an Obsidian markdown file and extracts its YAML frontmatter into a Python dict, returning both the frontmatter and the body content separately
  - Created `obsidian_parser.py` with `parse_obsidian_note()`, `parse_frontmatter()`, and `has_publish_flag()` functions on 2026-01-02
  - Added comprehensive test suite in `test_obsidian_parser.py` (13 tests passing)

- [x] Add a `find_publishable_notes()` function in `scripts/obsidian_parser.py` that recursively scans `~/Notes` for markdown files containing `publish: true` in their frontmatter (skip the People directory for performance)
  - Added `find_publishable_notes(vault_path, skip_dirs)` function on 2026-01-02
  - Defaults to scanning `~/Notes` and skipping `People` directory
  - Returns list of dicts with `path`, `frontmatter`, and `body` for each publishable note
  - Gracefully handles invalid YAML and unreadable files
  - Added 10 new unit tests (total now 23 tests passing)

- [x] Create `scripts/syntax_converter.py` module with a `convert_wikilinks()` function that transforms `[[Page Name]]` syntax to standard markdown `[Page Name](/post/page-name/)` links
  - Created `syntax_converter.py` with `convert_wikilinks()` and `slugify()` helper functions on 2026-01-02
  - Handles aliased wikilinks: `[[Page Name|Display Text]]` becomes `[Display Text](/post/page-name/)`
  - Correctly ignores embedded content syntax `![[...]]` (for images/media)
  - Supports custom base paths for different content types (default: `/post/`)
  - Added comprehensive test suite in `test_syntax_converter.py` (30 tests passing)

- [x] Add `convert_embedded_images()` function to `scripts/syntax_converter.py` that transforms `![[path/to/image.jpg]]` syntax to the Hugo shortcode format `{{</* s3cdn */>}}/path/to/image.jpg` (using a placeholder path for now)
  - Added `convert_embedded_images(content, cdn_path)` function on 2026-01-02
  - Transforms `![[image.jpg]]` to `![alt text]({{<s3cdn>}}/image.jpg)` markdown format
  - Supports all common image extensions: jpg, jpeg, png, gif, webp, svg, bmp, tiff, ico
  - Auto-generates alt text from filename (removes hyphens/underscores, converts to spaces)
  - Supports optional `cdn_path` prefix for custom image directory paths
  - Correctly ignores non-image embeds (videos, audio, PDFs) for handling by other functions
  - Added 28 unit tests (total now 59 tests passing in syntax_converter)

- [x] Add `convert_embedded_media()` function to handle video embeds `![[path/to/video.mp4]]` by converting them to HTML5 video tags with s3cdn source paths
  - Added `convert_embedded_media(content, cdn_path)` function on 2026-01-02
  - Converts video embeds `![[video.mp4]]` to `<video controls><source src="{{<s3cdn>}}/video.mp4" type="video/mp4"></video>`
  - Converts audio embeds `![[audio.mp3]]` to `<audio controls><source src="{{<s3cdn>}}/audio.mp3" type="audio/mpeg"></audio>`
  - Supports video formats: mp4, webm, ogg, ogv, mov, avi, mkv, m4v
  - Supports audio formats: mp3, wav, oga, m4a, flac, aac, wma
  - Includes proper MIME type detection for all formats
  - Added 34 comprehensive unit tests (total now 93 tests passing in syntax_converter)

- [x] Create `scripts/frontmatter_transformer.py` module with a `transform_to_hugo()` function that converts Obsidian frontmatter to Hugo-compatible format (ensuring required fields: title, date, draft, tags)
  - Created `frontmatter_transformer.py` with `transform_to_hugo()` function on 2026-01-02
  - Ensures required Hugo fields: title, date (normalized to YYYY-MM-DD), draft (boolean), tags (list)
  - Normalizes dates from various formats (datetime objects, ISO strings, quoted strings, slash-separated, etc.)
  - Preserves optional Hugo fields: author, description, categories, series, subtitle, headerimg, aliases, weight, featured, toc
  - Removes Obsidian-specific `publish` field from output
  - Added comprehensive test suite in `test_frontmatter_transformer.py` (45 tests passing, 161 total tests in scripts/)

- [x] Add logic to `frontmatter_transformer.py` to extract the first H1 heading as the title if no title exists in frontmatter
  - Added `extract_title_from_body(body)` function on 2026-01-02 that scans markdown content for the first H1 heading
  - Modified `transform_to_hugo()` to accept optional `body` parameter for title extraction fallback
  - When frontmatter has no title (or empty title), the first H1 heading (`# Title`) is used instead
  - Added 18 new unit tests (12 for extract_title_from_body, 6 for integration with transform_to_hugo)
  - Total tests in scripts/ now 179 (previously 161)

- [x] Add logic to generate a URL-friendly slug from the title for use as the output filename
  - Added `generate_slug(title, date_str)` function to `frontmatter_transformer.py` on 2026-01-02
  - Generates URL-friendly slugs matching existing blog post naming convention (e.g., `2024-01-15-my-blog-post`)
  - Handles unicode normalization (accented characters like é → e), special character removal, and proper hyphenation
  - Optional date parameter prepends `YYYY-MM-DD-` prefix when provided
  - Returns 'untitled' for empty/invalid titles
  - Added 23 comprehensive unit tests (total tests in scripts/ now 202, previously 179)

- [x] Create `scripts/hugo_writer.py` module with a `write_hugo_post()` function that takes transformed frontmatter and converted body content, then writes a properly formatted Hugo markdown file to a specified output path
  - Created `hugo_writer.py` with `write_hugo_post()`, `preview_hugo_post()`, and `format_frontmatter()` functions on 2026-01-02
  - `write_hugo_post(frontmatter, body, output_path)` writes complete Hugo posts with proper frontmatter formatting
  - `preview_hugo_post(frontmatter, body)` returns the formatted content as string (for --dry-run functionality)
  - Formats frontmatter with proper YAML syntax, maintains field ordering (layout, title, subtitle, author, date, draft, etc.)
  - Handles YAML quoting correctly: quotes strings with colons/special chars, preserves unquoted dates and paths
  - Creates parent directories automatically, ensures files end with newline
  - Added comprehensive test suite in `test_hugo_writer.py` (46 tests passing, 248 total tests in scripts/)

- [x] Implement the `scan` subcommand in `publish.py` that calls `find_publishable_notes()` and prints a formatted table showing: filename, title, date, and tags for each publishable note found
  - Implemented `cmd_scan()` with `print_scan_table()` helper function on 2026-01-02
  - Prints formatted table with columns: Filename, Title, Date, Tags
  - Added helper functions: `format_tags()`, `format_date()`, `truncate()` for display formatting
  - Supports `--vault` argument to specify custom Obsidian vault path
  - Shows summary with count of publishable notes found
  - Handles missing fields gracefully (displays dash for missing values)
  - Truncates long values with ellipsis to maintain table alignment
  - Proper error handling for FileNotFoundError and NotADirectoryError
  - Added comprehensive test suite in `test_publish_cli.py` (25 tests passing, 273 total tests in scripts/)

- [ ] Implement the `list` subcommand that shows the same information as `scan` but also displays where each note would be published in the Hugo content directory

- [ ] Implement the `convert` subcommand that takes a note path as argument, runs the full conversion pipeline (parse -> transform frontmatter -> convert syntax), and writes the result to `content/english/post/` with a `--dry-run` flag that prints output instead of writing

- [ ] Create `scripts/requirements.txt` with dependencies: `pyyaml` for frontmatter parsing and `rich` for beautiful CLI output formatting

- [ ] Add a `scripts/README.md` documenting how to use the publish CLI tool with example commands

- [ ] Test the CLI by running `python scripts/publish.py scan` to verify it finds notes in the vault (create a test note in `~/Notes/Blog/` with `publish: true` if none exist with that frontmatter)

- [ ] Run `hugo server -D` to verify the blog still builds and serves correctly on the develop branch
