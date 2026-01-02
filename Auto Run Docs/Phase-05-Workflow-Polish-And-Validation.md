# Phase 5: Workflow Polish and Validation

This phase adds validation, error handling, and quality-of-life improvements to make the publishing workflow robust and pleasant to use. It includes content validation, better error messages, and a preview feature so you can see exactly what will be published before committing.

## Tasks

- [x] Create `scripts/validators.py` module with a `validate_frontmatter()` function that checks for required fields (title, date, tags) and returns a list of validation errors
  - Created `validators.py` with `ValidationIssue` dataclass, `ValidationSeverity` enum, and `validate_frontmatter()` function
  - Checks for missing required fields (ERROR severity) and empty/malformed values (WARNING severity)
  - Includes helper functions: `is_valid()`, `has_warnings()`, `format_issues()`
  - Added comprehensive test suite in `test_validators.py` (44 tests, all passing)

- [x] Add `validate_media_references()` function to `scripts/validators.py` that checks all embedded media references resolve to existing files
  - Uses `find_media_references()` from `media_extractor.py` to extract all `![[path/to/file.ext]]` embeds
  - Uses `resolve_media_path()` to check each reference resolves to an existing file
  - Returns ERROR-level `ValidationIssue` for each missing file with helpful error message showing the reference and expected path
  - Added 20 tests covering: valid/missing images, videos, audio files, nested paths, edge cases (empty content, duplicates, non-media wikilinks)

- [x] Add `validate_internal_links()` function that checks wikilinks point to notes that either exist in the vault or have already been published to Hugo
  - Added `find_wikilinks()` helper to extract non-media wikilinks from content (handles `[[Page]]` and `[[Page|Alias]]` syntax)
  - Added `find_note_in_vault()` to search for notes by name in the Obsidian vault (case-insensitive, searches recursively)
  - Added `find_note_in_hugo()` to search Hugo content directories for published posts (supports dated filenames like `2017-01-04-post-name.md`)
  - Main `validate_internal_links()` validates links exist in either vault or Hugo content
  - Returns ERROR-level `ValidationIssue` for each broken link with descriptive message
  - Added 43 tests covering: wikilink extraction, vault search, Hugo search, link validation, edge cases (empty content, non-existent paths, aliased links, media exclusion)

- [x] Create a `validate` subcommand in `publish.py` that runs all validators on a note and displays a formatted report of any issues
  - Added `cmd_validate()` function that parses a note and runs all three validators (frontmatter, media, internal links)
  - Displays formatted validation report with note path, title, and results from each validator
  - Exit codes: 0 (all passed), 1 (errors found), 2 (warnings only)
  - Added CLI arguments: `--vault` and `--hugo-root` for customizing validation paths
  - Added 8 comprehensive tests covering all exit codes, error conditions, and output formatting

- [x] Add `--strict` flag to the `publish` subcommand that fails if any validation warnings are present (default is to only fail on errors)
  - Flag already implemented at `publish.py:1434-1438` with `action="store_true"`
  - Logic at `publish.py:917-933` checks `strict_mode` and exits with code 2 if warnings found
  - 4 comprehensive tests in `test_publish_cli.py` covering: warnings pass without strict, warnings fail with strict, valid passes with strict, errors+warnings show both
  - Help text: "Fail if any validation warnings are present (default: only fail on errors)"

- [ ] Implement a `preview` subcommand that converts a note, writes it to a temporary directory, runs `hugo server` pointing to that temp content, and opens the browser to preview the single post

- [ ] Add colored output throughout the CLI using `rich`: green for success, yellow for warnings, red for errors

- [ ] Create `scripts/exceptions.py` with custom exception classes: `PublishError`, `ValidationError`, `MediaNotFoundError`, `UploadError` for better error handling

- [ ] Add try/catch blocks throughout the pipeline with user-friendly error messages that explain what went wrong and how to fix it

- [ ] Implement `--verbose` flag for detailed logging of each step in the conversion and upload process

- [ ] Add `--quiet` flag that suppresses all output except errors

- [ ] Create a `status` subcommand that shows: count of publishable notes, count already published, MinIO connection status, and last publish date

- [ ] Add confirmation prompts before destructive operations (uploading to MinIO, overwriting existing Hugo posts) with `--yes` flag to skip prompts

- [ ] Implement `--force` flag for the `publish` subcommand to re-publish notes even if they've been published before (useful for updates)

- [ ] Add post-publish validation that builds Hugo and checks for errors after writing new content
