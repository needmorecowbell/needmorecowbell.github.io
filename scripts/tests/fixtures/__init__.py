"""
Test fixtures for the Obsidian to Hugo publishing pipeline.

This package contains sample Obsidian notes in various formats for testing:

- basic_publishable_post.md: Standard post with publish: true
- draft_post.md: Post with publish: false (should be ignored)
- no_publish_flag.md: Post without publish field (should be ignored)
- complex_frontmatter.md: Post with nested structures, aliases, content types
- post_with_pictures_section.md: Post with ## Pictures gallery section
- post_with_embedded_media.md: Post with images, video, and audio embeds
- post_with_wikilinks.md: Post with various wikilink formats
- unicode_content.md: Post with international characters and emoji
- invalid_yaml.md: Post with malformed YAML frontmatter
- empty_frontmatter.md: Post with empty frontmatter block
- photography_content_type.md: Photography-specific content type
- project_content_type.md: Project-specific content type
"""

from pathlib import Path

# Path to the fixtures directory
FIXTURES_DIR = Path(__file__).parent

def get_fixture_path(filename: str) -> Path:
    """Get the path to a fixture file."""
    return FIXTURES_DIR / filename

def read_fixture(filename: str) -> str:
    """Read and return the contents of a fixture file."""
    path = get_fixture_path(filename)
    return path.read_text(encoding='utf-8')
