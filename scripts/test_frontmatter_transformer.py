#!/usr/bin/env python3
"""
Tests for the frontmatter_transformer module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from datetime import datetime, date
from frontmatter_transformer import (
    transform_to_hugo,
    extract_title_from_body,
    generate_slug,
    _normalize_date,
    _normalize_draft,
    _normalize_tags
)


class TestGenerateSlug(unittest.TestCase):
    """Tests for the generate_slug function."""

    def test_simple_title(self):
        """Test generating a slug from a simple title."""
        result = generate_slug('My Blog Post')
        self.assertEqual(result, 'my-blog-post')

    def test_title_with_date(self):
        """Test generating a slug with date prepended."""
        result = generate_slug('My Blog Post', '2024-01-15')
        self.assertEqual(result, '2024-01-15-my-blog-post')

    def test_title_with_special_characters(self):
        """Test that special characters are removed."""
        result = generate_slug("My Post: A Journey (2024) - Part 1!")
        self.assertEqual(result, 'my-post-a-journey-2024-part-1')

    def test_title_with_underscores(self):
        """Test that underscores are converted to hyphens."""
        result = generate_slug('my_post_title')
        self.assertEqual(result, 'my-post-title')

    def test_title_with_multiple_spaces(self):
        """Test that multiple spaces become single hyphens."""
        result = generate_slug('My    Big     Title')
        self.assertEqual(result, 'my-big-title')

    def test_title_with_unicode(self):
        """Test that unicode characters are normalized to ASCII."""
        result = generate_slug('Café Résumé Naïve')
        self.assertEqual(result, 'cafe-resume-naive')

    def test_title_with_accents(self):
        """Test various accented characters."""
        result = generate_slug('über élève señor')
        self.assertEqual(result, 'uber-eleve-senor')

    def test_title_with_numbers(self):
        """Test that numbers are preserved."""
        result = generate_slug('Top 10 Tips for 2024')
        self.assertEqual(result, 'top-10-tips-for-2024')

    def test_empty_title(self):
        """Test that empty title returns 'untitled'."""
        result = generate_slug('')
        self.assertEqual(result, 'untitled')

    def test_none_title(self):
        """Test that None title returns 'untitled'."""
        result = generate_slug(None)
        self.assertEqual(result, 'untitled')

    def test_whitespace_only_title(self):
        """Test that whitespace-only title returns 'untitled'."""
        result = generate_slug('   ')
        self.assertEqual(result, 'untitled')

    def test_special_chars_only(self):
        """Test title with only special characters returns 'untitled'."""
        result = generate_slug('!@#$%^&*()')
        self.assertEqual(result, 'untitled')

    def test_leading_trailing_special_chars(self):
        """Test that leading/trailing special chars are stripped."""
        result = generate_slug('---My Title---')
        self.assertEqual(result, 'my-title')

    def test_apostrophes_removed(self):
        """Test that apostrophes are removed cleanly."""
        result = generate_slug("Let's Learn About YARA")
        self.assertEqual(result, 'lets-learn-about-yara')

    def test_colons_and_commas(self):
        """Test colons and commas are handled."""
        result = generate_slug('Part 1: Getting Started, An Introduction')
        self.assertEqual(result, 'part-1-getting-started-an-introduction')

    def test_question_marks(self):
        """Test question marks are removed."""
        result = generate_slug('What Is Python?')
        self.assertEqual(result, 'what-is-python')

    def test_mixed_case(self):
        """Test that mixed case is converted to lowercase."""
        result = generate_slug('UPPERCASE and MixedCase')
        self.assertEqual(result, 'uppercase-and-mixedcase')

    def test_date_with_empty_title(self):
        """Test date with empty title."""
        result = generate_slug('', '2024-01-15')
        self.assertEqual(result, '2024-01-15-untitled')

    def test_no_date(self):
        """Test slug without date (date_str is None)."""
        result = generate_slug('Simple Title', None)
        self.assertEqual(result, 'simple-title')

    def test_existing_post_style(self):
        """Test replicating the style of existing posts in the blog."""
        # Based on: 2018-11-13-coding-livestream-1-find-every-arby-s-in-america.md
        result = generate_slug("Coding Livestream 1: Find Every Arby's in America", '2018-11-13')
        self.assertEqual(result, '2018-11-13-coding-livestream-1-find-every-arbys-in-america')

    def test_linux_tips_style(self):
        """Test another existing post style."""
        # Based on: 2017-08-01-linux-tips-easy-aliases.md
        result = generate_slug('Linux Tips: Easy Aliases', '2017-08-01')
        self.assertEqual(result, '2017-08-01-linux-tips-easy-aliases')

    def test_ampersand_handling(self):
        """Test that ampersands are removed."""
        result = generate_slug('Tips & Tricks')
        self.assertEqual(result, 'tips-tricks')

    def test_parentheses_handling(self):
        """Test that parentheses are removed."""
        result = generate_slug('My Guide (Updated)')
        self.assertEqual(result, 'my-guide-updated')


class TestTransformToHugo(unittest.TestCase):
    """Tests for the transform_to_hugo function."""

    def test_empty_frontmatter(self):
        """Test transforming empty frontmatter provides defaults."""
        result = transform_to_hugo({})
        self.assertEqual(result['title'], '')
        self.assertFalse(result['draft'])
        self.assertEqual(result['tags'], [])
        # Date should be today's date
        self.assertEqual(result['date'], datetime.now().strftime('%Y-%m-%d'))

    def test_complete_frontmatter(self):
        """Test transforming complete frontmatter."""
        frontmatter = {
            'title': 'My Test Post',
            'date': '2024-01-15',
            'draft': False,
            'tags': ['python', 'hugo']
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['title'], 'My Test Post')
        self.assertEqual(result['date'], '2024-01-15')
        self.assertFalse(result['draft'])
        self.assertEqual(result['tags'], ['python', 'hugo'])

    def test_publish_field_removed(self):
        """Test that 'publish' field from Obsidian is not included in output."""
        frontmatter = {
            'title': 'Test',
            'publish': True,
            'tags': ['test']
        }
        result = transform_to_hugo(frontmatter)
        self.assertNotIn('publish', result)

    def test_optional_fields_preserved(self):
        """Test that optional Hugo fields are preserved if present."""
        frontmatter = {
            'title': 'Test',
            'author': 'Adam Musciano',
            'description': 'A test post',
            'categories': ['tech'],
            'series': ['tutorial'],
            'subtitle': 'A subtitle',
            'headerimg': '/img/header.jpg'
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['author'], 'Adam Musciano')
        self.assertEqual(result['description'], 'A test post')
        self.assertEqual(result['categories'], ['tech'])
        self.assertEqual(result['series'], ['tutorial'])
        self.assertEqual(result['subtitle'], 'A subtitle')
        self.assertEqual(result['headerimg'], '/img/header.jpg')

    def test_unknown_fields_not_copied(self):
        """Test that unknown/custom Obsidian fields are not copied."""
        frontmatter = {
            'title': 'Test',
            'custom_obsidian_field': 'value',
            'another_unknown': 123
        }
        result = transform_to_hugo(frontmatter)
        self.assertNotIn('custom_obsidian_field', result)
        self.assertNotIn('another_unknown', result)


class TestExtractTitleFromBody(unittest.TestCase):
    """Tests for the extract_title_from_body function."""

    def test_simple_h1_heading(self):
        """Test extracting a simple H1 heading."""
        body = "# My Blog Post\n\nThis is the content."
        result = extract_title_from_body(body)
        self.assertEqual(result, 'My Blog Post')

    def test_h1_with_preceding_content(self):
        """Test H1 heading that's not on the first line."""
        body = "Some intro text\n\n# The Real Title\n\nMore content"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'The Real Title')

    def test_no_h1_heading(self):
        """Test body with no H1 heading."""
        body = "## This is H2\n\n### This is H3\n\nJust some text."
        result = extract_title_from_body(body)
        self.assertIsNone(result)

    def test_h2_not_matched(self):
        """Test that H2 headings are not matched as title."""
        body = "## Section Header\n\nContent here"
        result = extract_title_from_body(body)
        self.assertIsNone(result)

    def test_h3_not_matched(self):
        """Test that H3 headings are not matched as title."""
        body = "### Subsection\n\nContent here"
        result = extract_title_from_body(body)
        self.assertIsNone(result)

    def test_empty_body(self):
        """Test empty body content."""
        result = extract_title_from_body('')
        self.assertIsNone(result)

    def test_none_body(self):
        """Test None body content."""
        result = extract_title_from_body(None)
        self.assertIsNone(result)

    def test_first_h1_is_used(self):
        """Test that only the first H1 heading is extracted."""
        body = "# First Title\n\nSome content\n\n# Second Title\n\nMore content"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'First Title')

    def test_h1_with_extra_whitespace(self):
        """Test H1 heading with extra whitespace."""
        body = "#    Spaced Out Title   \n\nContent"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'Spaced Out Title')

    def test_h1_with_special_characters(self):
        """Test H1 heading with special characters."""
        body = "# My Post: A Journey (2024) - Part 1!\n\nContent"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'My Post: A Journey (2024) - Part 1!')

    def test_h1_found_before_code_block(self):
        """Test H1 heading found before a code block with comment."""
        body = "# My Title\n\n```python\n# comment in code\n```\n\nContent"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'My Title')

    def test_h1_with_markdown_formatting(self):
        """Test H1 heading containing markdown formatting."""
        body = "# My **Bold** and *Italic* Title\n\nContent"
        result = extract_title_from_body(body)
        self.assertEqual(result, 'My **Bold** and *Italic* Title')


class TestTransformToHugoTitleExtraction(unittest.TestCase):
    """Tests for title extraction from body in transform_to_hugo."""

    def test_title_from_frontmatter_preferred(self):
        """Test that frontmatter title is used when present."""
        frontmatter = {'title': 'Frontmatter Title'}
        body = "# Body Title\n\nContent"
        result = transform_to_hugo(frontmatter, body)
        self.assertEqual(result['title'], 'Frontmatter Title')

    def test_title_from_body_when_no_frontmatter_title(self):
        """Test title extraction from body when frontmatter has no title."""
        frontmatter = {'publish': True}
        body = "# My Post Title\n\nThis is the content."
        result = transform_to_hugo(frontmatter, body)
        self.assertEqual(result['title'], 'My Post Title')

    def test_title_from_body_with_empty_frontmatter_title(self):
        """Test title extraction when frontmatter title is empty string."""
        frontmatter = {'title': ''}
        body = "# Extracted Title\n\nContent"
        result = transform_to_hugo(frontmatter, body)
        self.assertEqual(result['title'], 'Extracted Title')

    def test_empty_title_when_no_h1_in_body(self):
        """Test that title is empty when no H1 and no frontmatter title."""
        frontmatter = {'publish': True}
        body = "## Just H2\n\nContent without H1"
        result = transform_to_hugo(frontmatter, body)
        self.assertEqual(result['title'], '')

    def test_no_body_provided(self):
        """Test that function works without body parameter."""
        frontmatter = {'title': 'My Title'}
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['title'], 'My Title')

    def test_none_body_with_no_title(self):
        """Test empty title when body is None and no frontmatter title."""
        frontmatter = {}
        result = transform_to_hugo(frontmatter, None)
        self.assertEqual(result['title'], '')


class TestNormalizeDate(unittest.TestCase):
    """Tests for the _normalize_date function."""

    def test_none_returns_today(self):
        """Test that None returns today's date."""
        result = _normalize_date(None)
        expected = datetime.now().strftime('%Y-%m-%d')
        self.assertEqual(result, expected)

    def test_datetime_object(self):
        """Test normalizing a datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = _normalize_date(dt)
        self.assertEqual(result, '2024-01-15')

    def test_date_object(self):
        """Test normalizing a date object."""
        d = date(2024, 1, 15)
        result = _normalize_date(d)
        self.assertEqual(result, '2024-01-15')

    def test_iso_string(self):
        """Test normalizing ISO format string."""
        result = _normalize_date('2024-01-15')
        self.assertEqual(result, '2024-01-15')

    def test_quoted_string(self):
        """Test normalizing quoted date string."""
        result = _normalize_date('"2024-01-15"')
        self.assertEqual(result, '2024-01-15')

    def test_single_quoted_string(self):
        """Test normalizing single-quoted date string."""
        result = _normalize_date("'2024-01-15'")
        self.assertEqual(result, '2024-01-15')

    def test_slash_format(self):
        """Test normalizing slash-separated date."""
        result = _normalize_date('2024/01/15')
        self.assertEqual(result, '2024-01-15')

    def test_datetime_string_with_time(self):
        """Test normalizing datetime string with time."""
        result = _normalize_date('2024-01-15T10:30:00')
        self.assertEqual(result, '2024-01-15')

    def test_datetime_string_with_space(self):
        """Test normalizing datetime string with space separator."""
        result = _normalize_date('2024-01-15 10:30:00')
        self.assertEqual(result, '2024-01-15')

    def test_long_month_format(self):
        """Test normalizing 'Month DD, YYYY' format."""
        result = _normalize_date('January 15, 2024')
        self.assertEqual(result, '2024-01-15')

    def test_short_month_format(self):
        """Test normalizing 'Mon DD, YYYY' format."""
        result = _normalize_date('Jan 15, 2024')
        self.assertEqual(result, '2024-01-15')

    def test_empty_string_returns_today(self):
        """Test that empty string returns today's date."""
        result = _normalize_date('')
        expected = datetime.now().strftime('%Y-%m-%d')
        self.assertEqual(result, expected)

    def test_whitespace_only_returns_today(self):
        """Test that whitespace-only string returns today's date."""
        result = _normalize_date('   ')
        expected = datetime.now().strftime('%Y-%m-%d')
        self.assertEqual(result, expected)

    def test_unrecognized_format_returned_as_is(self):
        """Test that unrecognized date format is returned as-is."""
        result = _normalize_date('some-weird-date')
        self.assertEqual(result, 'some-weird-date')


class TestNormalizeDraft(unittest.TestCase):
    """Tests for the _normalize_draft function."""

    def test_none_returns_false(self):
        """Test that None returns False."""
        result = _normalize_draft(None)
        self.assertFalse(result)

    def test_true_boolean(self):
        """Test that True returns True."""
        result = _normalize_draft(True)
        self.assertTrue(result)

    def test_false_boolean(self):
        """Test that False returns False."""
        result = _normalize_draft(False)
        self.assertFalse(result)

    def test_string_true(self):
        """Test that 'true' string returns True."""
        result = _normalize_draft('true')
        self.assertTrue(result)

    def test_string_true_uppercase(self):
        """Test that 'TRUE' string returns True."""
        result = _normalize_draft('TRUE')
        self.assertTrue(result)

    def test_string_yes(self):
        """Test that 'yes' string returns True."""
        result = _normalize_draft('yes')
        self.assertTrue(result)

    def test_string_one(self):
        """Test that '1' string returns True."""
        result = _normalize_draft('1')
        self.assertTrue(result)

    def test_string_false(self):
        """Test that 'false' string returns False."""
        result = _normalize_draft('false')
        self.assertFalse(result)

    def test_string_no(self):
        """Test that 'no' string returns False."""
        result = _normalize_draft('no')
        self.assertFalse(result)

    def test_integer_truthy(self):
        """Test that truthy integer returns True."""
        result = _normalize_draft(1)
        self.assertTrue(result)

    def test_integer_falsy(self):
        """Test that falsy integer returns False."""
        result = _normalize_draft(0)
        self.assertFalse(result)


class TestNormalizeTags(unittest.TestCase):
    """Tests for the _normalize_tags function."""

    def test_none_returns_empty_list(self):
        """Test that None returns empty list."""
        result = _normalize_tags(None)
        self.assertEqual(result, [])

    def test_list_of_strings(self):
        """Test normalizing a list of strings."""
        result = _normalize_tags(['python', 'hugo', 'blog'])
        self.assertEqual(result, ['python', 'hugo', 'blog'])

    def test_list_with_whitespace(self):
        """Test normalizing a list with whitespace in items."""
        result = _normalize_tags(['  python  ', 'hugo', '  blog'])
        self.assertEqual(result, ['python', 'hugo', 'blog'])

    def test_list_with_empty_items(self):
        """Test that empty items are filtered out."""
        result = _normalize_tags(['python', '', 'hugo', None, 'blog'])
        self.assertEqual(result, ['python', 'hugo', 'blog'])

    def test_single_tag_string(self):
        """Test normalizing a single tag as string."""
        result = _normalize_tags('python')
        self.assertEqual(result, ['python'])

    def test_comma_separated_string(self):
        """Test normalizing comma-separated tags."""
        result = _normalize_tags('python, hugo, blog')
        self.assertEqual(result, ['python', 'hugo', 'blog'])

    def test_comma_separated_with_whitespace(self):
        """Test normalizing comma-separated tags with extra whitespace."""
        result = _normalize_tags('  python  ,  hugo  ,  blog  ')
        self.assertEqual(result, ['python', 'hugo', 'blog'])

    def test_empty_string_returns_empty_list(self):
        """Test that empty string returns empty list."""
        result = _normalize_tags('')
        self.assertEqual(result, [])

    def test_whitespace_only_string(self):
        """Test that whitespace-only string returns empty list."""
        result = _normalize_tags('   ')
        self.assertEqual(result, [])

    def test_list_with_integers(self):
        """Test that integers in list are converted to strings."""
        result = _normalize_tags([1, 2, 3])
        self.assertEqual(result, ['1', '2', '3'])

    def test_mixed_type_list(self):
        """Test normalizing a list with mixed types."""
        result = _normalize_tags(['python', 123, 'hugo'])
        self.assertEqual(result, ['python', '123', 'hugo'])


class TestTransformToHugoIntegration(unittest.TestCase):
    """Integration tests simulating real Obsidian frontmatter."""

    def test_typical_obsidian_note(self):
        """Test transforming typical Obsidian note frontmatter."""
        frontmatter = {
            'title': 'My Blog Post',
            'date': '2024-01-15',
            'publish': True,
            'tags': ['python', 'automation'],
            'draft': False
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['title'], 'My Blog Post')
        self.assertEqual(result['date'], '2024-01-15')
        self.assertEqual(result['tags'], ['python', 'automation'])
        self.assertFalse(result['draft'])
        self.assertNotIn('publish', result)

    def test_minimal_obsidian_note(self):
        """Test transforming minimal Obsidian note (just publish flag)."""
        frontmatter = {
            'publish': True
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['title'], '')
        self.assertEqual(result['tags'], [])
        self.assertFalse(result['draft'])
        # Date should be today
        self.assertIn('-', result['date'])

    def test_obsidian_with_yaml_date_object(self):
        """Test Obsidian note where YAML parsed date as datetime object."""
        frontmatter = {
            'title': 'Test',
            'date': datetime(2024, 6, 15, 12, 0, 0),
            'publish': True
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['date'], '2024-06-15')

    def test_preserves_series_for_hugo(self):
        """Test that series field is preserved for Hugo series support."""
        frontmatter = {
            'title': 'Tutorial Part 1',
            'series': ['my-tutorial-series'],
            'publish': True
        }
        result = transform_to_hugo(frontmatter)
        self.assertEqual(result['series'], ['my-tutorial-series'])


if __name__ == '__main__':
    unittest.main()
