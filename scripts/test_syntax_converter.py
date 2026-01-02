#!/usr/bin/env python3
"""
Tests for the syntax_converter module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from syntax_converter import slugify, convert_wikilinks


class TestSlugify(unittest.TestCase):
    """Tests for the slugify function."""

    def test_simple_text(self):
        """Test slugifying simple text."""
        self.assertEqual(slugify('Hello World'), 'hello-world')

    def test_already_lowercase(self):
        """Test text that's already lowercase."""
        self.assertEqual(slugify('hello world'), 'hello-world')

    def test_mixed_case(self):
        """Test mixed case text."""
        self.assertEqual(slugify('HeLLo WoRLd'), 'hello-world')

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        self.assertEqual(slugify("Hello, World! How's it going?"), 'hello-world-hows-it-going')

    def test_multiple_spaces(self):
        """Test multiple spaces become single hyphen."""
        self.assertEqual(slugify('Hello    World'), 'hello-world')

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        self.assertEqual(slugify('Post 123'), 'post-123')

    def test_underscores_preserved(self):
        """Test that underscores are preserved."""
        self.assertEqual(slugify('my_post_title'), 'my_post_title')

    def test_hyphens_preserved(self):
        """Test that existing hyphens are preserved."""
        self.assertEqual(slugify('my-post-title'), 'my-post-title')

    def test_leading_trailing_spaces(self):
        """Test leading/trailing spaces are handled."""
        self.assertEqual(slugify('  Hello World  '), 'hello-world')

    def test_empty_string(self):
        """Test empty string returns empty string."""
        self.assertEqual(slugify(''), '')

    def test_unicode_characters(self):
        """Test that unicode characters are removed (for URL safety)."""
        self.assertEqual(slugify('Café Résumé'), 'caf-rsum')


class TestConvertWikilinks(unittest.TestCase):
    """Tests for the convert_wikilinks function."""

    def test_simple_wikilink(self):
        """Test converting a simple wikilink."""
        content = 'Check out [[My Page]] for more info.'
        expected = 'Check out [My Page](/post/my-page/) for more info.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_multiple_wikilinks(self):
        """Test converting multiple wikilinks in same content."""
        content = 'See [[Page One]] and [[Page Two]] for details.'
        expected = 'See [Page One](/post/page-one/) and [Page Two](/post/page-two/) for details.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_aliased_wikilink(self):
        """Test converting wikilink with display text alias."""
        content = 'Check out [[My Long Page Name|this page]] for more.'
        expected = 'Check out [this page](/post/my-long-page-name/) for more.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_mixed_aliased_and_simple(self):
        """Test mix of aliased and simple wikilinks."""
        content = '[[Simple Link]] and [[Complex Page|easy link]] here.'
        expected = '[Simple Link](/post/simple-link/) and [easy link](/post/complex-page/) here.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_at_line_start(self):
        """Test wikilink at the start of a line."""
        content = '[[My Page]] is interesting.'
        expected = '[My Page](/post/my-page/) is interesting.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_at_line_end(self):
        """Test wikilink at the end of a line."""
        content = 'See more at [[My Page]]'
        expected = 'See more at [My Page](/post/my-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_alone_on_line(self):
        """Test wikilink as entire line content."""
        content = '[[Standalone Page]]'
        expected = '[Standalone Page](/post/standalone-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_preserves_regular_markdown_links(self):
        """Test that standard markdown links are not affected."""
        content = 'Regular [link](https://example.com) stays the same.'
        expected = 'Regular [link](https://example.com) stays the same.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_does_not_match_embedded_images(self):
        """Test that embedded images ![[image.jpg]] are NOT converted."""
        content = 'Here is an image: ![[my-image.jpg]]'
        expected = 'Here is an image: ![[my-image.jpg]]'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_mixed_wikilinks_and_embeds(self):
        """Test content with both wikilinks and embeds."""
        content = 'See [[My Page]] and look at ![[image.png]] for reference.'
        expected = 'See [My Page](/post/my-page/) and look at ![[image.png]] for reference.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_custom_base_path(self):
        """Test using a custom base path."""
        content = 'Check out [[My Project]].'
        expected = 'Check out [My Project](/projects/my-project/).'
        self.assertEqual(convert_wikilinks(content, base_path='/projects/'), expected)

    def test_base_path_without_trailing_slash(self):
        """Test base path without trailing slash."""
        content = '[[My Page]]'
        expected = '[My Page](/post/my-page/)'
        self.assertEqual(convert_wikilinks(content, base_path='/post'), expected)

    def test_whitespace_in_link_text(self):
        """Test that extra whitespace in link text is handled."""
        content = '[[  Spaced Page  ]]'
        expected = '[Spaced Page](/post/spaced-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_whitespace_in_alias(self):
        """Test that extra whitespace in alias is handled."""
        content = '[[Page Name |  Display Text  ]]'
        expected = '[Display Text](/post/page-name/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_no_wikilinks(self):
        """Test content with no wikilinks returns unchanged."""
        content = 'Just regular markdown text with no special links.'
        expected = 'Just regular markdown text with no special links.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_empty_content(self):
        """Test empty content returns empty string."""
        self.assertEqual(convert_wikilinks(''), '')

    def test_multiline_content(self):
        """Test wikilinks across multiple lines."""
        content = """First line with [[Link One]].

Second paragraph has [[Link Two|custom text]].

And [[Link Three]] at the end."""
        expected = """First line with [Link One](/post/link-one/).

Second paragraph has [custom text](/post/link-two/).

And [Link Three](/post/link-three/) at the end."""
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_with_numbers(self):
        """Test wikilink containing numbers."""
        content = '[[2024 Goals]]'
        expected = '[2024 Goals](/post/2024-goals/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_with_special_chars_in_name(self):
        """Test wikilink with special characters in page name."""
        content = "[[What's New?]]"
        expected = "[What's New?](/post/whats-new/)"
        self.assertEqual(convert_wikilinks(content), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
