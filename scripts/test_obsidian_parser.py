#!/usr/bin/env python3
"""
Tests for the obsidian_parser module.

Uses unittest (standard library) for compatibility.
"""

import unittest
import tempfile
from datetime import date
from pathlib import Path
from obsidian_parser import parse_obsidian_note, parse_frontmatter, has_publish_flag


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
        self.assertEqual(frontmatter['date'], date(2024, 1, 15))  # YAML parses dates as datetime.date
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
        # YAML should parse 'true' as boolean, but if it's a string, reject it
        self.assertIs(has_publish_flag({'publish': 'true'}), False)

    def test_empty_frontmatter(self):
        """Test empty frontmatter dict."""
        self.assertIs(has_publish_flag({}), False)


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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
title: Unicode Test 日本語
---

Content with emojis 🎉 and symbols © ®
""")
            f.flush()
            temp_path = Path(f.name)

        try:
            frontmatter, body = parse_obsidian_note(temp_path)

            self.assertEqual(frontmatter['title'], 'Unicode Test 日本語')
            self.assertIn('🎉', body)
            self.assertIn('©', body)
        finally:
            temp_path.unlink()


if __name__ == '__main__':
    unittest.main(verbosity=2)
