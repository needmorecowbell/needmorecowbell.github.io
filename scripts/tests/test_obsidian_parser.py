#!/usr/bin/env python3
"""
Tests for the obsidian_parser module.

Tests frontmatter extraction and publishable note finding functionality.
"""

import sys
import unittest
import tempfile
from datetime import date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_parser import (
    parse_obsidian_note,
    parse_frontmatter,
    has_publish_flag,
    find_publishable_notes,
)


class TestParseFrontmatter(unittest.TestCase):
    """Tests for parse_frontmatter function."""

    def test_standard_frontmatter(self):
        """Test parsing standard YAML frontmatter."""
        content = """---
title: My Test Post
date: 2024-01-15
tags:
  - python
  - testing
publish: true
---

# Hello World

This is the body content.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter['title'], 'My Test Post')
        self.assertEqual(frontmatter['date'], date(2024, 1, 15))
        self.assertEqual(frontmatter['tags'], ['python', 'testing'])
        self.assertIs(frontmatter['publish'], True)
        self.assertIn('# Hello World', body)
        self.assertIn('This is the body content.', body)

    def test_no_frontmatter(self):
        """Test parsing content with no frontmatter."""
        content = """# Just a Heading

Some regular markdown content.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter, {})
        self.assertIn('# Just a Heading', body)
        self.assertIn('Some regular markdown content.', body)

    def test_empty_frontmatter(self):
        """Test parsing empty frontmatter block."""
        content = """---
---

Body content here.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter, {})
        self.assertIn('Body content here.', body)

    def test_frontmatter_with_complex_types(self):
        """Test parsing frontmatter with nested structures."""
        content = """---
title: Complex Post
metadata:
  author: John
  version: 1.0
aliases:
  - old-post-name
  - another-alias
---

Content here.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter['title'], 'Complex Post')
        self.assertEqual(frontmatter['metadata']['author'], 'John')
        self.assertEqual(frontmatter['metadata']['version'], 1.0)
        self.assertEqual(len(frontmatter['aliases']), 2)

    def test_preserves_body_whitespace(self):
        """Test that body whitespace is preserved correctly."""
        content = """---
title: Test
---

First paragraph.

Second paragraph with    spaces.

    Indented code block.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertIn('First paragraph.', body)
        self.assertIn('Second paragraph with    spaces.', body)
        self.assertIn('    Indented code block.', body)

    def test_frontmatter_with_multiline_string(self):
        """Test parsing frontmatter with multiline string values."""
        content = """---
title: Test Post
description: |
  This is a multiline
  description that spans
  multiple lines.
---

Body content.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter['title'], 'Test Post')
        self.assertIn('multiline', frontmatter['description'])
        self.assertIn('multiple lines', frontmatter['description'])

    def test_frontmatter_with_quoted_strings(self):
        """Test parsing frontmatter with quoted string values."""
        content = """---
title: "A title with: colons"
subtitle: 'Single quoted value'
---

Body.
"""
        frontmatter, body = parse_frontmatter(content)

        self.assertEqual(frontmatter['title'], 'A title with: colons')
        self.assertEqual(frontmatter['subtitle'], 'Single quoted value')


class TestHasPublishFlag(unittest.TestCase):
    """Tests for has_publish_flag function."""

    def test_publish_true(self):
        """Test detecting publish: true."""
        self.assertIs(has_publish_flag({'publish': True}), True)

    def test_publish_false(self):
        """Test detecting publish: false."""
        self.assertIs(has_publish_flag({'publish': False}), False)

    def test_no_publish_key(self):
        """Test when publish key doesn't exist."""
        self.assertIs(has_publish_flag({'title': 'Test'}), False)

    def test_publish_string_true(self):
        """Test that string 'true' is not treated as boolean True."""
        self.assertIs(has_publish_flag({'publish': 'true'}), False)

    def test_empty_frontmatter(self):
        """Test empty frontmatter dict."""
        self.assertIs(has_publish_flag({}), False)

    def test_publish_none(self):
        """Test when publish is explicitly set to None."""
        self.assertIs(has_publish_flag({'publish': None}), False)

    def test_publish_integer_one(self):
        """Test that integer 1 is not treated as True."""
        self.assertIs(has_publish_flag({'publish': 1}), False)


class TestParseObsidianNote(unittest.TestCase):
    """Tests for parse_obsidian_note function."""

    def test_parse_real_file(self):
        """Test parsing an actual file from disk."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: File Test
publish: true
---

Content from file.
""")
            f.flush()
            temp_path = Path(f.name)

        try:
            frontmatter, body = parse_obsidian_note(temp_path)

            self.assertEqual(frontmatter['title'], 'File Test')
            self.assertIs(frontmatter['publish'], True)
            self.assertIn('Content from file.', body)
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Test FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            parse_obsidian_note(Path('/nonexistent/path/file.md'))

    def test_unicode_content(self):
        """Test handling of unicode characters."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8'
        ) as f:
            f.write("""---
title: Unicode Test 日本語
---

Content with emojis 🎉 and symbols (c) (r)
""")
            f.flush()
            temp_path = Path(f.name)

        try:
            frontmatter, body = parse_obsidian_note(temp_path)

            self.assertEqual(frontmatter['title'], 'Unicode Test 日本語')
            self.assertIn('🎉', body)
        finally:
            temp_path.unlink()

    def test_accepts_string_path(self):
        """Test that string paths are also accepted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: String Path Test
---

Content.
""")
            f.flush()
            temp_path = f.name  # String, not Path

        try:
            frontmatter, body = parse_obsidian_note(temp_path)
            self.assertEqual(frontmatter['title'], 'String Path Test')
        finally:
            Path(temp_path).unlink()


class TestFindPublishableNotes(unittest.TestCase):
    """Tests for find_publishable_notes function."""

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def _create_note(self, relative_path: str, content: str):
        """Helper to create a note file in the temp vault."""
        file_path = self.vault_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        return file_path

    def test_finds_publishable_note(self):
        """Test finding a single publishable note."""
        self._create_note('Blog/test-post.md', """---
title: Test Post
publish: true
---

Content here.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Test Post')
        self.assertIn('Content here.', results[0]['body'])

    def test_ignores_non_publishable_notes(self):
        """Test that notes without publish: true are skipped."""
        self._create_note('Blog/published.md', """---
title: Published
publish: true
---
Content.
""")
        self._create_note('Blog/draft.md', """---
title: Draft
publish: false
---
Draft content.
""")
        self._create_note('Blog/no-flag.md', """---
title: No Flag
---
No flag content.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Published')

    def test_skips_people_directory_by_default(self):
        """Test that People directory is skipped by default."""
        self._create_note('Blog/post.md', """---
title: Blog Post
publish: true
---
Blog content.
""")
        self._create_note('People/john.md', """---
title: John Doe
publish: true
---
Person note.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Blog Post')

    def test_custom_skip_dirs(self):
        """Test with custom directories to skip."""
        self._create_note('Blog/post.md', """---
title: Blog Post
publish: true
---
Content.
""")
        self._create_note('Private/secret.md', """---
title: Secret Note
publish: true
---
Secret content.
""")
        self._create_note('Archive/old.md', """---
title: Old Note
publish: true
---
Old content.
""")
        results = find_publishable_notes(
            self.vault_path, skip_dirs=['Private', 'Archive']
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Blog Post')

    def test_recursive_scanning(self):
        """Test that nested directories are scanned recursively."""
        self._create_note('Blog/2024/January/post1.md', """---
title: January Post
publish: true
---
Content.
""")
        self._create_note('Blog/2024/February/post2.md', """---
title: February Post
publish: true
---
Content.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 2)
        titles = [r['frontmatter']['title'] for r in results]
        self.assertIn('January Post', titles)
        self.assertIn('February Post', titles)

    def test_vault_not_found(self):
        """Test FileNotFoundError for non-existent vault."""
        with self.assertRaises(FileNotFoundError):
            find_publishable_notes(Path('/nonexistent/vault'))

    def test_vault_not_directory(self):
        """Test NotADirectoryError when vault path is a file."""
        file_path = self._create_note('file.md', 'content')
        with self.assertRaises(NotADirectoryError):
            find_publishable_notes(file_path)

    def test_skips_invalid_yaml(self):
        """Test that files with invalid YAML are skipped gracefully."""
        self._create_note('Blog/valid.md', """---
title: Valid Post
publish: true
---
Content.
""")
        self._create_note('Blog/invalid.md', """---
title: [Invalid YAML
  broken: {syntax
---
Content.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Valid Post')

    def test_empty_vault(self):
        """Test empty vault returns empty list."""
        results = find_publishable_notes(self.vault_path)
        self.assertEqual(results, [])

    def test_returns_path_in_results(self):
        """Test that results include the file path."""
        self._create_note('Blog/my-post.md', """---
title: My Post
publish: true
---
Content.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertIn('path', results[0])
        self.assertEqual(results[0]['path'].name, 'my-post.md')

    def test_multiple_publishable_notes(self):
        """Test finding multiple publishable notes in various locations."""
        self._create_note('Blog/post1.md', """---
title: Post 1
publish: true
---
Content 1.
""")
        self._create_note('Projects/project-log.md', """---
title: Project Log
publish: true
---
Project content.
""")
        self._create_note('Travel/trip-notes.md', """---
title: Trip Notes
publish: true
---
Travel content.
""")
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 3)
        titles = {r['frontmatter']['title'] for r in results}
        self.assertEqual(titles, {'Post 1', 'Project Log', 'Trip Notes'})

    def test_nested_skip_dir(self):
        """Test that skip_dirs works on nested paths."""
        self._create_note('Blog/post.md', """---
title: Blog Post
publish: true
---
Content.
""")
        self._create_note('Blog/People/author.md', """---
title: Author Bio
publish: true
---
Bio content.
""")
        # People is in the path, so it should be skipped by default
        results = find_publishable_notes(self.vault_path)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['frontmatter']['title'], 'Blog Post')


if __name__ == '__main__':
    unittest.main(verbosity=2)
