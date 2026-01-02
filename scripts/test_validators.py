#!/usr/bin/env python3
"""
Tests for the validators module.

Uses unittest (standard library) for compatibility.
"""

import os
import tempfile
import unittest
from pathlib import Path
from validators import (
    validate_frontmatter,
    validate_media_references,
    ValidationIssue,
    ValidationSeverity,
    REQUIRED_FIELDS,
    is_valid,
    has_warnings,
    format_issues,
)


class TestValidateFrontmatter(unittest.TestCase):
    """Tests for the validate_frontmatter function."""

    def test_valid_complete_frontmatter(self):
        """Test that complete valid frontmatter returns no issues."""
        frontmatter = {
            'title': 'My Blog Post',
            'date': '2024-01-15',
            'tags': ['python', 'hugo']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_valid_minimal_frontmatter(self):
        """Test minimal valid frontmatter with required fields only."""
        frontmatter = {
            'title': 'Test',
            'date': '2024-01-15',
            'tags': []
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_missing_title_is_error(self):
        """Test that missing title field returns an error."""
        frontmatter = {
            'date': '2024-01-15',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'title')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('missing', issues[0].message.lower())

    def test_missing_date_is_error(self):
        """Test that missing date field returns an error."""
        frontmatter = {
            'title': 'My Post',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'date')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('missing', issues[0].message.lower())

    def test_missing_tags_is_error(self):
        """Test that missing tags field returns an error."""
        frontmatter = {
            'title': 'My Post',
            'date': '2024-01-15'
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'tags')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('missing', issues[0].message.lower())

    def test_empty_frontmatter_returns_three_errors(self):
        """Test that empty frontmatter returns errors for all required fields."""
        issues = validate_frontmatter({})
        self.assertEqual(len(issues), 3)
        fields = {issue.field for issue in issues}
        self.assertEqual(fields, {'title', 'date', 'tags'})
        for issue in issues:
            self.assertEqual(issue.severity, ValidationSeverity.ERROR)

    def test_null_title_is_error(self):
        """Test that null title field returns an error."""
        frontmatter = {
            'title': None,
            'date': '2024-01-15',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'title')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('null', issues[0].message.lower())

    def test_null_date_is_error(self):
        """Test that null date field returns an error."""
        frontmatter = {
            'title': 'My Post',
            'date': None,
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'date')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('null', issues[0].message.lower())

    def test_empty_title_is_warning(self):
        """Test that empty title string returns a warning."""
        frontmatter = {
            'title': '',
            'date': '2024-01-15',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'title')
        self.assertEqual(issues[0].severity, ValidationSeverity.WARNING)
        self.assertIn('empty', issues[0].message.lower())

    def test_whitespace_only_title_is_warning(self):
        """Test that whitespace-only title returns a warning."""
        frontmatter = {
            'title': '   ',
            'date': '2024-01-15',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'title')
        self.assertEqual(issues[0].severity, ValidationSeverity.WARNING)

    def test_empty_date_is_warning(self):
        """Test that empty date string returns a warning."""
        frontmatter = {
            'title': 'My Post',
            'date': '',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'date')
        self.assertEqual(issues[0].severity, ValidationSeverity.WARNING)

    def test_non_string_title_is_warning(self):
        """Test that non-string title returns a warning."""
        frontmatter = {
            'title': 123,
            'date': '2024-01-15',
            'tags': ['python']
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'title')
        self.assertEqual(issues[0].severity, ValidationSeverity.WARNING)
        self.assertIn('string', issues[0].message.lower())

    def test_non_list_tags_is_warning(self):
        """Test that non-list/non-string tags returns a warning."""
        frontmatter = {
            'title': 'My Post',
            'date': '2024-01-15',
            'tags': 123
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'tags')
        self.assertEqual(issues[0].severity, ValidationSeverity.WARNING)

    def test_string_tags_is_valid(self):
        """Test that string tags (comma-separated) is valid."""
        frontmatter = {
            'title': 'My Post',
            'date': '2024-01-15',
            'tags': 'python, hugo'
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_null_tags_is_valid(self):
        """Test that null tags is valid (will be normalized to empty list)."""
        frontmatter = {
            'title': 'My Post',
            'date': '2024-01-15',
            'tags': None
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_extra_fields_ignored(self):
        """Test that extra fields don't cause issues."""
        frontmatter = {
            'title': 'My Post',
            'date': '2024-01-15',
            'tags': ['python'],
            'publish': True,
            'author': 'Adam',
            'custom_field': 'value'
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)


class TestValidationIssue(unittest.TestCase):
    """Tests for the ValidationIssue dataclass."""

    def test_issue_str_format_error(self):
        """Test string formatting of an error issue."""
        issue = ValidationIssue(
            field='title',
            message='Required field is missing',
            severity=ValidationSeverity.ERROR
        )
        result = str(issue)
        self.assertEqual(result, '[ERROR] title: Required field is missing')

    def test_issue_str_format_warning(self):
        """Test string formatting of a warning issue."""
        issue = ValidationIssue(
            field='date',
            message='Date format is unusual',
            severity=ValidationSeverity.WARNING
        )
        result = str(issue)
        self.assertEqual(result, '[WARNING] date: Date format is unusual')

    def test_issue_equality(self):
        """Test that identical issues are equal."""
        issue1 = ValidationIssue('title', 'Missing', ValidationSeverity.ERROR)
        issue2 = ValidationIssue('title', 'Missing', ValidationSeverity.ERROR)
        self.assertEqual(issue1, issue2)

    def test_issue_inequality(self):
        """Test that different issues are not equal."""
        issue1 = ValidationIssue('title', 'Missing', ValidationSeverity.ERROR)
        issue2 = ValidationIssue('date', 'Missing', ValidationSeverity.ERROR)
        self.assertNotEqual(issue1, issue2)


class TestValidationSeverity(unittest.TestCase):
    """Tests for the ValidationSeverity enum."""

    def test_error_value(self):
        """Test that ERROR has the correct value."""
        self.assertEqual(ValidationSeverity.ERROR.value, 'error')

    def test_warning_value(self):
        """Test that WARNING has the correct value."""
        self.assertEqual(ValidationSeverity.WARNING.value, 'warning')


class TestRequiredFieldsConstant(unittest.TestCase):
    """Tests for the REQUIRED_FIELDS constant."""

    def test_contains_title(self):
        """Test that REQUIRED_FIELDS contains 'title'."""
        self.assertIn('title', REQUIRED_FIELDS)

    def test_contains_date(self):
        """Test that REQUIRED_FIELDS contains 'date'."""
        self.assertIn('date', REQUIRED_FIELDS)

    def test_contains_tags(self):
        """Test that REQUIRED_FIELDS contains 'tags'."""
        self.assertIn('tags', REQUIRED_FIELDS)

    def test_has_three_fields(self):
        """Test that REQUIRED_FIELDS has exactly three fields."""
        self.assertEqual(len(REQUIRED_FIELDS), 3)


class TestIsValid(unittest.TestCase):
    """Tests for the is_valid helper function."""

    def test_empty_list_is_valid(self):
        """Test that empty issues list is valid."""
        self.assertTrue(is_valid([]))

    def test_only_warnings_is_valid(self):
        """Test that only warnings is still valid."""
        issues = [
            ValidationIssue('title', 'Empty', ValidationSeverity.WARNING),
            ValidationIssue('date', 'Unusual format', ValidationSeverity.WARNING),
        ]
        self.assertTrue(is_valid(issues))

    def test_errors_is_not_valid(self):
        """Test that errors make it not valid."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
        ]
        self.assertFalse(is_valid(issues))

    def test_mixed_errors_and_warnings_is_not_valid(self):
        """Test that mixed errors and warnings is not valid."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
            ValidationIssue('date', 'Unusual format', ValidationSeverity.WARNING),
        ]
        self.assertFalse(is_valid(issues))


class TestHasWarnings(unittest.TestCase):
    """Tests for the has_warnings helper function."""

    def test_empty_list_has_no_warnings(self):
        """Test that empty issues list has no warnings."""
        self.assertFalse(has_warnings([]))

    def test_only_errors_has_no_warnings(self):
        """Test that only errors has no warnings."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
        ]
        self.assertFalse(has_warnings(issues))

    def test_warnings_returns_true(self):
        """Test that warnings returns True."""
        issues = [
            ValidationIssue('title', 'Empty', ValidationSeverity.WARNING),
        ]
        self.assertTrue(has_warnings(issues))

    def test_mixed_has_warnings(self):
        """Test that mixed errors and warnings has warnings."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
            ValidationIssue('date', 'Unusual', ValidationSeverity.WARNING),
        ]
        self.assertTrue(has_warnings(issues))


class TestFormatIssues(unittest.TestCase):
    """Tests for the format_issues function."""

    def test_empty_issues(self):
        """Test formatting empty issues list."""
        result = format_issues([])
        self.assertEqual(result, "No validation issues found.")

    def test_single_error(self):
        """Test formatting a single error."""
        issues = [
            ValidationIssue('title', 'Required field is missing', ValidationSeverity.ERROR),
        ]
        result = format_issues(issues)
        self.assertIn('Errors (1):', result)
        self.assertIn('title: Required field is missing', result)

    def test_single_warning(self):
        """Test formatting a single warning."""
        issues = [
            ValidationIssue('date', 'Unusual format', ValidationSeverity.WARNING),
        ]
        result = format_issues(issues)
        self.assertIn('Warnings (1):', result)
        self.assertIn('date: Unusual format', result)

    def test_mixed_errors_and_warnings(self):
        """Test formatting mixed errors and warnings."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
            ValidationIssue('date', 'Unusual', ValidationSeverity.WARNING),
        ]
        result = format_issues(issues)
        self.assertIn('Errors (1):', result)
        self.assertIn('Warnings (1):', result)
        # Errors should come before warnings
        error_pos = result.index('Errors')
        warning_pos = result.index('Warnings')
        self.assertLess(error_pos, warning_pos)

    def test_multiple_errors(self):
        """Test formatting multiple errors."""
        issues = [
            ValidationIssue('title', 'Missing', ValidationSeverity.ERROR),
            ValidationIssue('date', 'Missing', ValidationSeverity.ERROR),
            ValidationIssue('tags', 'Missing', ValidationSeverity.ERROR),
        ]
        result = format_issues(issues)
        self.assertIn('Errors (3):', result)


class TestValidateFrontmatterIntegration(unittest.TestCase):
    """Integration tests simulating real-world Obsidian frontmatter."""

    def test_typical_obsidian_note(self):
        """Test validation of typical Obsidian note frontmatter."""
        frontmatter = {
            'title': 'My Blog Post',
            'date': '2024-01-15',
            'publish': True,
            'tags': ['python', 'automation'],
            'draft': False
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_project_frontmatter(self):
        """Test validation of project frontmatter."""
        frontmatter = {
            'title': 'Slab Computer Desk',
            'date': '2020-06-15',
            'tags': ['DIY', 'furniture', 'woodwork'],
            'content_type': 'project',
            'description': 'Black walnut desk with hairpin legs'
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_photography_frontmatter(self):
        """Test validation of photography frontmatter."""
        frontmatter = {
            'title': 'Nova Scotia Trip',
            'date': '2023-08-20',
            'tags': ['travel', 'photography'],
            'content_type': 'photography',
            'location': 'Nova Scotia, Canada'
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_minimal_publishable_note(self):
        """Test validation of minimal but publishable note."""
        frontmatter = {
            'title': 'Quick Note',
            'date': '2024-01-15',
            'tags': [],
            'publish': True
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)

    def test_note_missing_only_publish_flag(self):
        """Test that missing publish flag doesn't cause validation issues."""
        frontmatter = {
            'title': 'Draft Note',
            'date': '2024-01-15',
            'tags': ['draft']
            # No publish field - that's fine for validation
        }
        issues = validate_frontmatter(frontmatter)
        self.assertEqual(len(issues), 0)


class TestValidateMediaReferences(unittest.TestCase):
    """Tests for the validate_media_references function."""

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.media_base = Path(self.temp_dir)

        # Create some test media files
        # images/test.jpg
        images_dir = self.media_base / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        (images_dir / "test.jpg").touch()
        (images_dir / "photo.png").touch()

        # 2021/06/vacation.jpg
        dated_dir = self.media_base / "2021" / "06"
        dated_dir.mkdir(parents=True, exist_ok=True)
        (dated_dir / "vacation.jpg").touch()

        # videos/demo.mp4
        videos_dir = self.media_base / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        (videos_dir / "demo.mp4").touch()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_no_media_references_returns_empty(self):
        """Test that content with no media references returns no issues."""
        content = "This is just plain text with no images."
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_valid_single_reference(self):
        """Test that a valid media reference returns no issues."""
        content = "Here's an image: ![[images/test.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_valid_multiple_references(self):
        """Test that multiple valid media references return no issues."""
        content = """
        First image: ![[images/test.jpg]]
        Second image: ![[images/photo.png]]
        Video: ![[videos/demo.mp4]]
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_valid_nested_path_reference(self):
        """Test that a valid nested path reference returns no issues."""
        content = "Vacation photo: ![[2021/06/vacation.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_missing_file_returns_error(self):
        """Test that a missing file reference returns an error."""
        content = "Missing image: ![[images/nonexistent.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, 'media')
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertIn('nonexistent.jpg', issues[0].message)
        self.assertIn('not found', issues[0].message.lower())

    def test_missing_multiple_files_returns_multiple_errors(self):
        """Test that multiple missing files return multiple errors."""
        content = """
        ![[missing1.jpg]]
        ![[also/missing.png]]
        ![[nope.gif]]
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 3)
        for issue in issues:
            self.assertEqual(issue.field, 'media')
            self.assertEqual(issue.severity, ValidationSeverity.ERROR)

    def test_mixed_valid_and_invalid_references(self):
        """Test content with both valid and invalid media references."""
        content = """
        Valid: ![[images/test.jpg]]
        Invalid: ![[images/missing.jpg]]
        Valid: ![[videos/demo.mp4]]
        Invalid: ![[nonexistent.png]]
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 2)
        # Check that both missing files are reported
        messages = [issue.message for issue in issues]
        self.assertTrue(any('missing.jpg' in msg for msg in messages))
        self.assertTrue(any('nonexistent.png' in msg for msg in messages))

    def test_error_message_includes_reference_path(self):
        """Test that the error message includes the original reference path."""
        content = "![[some/deep/path/image.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 1)
        self.assertIn('some/deep/path/image.jpg', issues[0].message)

    def test_error_message_includes_expected_path(self):
        """Test that the error message includes the expected filesystem path."""
        content = "![[images/missing.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 1)
        self.assertIn('expected at:', issues[0].message.lower())

    def test_non_media_wikilinks_ignored(self):
        """Test that non-media wikilinks (text links) are ignored."""
        content = """
        This is a [[link to another note]].
        This is [[Another Note|with alias]].
        Regular text without embeds.
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_empty_content_returns_empty(self):
        """Test that empty content returns no issues."""
        issues = validate_media_references("", self.media_base)
        self.assertEqual(len(issues), 0)

    def test_whitespace_only_content_returns_empty(self):
        """Test that whitespace-only content returns no issues."""
        issues = validate_media_references("   \n\t\n  ", self.media_base)
        self.assertEqual(len(issues), 0)

    def test_leading_slash_in_reference_handled(self):
        """Test that leading slashes in references are normalized."""
        # Create a file that should match /images/test.jpg
        content = "![[/images/test.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_is_valid_helper_with_media_issues(self):
        """Test that is_valid works correctly with media validation issues."""
        content = "![[missing.jpg]]"
        issues = validate_media_references(content, self.media_base)
        self.assertFalse(is_valid(issues))

    def test_format_issues_with_media_errors(self):
        """Test that format_issues works correctly with media validation errors."""
        content = "![[missing1.jpg]]\n![[missing2.png]]"
        issues = validate_media_references(content, self.media_base)
        formatted = format_issues(issues)
        self.assertIn('Errors (2):', formatted)
        self.assertIn('missing1.jpg', formatted)
        self.assertIn('missing2.png', formatted)

    def test_duplicate_references_checked_separately(self):
        """Test that duplicate media references are each validated."""
        content = """
        ![[missing.jpg]]
        ![[missing.jpg]]
        """
        issues = validate_media_references(content, self.media_base)
        # Both references are checked, resulting in 2 issues
        self.assertEqual(len(issues), 2)


class TestValidateMediaReferencesVideoAudio(unittest.TestCase):
    """Tests for validate_media_references with video and audio files."""

    def setUp(self):
        """Create a temporary directory with video and audio files."""
        self.temp_dir = tempfile.mkdtemp()
        self.media_base = Path(self.temp_dir)

        # Create video files
        videos_dir = self.media_base / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)
        (videos_dir / "presentation.mp4").touch()
        (videos_dir / "clip.webm").touch()

        # Create audio files
        audio_dir = self.media_base / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        (audio_dir / "podcast.mp3").touch()
        (audio_dir / "song.wav").touch()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_video_references(self):
        """Test that valid video references return no issues."""
        content = """
        ![[videos/presentation.mp4]]
        ![[videos/clip.webm]]
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_valid_audio_references(self):
        """Test that valid audio references return no issues."""
        content = """
        ![[audio/podcast.mp3]]
        ![[audio/song.wav]]
        """
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 0)

    def test_missing_video_returns_error(self):
        """Test that missing video file returns an error."""
        content = "![[videos/missing.mp4]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 1)
        self.assertIn('missing.mp4', issues[0].message)

    def test_missing_audio_returns_error(self):
        """Test that missing audio file returns an error."""
        content = "![[audio/missing.mp3]]"
        issues = validate_media_references(content, self.media_base)
        self.assertEqual(len(issues), 1)
        self.assertIn('missing.mp3', issues[0].message)


if __name__ == '__main__':
    unittest.main()
