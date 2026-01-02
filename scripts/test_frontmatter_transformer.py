#!/usr/bin/env python3
"""
Tests for the frontmatter_transformer module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from datetime import datetime, date
from frontmatter_transformer import (
    transform_to_hugo,
    _normalize_date,
    _normalize_draft,
    _normalize_tags
)


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
