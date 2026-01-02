# Phase 2: Media Extraction and MinIO Integration

This phase adds media handling to the publish pipeline. The CLI will extract all embedded media references from Obsidian notes, resolve them to actual files via the symlinked Media folder, and upload them to MinIO. This transforms the publish tool from a text converter into a complete content pipeline that handles images and videos automatically.

## Tasks

- [x] Create `scripts/media_extractor.py` module with a `find_media_references()` function that parses Obsidian markdown and returns a list of all embedded media paths (from `![[...]]` syntax)
  - Implemented with regex parsing for `![[...]]` syntax
  - Supports all image formats (jpg, jpeg, png, gif, webp, svg, bmp, tiff, ico)
  - Supports all video formats (mp4, webm, ogg, ogv, mov, avi, mkv, m4v)
  - Supports all audio formats (mp3, wav, oga, m4a, flac, aac, wma)
  - 19 unit tests in `test_media_extractor.py`

- [ ] Add `resolve_media_path()` function to `scripts/media_extractor.py` that takes an Obsidian media reference and resolves it to the actual file path via `~/Notes/Media` symlink (returning the full path like `/home/adam/Media/2021/06/image.jpg`)

- [ ] Add validation to `resolve_media_path()` that checks if the resolved file actually exists and logs a warning for missing files

- [ ] Create `scripts/minio_uploader.py` module with MinIO client initialization using environment variables: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`

- [ ] Add `upload_file()` function to `scripts/minio_uploader.py` that uploads a single file to MinIO, preserving the relative path structure (e.g., `2021/06/image.jpg` becomes `assets/2021/06/image.jpg` in the bucket)

- [ ] Add `upload_media_batch()` function that takes a list of resolved media paths and uploads them all, returning a mapping of original Obsidian references to their final MinIO URLs

- [ ] Add `--skip-upload` flag to the `convert` subcommand for testing the media extraction without requiring MinIO access

- [ ] Update `syntax_converter.py` to accept the media URL mapping and use actual MinIO URLs instead of placeholder paths when converting embedded images/videos

- [ ] Add `check_existing()` function to `scripts/minio_uploader.py` that checks if a file already exists in MinIO (by path) to avoid redundant uploads

- [ ] Create `scripts/.env.example` file documenting the required environment variables for MinIO configuration

- [ ] Add `python-dotenv` to `scripts/requirements.txt` and update `publish.py` to load environment variables from `scripts/.env` if it exists

- [ ] Update the `convert` subcommand to extract media references, resolve paths, upload to MinIO (unless `--skip-upload`), and use the resulting URLs in the converted output

- [ ] Add a `media` subcommand to `publish.py` that lists all media files referenced by a given note without uploading them (useful for previewing what would be uploaded)

- [ ] Add progress bars using `rich` for media upload operations showing current file and overall progress

- [ ] Handle common image formats (jpg, jpeg, png, gif, webp) and video formats (mp4, mov, webm) in the media extractor

- [ ] Update `scripts/README.md` with MinIO setup instructions and the new media-related commands
