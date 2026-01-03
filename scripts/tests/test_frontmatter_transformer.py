#!/usr/bin/env python3
"""
Tests for the frontmatter_transformer module.

Tests Hugo frontmatter generation and slug creation functionality.
"""

import sys
import unittest
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from frontmatter_transformer import (
    VALID_CONTENT_TYPES,
    CONTENT_TYPE_FIELDS,
    COMMON_OPTIONAL_FIELDS,
    get_optional_fields_for_content_type,
    validate_content_type,
    generate_slug,
    extract_title_from_body,
    transform_to_hugo,
    _normalize_date,
    _normalize_draft,
    _normalize_tags,
)


class TestGetOptionalFieldsForContentType(unittest.TestCase):
    """Tests for get_optional_fields_for_content_type function."""

    def test_post_content_type(self):
        """Test getting optional fields for post content type."""
        fields = get_optional_fields_for_content_type('post')
        self.assertIn('author', fields)
        self.assertIn('description', fields)
        self.assertIn('categories', fields)
        self.assertIn('series', fields)
        self.assertIn('toc', fields)

    def test_project_content_type(self):
        """Test getting optional fields for project content type."""
        fields = get_optional_fields_for_content_type('project')
        self.assertIn('author', fields)
        self.assertIn('description', fields)
        self.assertIn('featured', fields)

    def test_photography_content_type(self):
        """Test getting optional fields for photography content type."""
        fields = get_optional_fields_for_content_type('photography')
        self.assertIn('author', fields)
        self.assertIn('description', fields)
        self.assertIn('location', fields)

    def test_none_content_type(self):
        """Test getting optional fields when content type is None."""
        fields = get_optional_fields_for_content_type(None)
        self.assertEqual(fields, COMMON_OPTIONAL_FIELDS)

    def test_invalid_content_type(self):
        """Test getting optional fields for invalid content type falls back to common."""
        fields = get_optional_fields_for_content_type('invalid')
        self.assertEqual(fields, COMMON_OPTIONAL_FIELDS)

    def test_returns_copy(self):
        """Test that the returned list is a copy, not the original."""
        fields1 = get_optional_fields_for_content_type('post')
        fields2 = get_optional_fields_for_content_type('post')
        fields1.append('custom_field')
        self.assertNotIn('custom_field', fields2)


class TestValidateContentType(unittest.TestCase):
    """Tests for validate_content_type function."""

    def test_valid_post(self):
        """Test validating 'post' content type."""
        self.assertEqual(validate_content_type('post'), 'post')

    def test_valid_project(self):
        """Test validating 'project' content type."""
        self.assertEqual(validate_content_type('project'), 'project')

    def test_valid_photography(self):
        """Test validating 'photography' content type."""
        self.assertEqual(validate_content_type('photography'), 'photography')

    def test_case_insensitive(self):
        """Test that content type validation is case insensitive."""
        self.assertEqual(validate_content_type('POST'), 'post')
        self.assertEqual(validate_content_type('Project'), 'project')
        self.assertEqual(validate_content_type('PHOTOGRAPHY'), 'photography')

    def test_with_whitespace(self):
        """Test that whitespace is trimmed."""
        self.assertEqual(validate_content_type('  post  '), 'post')
        self.assertEqual(validate_content_type('\tproject\n'), 'project')

    def test_none_value(self):
        """Test that None returns None."""
        self.assertIsNone(validate_content_type(None))

    def test_invalid_string(self):
        """Test that invalid strings return None."""
        self.assertIsNone(validate_content_type('blog'))
        self.assertIsNone(validate_content_type('article'))
        self.assertIsNone(validate_content_type('invalid'))

    def test_empty_string(self):
        """Test that empty string returns None."""
        self.assertIsNone(validate_content_type(''))
        self.assertIsNone(validate_content_type('   '))

    def test_non_string_types(self):
        """Test that non-string types return None."""
        self.assertIsNone(validate_content_type(123))
        self.assertIsNone(validate_content_type(['post']))
        self.assertIsNone(validate_content_type({'type': 'post'}))


class TestGenerateSlug(unittest.TestCase):
    """Tests for generate_slug function."""

    def test_simple_title(self):
        """Test generating slug from simple title."""
        self.assertEqual(generate_slug('Hello World'), 'hello-world')

    def test_already_lowercase(self):
        """Test title that's already lowercase."""
        self.assertEqual(generate_slug('hello world'), 'hello-world')

    def test_mixed_case(self):
        """Test mixed case title."""
        self.assertEqual(generate_slug('My AWESOME Post Title'), 'my-awesome-post-title')

    def test_special_characters(self):
        """Test removal of special characters."""
        self.assertEqual(generate_slug("What's New in 2024?"), 'whats-new-in-2024')
        self.assertEqual(generate_slug("Hello, World! @Test"), 'hello-world-test')

    def test_underscores_converted(self):
        """Test that underscores are converted to hyphens."""
        self.assertEqual(generate_slug('my_post_title'), 'my-post-title')

    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces."""
        self.assertEqual(generate_slug('Hello   World'), 'hello-world')

    def test_leading_trailing_spaces(self):
        """Test stripping of leading and trailing spaces."""
        self.assertEqual(generate_slug('  Hello World  '), 'hello-world')

    def test_unicode_characters(self):
        """Test unicode normalization (accented chars to ASCII)."""
        self.assertEqual(generate_slug('Café Résumé'), 'cafe-resume')
        self.assertEqual(generate_slug('naïve coöperate'), 'naive-cooperate')

    def test_unicode_non_latin_removed(self):
        """Test that non-Latin unicode characters are removed."""
        self.assertEqual(generate_slug('Hello 日本語 World'), 'hello-world')
        self.assertEqual(generate_slug('Post 中文标题'), 'post')

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        self.assertEqual(generate_slug('Top 10 Tips for 2024'), 'top-10-tips-for-2024')

    def test_hyphens_preserved(self):
        """Test that existing hyphens are preserved."""
        self.assertEqual(generate_slug('pre-existing-slug'), 'pre-existing-slug')

    def test_multiple_hyphens_collapsed(self):
        """Test that multiple consecutive hyphens are collapsed."""
        self.assertEqual(generate_slug('Hello -- World --- Test'), 'hello-world-test')

    def test_empty_string(self):
        """Test empty string returns 'untitled'."""
        self.assertEqual(generate_slug(''), 'untitled')

    def test_only_special_chars(self):
        """Test string with only special characters returns 'untitled'."""
        self.assertEqual(generate_slug('!@#$%^&*()'), 'untitled')

    def test_with_date_prefix(self):
        """Test slug generation with date prefix."""
        self.assertEqual(
            generate_slug('My Post', date_str='2024-01-15'),
            '2024-01-15-my-post'
        )

    def test_with_date_prefix_empty_title(self):
        """Test slug with date prefix and empty title."""
        self.assertEqual(
            generate_slug('', date_str='2024-01-15'),
            '2024-01-15-untitled'
        )

    def test_no_date_prefix(self):
        """Test that no date prefix when not provided."""
        slug = generate_slug('My Post')
        self.assertNotIn('2024', slug)
        self.assertEqual(slug, 'my-post')


class TestExtractTitleFromBody(unittest.TestCase):
    """Tests for extract_title_from_body function."""

    def test_simple_h1(self):
        """Test extracting simple H1 heading."""
        body = "# Hello World\n\nThis is content."
        self.assertEqual(extract_title_from_body(body), 'Hello World')

    def test_h1_with_leading_whitespace(self):
        """Test extracting H1 with leading whitespace in body."""
        body = "\n\n# My Title\n\nContent here."
        self.assertEqual(extract_title_from_body(body), 'My Title')

    def test_h1_among_other_content(self):
        """Test finding H1 among other content."""
        body = """Some intro text.

# The Real Title

More content here.
"""
        self.assertEqual(extract_title_from_body(body), 'The Real Title')

    def test_only_h2_headings(self):
        """Test that H2 headings are not matched."""
        body = "## This is H2\n\n### This is H3"
        self.assertIsNone(extract_title_from_body(body))

    def test_multiple_h1_returns_first(self):
        """Test that only the first H1 is returned."""
        body = """# First Title

Some content.

# Second Title

More content.
"""
        self.assertEqual(extract_title_from_body(body), 'First Title')

    def test_h1_with_special_characters(self):
        """Test H1 with special characters."""
        body = "# What's New in 2024? A Complete Guide!"
        self.assertEqual(extract_title_from_body(body), "What's New in 2024? A Complete Guide!")

    def test_h1_with_markdown_formatting(self):
        """Test H1 with inline markdown formatting."""
        body = "# **Bold** and *Italic* Title"
        self.assertEqual(extract_title_from_body(body), '**Bold** and *Italic* Title')

    def test_empty_body(self):
        """Test empty body returns None."""
        self.assertIsNone(extract_title_from_body(''))

    def test_none_body(self):
        """Test None body returns None."""
        self.assertIsNone(extract_title_from_body(None))

    def test_no_headings(self):
        """Test body with no headings returns None."""
        body = "Just some regular text without any headings."
        self.assertIsNone(extract_title_from_body(body))

    def test_h1_without_space(self):
        """Test that H1 without space after # is not matched."""
        body = "#NoSpaceTitle\n\n# Valid Title"
        self.assertEqual(extract_title_from_body(body), 'Valid Title')

    def test_h1_with_trailing_whitespace(self):
        """Test that trailing whitespace in H1 is stripped."""
        body = "# Title with trailing space   \n\nContent."
        self.assertEqual(extract_title_from_body(body), 'Title with trailing space')


class TestNormalizeDate(unittest.TestCase):
    """Tests for _normalize_date function."""

    def test_datetime_object(self):
        """Test normalizing datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        self.assertEqual(_normalize_date(dt), '2024-01-15')

    def test_date_object(self):
        """Test normalizing date object."""
        d = date(2024, 1, 15)
        self.assertEqual(_normalize_date(d), '2024-01-15')

    def test_iso_date_string(self):
        """Test normalizing ISO date string."""
        self.assertEqual(_normalize_date('2024-01-15'), '2024-01-15')

    def test_slash_date_string(self):
        """Test normalizing slash-separated date string."""
        self.assertEqual(_normalize_date('2024/01/15'), '2024-01-15')

    def test_datetime_string(self):
        """Test normalizing datetime string."""
        self.assertEqual(_normalize_date('2024-01-15T10:30:00'), '2024-01-15')
        self.assertEqual(_normalize_date('2024-01-15 10:30:00'), '2024-01-15')

    def test_human_readable_dates(self):
        """Test normalizing human-readable date formats."""
        self.assertEqual(_normalize_date('January 15, 2024'), '2024-01-15')
        self.assertEqual(_normalize_date('Jan 15, 2024'), '2024-01-15')
        self.assertEqual(_normalize_date('15 January 2024'), '2024-01-15')
        self.assertEqual(_normalize_date('15 Jan 2024'), '2024-01-15')

    def test_none_value(self):
        """Test that None returns today's date."""
        result = _normalize_date(None)
        self.assertEqual(result, datetime.now().strftime('%Y-%m-%d'))

    def test_empty_string(self):
        """Test that empty string returns today's date."""
        result = _normalize_date('')
        self.assertEqual(result, datetime.now().strftime('%Y-%m-%d'))

    def test_quoted_string(self):
        """Test that quoted strings are unquoted."""
        self.assertEqual(_normalize_date('"2024-01-15"'), '2024-01-15')
        self.assertEqual(_normalize_date("'2024-01-15'"), '2024-01-15')

    def test_post_content_type_preserves_timezone(self):
        """Test that post content type preserves timezone info in strings."""
        result = _normalize_date('2024-01-15T10:30:00-05:00', content_type='post')
        self.assertEqual(result, '2024-01-15T10:30:00-05:00')

        result = _normalize_date('2024-01-15T10:30:00Z', content_type='post')
        self.assertEqual(result, '2024-01-15T10:30:00Z')

    def test_post_content_type_datetime_with_tz(self):
        """Test that post content type preserves timezone in datetime objects."""
        tz = timezone(timedelta(hours=-5))
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=tz)
        result = _normalize_date(dt, content_type='post')
        self.assertIn('2024-01-15', result)
        self.assertIn('-05:00', result)

    def test_non_post_iso_datetime_passthrough(self):
        """Test that non-post content types pass through unrecognized ISO formats.

        Note: ISO 8601 datetime strings with timezone (like 2024-01-15T10:30:00-05:00)
        don't match the current parsing formats, so they pass through unchanged.
        This differs from the post content type which explicitly preserves them.
        """
        result = _normalize_date('2024-01-15T10:30:00-05:00', content_type='project')
        # Currently passes through unchanged (format not in parsing list)
        self.assertEqual(result, '2024-01-15T10:30:00-05:00')

    def test_unrecognized_format_passthrough(self):
        """Test that unrecognized formats pass through unchanged."""
        result = _normalize_date('custom-date-format')
        self.assertEqual(result, 'custom-date-format')

    def test_non_string_non_date_returns_today(self):
        """Test that unexpected types return today's date."""
        result = _normalize_date(12345)
        self.assertEqual(result, datetime.now().strftime('%Y-%m-%d'))


class TestNormalizeDraft(unittest.TestCase):
    """Tests for _normalize_draft function."""

    def test_boolean_true(self):
        """Test that boolean True returns True."""
        self.assertIs(_normalize_draft(True), True)

    def test_boolean_false(self):
        """Test that boolean False returns False."""
        self.assertIs(_normalize_draft(False), False)

    def test_none_value(self):
        """Test that None returns False."""
        self.assertIs(_normalize_draft(None), False)

    def test_string_true(self):
        """Test that string 'true' returns True."""
        self.assertIs(_normalize_draft('true'), True)
        self.assertIs(_normalize_draft('TRUE'), True)
        self.assertIs(_normalize_draft('True'), True)

    def test_string_yes(self):
        """Test that string 'yes' returns True."""
        self.assertIs(_normalize_draft('yes'), True)
        self.assertIs(_normalize_draft('YES'), True)

    def test_string_one(self):
        """Test that string '1' returns True."""
        self.assertIs(_normalize_draft('1'), True)

    def test_string_false(self):
        """Test that string 'false' returns False."""
        self.assertIs(_normalize_draft('false'), False)
        self.assertIs(_normalize_draft('FALSE'), False)

    def test_string_no(self):
        """Test that string 'no' returns False."""
        self.assertIs(_normalize_draft('no'), False)

    def test_integer_truthy(self):
        """Test that truthy integers return True."""
        self.assertIs(_normalize_draft(1), True)
        self.assertIs(_normalize_draft(42), True)

    def test_integer_zero(self):
        """Test that zero returns False."""
        self.assertIs(_normalize_draft(0), False)


class TestNormalizeTags(unittest.TestCase):
    """Tests for _normalize_tags function."""

    def test_list_of_strings(self):
        """Test normalizing a list of strings."""
        result = _normalize_tags(['python', 'testing', 'automation'])
        self.assertEqual(result, ['python', 'testing', 'automation'])

    def test_list_with_whitespace(self):
        """Test that whitespace is stripped from tag values."""
        result = _normalize_tags(['  python  ', 'testing', '  automation'])
        self.assertEqual(result, ['python', 'testing', 'automation'])

    def test_list_with_empty_strings(self):
        """Test that empty strings are filtered out."""
        result = _normalize_tags(['python', '', 'testing', ''])
        self.assertEqual(result, ['python', 'testing'])

    def test_list_with_mixed_types(self):
        """Test that non-string items are converted."""
        result = _normalize_tags(['python', 123, True])
        self.assertEqual(result, ['python', '123', 'True'])

    def test_single_tag_string(self):
        """Test single tag as string."""
        result = _normalize_tags('python')
        self.assertEqual(result, ['python'])

    def test_comma_separated_string(self):
        """Test comma-separated tags string."""
        result = _normalize_tags('python, testing, automation')
        self.assertEqual(result, ['python', 'testing', 'automation'])

    def test_comma_separated_with_empty(self):
        """Test comma-separated with empty segments."""
        result = _normalize_tags('python,,testing,')
        self.assertEqual(result, ['python', 'testing'])

    def test_none_value(self):
        """Test that None returns empty list."""
        self.assertEqual(_normalize_tags(None), [])

    def test_empty_string(self):
        """Test that empty string returns empty list."""
        self.assertEqual(_normalize_tags(''), [])

    def test_empty_list(self):
        """Test that empty list returns empty list."""
        self.assertEqual(_normalize_tags([]), [])


class TestTransformToHugo(unittest.TestCase):
    """Tests for transform_to_hugo function."""

    def test_minimal_frontmatter(self):
        """Test transformation with minimal frontmatter."""
        result = transform_to_hugo({})

        self.assertEqual(result['title'], '')
        self.assertIn('date', result)
        self.assertIs(result['draft'], False)
        self.assertEqual(result['tags'], [])

    def test_title_from_frontmatter(self):
        """Test that title is taken from frontmatter."""
        result = transform_to_hugo({'title': 'My Post Title'})
        self.assertEqual(result['title'], 'My Post Title')

    def test_title_from_body_h1(self):
        """Test that title is extracted from body H1 when not in frontmatter."""
        body = "# Title From H1\n\nContent here."
        result = transform_to_hugo({}, body=body)
        self.assertEqual(result['title'], 'Title From H1')

    def test_frontmatter_title_takes_precedence(self):
        """Test that frontmatter title takes precedence over body H1."""
        body = "# Body Title\n\nContent."
        result = transform_to_hugo({'title': 'Frontmatter Title'}, body=body)
        self.assertEqual(result['title'], 'Frontmatter Title')

    def test_date_normalized(self):
        """Test that date is normalized."""
        result = transform_to_hugo({'date': 'January 15, 2024'})
        self.assertEqual(result['date'], '2024-01-15')

    def test_draft_normalized(self):
        """Test that draft is normalized to boolean."""
        result = transform_to_hugo({'draft': 'true'})
        self.assertIs(result['draft'], True)

    def test_tags_normalized(self):
        """Test that tags are normalized to list."""
        result = transform_to_hugo({'tags': 'python, testing'})
        self.assertEqual(result['tags'], ['python', 'testing'])

    def test_publish_field_removed(self):
        """Test that publish field is NOT included in output."""
        result = transform_to_hugo({'publish': True, 'title': 'Test'})
        self.assertNotIn('publish', result)

    def test_content_type_included(self):
        """Test that valid content_type is included."""
        result = transform_to_hugo({'content_type': 'post'})
        self.assertEqual(result['content_type'], 'post')

    def test_invalid_content_type_excluded(self):
        """Test that invalid content_type is excluded."""
        result = transform_to_hugo({'content_type': 'invalid'})
        self.assertNotIn('content_type', result)

    def test_content_type_parameter_overrides(self):
        """Test that content_type parameter overrides frontmatter."""
        result = transform_to_hugo(
            {'content_type': 'post'},
            content_type='project'
        )
        self.assertEqual(result['content_type'], 'project')

    def test_optional_fields_included(self):
        """Test that optional fields are included when present."""
        frontmatter = {
            'title': 'Test',
            'author': 'John Doe',
            'description': 'A test post',
            'categories': ['tech', 'python'],
        }
        result = transform_to_hugo(frontmatter)

        self.assertEqual(result['author'], 'John Doe')
        self.assertEqual(result['description'], 'A test post')
        self.assertEqual(result['categories'], ['tech', 'python'])

    def test_content_type_specific_fields(self):
        """Test that content-type-specific fields are included."""
        frontmatter = {
            'title': 'Test',
            'content_type': 'photography',
            'location': 'Paris, France',
        }
        result = transform_to_hugo(frontmatter)

        self.assertEqual(result['location'], 'Paris, France')

    def test_post_date_format(self):
        """Test that post content type preserves timezone in date."""
        frontmatter = {
            'title': 'Test',
            'date': '2024-01-15T10:30:00-05:00',
            'content_type': 'post',
        }
        result = transform_to_hugo(frontmatter)

        self.assertEqual(result['date'], '2024-01-15T10:30:00-05:00')

    def test_project_date_format(self):
        """Test date handling for project content type.

        Note: ISO 8601 datetime strings with timezone pass through unchanged
        since they don't match the current parsing formats. For simple dates,
        the format is preserved as-is.
        """
        # Simple date format works correctly
        frontmatter_simple = {
            'title': 'Test',
            'date': '2024-01-15',
            'content_type': 'project',
        }
        result_simple = transform_to_hugo(frontmatter_simple)
        self.assertEqual(result_simple['date'], '2024-01-15')

        # ISO datetime with timezone passes through unchanged (format not parsed)
        frontmatter_tz = {
            'title': 'Test',
            'date': '2024-01-15T10:30:00-05:00',
            'content_type': 'project',
        }
        result_tz = transform_to_hugo(frontmatter_tz)
        self.assertEqual(result_tz['date'], '2024-01-15T10:30:00-05:00')


class TestIntegration(unittest.TestCase):
    """Integration tests for frontmatter transformation workflows."""

    def test_full_post_transformation(self):
        """Test complete transformation of a blog post."""
        frontmatter = {
            'title': 'My Amazing Blog Post',
            'date': '2024-01-15',
            'draft': False,
            'publish': True,
            'tags': ['python', 'hugo', 'automation'],
            'content_type': 'post',
            'author': 'John Doe',
            'description': 'A great post about automation',
            'categories': ['tutorials'],
        }

        result = transform_to_hugo(frontmatter)

        self.assertEqual(result['title'], 'My Amazing Blog Post')
        self.assertEqual(result['date'], '2024-01-15')
        self.assertIs(result['draft'], False)
        self.assertEqual(result['tags'], ['python', 'hugo', 'automation'])
        self.assertEqual(result['content_type'], 'post')
        self.assertEqual(result['author'], 'John Doe')
        self.assertEqual(result['description'], 'A great post about automation')
        self.assertEqual(result['categories'], ['tutorials'])
        self.assertNotIn('publish', result)

    def test_slug_with_transformed_date(self):
        """Test generating slug using date from transformed frontmatter."""
        frontmatter = {
            'title': 'My Blog Post',
            'date': 'January 15, 2024',
        }

        result = transform_to_hugo(frontmatter)
        slug = generate_slug(result['title'], date_str=result['date'])

        self.assertEqual(slug, '2024-01-15-my-blog-post')

    def test_photography_content_workflow(self):
        """Test complete workflow for photography content type."""
        frontmatter = {
            'title': 'Paris Photos',
            'date': '2024-03-20',
            'publish': True,
            'content_type': 'photography',
            'location': 'Paris, France',
            'description': 'Beautiful photos from my trip to Paris',
            'tags': ['travel', 'paris', 'photography'],
        }

        result = transform_to_hugo(frontmatter)

        self.assertEqual(result['content_type'], 'photography')
        self.assertEqual(result['location'], 'Paris, France')
        self.assertNotIn('publish', result)

    def test_title_fallback_chain(self):
        """Test title extraction fallback: frontmatter -> body H1 -> empty."""
        # With frontmatter title
        result1 = transform_to_hugo({'title': 'FM Title'}, body='# Body Title')
        self.assertEqual(result1['title'], 'FM Title')

        # Without frontmatter title, with body H1
        result2 = transform_to_hugo({}, body='# Body Title')
        self.assertEqual(result2['title'], 'Body Title')

        # Without frontmatter title, without body H1
        result3 = transform_to_hugo({}, body='No heading here')
        self.assertEqual(result3['title'], '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
