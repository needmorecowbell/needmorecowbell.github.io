# Phase 4: Hugo Config and S3CDN Migration

This phase updates the Hugo configuration and s3cdn shortcode to work with your MinIO instance instead of the legacy S3 bucket. It also adds development/production configuration profiles so you can test with local or staging URLs before publishing to the live site. This ensures the blog infrastructure is ready for the new publishing workflow.

## Tasks

- [x] Create `config/development/params.toml` with S3CDN pointing to your MinIO bucket URL for development testing
  - Created `config/development/params.toml` with `S3CDN = "http://localhost:9000/blog-assets"` for local MinIO testing
  - Added `mediaBasePath` parameter for publish script integration
  - Verified Hugo correctly reads the override (tested with `hugo config -e development`)

- [ ] Update `config/_default/params.toml` to document both the production S3CDN URL and instructions for switching between environments

- [ ] Enhance `layouts/shortcodes/s3cdn.html` to support optional path parameter: `{{</* s3cdn "path/to/file.jpg" */>}}` outputs the full URL, while `{{</* s3cdn */>}}` outputs just the base URL (maintaining backward compatibility)

- [ ] Create `layouts/shortcodes/video.html` shortcode for embedding videos with HTML5 video tag, accepting path, poster (thumbnail), and optional autoplay/loop/muted attributes

- [ ] Create `layouts/shortcodes/gallery.html` shortcode that wraps nanogallery2 initialization, accepting a gallery ID and thumbnail path prefix as parameters

- [ ] Add a config option `params.mediaBasePath` that the publish script can use to determine where to upload media (separate from the public-facing S3CDN URL)

- [ ] Create `scripts/config_manager.py` module that reads Hugo config files and provides the current S3CDN base URL and media upload path to the publish scripts

- [ ] Update `syntax_converter.py` to use `config_manager.py` for the S3CDN base URL instead of hardcoded values

- [ ] Add `--environment` flag to `publish.py` that sets the Hugo environment (development/production) and uses the appropriate config values

- [ ] Create a `Makefile` in the blog root with common commands: `make dev` (hugo server with development config), `make build` (production build), `make publish-dry` (dry-run publish scan)

- [ ] Add `make test-publish` target that runs the publish pipeline in dry-run mode and builds Hugo to verify the output is valid

- [ ] Update `.gitignore` to exclude `scripts/.env` and `scripts/.published.json` from version control

- [ ] Add `scripts/.env` to `.gitignore` but ensure `scripts/.env.example` is tracked

- [ ] Test the full pipeline by running `make dev` and verifying the site loads with the development S3CDN configuration
