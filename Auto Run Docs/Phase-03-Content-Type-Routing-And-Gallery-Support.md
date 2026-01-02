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

- [x] Update `hugo_writer.py` to accept the content type and write to the appropriate directory: `content/english/post/`, `content/english/projects/`, or `content/english/photography/`
  - Added `get_output_path()` function that determines the full output path based on content type and hugo root
  - Added `write_hugo_post_routed()` function that combines content type determination with writing
  - Integrates with `content_router.py` to use `determine_content_type()` and `get_hugo_section_path()`
  - Added 25 new tests covering path generation, routing by tags, explicit content types, and integration scenarios

- [x] Create `scripts/gallery_generator.py` module with a `extract_pictures_section()` function that parses the `## Pictures` section from Obsidian notes and extracts all media references listed there
  - Implemented `extract_pictures_section()` that finds and extracts content from `## Pictures` or `## Picture` sections (case-insensitive)
  - Added `extract_media_from_pictures_section()` to extract all Obsidian media embeds (![[...]]) from the Pictures section
  - Added `find_media_in_section()` helper to parse media references with support for all image/video/audio extensions
  - Added `has_pictures_section()`, `get_pictures_section_location()`, and `remove_pictures_section()` utility functions
  - Created 57 comprehensive tests in `test_gallery_generator.py` covering edge cases and integration scenarios

- [x] Add `generate_nanogallery_html()` function to `scripts/gallery_generator.py` that creates the nanogallery2 HTML structure matching the format used in existing project pages (with thumbnails and full-size images)
  - Implemented `generate_nanogallery_html()` that creates nanogallery2 div with anchor tags, matching existing project page format
  - Added `DEFAULT_NANOGALLERY_CONFIG` constant with settings matching existing projects (250px thumbnails, pagination, center alignment)
  - Added `generate_gallery_from_obsidian()` convenience function for Obsidian notes that extracts media and builds gallery
  - Supports thumbnail suffixes, descriptions per media file, and custom config overrides with deep merging
  - Created 29 new tests covering basic generation, config overrides, edge cases, and integration scenarios

- [x] Update the conversion pipeline to detect notes with a Pictures section and automatically generate a gallery at the end of the converted content
  - Updated `convert_note()` in `publish.py` to detect Pictures sections using `has_pictures_section()`
  - Automatically generates nanogallery2 HTML using `generate_gallery_from_obsidian()` when Pictures section is found
  - Removes the Pictures section from body content before syntax conversion (avoiding duplicate media embeds)
  - Appends gallery HTML at the end of the converted content
  - Added `generate_gallery=True` parameter to allow skipping gallery generation
  - Updated `cmd_convert()` to display gallery info in both dry-run and actual conversion modes
  - Added 9 new tests in `test_publish_cli.py` covering gallery generation scenarios

- [x] Add `--no-gallery` flag to the `convert` subcommand to skip gallery generation even if a Pictures section exists
  - Added `--no-gallery` argument to the convert subparser in `publish.py`
  - Modified `cmd_convert()` to pass `generate_gallery` parameter (inverted from `--no-gallery`) to `convert_note()`
  - Updated display logic for both dry-run and actual conversion modes to show "SKIPPED" when gallery is disabled
  - Added 5 new tests in `TestCmdConvertNoGalleryFlag` covering flag behavior, dry-run mode, actual conversion, preservation of Pictures section, and no-effect scenarios
  - Fixed 3 existing tests that needed explicit `no_gallery=False` to work with MagicMock objects

- [x] Update `frontmatter_transformer.py` to handle project-specific frontmatter fields like `description` and ensure proper date formatting for each content type
  - Added `CONTENT_TYPE_FIELDS` constant defining optional fields for each content type (post, project, photography)
  - Added `COMMON_OPTIONAL_FIELDS` for fields that apply to all content types
  - Added `get_optional_fields_for_content_type()` helper function to retrieve appropriate fields
  - Updated `transform_to_hugo()` to accept optional `content_type` parameter that overrides frontmatter value
  - Updated `_normalize_date()` to accept optional `content_type` parameter for content-specific date formatting
  - Post content type preserves ISO 8601 dates with timezone info (e.g., `2024-01-15T10:30:00-05:00`)
  - Project and photography content types normalize to simple `YYYY-MM-DD` format
  - Added 27 new tests covering content-type-specific fields, date formatting, and integration scenarios

- [x] Add support for the `## Associations` section in Obsidian notes by converting the wikilinks to internal Hugo links or removing them based on a `--keep-associations` flag
  - Added `ASSOCIATIONS_SECTION_PATTERN` and `WIKILINK_PATTERN` regex patterns to `gallery_generator.py`
  - Implemented `has_associations_section()`, `extract_associations_section()`, `get_associations_section_location()`, and `remove_associations_section()` functions mirroring the Pictures section pattern
  - Added `extract_wikilinks_from_associations()` and `find_wikilinks_in_section()` to parse wikilinks with support for aliased links ([[Page|Text]])
  - Implemented `convert_associations_to_hugo_links()` that converts wikilinks to Hugo internal links and renames the section header to "## Related"
  - Added `_slugify_for_hugo()` helper function for URL-friendly slug generation
  - Updated `convert_note()` in `publish.py` to handle Associations section: removes by default, or converts with `keep_associations=True`
  - Added `--keep-associations` argument to the convert subparser in `publish.py`
  - Updated `cmd_convert()` to display Associations handling info in both dry-run and actual conversion modes
  - Created 44 new tests in `test_gallery_generator.py` covering all Associations functions
  - Added 9 new tests in `test_publish_cli.py` covering convert_note() and cmd_convert() integration with Associations

- [x] Create thumbnail generation for gallery images using Pillow: add `generate_thumbnail()` function to `scripts/media_extractor.py` that creates a 400px-wide thumbnail version of each gallery image
  - Implemented `generate_thumbnail()` function with 400px default width and aspect ratio preservation
  - Uses LANCZOS resampling for high-quality downsampling
  - Handles RGBA to RGB conversion for JPEG output (using white background for transparency)
  - Supports configurable quality parameter for lossy formats (JPEG, WebP)
  - Added `get_thumbnail_path()` helper function for path generation
  - Added `DEFAULT_THUMBNAIL_WIDTH` (400px) and `THUMBNAIL_SUPPORTED_EXTENSIONS` constants
  - Returns None gracefully for: missing files, unsupported formats, images smaller than target width, or processing errors
  - Created 29 new tests in `TestGenerateThumbnail` class covering all edge cases
  - Created 5 tests in `TestGetThumbnailPath` class for the utility function

- [x] Add `Pillow` to `scripts/requirements.txt` for image processing
  - Added `Pillow>=10.0.0` with descriptive comment

- [x] Update MinIO uploader to upload both full-size images and thumbnails for gallery content, organizing them in `assets/` and `assets/thumbnails/` paths
  - Added `DEFAULT_THUMBNAIL_PREFIX` constant (`assets/thumbnails`) for thumbnail path organization
  - Added `THUMBNAIL_EXTENSIONS` constant with thumbnailable image formats
  - Added `GalleryUploadResult` NamedTuple to return both image and thumbnail URLs
  - Implemented `upload_gallery_media_batch()` function that:
    - Uploads full-size images to `assets/` path
    - Generates thumbnails using `generate_thumbnail()` from `media_extractor.py`
    - Uploads thumbnails to `assets/thumbnails/` path
    - Supports configurable thumbnail width (default 400px) and quality (default 85)
    - Handles mixed media types (images with thumbnails, videos/audio without)
    - Provides progress callback with `has_thumbnail` flag
  - Added 24 new tests in `TestUploadGalleryMediaBatch` class covering all scenarios

- [ ] Add a `publish` subcommand (the main command users will run) that combines scan + convert + upload for a single note, with confirmation prompts for non-dry-run mode

- [ ] Implement `--all` flag for the `publish` subcommand that processes all notes with `publish: true` that haven't been published yet (tracking published state in a local JSON file)

- [ ] Create `scripts/.published.json` tracking file that records which notes have been published (by file hash) to prevent duplicate publishing
