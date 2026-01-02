# Phase 2: Media Extraction and MinIO Integration

This phase adds media handling to the publish pipeline. The CLI will extract all embedded media references from Obsidian notes, resolve them to actual files via the symlinked Media folder, and upload them to MinIO. This transforms the publish tool from a text converter into a complete content pipeline that handles images and videos automatically.

## Tasks

- [x] Create `scripts/media_extractor.py` module with a `find_media_references()` function that parses Obsidian markdown and returns a list of all embedded media paths (from `![[...]]` syntax)
  - Implemented with regex parsing for `![[...]]` syntax
  - Supports all image formats (jpg, jpeg, png, gif, webp, svg, bmp, tiff, ico)
  - Supports all video formats (mp4, webm, ogg, ogv, mov, avi, mkv, m4v)
  - Supports all audio formats (mp3, wav, oga, m4a, flac, aac, wma)
  - 19 unit tests in `test_media_extractor.py`

- [x] Add `resolve_media_path()` function to `scripts/media_extractor.py` that takes an Obsidian media reference and resolves it to the actual file path via `~/Notes/Media` symlink (returning the full path like `/home/adam/Media/2021/06/image.jpg`)
  - Implemented with configurable `media_base` parameter (defaults to `~/Notes/Media`)
  - Resolves symlinks in the base path for accurate final paths
  - Strips leading slashes from references for proper path joining
  - Returns full absolute path string (e.g., `/home/adam/Media/2021/06/image.jpg`)

- [x] Add validation to `resolve_media_path()` that checks if the resolved file actually exists and logs a warning for missing files
  - `validate` parameter (default `True`) controls existence checking
  - Logs warning via `logging` module for missing files or non-file paths
  - Returns `None` when validation fails, path string otherwise
  - 13 unit tests added to `test_media_extractor.py` (total now 32 tests)

- [x] Create `scripts/minio_uploader.py` module with MinIO client initialization using environment variables: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
  - Implemented with lazy module loading to allow testing without minio package installed
  - `get_minio_client()` reads from env vars or accepts direct parameters
  - Supports `MINIO_SECURE` env var (defaults to True for HTTPS)
  - `get_bucket_name()` helper for reading `MINIO_BUCKET` from environment
  - `ensure_bucket_exists()` creates bucket if it doesn't exist
  - Custom `MinioConfigError` exception for missing configuration
  - Added `minio>=7.2.0` to requirements.txt
  - 19 unit tests in `test_minio_uploader.py` (total project tests: 350)

- [x] Add `upload_file()` function to `scripts/minio_uploader.py` that uploads a single file to MinIO, preserving the relative path structure (e.g., `2021/06/image.jpg` becomes `assets/2021/06/image.jpg` in the bucket)
  - Uploads local files to MinIO with configurable `asset_prefix` (defaults to "assets")
  - Normalizes paths by stripping leading slashes from both relative_path and prefix
  - Auto-detects content type using `mimetypes` module (falls back to `application/octet-stream`)
  - Validates that local file exists and is a file (not directory)
  - Returns the object name on success (e.g., `assets/2021/06/image.jpg`), None on S3Error
  - 12 unit tests added to `test_minio_uploader.py` (total project tests: 362)

- [x] Add `upload_media_batch()` function that takes a list of resolved media paths and uploads them all, returning a mapping of original Obsidian references to their final MinIO URLs
  - Takes list of (obsidian_reference, resolved_local_path) tuples
  - Uploads each file to MinIO using `upload_file()` and builds full URLs
  - Returns Dict[str, Optional[str]] mapping references to MinIO URLs (None for failed uploads)
  - Reads endpoint/secure settings from environment if not provided as parameters
  - Added `build_minio_url()` helper function for URL construction
  - 14 unit tests added: 4 for `build_minio_url()` + 10 for `upload_media_batch()` (total project tests: 375)

- [x] Add `--skip-upload` flag to the `convert` subcommand for testing the media extraction without requiring MinIO access
  - Added `--skip-upload` flag to convert subcommand argument parser
  - Flag is stored via `getattr(args, 'skip_upload', False)` for safe access
  - Dry-run output shows "Media upload: SKIPPED" when flag is active
  - 3 new unit tests in `test_publish_cli.py` (total project tests: 378)

- [x] Update `syntax_converter.py` to accept the media URL mapping and use actual MinIO URLs instead of placeholder paths when converting embedded images/videos
  - Added `media_url_map: Optional[Dict[str, str]]` parameter to both `convert_embedded_images()` and `convert_embedded_media()` functions
  - When a media reference is found in the mapping, the full MinIO URL is used instead of the `{{<s3cdn>}}` shortcode
  - Normalizes leading slashes in content paths for consistent lookup
  - Falls back to s3cdn shortcode when: mapping is None, path not in mapping, or URL value is None (failed upload)
  - 17 new unit tests added: 8 for images, 9 for video/audio (total project tests: 395)

- [x] Add `check_existing()` function to `scripts/minio_uploader.py` that checks if a file already exists in MinIO (by path) to avoid redundant uploads
  - Uses MinIO `stat_object` API for efficient metadata-only lookup
  - Returns `True` if object exists, `False` if `NoSuchKey` error
  - Re-raises other S3 errors (permissions, network issues) for proper error handling
  - 5 unit tests added to `test_minio_uploader.py` (total project tests: 400)

- [x] Create `scripts/.env.example` file documenting the required environment variables for MinIO configuration
  - Documents all 5 environment variables: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`
  - Includes examples for self-hosted MinIO and S3-compatible endpoints
  - Added `.env` entries to `.gitignore` to prevent accidental credential commits

- [x] Add `python-dotenv` to `scripts/requirements.txt` and update `publish.py` to load environment variables from `scripts/.env` if it exists
  - Added `python-dotenv>=1.0.0` to requirements.txt
  - Created `load_dotenv()` function in publish.py that loads from `scripts/.env` if present
  - Gracefully handles missing python-dotenv package (returns False instead of crashing)
  - Loads environment variables at module import time before other modules are imported
  - Added 6 unit tests to `test_publish_cli.py` (2 skip if python-dotenv not installed)
  - Total project tests: 406

- [x] Update the `convert` subcommand to extract media references, resolve paths, upload to MinIO (unless `--skip-upload`), and use the resulting URLs in the converted output
  - Added `extract_and_resolve_media()` function that parses note content for media references and resolves them to local file paths
  - Added `upload_media_to_minio()` function that uploads files to MinIO, skipping files that already exist
  - Updated `convert_note()` to accept `media_url_map` parameter for passing MinIO URLs to syntax converters
  - Updated `cmd_convert()` to: extract media references, resolve paths, upload to MinIO (unless `--skip-upload`), and use resulting URLs in converted output
  - Graceful error handling: continues with s3cdn shortcode fallback if MinIO upload fails or minio package isn't installed
  - Dry-run mode shows media files found and missing counts
  - 13 new unit tests added to `test_publish_cli.py` (total project tests: 417)

- [x] Add a `media` subcommand to `publish.py` that lists all media files referenced by a given note without uploading them (useful for previewing what would be uploaded)
  - Takes a note path as argument and analyzes it for `![[...]]` media embeds
  - Shows resolved files with their full local paths (e.g., `/home/user/Media/2021/photo.jpg`)
  - Shows missing files with `[NOT FOUND]` indicator
  - Displays summary with counts: total references, resolved, missing
  - 6 unit tests added to `test_publish_cli.py` (total project tests: 423)

- [x] Add progress bars using `rich` for media upload operations showing current file and overall progress
  - Added `progress_callback` parameter to `upload_media_batch()` in `minio_uploader.py`
  - Callback receives `(filename, current_index, total_count)` for progress tracking
  - Updated `upload_media_to_minio()` in `publish.py` to use `rich.progress` with:
    - Spinner + text column for checking existing files phase
    - Spinner + text + bar + percentage + current file display for upload phase
  - Long filenames are truncated to 30 chars for clean display
  - Falls back to simple text output if `rich` is not installed
  - Added `show_progress` parameter to `upload_media_to_minio()` to disable progress bars when needed
  - 4 new unit tests added to `test_minio_uploader.py` (total project tests: 426)

- [x] Handle common image formats (jpg, jpeg, png, gif, webp) and video formats (mp4, mov, webm) in the media extractor
  - Already implemented in first task: IMAGE_EXTENSIONS and VIDEO_EXTENSIONS sets in `media_extractor.py` include all requested formats
  - Tests `test_all_image_extensions()` and `test_all_video_extensions()` verify full format support
  - All 32 media extractor tests pass

- [ ] Update `scripts/README.md` with MinIO setup instructions and the new media-related commands
