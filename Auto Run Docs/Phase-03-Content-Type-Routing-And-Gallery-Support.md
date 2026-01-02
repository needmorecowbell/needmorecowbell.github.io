# Phase 3: Content Type Routing and Gallery Support

This phase adds intelligent content routing so notes are published to the appropriate Hugo section (posts, projects, or photography) based on their tags or explicit configuration. It also adds support for generating nanogallery2 image galleries from Obsidian notes that have a Pictures section, matching the existing project format in the blog.

## Tasks

- [x] Add `content_type` field support in frontmatter that can be set to `post`, `project`, or `photography` to explicitly control where content is published
  - Added `VALID_CONTENT_TYPES` constant and `validate_content_type()` function to `frontmatter_transformer.py`
  - Updated `transform_to_hugo()` to include `content_type` in output when valid
  - Added 28 new tests covering validation, normalization, and integration

- [x] Create `scripts/content_router.py` module with a `determine_content_type()` function that infers the content type from tags if not explicitly set (e.g., `project` tag -> projects section, `photography` tag -> photography section, default to post)
  - Implemented `determine_content_type()` that checks explicit content_type first, then infers from tags
  - Added `infer_content_type_from_tags()` with PROJECT_TAGS (project, projects, woodworking, diy, maker, build, craft, crafts) and PHOTOGRAPHY_TAGS (photography, photos, photo, travel, trip, gallery)
  - Added `get_hugo_section_path()` helper to map content types to Hugo directory paths
  - Created 63 comprehensive tests in `test_content_router.py`

- [ ] Update `hugo_writer.py` to accept the content type and write to the appropriate directory: `content/english/post/`, `content/english/projects/`, or `content/english/photography/`

- [ ] Create `scripts/gallery_generator.py` module with a `extract_pictures_section()` function that parses the `## Pictures` section from Obsidian notes and extracts all media references listed there

- [ ] Add `generate_nanogallery_html()` function to `scripts/gallery_generator.py` that creates the nanogallery2 HTML structure matching the format used in existing project pages (with thumbnails and full-size images)

- [ ] Update the conversion pipeline to detect notes with a Pictures section and automatically generate a gallery at the end of the converted content

- [ ] Add `--no-gallery` flag to the `convert` subcommand to skip gallery generation even if a Pictures section exists

- [ ] Update `frontmatter_transformer.py` to handle project-specific frontmatter fields like `description` and ensure proper date formatting for each content type

- [ ] Add support for the `## Associations` section in Obsidian notes by converting the wikilinks to internal Hugo links or removing them based on a `--keep-associations` flag

- [ ] Create thumbnail generation for gallery images using Pillow: add `generate_thumbnail()` function to `scripts/media_extractor.py` that creates a 400px-wide thumbnail version of each gallery image

- [ ] Add `Pillow` to `scripts/requirements.txt` for image processing

- [ ] Update MinIO uploader to upload both full-size images and thumbnails for gallery content, organizing them in `assets/` and `assets/thumbnails/` paths

- [ ] Add a `publish` subcommand (the main command users will run) that combines scan + convert + upload for a single note, with confirmation prompts for non-dry-run mode

- [ ] Implement `--all` flag for the `publish` subcommand that processes all notes with `publish: true` that haven't been published yet (tracking published state in a local JSON file)

- [ ] Create `scripts/.published.json` tracking file that records which notes have been published (by file hash) to prevent duplicate publishing
