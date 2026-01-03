# Phase 6: Testing and Production Deployment

This phase adds a test suite to ensure the publishing pipeline works correctly, then prepares the develop branch for merging to master. It includes end-to-end tests, a sample publish workflow, and final verification that everything works with Cloudflare Pages deployment.

## Tasks

- [x] Create `scripts/tests/` directory for the test suite
  - Created `scripts/tests/` directory with `__init__.py` to make it a proper Python package

- [ ] Create `scripts/tests/test_obsidian_parser.py` with unit tests for frontmatter extraction and publishable note finding

- [ ] Create `scripts/tests/test_syntax_converter.py` with unit tests for wikilink conversion, image embedding, and video embedding

- [ ] Create `scripts/tests/test_frontmatter_transformer.py` with unit tests for Hugo frontmatter generation and slug creation

- [ ] Create `scripts/tests/test_media_extractor.py` with unit tests for media reference extraction and path resolution

- [ ] Create `scripts/tests/fixtures/` directory with sample Obsidian notes in various formats for testing

- [ ] Add `pytest` to `scripts/requirements.txt`

- [ ] Create `scripts/tests/test_integration.py` with end-to-end tests that convert a sample note and verify the Hugo output

- [ ] Add a `test` target to the Makefile that runs `pytest scripts/tests/`

- [ ] Create `scripts/tests/test_gallery_generator.py` with tests for Pictures section extraction and nanogallery HTML generation

- [ ] Run the full test suite and fix any failing tests

- [ ] Create a sample blog post in `~/Notes/Blog/` with `publish: true`, embedded images, wikilinks, and a Pictures section to serve as a complete test case

- [ ] Run the full publish pipeline on the sample post in dry-run mode and verify the output

- [ ] Run Hugo build (`hugo --environment production`) and verify no errors

- [ ] Create a pull request description template in `.github/PULL_REQUEST_TEMPLATE.md` documenting the new publishing workflow

- [ ] Document the complete publishing workflow in `scripts/README.md` with step-by-step instructions from authoring in Obsidian to seeing the post live

- [ ] Merge the develop branch to master (user should verify Cloudflare Pages builds successfully after this step)
