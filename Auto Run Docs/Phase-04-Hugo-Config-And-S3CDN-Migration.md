# Phase 4: Hugo Config and S3CDN Migration

This phase updates the Hugo configuration and s3cdn shortcode to work with your MinIO instance instead of the legacy S3 bucket. It also adds development/production configuration profiles so you can test with local or staging URLs before publishing to the live site. This ensures the blog infrastructure is ready for the new publishing workflow.

## Tasks

- [x] Create `config/development/params.toml` with S3CDN pointing to your MinIO bucket URL for development testing
  - Created `config/development/params.toml` with `S3CDN = "http://localhost:9000/blog-assets"` for local MinIO testing
  - Added `mediaBasePath` parameter for publish script integration
  - Verified Hugo correctly reads the override (tested with `hugo config -e development`)

- [x] Update `config/_default/params.toml` to document both the production S3CDN URL and instructions for switching between environments
  - Added comprehensive documentation header explaining S3CDN configuration
  - Documented both production (`https://s3cdn.617a.net/amblog/assets`) and development (`http://localhost:9000/blog-assets`) URLs
  - Added instructions for switching environments: `hugo server -e development` vs `hugo -e production`
  - Added `mediaBasePath = "amblog/assets"` parameter for publish script integration
  - Cross-referenced config/development/params.toml and scripts/.env files

- [x] Enhance `layouts/shortcodes/s3cdn.html` to support optional path parameter: `{{</* s3cdn "path/to/file.jpg" */>}}` outputs the full URL, while `{{</* s3cdn */>}}` outputs just the base URL (maintaining backward compatibility)
  - Updated shortcode to check for positional parameter `.Get 0`
  - When path is provided: outputs `{baseURL}/{path}`
  - When no path: outputs just `{baseURL}` (backward compatible with existing `{{<s3cdn>}}/path` usage)
  - Uses Hugo whitespace trimming (`{{-` and `-}}`) for clean output
  - Verified with Hugo build - existing gallery and photography pages render correctly

- [x] Create `layouts/shortcodes/video.html` shortcode for embedding videos with HTML5 video tag, accepting path, poster (thumbnail), and optional autoplay/loop/muted attributes
  - Created HTML5 video shortcode with support for both positional and named `path` parameter
  - Supports `poster` for thumbnail images (auto-prefixed with S3CDN URL unless absolute)
  - Supports `autoplay`, `loop`, `muted` boolean attributes (default: false)
  - Supports `controls` (default: true) and `class` (default: "video-player") parameters
  - Automatically prefixes relative paths with S3CDN base URL; absolute URLs pass through unchanged
  - Includes `playsinline` attribute for mobile compatibility
  - Usage examples: `{{</* video "path/to/video.mp4" */>}}` or `{{</* video path="video.mp4" poster="thumb.jpg" autoplay="true" */>}}`
  - Verified with Hugo build - all test cases render correctly

- [x] Create `layouts/shortcodes/gallery.html` shortcode that wraps nanogallery2 initialization, accepting a gallery ID and thumbnail path prefix as parameters
  - Created shortcode with named parameters: `id` (default: "gallery"), `path` (thumbnail path prefix), `maxRows` (default: 2), `thumbnailWidth`/`thumbnailHeight` (default: "250")
  - Uses `{{.Inner}}` to support inline `<a>` tags for gallery items
  - Automatically constructs `itemsBaseURL` from S3CDN param + path with trailing slash
  - Matches existing nanogallery2 configuration from project pages exactly
  - Usage: `{{</* gallery id="my-gallery" path="projects/my_project" maxRows="3" */>}}<a href="...">{{</* /gallery */>}}`
  - Verified with Hugo build - shortcode renders correctly with all parameter combinations

- [x] Add a config option `params.mediaBasePath` that the publish script can use to determine where to upload media (separate from the public-facing S3CDN URL)
  - Already implemented in tasks 1 and 2 above:
    - Production: `mediaBasePath = "amblog/assets"` in `config/_default/params.toml`
    - Development: `mediaBasePath = "blog-assets"` in `config/development/params.toml`
  - Verified both config files contain the parameter with appropriate values for each environment

- [x] Create `scripts/config_manager.py` module that reads Hugo config files and provides the current S3CDN base URL and media upload path to the publish scripts
  - Created `config_manager.py` with functions: `get_hugo_config()`, `get_s3cdn_url()`, `get_media_base_path()`, `get_base_url()`, `list_environments()`
  - Supports environment switching: pass `environment='development'` or `environment='production'` (default)
  - Loads base config from `config/_default/*.toml` and merges environment-specific overrides from `config/<env>/*.toml`
  - Uses Python 3.11+ built-in `tomllib` for TOML parsing (no external dependencies)
  - Includes CLI interface: `python config_manager.py --s3cdn`, `--media-path`, `--list-envs`, `--json`
  - Created comprehensive test suite with 37 tests covering TOML loading, config merging, and real config integration
  - All 855 project tests pass

- [x] Update `syntax_converter.py` to use `config_manager.py` for the S3CDN base URL instead of hardcoded values
  - Added `get_s3cdn_base_url(environment)` convenience function that wraps `config_manager.get_s3cdn_url()`
  - Updated `convert_embedded_images()` to accept optional `s3cdn_base_url` parameter for direct URL output
  - Updated `convert_embedded_media()` to accept optional `s3cdn_base_url` parameter for direct URL output
  - When `s3cdn_base_url` is provided, outputs actual URLs instead of `{{<s3cdn>}}` shortcodes
  - `media_url_map` still takes precedence over `s3cdn_base_url` when both are provided
  - Added 17 new tests covering direct URL output and config_manager integration
  - All 872 tests pass

- [ ] Add `--environment` flag to `publish.py` that sets the Hugo environment (development/production) and uses the appropriate config values

- [ ] Create a `Makefile` in the blog root with common commands: `make dev` (hugo server with development config), `make build` (production build), `make publish-dry` (dry-run publish scan)

- [ ] Add `make test-publish` target that runs the publish pipeline in dry-run mode and builds Hugo to verify the output is valid

- [ ] Update `.gitignore` to exclude `scripts/.env` and `scripts/.published.json` from version control

- [ ] Add `scripts/.env` to `.gitignore` but ensure `scripts/.env.example` is tracked

- [ ] Test the full pipeline by running `make dev` and verifying the site loads with the development S3CDN configuration
