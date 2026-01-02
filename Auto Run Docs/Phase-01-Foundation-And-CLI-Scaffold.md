# Phase 1: Foundation and CLI Scaffold

This phase establishes the development environment and builds a working CLI tool that can scan your Obsidian vault for publishable notes. By the end of this phase, you'll have a `publish` command that finds notes marked with `publish: true` in their frontmatter, displays them in a formatted list, and demonstrates the core Obsidian-to-Hugo syntax conversion. The tool will run end-to-end, proving the concept works before we add media handling in later phases.

## Tasks

- [x] Create a `develop` branch from master to isolate all development work from the live site
  - Branch created and pushed to origin on 2026-01-02

- [x] Create a `scripts/` directory in the blog root for the publishing tools
  - Created `/home/adam/Dev/blog/needmorecowbell.github.io/scripts/` on 2026-01-02

- [ ] Create `scripts/publish.py` as the main CLI entry point with argparse supporting these subcommands: `scan` (find publishable notes), `convert` (process a single note), and `list` (show what would be published)

- [ ] Create `scripts/obsidian_parser.py` module that reads an Obsidian markdown file and extracts its YAML frontmatter into a Python dict, returning both the frontmatter and the body content separately

- [ ] Add a `find_publishable_notes()` function in `scripts/obsidian_parser.py` that recursively scans `~/Notes` for markdown files containing `publish: true` in their frontmatter (skip the People directory for performance)

- [ ] Create `scripts/syntax_converter.py` module with a `convert_wikilinks()` function that transforms `[[Page Name]]` syntax to standard markdown `[Page Name](/post/page-name/)` links

- [ ] Add `convert_embedded_images()` function to `scripts/syntax_converter.py` that transforms `![[path/to/image.jpg]]` syntax to the Hugo shortcode format `{{</* s3cdn */>}}/path/to/image.jpg` (using a placeholder path for now)

- [ ] Add `convert_embedded_media()` function to handle video embeds `![[path/to/video.mp4]]` by converting them to HTML5 video tags with s3cdn source paths

- [ ] Create `scripts/frontmatter_transformer.py` module with a `transform_to_hugo()` function that converts Obsidian frontmatter to Hugo-compatible format (ensuring required fields: title, date, draft, tags)

- [ ] Add logic to `frontmatter_transformer.py` to extract the first H1 heading as the title if no title exists in frontmatter

- [ ] Add logic to generate a URL-friendly slug from the title for use as the output filename

- [ ] Create `scripts/hugo_writer.py` module with a `write_hugo_post()` function that takes transformed frontmatter and converted body content, then writes a properly formatted Hugo markdown file to a specified output path

- [ ] Implement the `scan` subcommand in `publish.py` that calls `find_publishable_notes()` and prints a formatted table showing: filename, title, date, and tags for each publishable note found

- [ ] Implement the `list` subcommand that shows the same information as `scan` but also displays where each note would be published in the Hugo content directory

- [ ] Implement the `convert` subcommand that takes a note path as argument, runs the full conversion pipeline (parse -> transform frontmatter -> convert syntax), and writes the result to `content/english/post/` with a `--dry-run` flag that prints output instead of writing

- [ ] Create `scripts/requirements.txt` with dependencies: `pyyaml` for frontmatter parsing and `rich` for beautiful CLI output formatting

- [ ] Add a `scripts/README.md` documenting how to use the publish CLI tool with example commands

- [ ] Test the CLI by running `python scripts/publish.py scan` to verify it finds notes in the vault (create a test note in `~/Notes/Blog/` with `publish: true` if none exist with that frontmatter)

- [ ] Run `hugo server -D` to verify the blog still builds and serves correctly on the develop branch
