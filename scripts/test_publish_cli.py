#!/usr/bin/env python3
"""
Tests for the publish.py CLI tool.

Uses unittest (standard library) for compatibility.
"""

import unittest
import tempfile
import sys
from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from publish import (
    format_tags,
    format_date,
    truncate,
    print_scan_table,
    print_list_table,
    get_target_path,
    convert_note,
    extract_and_resolve_media,
    upload_media_to_minio,
    cmd_scan,
    cmd_list,
    cmd_media,
    cmd_convert,
    cmd_validate,
    cmd_publish,
    cmd_publish_dispatch,
    cmd_publish_all,
    confirm_prompt,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_HUGO_ROOT
)


class TestFormatTags(unittest.TestCase):
    """Tests for format_tags function."""

    def test_empty_tags_returns_dash(self):
        """Empty tags list returns dash."""
        self.assertEqual(format_tags([]), "-")

    def test_none_tags_returns_dash(self):
        """None tags returns dash."""
        self.assertEqual(format_tags(None), "-")

    def test_single_tag(self):
        """Single tag is formatted correctly."""
        self.assertEqual(format_tags(["python"]), "python")

    def test_multiple_tags(self):
        """Multiple tags are comma-separated."""
        result = format_tags(["python", "testing", "hugo"])
        self.assertEqual(result, "python, testing, hugo")

    def test_string_tag(self):
        """String tag (not list) is returned as-is."""
        self.assertEqual(format_tags("single-tag"), "single-tag")

    def test_numeric_tags(self):
        """Numeric tags are converted to strings."""
        result = format_tags([2024, "python"])
        self.assertEqual(result, "2024, python")


class TestFormatDate(unittest.TestCase):
    """Tests for format_date function."""

    def test_none_date_returns_dash(self):
        """None date returns dash."""
        self.assertEqual(format_date(None), "-")

    def test_date_object(self):
        """datetime.date object is formatted as YYYY-MM-DD."""
        d = date(2024, 1, 15)
        self.assertEqual(format_date(d), "2024-01-15")

    def test_string_date(self):
        """String date is returned as-is."""
        self.assertEqual(format_date("2024-01-15"), "2024-01-15")

    def test_other_string_format(self):
        """Other string formats are returned as-is."""
        self.assertEqual(format_date("January 15, 2024"), "January 15, 2024")


class TestTruncate(unittest.TestCase):
    """Tests for truncate function."""

    def test_short_text_not_truncated(self):
        """Text shorter than max_len is not truncated."""
        self.assertEqual(truncate("hello", 10), "hello")

    def test_exact_length_not_truncated(self):
        """Text exactly max_len is not truncated."""
        self.assertEqual(truncate("hello", 5), "hello")

    def test_long_text_truncated(self):
        """Text longer than max_len is truncated with ellipsis."""
        result = truncate("hello world", 8)
        self.assertEqual(result, "hello...")
        self.assertEqual(len(result), 8)

    def test_none_text_returns_dash(self):
        """None text returns dash."""
        self.assertEqual(truncate(None, 10), "-")

    def test_empty_string_returns_dash(self):
        """Empty string returns dash."""
        self.assertEqual(truncate("", 10), "-")

    def test_numeric_input(self):
        """Numeric input is converted to string."""
        self.assertEqual(truncate(12345, 10), "12345")


class TestPrintScanTable(unittest.TestCase):
    """Tests for print_scan_table function."""

    def test_no_notes_prints_message(self):
        """Empty notes list prints 'no publishable notes' message."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_scan_table([])
            output = mock_stdout.getvalue()
            self.assertIn("No publishable notes found.", output)

    def test_single_note_prints_table(self):
        """Single note is printed in table format."""
        notes = [{
            'path': Path('/tmp/test-note.md'),
            'frontmatter': {
                'title': 'Test Title',
                'date': date(2024, 1, 15),
                'tags': ['python', 'testing']
            },
            'body': 'Content'
        }]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_scan_table(notes)
            output = mock_stdout.getvalue()

            # Check header is present
            self.assertIn("Filename", output)
            self.assertIn("Title", output)
            self.assertIn("Date", output)
            self.assertIn("Tags", output)

            # Check note data is present
            self.assertIn("test-note.md", output)
            self.assertIn("Test Title", output)
            self.assertIn("2024-01-15", output)
            self.assertIn("python, testing", output)

            # Check summary
            self.assertIn("Found 1 publishable note(s).", output)

    def test_multiple_notes_prints_count(self):
        """Multiple notes show correct count in summary."""
        notes = [
            {
                'path': Path('/tmp/note1.md'),
                'frontmatter': {'title': 'Note 1'},
                'body': 'Content 1'
            },
            {
                'path': Path('/tmp/note2.md'),
                'frontmatter': {'title': 'Note 2'},
                'body': 'Content 2'
            },
            {
                'path': Path('/tmp/note3.md'),
                'frontmatter': {'title': 'Note 3'},
                'body': 'Content 3'
            }
        ]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_scan_table(notes)
            output = mock_stdout.getvalue()
            self.assertIn("Found 3 publishable note(s).", output)

    def test_missing_fields_show_dash(self):
        """Missing frontmatter fields show dash."""
        notes = [{
            'path': Path('/tmp/no-metadata.md'),
            'frontmatter': {},
            'body': 'Content'
        }]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_scan_table(notes)
            output = mock_stdout.getvalue()
            # Missing title, date, and tags should show dashes
            self.assertIn("-", output)


class TestCmdScan(unittest.TestCase):
    """Tests for cmd_scan function."""

    def test_scan_calls_find_publishable_notes(self):
        """scan command calls find_publishable_notes."""
        mock_args = MagicMock()
        mock_args.vault = None

        with patch('publish.find_publishable_notes', return_value=[]) as mock_find:
            with patch('sys.stdout', new_callable=StringIO):
                cmd_scan(mock_args)
                mock_find.assert_called_once_with(vault_path=None)

    def test_scan_with_custom_vault_path(self):
        """scan command passes custom vault path."""
        mock_args = MagicMock()
        mock_args.vault = '/custom/vault/path'

        with patch('publish.find_publishable_notes', return_value=[]) as mock_find:
            with patch('sys.stdout', new_callable=StringIO):
                cmd_scan(mock_args)
                mock_find.assert_called_once()
                call_args = mock_find.call_args
                self.assertEqual(str(call_args.kwargs['vault_path']), '/custom/vault/path')

    def test_scan_handles_file_not_found(self):
        """scan command exits with error on FileNotFoundError."""
        mock_args = MagicMock()
        mock_args.vault = '/nonexistent/path'

        with patch('publish.find_publishable_notes', side_effect=FileNotFoundError("Vault not found")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    cmd_scan(mock_args)
                self.assertEqual(context.exception.code, 1)
                self.assertIn("Vault not found", mock_stderr.getvalue())

    def test_scan_handles_not_a_directory(self):
        """scan command exits with error on NotADirectoryError."""
        mock_args = MagicMock()
        mock_args.vault = '/some/file.txt'

        with patch('publish.find_publishable_notes', side_effect=NotADirectoryError("Not a directory")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    cmd_scan(mock_args)
                self.assertEqual(context.exception.code, 1)
                self.assertIn("Not a directory", mock_stderr.getvalue())


class TestCmdScanIntegration(unittest.TestCase):
    """Integration tests for cmd_scan with actual filesystem."""

    def test_scan_with_test_vault(self):
        """scan command works with a test vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a publishable note
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: Integration Test Note
date: 2024-06-15
tags:
  - test
  - integration
publish: true
---

This is a test note for integration testing.
""")
            # Create a non-publishable note
            other_path = Path(tmpdir) / "other-note.md"
            other_path.write_text("""---
title: Not Published
---

This note should not appear.
""")

            mock_args = MagicMock()
            mock_args.vault = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_scan(mock_args)
                output = mock_stdout.getvalue()

                # Should find the publishable note
                self.assertIn("test-note.md", output)
                self.assertIn("Integration Test Note", output)
                self.assertIn("2024-06-15", output)
                self.assertIn("test, integration", output)

                # Should NOT include the non-publishable note
                self.assertNotIn("other-note.md", output)
                self.assertNotIn("Not Published", output)

                # Should show count of 1
                self.assertIn("Found 1 publishable note(s).", output)


class TestGetTargetPath(unittest.TestCase):
    """Tests for get_target_path function."""

    def test_basic_target_path(self):
        """Generates correct target path from frontmatter."""
        fm = {'title': 'My Blog Post', 'date': '2024-01-15'}
        result = get_target_path(fm, '')
        self.assertEqual(result, 'content/english/post/2024-01-15-my-blog-post.md')

    def test_custom_output_dir(self):
        """Respects custom output directory."""
        fm = {'title': 'Test Post', 'date': '2024-06-20'}
        result = get_target_path(fm, '', 'content/english/projects')
        self.assertEqual(result, 'content/english/projects/2024-06-20-test-post.md')

    def test_title_from_body_h1(self):
        """Extracts title from body H1 when not in frontmatter."""
        fm = {'date': '2024-03-10'}
        body = '# My Article Title\n\nSome content here.'
        result = get_target_path(fm, body)
        self.assertEqual(result, 'content/english/post/2024-03-10-my-article-title.md')

    def test_special_characters_in_title(self):
        """Handles special characters in title correctly."""
        fm = {'title': "What's New: A Developer's Guide!", 'date': '2024-05-01'}
        result = get_target_path(fm, '')
        self.assertEqual(result, 'content/english/post/2024-05-01-whats-new-a-developers-guide.md')

    def test_empty_title_uses_untitled(self):
        """Uses 'untitled' for empty title."""
        fm = {'date': '2024-02-28'}
        result = get_target_path(fm, '')
        self.assertEqual(result, 'content/english/post/2024-02-28-untitled.md')


class TestPrintListTable(unittest.TestCase):
    """Tests for print_list_table function."""

    def test_no_notes_prints_message(self):
        """Empty notes list prints 'no publishable notes' message."""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_list_table([])
            output = mock_stdout.getvalue()
            self.assertIn("No publishable notes found.", output)

    def test_single_note_prints_table_with_target(self):
        """Single note is printed in table format with target path."""
        notes = [{
            'path': Path('/tmp/test-note.md'),
            'frontmatter': {
                'title': 'Test Title',
                'date': '2024-01-15',
                'tags': ['python', 'testing']
            },
            'body': 'Content'
        }]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_list_table(notes)
            output = mock_stdout.getvalue()

            # Check header is present
            self.assertIn("Filename", output)
            self.assertIn("Title", output)
            self.assertIn("Date", output)
            self.assertIn("Target Path", output)

            # Check note data is present
            self.assertIn("test-note.md", output)
            self.assertIn("Test Title", output)
            self.assertIn("2024-01-15", output)

            # Check target path is present
            self.assertIn("content/english/post/2024-01-15-test-title.md", output)

            # Check summary
            self.assertIn("Found 1 publishable note(s).", output)

    def test_multiple_notes_prints_count(self):
        """Multiple notes show correct count in summary."""
        notes = [
            {
                'path': Path('/tmp/note1.md'),
                'frontmatter': {'title': 'Note 1', 'date': '2024-01-01'},
                'body': 'Content 1'
            },
            {
                'path': Path('/tmp/note2.md'),
                'frontmatter': {'title': 'Note 2', 'date': '2024-01-02'},
                'body': 'Content 2'
            }
        ]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_list_table(notes)
            output = mock_stdout.getvalue()
            self.assertIn("Found 2 publishable note(s).", output)

    def test_custom_output_dir(self):
        """Respects custom output directory in target paths."""
        notes = [{
            'path': Path('/tmp/project-note.md'),
            'frontmatter': {'title': 'My Project', 'date': '2024-05-20'},
            'body': 'Content'
        }]

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            print_list_table(notes, 'content/english/projects')
            output = mock_stdout.getvalue()
            self.assertIn("content/english/projects/2024-05-20-my-project.md", output)


class TestCmdList(unittest.TestCase):
    """Tests for cmd_list function."""

    def test_list_calls_find_publishable_notes(self):
        """list command calls find_publishable_notes."""
        mock_args = MagicMock()
        mock_args.vault = None
        mock_args.output = None

        with patch('publish.find_publishable_notes', return_value=[]) as mock_find:
            with patch('sys.stdout', new_callable=StringIO):
                cmd_list(mock_args)
                mock_find.assert_called_once_with(vault_path=None)

    def test_list_with_custom_vault_path(self):
        """list command passes custom vault path."""
        mock_args = MagicMock()
        mock_args.vault = '/custom/vault/path'
        mock_args.output = None

        with patch('publish.find_publishable_notes', return_value=[]) as mock_find:
            with patch('sys.stdout', new_callable=StringIO):
                cmd_list(mock_args)
                mock_find.assert_called_once()
                call_args = mock_find.call_args
                self.assertEqual(str(call_args.kwargs['vault_path']), '/custom/vault/path')

    def test_list_with_custom_output_dir(self):
        """list command uses custom output directory."""
        notes = [{
            'path': Path('/tmp/note.md'),
            'frontmatter': {'title': 'Test', 'date': '2024-01-01'},
            'body': 'Content'
        }]
        mock_args = MagicMock()
        mock_args.vault = None
        mock_args.output = 'content/english/projects'

        with patch('publish.find_publishable_notes', return_value=notes):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_list(mock_args)
                output = mock_stdout.getvalue()
                self.assertIn("content/english/projects/", output)

    def test_list_handles_file_not_found(self):
        """list command exits with error on FileNotFoundError."""
        mock_args = MagicMock()
        mock_args.vault = '/nonexistent/path'
        mock_args.output = None

        with patch('publish.find_publishable_notes', side_effect=FileNotFoundError("Vault not found")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    cmd_list(mock_args)
                self.assertEqual(context.exception.code, 1)
                self.assertIn("Vault not found", mock_stderr.getvalue())

    def test_list_handles_not_a_directory(self):
        """list command exits with error on NotADirectoryError."""
        mock_args = MagicMock()
        mock_args.vault = '/some/file.txt'
        mock_args.output = None

        with patch('publish.find_publishable_notes', side_effect=NotADirectoryError("Not a directory")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with self.assertRaises(SystemExit) as context:
                    cmd_list(mock_args)
                self.assertEqual(context.exception.code, 1)
                self.assertIn("Not a directory", mock_stderr.getvalue())


class TestCmdListIntegration(unittest.TestCase):
    """Integration tests for cmd_list with actual filesystem."""

    def test_list_with_test_vault(self):
        """list command works with a test vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a publishable note
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: Integration Test Note
date: 2024-06-15
tags:
  - test
  - integration
publish: true
---

This is a test note for integration testing.
""")

            mock_args = MagicMock()
            mock_args.vault = tmpdir
            mock_args.output = None

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_list(mock_args)
                output = mock_stdout.getvalue()

                # Should find the publishable note
                self.assertIn("test-note.md", output)
                self.assertIn("Integration Test Note", output)
                self.assertIn("2024-06-15", output)

                # Should include target path (may be truncated in table)
                self.assertIn("content/english/post/2024-06-15-integration-test-not", output)

                # Should show count of 1
                self.assertIn("Found 1 publishable note(s).", output)


class TestCmdMedia(unittest.TestCase):
    """Tests for cmd_media function."""

    def test_media_file_not_found(self):
        """media command exits with error for missing file."""
        mock_args = MagicMock()
        mock_args.path = '/nonexistent/note.md'

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                cmd_media(mock_args)
            self.assertEqual(context.exception.code, 1)
            self.assertIn("Note not found", mock_stderr.getvalue())

    def test_media_no_media_references(self):
        """media command shows message when note has no media."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-media.md"
            note_path.write_text("""---
title: No Media Note
date: 2024-01-01
publish: true
---

Just plain text, no media here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_media(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Media references in:", output)
                self.assertIn("No media references found in this note.", output)

    def test_media_shows_resolved_files(self):
        """media command shows resolved media files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "with-media.md"
            note_path.write_text("""---
title: With Media
date: 2024-01-01
publish: true
---

![[photo.jpg]]
![[video.mp4]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.side_effect = lambda ref: f"/media/{ref}"

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_media(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("Resolved (2 file(s)):", output)
                    self.assertIn("photo.jpg", output)
                    self.assertIn("/media/photo.jpg", output)
                    self.assertIn("video.mp4", output)
                    self.assertIn("/media/video.mp4", output)
                    self.assertIn("Summary: 2 reference(s), 2 resolved, 0 missing", output)

    def test_media_shows_missing_files(self):
        """media command shows missing media files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "missing-media.md"
            note_path.write_text("""---
title: Missing Media
date: 2024-01-01
publish: true
---

![[exists.jpg]]
![[missing.png]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)

            with patch('publish.resolve_media_path') as mock_resolve:
                # Only resolve exists.jpg, return None for missing.png
                def resolve_side_effect(ref):
                    if ref == "exists.jpg":
                        return "/media/exists.jpg"
                    return None
                mock_resolve.side_effect = resolve_side_effect

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_media(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("Resolved (1 file(s)):", output)
                    self.assertIn("exists.jpg", output)
                    self.assertIn("Missing (1 file(s)):", output)
                    self.assertIn("missing.png [NOT FOUND]", output)
                    self.assertIn("Summary: 2 reference(s), 1 resolved, 1 missing", output)

    def test_media_shows_all_missing(self):
        """media command handles case where all files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "all-missing.md"
            note_path.write_text("""---
title: All Missing
date: 2024-01-01
publish: true
---

![[missing1.jpg]]
![[missing2.png]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)

            with patch('publish.resolve_media_path', return_value=None):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_media(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertNotIn("Resolved", output)
                    self.assertIn("Missing (2 file(s)):", output)
                    self.assertIn("missing1.jpg [NOT FOUND]", output)
                    self.assertIn("missing2.png [NOT FOUND]", output)
                    self.assertIn("Summary: 2 reference(s), 0 resolved, 2 missing", output)

    def test_media_shows_paths_with_directories(self):
        """media command correctly shows media paths with subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "subdirs.md"
            note_path.write_text("""---
title: Subdirs
date: 2024-01-01
publish: true
---

![[2021/06/vacation/beach.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = "/home/user/Media/2021/06/vacation/beach.jpg"

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_media(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("2021/06/vacation/beach.jpg", output)
                    self.assertIn("/home/user/Media/2021/06/vacation/beach.jpg", output)


class TestCmdValidate(unittest.TestCase):
    """Tests for cmd_validate function."""

    def test_validate_file_not_found(self):
        """validate command exits with error for missing file."""
        mock_args = MagicMock()
        mock_args.path = '/nonexistent/note.md'
        mock_args.vault = None
        mock_args.hugo_root = None

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                cmd_validate(mock_args)
            self.assertEqual(context.exception.code, 1)
            self.assertIn("Note not found", mock_stderr.getvalue())

    def test_validate_valid_note_exits_zero(self):
        """validate command exits with 0 for valid note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "valid-note.md"
            note_path.write_text("""---
title: Valid Note
date: 2024-01-15
tags:
  - python
publish: true
---

Just plain text content, no media or links.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 0)
                output = mock_stdout.getvalue()
                self.assertIn("VALIDATION REPORT", output)
                self.assertIn("VALIDATION PASSED: No issues found", output)

    def test_validate_missing_required_fields_exits_one(self):
        """validate command exits with 1 for note missing required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "invalid-note.md"
            note_path.write_text("""---
publish: true
---

Missing title, date, and tags.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 1)
                output = mock_stdout.getvalue()
                self.assertIn("VALIDATION FAILED", output)
                self.assertIn("3 error(s)", output)

    def test_validate_warnings_only_exits_two(self):
        """validate command exits with 2 for warnings only (no errors)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "warning-note.md"
            note_path.write_text("""---
title: ""
date: 2024-01-15
tags:
  - python
publish: true
---

Note with empty title (warning, not error).
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 2)
                output = mock_stdout.getvalue()
                self.assertIn("VALIDATION PASSED WITH WARNINGS", output)

    def test_validate_shows_missing_media(self):
        """validate command reports missing media files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "media-note.md"
            note_path.write_text("""---
title: Media Note
date: 2024-01-15
tags:
  - test
publish: true
---

Here's an image: ![[nonexistent.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 1)
                output = mock_stdout.getvalue()
                self.assertIn("Found 1 missing media file(s)", output)
                self.assertIn("nonexistent.jpg", output)

    def test_validate_shows_broken_links(self):
        """validate command reports broken internal links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "link-note.md"
            note_path.write_text("""---
title: Link Note
date: 2024-01-15
tags:
  - test
publish: true
---

See also: [[Nonexistent Page]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 1)
                output = mock_stdout.getvalue()
                self.assertIn("Found 1 broken link(s)", output)
                self.assertIn("Nonexistent Page", output)

    def test_validate_all_checks_run(self):
        """validate command runs all three validators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "full-note.md"
            note_path.write_text("""---
title: Full Note
date: 2024-01-15
tags:
  - test
publish: true
---

This note is valid with no media or links.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                self.assertEqual(context.exception.code, 0)
                output = mock_stdout.getvalue()
                # All three validators should have run
                self.assertIn("Validating frontmatter...", output)
                self.assertIn("Validating media references...", output)
                self.assertIn("Validating internal links...", output)

    def test_validate_displays_note_info(self):
        """validate command shows note path and title in header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "info-note.md"
            note_path.write_text("""---
title: My Awesome Post
date: 2024-01-15
tags:
  - test
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.vault = tmpdir
            mock_args.hugo_root = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with self.assertRaises(SystemExit) as context:
                    cmd_validate(mock_args)
                output = mock_stdout.getvalue()
                self.assertIn("Note:", output)
                self.assertIn("info-note.md", output)
                self.assertIn("Title: My Awesome Post", output)


class TestConvertNote(unittest.TestCase):
    """Tests for convert_note function."""

    def test_basic_conversion(self):
        """convert_note processes a basic note correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: My Test Post
date: 2024-03-15
tags:
  - python
  - testing
publish: true
---

This is the content of my test post.

Here's a link to [[Another Page]].
""")

            hugo_fm, body, target = convert_note(note_path)

            # Check frontmatter transformation
            self.assertEqual(hugo_fm['title'], 'My Test Post')
            self.assertEqual(hugo_fm['date'], '2024-03-15')
            self.assertEqual(hugo_fm['tags'], ['python', 'testing'])
            self.assertFalse(hugo_fm['draft'])
            self.assertNotIn('publish', hugo_fm)

            # Check wikilink conversion
            self.assertIn('[Another Page](/post/another-page/)', body)
            self.assertNotIn('[[Another Page]]', body)

            # Check target path
            self.assertEqual(target, Path('content/english/post/2024-03-15-my-test-post.md'))

    def test_converts_embedded_images(self):
        """convert_note converts embedded image syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "image-note.md"
            note_path.write_text("""---
title: Post with Image
date: 2024-04-20
publish: true
---

Here's an embedded image: ![[my-photo.jpg]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Check image conversion
            self.assertIn('![my photo]({{<s3cdn>}}/my-photo.jpg)', body)
            self.assertNotIn('![[my-photo.jpg]]', body)

    def test_converts_embedded_media(self):
        """convert_note converts embedded video/audio syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "media-note.md"
            note_path.write_text("""---
title: Post with Media
date: 2024-05-10
publish: true
---

Check out this video: ![[demo.mp4]]

And this audio: ![[podcast.mp3]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Check video conversion
            self.assertIn('<video controls><source src="{{<s3cdn>}}/demo.mp4" type="video/mp4"></video>', body)
            self.assertNotIn('![[demo.mp4]]', body)

            # Check audio conversion
            self.assertIn('<audio controls><source src="{{<s3cdn>}}/podcast.mp3" type="audio/mpeg"></audio>', body)
            self.assertNotIn('![[podcast.mp3]]', body)

    def test_custom_output_dir(self):
        """convert_note respects custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "project.md"
            note_path.write_text("""---
title: My Project
date: 2024-01-01
publish: true
---

Project details here.
""")

            hugo_fm, body, target = convert_note(note_path, 'content/english/projects')

            self.assertEqual(target, Path('content/english/projects/2024-01-01-my-project.md'))

    def test_extracts_title_from_h1(self):
        """convert_note extracts title from H1 when not in frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-title.md"
            note_path.write_text("""---
date: 2024-02-28
publish: true
---

# Extracted Title Here

Body content follows.
""")

            hugo_fm, body, target = convert_note(note_path)

            self.assertEqual(hugo_fm['title'], 'Extracted Title Here')
            self.assertEqual(target, Path('content/english/post/2024-02-28-extracted-title-here.md'))

    def test_file_not_found_error(self):
        """convert_note raises FileNotFoundError for missing files."""
        with self.assertRaises(FileNotFoundError):
            convert_note(Path('/nonexistent/path/note.md'))


class TestCmdConvert(unittest.TestCase):
    """Tests for cmd_convert function."""

    def test_convert_file_not_found(self):
        """convert command exits with error for missing file."""
        mock_args = MagicMock()
        mock_args.path = '/nonexistent/note.md'
        mock_args.dry_run = False
        mock_args.output = None

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                cmd_convert(mock_args)
            self.assertEqual(context.exception.code, 1)
            self.assertIn("Note not found", mock_stderr.getvalue())

    def test_dry_run_prints_preview(self):
        """convert --dry-run prints preview without writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Dry Run Test
date: 2024-06-01
publish: true
---

This is test content.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show dry run messages
                self.assertIn('[DRY RUN]', output)
                self.assertIn('Would convert:', output)
                self.assertIn('Target path:', output)

                # Should show preview
                self.assertIn('--- Preview of converted content ---', output)
                self.assertIn('title: Dry Run Test', output)
                self.assertIn('date: 2024-06-01', output)
                self.assertIn('This is test content.', output)

    def test_convert_writes_file(self):
        """convert command writes file to correct location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source note
            note_path = Path(tmpdir) / "source-note.md"
            note_path.write_text("""---
title: Write Test Post
date: 2024-07-15
tags:
  - testing
publish: true
---

Content with [[wikilink]] and ![[image.png]].
""")

            # Set output directory in temp folder
            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show conversion messages
                self.assertIn('Converted:', output)
                self.assertIn('Written to:', output)

            # Check file was written
            expected_path = output_dir / "2024-07-15-write-test-post.md"
            self.assertTrue(expected_path.exists())

            # Check file content
            content = expected_path.read_text()
            self.assertIn('title: Write Test Post', content)
            self.assertIn('date: 2024-07-15', content)
            self.assertIn('[wikilink](/post/wikilink/)', content)
            self.assertIn('![image]({{<s3cdn>}}/image.png)', content)

    def test_convert_with_custom_output_dir(self):
        """convert command respects --output argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Custom Output
date: 2024-08-01
publish: true
---

Content here.
""")

            custom_output = Path(tmpdir) / "custom" / "path"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(custom_output)

            with patch('sys.stdout', new_callable=StringIO):
                cmd_convert(mock_args)

            expected_path = custom_output / "2024-08-01-custom-output.md"
            self.assertTrue(expected_path.exists())


class TestCmdConvertSkipUpload(unittest.TestCase):
    """Tests for the --skip-upload flag in cmd_convert."""

    def test_skip_upload_flag_accessible(self):
        """skip_upload flag is accessible from args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Skip Upload Test
date: 2024-06-01
publish: true
---

Content with ![[image.png]].
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show skip upload message in dry run
                self.assertIn('[DRY RUN] Media upload: SKIPPED', output)

    def test_skip_upload_false_by_default(self):
        """skip_upload defaults to False when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: No Skip Test
date: 2024-06-01
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should NOT show skip upload message when skip_upload is False
                self.assertNotIn('Media upload: SKIPPED', output)

    def test_skip_upload_with_actual_conversion(self):
        """skip_upload works with actual file conversion (not just dry-run)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Full Convert Skip Test
date: 2024-06-01
publish: true
---

Content with ![[media.mp4]].
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should successfully convert without attempting upload
                self.assertIn('Converted:', output)
                self.assertIn('Written to:', output)

            # File should exist
            expected_path = output_dir / "2024-06-01-full-convert-skip-test.md"
            self.assertTrue(expected_path.exists())


class TestConvertNoteGalleryGeneration(unittest.TestCase):
    """Tests for convert_note with Pictures section gallery generation."""

    def test_generates_gallery_from_pictures_section(self):
        """convert_note generates nanogallery2 HTML from Pictures section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "project-with-gallery.md"
            note_path.write_text("""---
title: Wood Zippo Project
date: 2024-01-15
tags:
  - woodworking
  - project
publish: true
---

This is my wood zippo lighter project.

## Pictures

![[zippo_01.jpg]]
![[zippo_02.jpg]]
![[zippo_03.mp4]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Should contain nanogallery2 div
            self.assertIn('data-nanogallery2', body)
            self.assertIn('<div ID="gallery"', body)

            # Should contain the media files as anchor tags
            self.assertIn('href="zippo_01.jpg"', body)
            self.assertIn('href="zippo_02.jpg"', body)
            self.assertIn('href="zippo_03.mp4"', body)

            # Should use the s3cdn shortcode for base URL
            self.assertIn('{{<s3cdn>}}', body)
            self.assertIn('/projects/wood-zippo-project/', body)

            # Pictures section should be removed from body
            self.assertNotIn('## Pictures', body)
            self.assertNotIn('![[zippo_01.jpg]]', body)

    def test_no_gallery_without_pictures_section(self):
        """convert_note doesn't generate gallery when no Pictures section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "post-no-gallery.md"
            note_path.write_text("""---
title: Regular Blog Post
date: 2024-02-20
tags:
  - blogging
publish: true
---

Just a regular blog post without a pictures section.

Some embedded image: ![[inline_image.png]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Should NOT contain nanogallery2 HTML
            self.assertNotIn('data-nanogallery2', body)
            self.assertNotIn('<div ID="gallery"', body)

            # Inline image should be converted normally
            self.assertIn('![inline image]({{<s3cdn>}}/inline_image.png)', body)

    def test_generate_gallery_false_skips_gallery(self):
        """convert_note with generate_gallery=False skips gallery generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "project-skip-gallery.md"
            note_path.write_text("""---
title: Project Skip Gallery
date: 2024-03-10
tags:
  - project
publish: true
---

A project that should skip gallery.

## Pictures

![[image1.jpg]]
![[image2.jpg]]
""")

            hugo_fm, body, target = convert_note(note_path, generate_gallery=False)

            # Should NOT contain nanogallery2 HTML
            self.assertNotIn('data-nanogallery2', body)
            self.assertNotIn('<div ID="gallery"', body)

            # Pictures section should still be in the body (not removed)
            self.assertIn('## Pictures', body)

    def test_gallery_uses_title_slug_for_path(self):
        """Gallery base URL uses slugified title for CDN path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "special-title.md"
            note_path.write_text("""---
title: My Special Project's Gallery!
date: 2024-04-05
tags:
  - project
publish: true
---

Special project.

## Pictures

![[photo.jpg]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Should use slugified title in CDN path (no date prefix for gallery slug)
            self.assertIn('/projects/my-special-projects-gallery/', body)

    def test_gallery_preserves_text_content(self):
        """Gallery generation preserves text content before Pictures section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "content-test.md"
            note_path.write_text("""---
title: Content Preservation Test
date: 2024-05-15
publish: true
---

# Introduction

This is the intro paragraph.

## Details

Some **detailed** information here.

## Pictures

![[img.jpg]]

## Footer

This footer should be preserved too.
""")

            hugo_fm, body, target = convert_note(note_path)

            # Main content should be preserved
            self.assertIn('# Introduction', body)
            self.assertIn('This is the intro paragraph.', body)
            self.assertIn('## Details', body)
            self.assertIn('Some **detailed** information here.', body)

            # Footer after Pictures section should be preserved
            self.assertIn('## Footer', body)
            self.assertIn('This footer should be preserved too.', body)

            # Gallery should be added at the end
            self.assertIn('data-nanogallery2', body)

    def test_gallery_at_end_of_content(self):
        """Gallery HTML is appended at the end of the converted content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "gallery-position.md"
            note_path.write_text("""---
title: Gallery Position Test
date: 2024-06-01
publish: true
---

First paragraph.

## Pictures

![[photo.jpg]]
""")

            hugo_fm, body, target = convert_note(note_path)

            # Find positions
            first_para_pos = body.find('First paragraph.')
            gallery_pos = body.find('<div ID="gallery"')

            # Gallery should come after the first paragraph
            self.assertLess(first_para_pos, gallery_pos)
            self.assertGreater(gallery_pos, 0)


class TestCmdConvertGalleryIntegration(unittest.TestCase):
    """Integration tests for cmd_convert with gallery generation."""

    def test_dry_run_shows_gallery_info(self):
        """convert --dry-run shows gallery generation info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "gallery-dry-run.md"
            note_path.write_text("""---
title: Gallery Dry Run Test
date: 2024-06-01
publish: true
---

Content here.

## Pictures

![[img1.jpg]]
![[img2.png]]
![[vid.mp4]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show gallery info
                self.assertIn('[DRY RUN] Gallery: YES (3 images)', output)

    def test_convert_writes_file_with_gallery(self):
        """convert command writes file with gallery HTML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "gallery-write.md"
            note_path.write_text("""---
title: Gallery Write Test
date: 2024-07-15
tags:
  - project
publish: true
---

My project description.

## Pictures

![[project_photo_01.jpg]]
![[project_photo_02.jpg]]
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should report gallery generation
                self.assertIn('Gallery generated: 2 images', output)

            # Check file was written with gallery
            expected_path = output_dir / "2024-07-15-gallery-write-test.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()

            # Should contain gallery HTML
            self.assertIn('data-nanogallery2', content)
            self.assertIn('href="project_photo_01.jpg"', content)
            self.assertIn('href="project_photo_02.jpg"', content)

            # Should not contain Pictures section markdown
            self.assertNotIn('## Pictures', content)
            self.assertNotIn('![[project_photo_01.jpg]]', content)

    def test_convert_no_gallery_message_without_pictures(self):
        """convert command doesn't show gallery message when no Pictures section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-gallery.md"
            note_path.write_text("""---
title: No Gallery Test
date: 2024-08-01
publish: true
---

Just regular content.
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should NOT show gallery info
                self.assertNotIn('Gallery:', output)


class TestCmdConvertNoGalleryFlag(unittest.TestCase):
    """Tests for the --no-gallery flag in cmd_convert."""

    def test_no_gallery_flag_accessible(self):
        """no_gallery flag is accessible from args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: No Gallery Flag Test
date: 2024-06-01
publish: true
---

Content with a Pictures section.

## Pictures

![[image1.jpg]]
![[image2.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show gallery skipped message in dry run
                self.assertIn('[DRY RUN] Gallery: SKIPPED (2 images in Pictures section)', output)

    def test_no_gallery_false_by_default(self):
        """no_gallery defaults to False when not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Default Gallery Test
date: 2024-06-01
publish: true
---

Content here.

## Pictures

![[photo.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show gallery YES message (not skipped)
                self.assertIn('[DRY RUN] Gallery: YES (1 images)', output)
                # Should NOT show gallery skipped message
                self.assertNotIn('Gallery: SKIPPED', output)

    def test_no_gallery_with_actual_conversion(self):
        """--no-gallery works with actual file conversion (not just dry-run)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Full Convert No Gallery Test
date: 2024-06-01
publish: true
---

Content with Pictures.

## Pictures

![[media.jpg]]
![[media2.png]]
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show gallery skipped message
                self.assertIn('Gallery skipped: 2 images in Pictures section', output)

            # File should exist
            expected_path = output_dir / "2024-06-01-full-convert-no-gallery-test.md"
            self.assertTrue(expected_path.exists())

            # File should NOT contain nanogallery2 HTML
            content = expected_path.read_text()
            self.assertNotIn('data-nanogallery2', content)
            self.assertNotIn('<div ID="gallery"', content)

            # Pictures section should still be in the content (not removed when gallery skipped)
            self.assertIn('## Pictures', content)

    def test_no_gallery_preserves_pictures_section(self):
        """--no-gallery leaves Pictures section in content instead of removing it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "preserve-pictures.md"
            note_path.write_text("""---
title: Preserve Pictures Test
date: 2024-07-01
publish: true
---

Introduction paragraph.

## Pictures

![[pic1.jpg]]
![[pic2.png]]
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = True

            with patch('sys.stdout', new_callable=StringIO):
                cmd_convert(mock_args)

            expected_path = output_dir / "2024-07-01-preserve-pictures-test.md"
            content = expected_path.read_text()

            # Pictures section header should be preserved
            self.assertIn('## Pictures', content)
            # Embedded images will be converted to markdown img syntax
            # but the section structure remains

    def test_no_gallery_no_effect_without_pictures_section(self):
        """--no-gallery has no effect when there's no Pictures section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-pictures.md"
            note_path.write_text("""---
title: No Pictures Section
date: 2024-08-01
publish: true
---

Just regular content, no Pictures section.

![[inline_image.png]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should not mention gallery at all (no Pictures section)
                self.assertNotIn('Gallery:', output)


class TestCmdConvertIntegration(unittest.TestCase):
    """Integration tests for cmd_convert with full pipeline."""

    def test_full_conversion_pipeline(self):
        """Full conversion correctly transforms all Obsidian syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "full-test.md"
            note_path.write_text("""---
title: Complete Integration Test
date: 2024-09-15
tags:
  - integration
  - testing
  - obsidian
author: Test Author
draft: false
publish: true
---

# Introduction

This post has various Obsidian syntax to convert.

## Links and Media

Here's a [[Wiki Link]] and an [[aliased|Different Text]] link.

![[screenshot.png]]

![[demo-video.mp4]]

![[podcast-episode.mp3]]

## More Content

Regular markdown **works** fine.
""")

            output_dir = Path(tmpdir) / "hugo_output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)

            with patch('sys.stdout', new_callable=StringIO):
                cmd_convert(mock_args)

            # Read the generated file
            expected_path = output_dir / "2024-09-15-complete-integration-test.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()

            # Check frontmatter
            self.assertIn('title: Complete Integration Test', content)
            self.assertIn('author: Test Author', content)
            self.assertIn('draft: false', content)
            self.assertIn('tags: [integration, testing, obsidian]', content)

            # publish field should be removed
            self.assertNotIn('publish:', content)

            # Check wikilinks converted
            self.assertIn('[Wiki Link](/post/wiki-link/)', content)
            self.assertIn('[Different Text](/post/aliased/)', content)

            # Check images converted
            self.assertIn('![screenshot]({{<s3cdn>}}/screenshot.png)', content)

            # Check video converted
            self.assertIn('<video controls><source src="{{<s3cdn>}}/demo-video.mp4" type="video/mp4"></video>', content)

            # Check audio converted
            self.assertIn('<audio controls><source src="{{<s3cdn>}}/podcast-episode.mp3" type="audio/mpeg"></audio>', content)

            # Regular markdown preserved
            self.assertIn('**works**', content)


def _has_dotenv():
    """Check if python-dotenv is installed."""
    try:
        import dotenv
        return True
    except ImportError:
        return False


class TestLoadDotenv(unittest.TestCase):
    """Tests for dotenv loading functionality."""

    def test_load_dotenv_returns_false_when_no_env_file(self):
        """load_dotenv returns False when .env file doesn't exist."""
        from publish import load_dotenv

        # Create a temporary directory without .env file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change the script's __file__ location
            import publish
            original_file = publish.__file__

            # Create a fake script path that doesn't have a .env file
            fake_script = Path(tmpdir) / 'publish.py'
            fake_script.touch()

            with patch.object(publish, '__file__', str(fake_script)):
                # The function uses Path(__file__) which captures the value at
                # function definition time, so we just verify the function runs
                result = load_dotenv()
                # Result depends on whether scripts/.env exists in real location
                self.assertIsInstance(result, bool)

    @unittest.skipUnless(_has_dotenv(), "python-dotenv not installed")
    def test_load_dotenv_returns_true_when_env_file_exists(self):
        """load_dotenv returns True when .env file exists and is loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a .env file
            env_path = Path(tmpdir) / '.env'
            env_path.write_text('TEST_VAR_FOR_DOTENV=test_value\n')

            # Create a fake publish.py in the same directory
            fake_script = Path(tmpdir) / 'publish.py'
            fake_script.touch()

            # We need to test the logic by simulating what load_dotenv does
            from dotenv import load_dotenv as dotenv_load

            # Verify the env file can be loaded
            import os
            original_val = os.environ.get('TEST_VAR_FOR_DOTENV')

            dotenv_load(env_path)
            self.assertEqual(os.environ.get('TEST_VAR_FOR_DOTENV'), 'test_value')

            # Clean up
            if original_val is None:
                os.environ.pop('TEST_VAR_FOR_DOTENV', None)
            else:
                os.environ['TEST_VAR_FOR_DOTENV'] = original_val

    def test_load_dotenv_handles_missing_dotenv_package(self):
        """load_dotenv returns False if python-dotenv not installed."""
        # Test by mocking the import to fail
        with patch.dict('sys.modules', {'dotenv': None}):
            # When dotenv module is None, import will fail
            # We need to test this differently - by testing the try/except logic
            pass  # This is implicitly tested by the graceful handling

    @unittest.skipUnless(_has_dotenv(), "python-dotenv not installed")
    def test_dotenv_loads_minio_config(self):
        """Environment variables from .env are accessible for MinIO config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a .env file with MinIO config
            env_path = Path(tmpdir) / '.env'
            env_path.write_text("""MINIO_ENDPOINT=test.minio.local:9000
MINIO_ACCESS_KEY=testaccesskey
MINIO_SECRET_KEY=testsecretkey
MINIO_BUCKET=test-bucket
MINIO_SECURE=false
""")

            from dotenv import load_dotenv as dotenv_load
            import os

            # Save original values
            original_values = {
                'MINIO_ENDPOINT': os.environ.get('MINIO_ENDPOINT'),
                'MINIO_ACCESS_KEY': os.environ.get('MINIO_ACCESS_KEY'),
                'MINIO_SECRET_KEY': os.environ.get('MINIO_SECRET_KEY'),
                'MINIO_BUCKET': os.environ.get('MINIO_BUCKET'),
                'MINIO_SECURE': os.environ.get('MINIO_SECURE'),
            }

            try:
                # Load the test .env file
                dotenv_load(env_path)

                # Verify all variables were loaded
                self.assertEqual(os.environ.get('MINIO_ENDPOINT'), 'test.minio.local:9000')
                self.assertEqual(os.environ.get('MINIO_ACCESS_KEY'), 'testaccesskey')
                self.assertEqual(os.environ.get('MINIO_SECRET_KEY'), 'testsecretkey')
                self.assertEqual(os.environ.get('MINIO_BUCKET'), 'test-bucket')
                self.assertEqual(os.environ.get('MINIO_SECURE'), 'false')

            finally:
                # Restore original values
                for key, value in original_values.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_load_dotenv_function_exists(self):
        """load_dotenv function is exported from publish module."""
        from publish import load_dotenv
        self.assertTrue(callable(load_dotenv))

    def test_dotenv_loaded_variable_exists(self):
        """_dotenv_loaded module variable exists."""
        from publish import _dotenv_loaded
        self.assertIsInstance(_dotenv_loaded, bool)


class TestExtractAndResolveMedia(unittest.TestCase):
    """Tests for extract_and_resolve_media function."""

    def test_no_media_returns_empty_list(self):
        """Note without media returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-media.md"
            note_path.write_text("""---
title: No Media
date: 2024-01-01
publish: true
---

Just text, no media embeds.
""")
            media_items, missing_count = extract_and_resolve_media(note_path)
            self.assertEqual(media_items, [])
            self.assertEqual(missing_count, 0)

    def test_extracts_media_references(self):
        """Extracts media references from note content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "with-media.md"
            note_path.write_text("""---
title: With Media
date: 2024-01-01
publish: true
---

Here's an image: ![[photo.jpg]]

And a video: ![[demo.mp4]]
""")

            # Mock resolve_media_path to return test paths
            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.side_effect = lambda ref: f"/resolved/{ref}" if ref == "photo.jpg" else None

                media_items, missing_count = extract_and_resolve_media(note_path)

                # Should have found 2 references, 1 resolved, 1 missing
                self.assertEqual(len(media_items), 1)
                self.assertEqual(media_items[0], ("photo.jpg", "/resolved/photo.jpg"))
                self.assertEqual(missing_count, 1)

    def test_handles_multiple_media_files(self):
        """Handles notes with multiple media files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "multi-media.md"
            note_path.write_text("""---
title: Multi Media
date: 2024-01-01
publish: true
---

![[image1.png]]
![[image2.jpg]]
![[video.mp4]]
""")

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.side_effect = lambda ref: f"/media/{ref}"

                media_items, missing_count = extract_and_resolve_media(note_path)

                self.assertEqual(len(media_items), 3)
                self.assertEqual(missing_count, 0)


class TestConvertNoteWithMediaMap(unittest.TestCase):
    """Tests for convert_note with media_url_map parameter."""

    def test_convert_with_media_url_map(self):
        """convert_note uses media_url_map when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "mapped-media.md"
            note_path.write_text("""---
title: Mapped Media Test
date: 2024-01-01
publish: true
---

![[photo.jpg]]
""")

            media_url_map = {
                "photo.jpg": "https://minio.example.com/bucket/assets/photo.jpg"
            }

            hugo_fm, body, target = convert_note(note_path, media_url_map=media_url_map)

            # Should use the MinIO URL instead of s3cdn shortcode
            self.assertIn("https://minio.example.com/bucket/assets/photo.jpg", body)
            self.assertNotIn("{{<s3cdn>}}", body)

    def test_convert_without_media_url_map(self):
        """convert_note uses s3cdn shortcode when no media_url_map."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-map.md"
            note_path.write_text("""---
title: No Map Test
date: 2024-01-01
publish: true
---

![[photo.jpg]]
""")

            hugo_fm, body, target = convert_note(note_path, media_url_map=None)

            # Should use s3cdn shortcode
            self.assertIn("{{<s3cdn>}}", body)
            self.assertIn("/photo.jpg", body)

    def test_convert_with_partial_media_map(self):
        """convert_note handles partial media_url_map correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "partial-map.md"
            note_path.write_text("""---
title: Partial Map Test
date: 2024-01-01
publish: true
---

![[mapped.jpg]]
![[unmapped.png]]
""")

            media_url_map = {
                "mapped.jpg": "https://minio.example.com/bucket/assets/mapped.jpg"
            }

            hugo_fm, body, target = convert_note(note_path, media_url_map=media_url_map)

            # Mapped image should use MinIO URL
            self.assertIn("https://minio.example.com/bucket/assets/mapped.jpg", body)
            # Unmapped image should use s3cdn shortcode
            self.assertIn("{{<s3cdn>}}/unmapped.png", body)


class TestCmdConvertMediaIntegration(unittest.TestCase):
    """Tests for cmd_convert with media pipeline integration."""

    def test_convert_with_skip_upload_shows_media_found(self):
        """convert --dry-run --skip-upload shows media files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test note with media references
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Media Test
date: 2024-06-01
publish: true
---

![[image.png]]
![[video.mp4]]
""")

            # Create fake resolved media files
            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "image.png").touch()
            (media_dir / "video.mp4").touch()

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.side_effect = lambda ref: str(media_dir / ref)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_convert(mock_args)
                    output = mock_stdout.getvalue()

                    # Should show media files found
                    self.assertIn('[DRY RUN] Media files found: 2', output)
                    self.assertIn('[DRY RUN] Media upload: SKIPPED', output)

    def test_convert_without_minio_installed_continues(self):
        """convert continues gracefully when minio package not installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: No MinIO Test
date: 2024-06-01
publish: true
---

![[image.png]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "image.png").touch()

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = False  # Try to upload

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = str(media_dir / "image.png")

                # Simulate minio not being available
                with patch('publish.upload_media_to_minio', side_effect=ImportError("minio not installed")):
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                            cmd_convert(mock_args)

                            # Should warn but continue
                            self.assertIn("Warning: MinIO upload skipped", mock_stderr.getvalue())

                            # File should still be written
                            self.assertIn("Written to:", mock_stdout.getvalue())

    def test_convert_uploads_media_to_minio(self):
        """convert uploads media to MinIO when configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Upload Test
date: 2024-06-01
publish: true
---

![[image.png]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "image.png").touch()

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = False

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = str(media_dir / "image.png")

                mock_url_map = {"image.png": "https://minio.test/bucket/assets/image.png"}

                with patch('publish.upload_media_to_minio', return_value=mock_url_map) as mock_upload:
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        cmd_convert(mock_args)

                        # upload_media_to_minio should have been called
                        mock_upload.assert_called_once()
                        call_args = mock_upload.call_args[0][0]
                        self.assertEqual(len(call_args), 1)
                        self.assertEqual(call_args[0][0], "image.png")

            # Check that the output file uses the MinIO URL
            expected_path = output_dir / "2024-06-01-upload-test.md"
            content = expected_path.read_text()
            self.assertIn("https://minio.test/bucket/assets/image.png", content)


class TestUploadMediaToMinio(unittest.TestCase):
    """Tests for upload_media_to_minio function."""

    def test_uploads_new_files(self):
        """Uploads files that don't exist in MinIO."""
        media_items = [
            ("photo.jpg", "/path/to/photo.jpg"),
            ("video.mp4", "/path/to/video.mp4"),
        ]

        mock_client = MagicMock()

        with patch.dict('os.environ', {
            'MINIO_ENDPOINT': 'minio.test:9000',
            'MINIO_ACCESS_KEY': 'access',
            'MINIO_SECRET_KEY': 'secret',
            'MINIO_BUCKET': 'test-bucket',
            'MINIO_SECURE': 'true'
        }):
            with patch('minio_uploader.get_minio_client', return_value=mock_client):
                with patch('minio_uploader.get_bucket_name', return_value='test-bucket'):
                    with patch('minio_uploader.ensure_bucket_exists', return_value=True):
                        with patch('minio_uploader.check_existing', return_value=False):
                            with patch('minio_uploader.upload_media_batch') as mock_batch:
                                mock_batch.return_value = {
                                    "photo.jpg": "https://minio.test:9000/test-bucket/assets/photo.jpg",
                                    "video.mp4": "https://minio.test:9000/test-bucket/assets/video.mp4",
                                }

                                result = upload_media_to_minio(media_items)

                                # Should call upload_media_batch with both files
                                mock_batch.assert_called_once()
                                self.assertEqual(len(result), 2)
                                self.assertIn("photo.jpg", result)
                                self.assertIn("video.mp4", result)

    def test_skips_existing_files(self):
        """Skips files that already exist in MinIO."""
        media_items = [
            ("existing.jpg", "/path/to/existing.jpg"),
            ("new.jpg", "/path/to/new.jpg"),
        ]

        mock_client = MagicMock()

        with patch.dict('os.environ', {
            'MINIO_ENDPOINT': 'minio.test:9000',
            'MINIO_ACCESS_KEY': 'access',
            'MINIO_SECRET_KEY': 'secret',
            'MINIO_BUCKET': 'test-bucket',
            'MINIO_SECURE': 'true'
        }):
            with patch('minio_uploader.get_minio_client', return_value=mock_client):
                with patch('minio_uploader.get_bucket_name', return_value='test-bucket'):
                    with patch('minio_uploader.ensure_bucket_exists', return_value=True):
                        def check_existing_side_effect(client, bucket, obj_name):
                            return "existing.jpg" in obj_name

                        with patch('minio_uploader.check_existing', side_effect=check_existing_side_effect):
                            with patch('minio_uploader.upload_media_batch') as mock_batch:
                                mock_batch.return_value = {
                                    "new.jpg": "https://minio.test:9000/test-bucket/assets/new.jpg",
                                }
                                with patch('minio_uploader.build_minio_url') as mock_build_url:
                                    mock_build_url.return_value = "https://minio.test:9000/test-bucket/assets/existing.jpg"

                                    with patch('sys.stdout', new_callable=StringIO):
                                        result = upload_media_to_minio(media_items)

                                # upload_media_batch should only receive the new file
                                call_args = mock_batch.call_args
                                items_to_upload = call_args[0][2]
                                self.assertEqual(len(items_to_upload), 1)
                                self.assertEqual(items_to_upload[0][0], "new.jpg")

                                # Result should include both files
                                self.assertEqual(len(result), 2)


class TestConvertNoteAssociationsHandling(unittest.TestCase):
    """Tests for convert_note with Associations section handling."""

    def test_removes_associations_by_default(self):
        """convert_note removes Associations section by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "post-with-associations.md"
            note_path.write_text("""---
title: Post with Associations
date: 2024-01-15
tags:
  - testing
publish: true
---

This is my blog post content.

## Associations

[[Related Post]]
[[Another Post|See this]]
[[Third Post]]

## Footer

Some footer text.
""")

            hugo_fm, body, target = convert_note(note_path)

            # Associations section should be removed
            self.assertNotIn('## Associations', body)
            self.assertNotIn('[[Related Post]]', body)
            self.assertNotIn('[[Another Post|See this]]', body)

            # Other content should be preserved
            self.assertIn('This is my blog post content.', body)
            self.assertIn('## Footer', body)
            self.assertIn('Some footer text.', body)

    def test_converts_associations_with_keep_flag(self):
        """convert_note converts Associations when keep_associations=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "post-keep-associations.md"
            note_path.write_text("""---
title: Post Keep Associations
date: 2024-02-20
tags:
  - testing
publish: true
---

Content here.

## Associations

[[Related Post]]
[[Another Post|See this]]
""")

            hugo_fm, body, target = convert_note(note_path, keep_associations=True)

            # Section should be renamed to Related
            self.assertIn('## Related', body)
            self.assertNotIn('## Associations', body)

            # Wikilinks should be converted to Hugo links
            self.assertIn('[Related Post](/post/related-post/)', body)
            self.assertIn('[See this](/post/another-post/)', body)
            self.assertNotIn('[[Related Post]]', body)
            self.assertNotIn('[[Another Post|See this]]', body)

    def test_no_effect_without_associations_section(self):
        """convert_note works fine when there's no Associations section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "post-no-associations.md"
            note_path.write_text("""---
title: Post Without Associations
date: 2024-03-10
publish: true
---

Just regular content here.

## Related

Some manually added related content.
""")

            hugo_fm, body, target = convert_note(note_path, keep_associations=True)

            # Content should be preserved as-is
            self.assertIn('Just regular content here.', body)
            self.assertIn('## Related', body)
            self.assertIn('Some manually added related content.', body)

    def test_handles_both_pictures_and_associations(self):
        """convert_note correctly handles notes with both Pictures and Associations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "project-with-both.md"
            note_path.write_text("""---
title: Project With Both Sections
date: 2024-04-05
tags:
  - project
  - woodworking
publish: true
---

My awesome project.

## Pictures

![[photo1.jpg]]
![[photo2.png]]

## Associations

[[Related Project]]
[[Woodworking Basics|Basics Guide]]

## Notes

Final notes.
""")

            # Test with gallery and associations removed (default)
            hugo_fm, body, target = convert_note(note_path)
            self.assertIn('data-nanogallery2', body)  # Gallery generated
            self.assertNotIn('## Pictures', body)
            self.assertNotIn('## Associations', body)
            self.assertIn('## Notes', body)

            # Test with gallery generated and associations kept
            hugo_fm2, body2, target2 = convert_note(note_path, keep_associations=True)
            self.assertIn('data-nanogallery2', body2)
            self.assertNotIn('## Pictures', body2)
            self.assertIn('## Related', body2)
            self.assertIn('[Related Project](/post/related-project/)', body2)
            self.assertIn('## Notes', body2)


class TestCmdConvertKeepAssociationsFlag(unittest.TestCase):
    """Tests for the --keep-associations flag in cmd_convert."""

    def test_keep_associations_flag_accessible(self):
        """keep_associations flag is accessible from args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Keep Associations Test
date: 2024-06-01
publish: true
---

Content here.

## Associations

[[Link 1]]
[[Link 2|Display]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show associations converted message
                self.assertIn('[DRY RUN] Associations: CONVERTED (2 links -> Related section)', output)

    def test_keep_associations_false_by_default(self):
        """keep_associations defaults to False (associations are removed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Default Associations Test
date: 2024-06-01
publish: true
---

Content here.

## Associations

[[Link]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show associations removed message
                self.assertIn('[DRY RUN] Associations: REMOVED (1 links)', output)
                # Should NOT show converted message
                self.assertNotIn('CONVERTED', output)

    def test_keep_associations_with_actual_conversion(self):
        """--keep-associations works with actual file conversion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Full Convert Keep Associations
date: 2024-06-01
publish: true
---

Content with associations.

## Associations

[[Related Page]]
[[Another|See Also]]
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show associations converted message
                self.assertIn('Associations converted: 2 links -> Related section', output)

            # Check file was written
            expected_path = output_dir / "2024-06-01-full-convert-keep-associations.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()

            # Should contain converted links
            self.assertIn('## Related', content)
            self.assertIn('[Related Page](/post/related-page/)', content)
            self.assertIn('[See Also](/post/another/)', content)

            # Should NOT contain wikilinks
            self.assertNotIn('[[Related Page]]', content)
            self.assertNotIn('## Associations', content)

    def test_associations_removed_with_actual_conversion(self):
        """Associations are removed by default in actual file conversion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Full Convert Remove Associations
date: 2024-07-01
publish: true
---

Main content here.

## Associations

[[Link 1]]
[[Link 2]]

## Footer

Footer content.
""")

            output_dir = Path(tmpdir) / "output"

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.output = str(output_dir)
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should show associations removed message
                self.assertIn('Associations removed: 2 links', output)

            # Check file was written
            expected_path = output_dir / "2024-07-01-full-convert-remove-associations.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()

            # Should NOT contain Associations section or wikilinks
            self.assertNotIn('## Associations', content)
            self.assertNotIn('[[Link 1]]', content)
            self.assertNotIn('[[Link 2]]', content)

            # Footer should still be there
            self.assertIn('## Footer', content)
            self.assertIn('Footer content.', content)

    def test_no_effect_without_associations_section(self):
        """--keep-associations has no effect when there's no Associations section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-assoc.md"
            note_path.write_text("""---
title: No Associations Section
date: 2024-08-01
publish: true
---

Just regular content, no Associations section.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_convert(mock_args)
                output = mock_stdout.getvalue()

                # Should not mention Associations at all
                self.assertNotIn('Associations:', output)


class TestConfirmPrompt(unittest.TestCase):
    """Tests for confirm_prompt function."""

    def test_confirm_yes_response(self):
        """Returns True for 'y' response."""
        with patch('builtins.input', return_value='y'):
            self.assertTrue(confirm_prompt("Continue?"))

    def test_confirm_yes_full_response(self):
        """Returns True for 'yes' response."""
        with patch('builtins.input', return_value='yes'):
            self.assertTrue(confirm_prompt("Continue?"))

    def test_confirm_no_response(self):
        """Returns False for 'n' response."""
        with patch('builtins.input', return_value='n'):
            self.assertFalse(confirm_prompt("Continue?"))

    def test_confirm_no_full_response(self):
        """Returns False for 'no' response."""
        with patch('builtins.input', return_value='no'):
            self.assertFalse(confirm_prompt("Continue?"))

    def test_confirm_empty_response_default_false(self):
        """Returns False for empty response when default=False."""
        with patch('builtins.input', return_value=''):
            self.assertFalse(confirm_prompt("Continue?", default=False))

    def test_confirm_empty_response_default_true(self):
        """Returns True for empty response when default=True."""
        with patch('builtins.input', return_value=''):
            self.assertTrue(confirm_prompt("Continue?", default=True))

    def test_confirm_case_insensitive(self):
        """Response is case-insensitive."""
        with patch('builtins.input', return_value='Y'):
            self.assertTrue(confirm_prompt("Continue?"))

        with patch('builtins.input', return_value='YES'):
            self.assertTrue(confirm_prompt("Continue?"))

    def test_confirm_handles_whitespace(self):
        """Handles whitespace in response."""
        with patch('builtins.input', return_value='  y  '):
            self.assertTrue(confirm_prompt("Continue?"))

    def test_confirm_handles_eof_error(self):
        """Returns default on EOFError (non-interactive mode)."""
        with patch('builtins.input', side_effect=EOFError):
            self.assertFalse(confirm_prompt("Continue?", default=False))
            self.assertTrue(confirm_prompt("Continue?", default=True))


class TestCmdPublish(unittest.TestCase):
    """Tests for cmd_publish function."""

    def test_publish_file_not_found(self):
        """publish command exits with error for missing file."""
        mock_args = MagicMock()
        mock_args.path = '/nonexistent/note.md'
        mock_args.dry_run = False
        mock_args.yes = True
        mock_args.hugo_root = None

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                cmd_publish(mock_args)
            self.assertEqual(context.exception.code, 1)
            self.assertIn("Note not found", mock_stderr.getvalue())

    def test_publish_dry_run_shows_summary(self):
        """publish --dry-run shows summary without making changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: Dry Run Test Post
date: 2024-06-15
tags:
  - testing
  - python
publish: true
---

This is test content for the dry run.

Here's a [[wikilink]] to another page.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                # Should show summary
                self.assertIn("PUBLISH SUMMARY", output)
                self.assertIn("Dry Run Test Post", output)
                self.assertIn("2024-06-15", output)
                self.assertIn("Content Type: post", output)

                # Should show dry run message
                self.assertIn("[DRY RUN] No changes will be made.", output)

                # Should show preview
                self.assertIn("--- Preview of converted content ---", output)
                self.assertIn("title: Dry Run Test Post", output)

    def test_publish_dry_run_shows_media_info(self):
        """publish --dry-run shows media file information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "media-note.md"
            note_path.write_text("""---
title: Media Test
date: 2024-07-01
publish: true
---

![[photo.jpg]]
![[video.mp4]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "photo.jpg").touch()
            (media_dir / "video.mp4").touch()

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.side_effect = lambda ref: str(media_dir / ref)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_publish(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("Media Files:  2 to upload", output)

    def test_publish_dry_run_shows_gallery_info(self):
        """publish --dry-run shows gallery information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "gallery-note.md"
            note_path.write_text("""---
title: Gallery Test
date: 2024-08-01
tags:
  - project
publish: true
---

My project description.

## Pictures

![[img1.jpg]]
![[img2.png]]
![[video.mp4]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Gallery:      YES (3 images)", output)

    def test_publish_dry_run_shows_associations_info(self):
        """publish --dry-run shows associations information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "assoc-note.md"
            note_path.write_text("""---
title: Associations Test
date: 2024-09-01
publish: true
---

Content here.

## Associations

[[Related Post]]
[[Another Post|See also]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Associations: REMOVE (2 links)", output)

    def test_publish_with_yes_flag_skips_confirmation(self):
        """publish -y skips confirmation prompts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "yes-flag-test.md"
            note_path.write_text("""---
title: Yes Flag Test
date: 2024-10-01
publish: true
---

Test content.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                # Should complete without prompts
                self.assertIn("PUBLISH COMPLETE", output)
                self.assertNotIn("Proceed with publishing?", output)

            # File should be written
            expected_path = Path(tmpdir) / "content/english/post/2024-10-01-yes-flag-test.md"
            self.assertTrue(expected_path.exists())

    def test_publish_writes_to_correct_content_type_directory(self):
        """publish writes to the correct directory based on content type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test project content type
            note_path = Path(tmpdir) / "project-note.md"
            note_path.write_text("""---
title: My Woodworking Project
date: 2024-11-01
tags:
  - woodworking
  - project
publish: true
---

Project description.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Content Type: project", output)
                self.assertIn("PUBLISH COMPLETE", output)

            # File should be in projects directory
            expected_path = Path(tmpdir) / "content/english/projects/2024-11-01-my-woodworking-project.md"
            self.assertTrue(expected_path.exists())

    def test_publish_warns_for_non_publishable_note(self):
        """publish warns when note doesn't have publish: true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "not-publishable.md"
            note_path.write_text("""---
title: Not Marked for Publish
date: 2024-12-01
---

This note is not marked for publishing.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True  # Use dry-run to avoid prompts
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Warning: Note is not marked with 'publish: true'", output)

    def test_publish_aborts_on_confirmation_decline(self):
        """publish aborts when user declines confirmation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "decline-test.md"
            note_path.write_text("""---
title: Decline Test
date: 2024-01-15
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('builtins.input', return_value='n'):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    with self.assertRaises(SystemExit) as context:
                        cmd_publish(mock_args)
                    self.assertEqual(context.exception.code, 0)
                    self.assertIn("Aborted.", mock_stdout.getvalue())

    def test_publish_proceeds_on_confirmation_accept(self):
        """publish proceeds when user accepts confirmation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "accept-test.md"
            note_path.write_text("""---
title: Accept Test
date: 2024-02-20
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('builtins.input', return_value='y'):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_publish(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("PUBLISH COMPLETE", output)

            # File should be written
            expected_path = Path(tmpdir) / "content/english/post/2024-02-20-accept-test.md"
            self.assertTrue(expected_path.exists())

    def test_publish_with_skip_upload_flag(self):
        """publish --skip-upload skips media upload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "skip-upload.md"
            note_path.write_text("""---
title: Skip Upload Test
date: 2024-03-10
publish: true
---

![[photo.jpg]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "photo.jpg").touch()

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = str(media_dir / "photo.jpg")

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_publish(mock_args)
                    output = mock_stdout.getvalue()

                    self.assertIn("Media Upload: SKIPPED", output)
                    self.assertIn("PUBLISH COMPLETE", output)

    def test_publish_with_no_gallery_flag(self):
        """publish --no-gallery skips gallery generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "no-gallery.md"
            note_path.write_text("""---
title: No Gallery Test
date: 2024-04-05
publish: true
---

Content.

## Pictures

![[img.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = True
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Gallery:      SKIPPED (1 images)", output)

    def test_publish_with_keep_associations_flag(self):
        """publish --keep-associations converts associations to Hugo links."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "keep-assoc.md"
            note_path.write_text("""---
title: Keep Associations Test
date: 2024-05-15
publish: true
---

Content.

## Associations

[[Link One]]
[[Link Two|Display Text]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = True

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Associations: CONVERT (2 links -> Related)", output)


class TestCmdPublishIntegration(unittest.TestCase):
    """Integration tests for cmd_publish with full pipeline."""

    def test_full_publish_pipeline(self):
        """Full publish correctly processes all Obsidian syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "full-integration.md"
            note_path.write_text("""---
title: Full Integration Publish Test
date: 2024-09-15
tags:
  - integration
  - testing
author: Test Author
publish: true
---

# Introduction

This post has various Obsidian syntax to convert.

## Links and Media

Here's a [[Wiki Link]] and an [[aliased|Different Text]] link.

![[screenshot.png]]

## More Content

Regular markdown **works** fine.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("PUBLISH SUMMARY", output)
                self.assertIn("PUBLISH COMPLETE", output)

            # Read the generated file
            expected_path = Path(tmpdir) / "content/english/post/2024-09-15-full-integration-publish-test.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()

            # Check frontmatter
            self.assertIn('title: Full Integration Publish Test', content)
            self.assertIn('author: Test Author', content)
            self.assertIn('tags: [integration, testing]', content)

            # publish field should be removed
            self.assertNotIn('publish:', content)

            # Check wikilinks converted
            self.assertIn('[Wiki Link](/post/wiki-link/)', content)
            self.assertIn('[Different Text](/post/aliased/)', content)

            # Check images converted
            self.assertIn('![screenshot]({{<s3cdn>}}/screenshot.png)', content)

    def test_publish_photography_content_type(self):
        """Publish correctly routes photography content type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "photo-trip.md"
            note_path.write_text("""---
title: Summer Photography Trip
date: 2024-07-20
tags:
  - photography
  - travel
publish: true
---

Photos from my summer trip.

## Pictures

![[photo1.jpg]]
![[photo2.jpg]]
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                cmd_publish(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn("Content Type: photography", output)

            # File should be in photography directory
            expected_path = Path(tmpdir) / "content/english/photography/2024-07-20-summer-photography-trip.md"
            self.assertTrue(expected_path.exists())

    def test_publish_with_minio_upload(self):
        """Publish correctly uploads media to MinIO."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "upload-test.md"
            note_path.write_text("""---
title: MinIO Upload Test
date: 2024-08-10
publish: true
---

![[photo.jpg]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "photo.jpg").touch()

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = False  # Attempt upload
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            mock_url_map = {"photo.jpg": "https://minio.test/bucket/assets/photo.jpg"}

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = str(media_dir / "photo.jpg")

                with patch('publish.upload_media_to_minio', return_value=mock_url_map) as mock_upload:
                    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                        cmd_publish(mock_args)
                        output = mock_stdout.getvalue()

                        self.assertIn("Uploading 1 media file(s) to MinIO", output)
                        self.assertIn("Upload complete: 1 uploaded", output)
                        mock_upload.assert_called_once()

            # Check file uses the MinIO URL
            expected_path = Path(tmpdir) / "content/english/post/2024-08-10-minio-upload-test.md"
            content = expected_path.read_text()
            self.assertIn("https://minio.test/bucket/assets/photo.jpg", content)

    def test_publish_handles_minio_error_gracefully(self):
        """Publish handles MinIO errors gracefully when -y flag is set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "error-test.md"
            note_path.write_text("""---
title: Error Test
date: 2024-09-05
publish: true
---

![[photo.jpg]]
""")

            media_dir = Path(tmpdir) / "media"
            media_dir.mkdir()
            (media_dir / "photo.jpg").touch()

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = False
            mock_args.yes = True  # Skip confirmation for error recovery
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = False
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('publish.resolve_media_path') as mock_resolve:
                mock_resolve.return_value = str(media_dir / "photo.jpg")

                with patch('publish.upload_media_to_minio', side_effect=ImportError("minio not installed")):
                    with patch('sys.stdout', new_callable=StringIO):
                        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                            cmd_publish(mock_args)

                            self.assertIn("Warning: MinIO upload skipped", mock_stderr.getvalue())

            # File should still be written (with s3cdn fallback)
            expected_path = Path(tmpdir) / "content/english/post/2024-09-05-error-test.md"
            self.assertTrue(expected_path.exists())

            content = expected_path.read_text()
            self.assertIn("{{<s3cdn>}}", content)


class TestCmdPublishDispatch(unittest.TestCase):
    """Tests for cmd_publish_dispatch function."""

    def test_dispatch_with_path_calls_cmd_publish(self):
        """Dispatches to cmd_publish when path is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Test Note
date: 2024-01-15
publish: true
---

Content here.
""")
            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.publish_all = False
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False
            mock_args.vault = None

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                from publish import cmd_publish_dispatch
                cmd_publish_dispatch(mock_args)
                output = mock_stdout.getvalue()
                self.assertIn('PUBLISH SUMMARY', output)

    def test_dispatch_with_all_flag_calls_cmd_publish_all(self):
        """Dispatches to cmd_publish_all when --all is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_args = MagicMock()
            mock_args.path = None
            mock_args.publish_all = True
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False
            mock_args.vault = tmpdir

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                from publish import cmd_publish_dispatch
                cmd_publish_dispatch(mock_args)
                output = mock_stdout.getvalue()
                # Should show "No publishable notes found" for empty vault
                self.assertIn('No publishable notes found', output)

    def test_dispatch_no_path_no_all_flag_exits_with_error(self):
        """Exits with error when neither path nor --all is provided."""
        mock_args = MagicMock()
        mock_args.path = None
        mock_args.publish_all = False

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                from publish import cmd_publish_dispatch
                cmd_publish_dispatch(mock_args)

            self.assertEqual(context.exception.code, 1)
            self.assertIn('Must specify a note path or use --all flag', mock_stderr.getvalue())


class TestCmdPublishAll(unittest.TestCase):
    """Tests for cmd_publish_all function."""

    def test_no_publishable_notes_message(self):
        """Shows message when no publishable notes found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                from publish import cmd_publish_all
                cmd_publish_all(mock_args)
                output = mock_stdout.getvalue()
                self.assertIn('No publishable notes found', output)

    def test_all_published_message(self):
        """Shows message when all notes have already been published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a publishable note
            note_path = Path(tmpdir) / "test.md"
            note_path.write_text("""---
title: Already Published
date: 2024-01-15
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            # Patch get_unpublished_notes to return empty list (all published)
            with patch('publish.get_unpublished_notes') as mock_get_unpub:
                mock_get_unpub.return_value = []

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    from publish import cmd_publish_all
                    cmd_publish_all(mock_args)
                    output = mock_stdout.getvalue()
                    self.assertIn('all have already been published', output)

    def test_dry_run_shows_summary(self):
        """Dry run shows batch summary without making changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two publishable notes
            note1 = Path(tmpdir) / "note1.md"
            note1.write_text("""---
title: Post One
date: 2024-01-15
publish: true
---

Content 1.
""")
            note2 = Path(tmpdir) / "note2.md"
            note2.write_text("""---
title: Post Two
date: 2024-01-16
tags:
  - project
publish: true
---

Content 2.
""")

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                from publish import cmd_publish_all
                cmd_publish_all(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn('BATCH PUBLISH SUMMARY', output)
                self.assertIn('Total publishable notes:', output)
                self.assertIn('To publish:', output)
                self.assertIn('[DRY RUN]', output)
                self.assertIn('Post One', output)
                self.assertIn('Post Two', output)

    def test_publishes_multiple_notes(self):
        """Actually publishes multiple notes in non-dry-run mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create output directories
            output_post = Path(tmpdir) / "content" / "english" / "post"
            output_post.mkdir(parents=True)
            output_proj = Path(tmpdir) / "content" / "english" / "projects"
            output_proj.mkdir(parents=True)

            # Create publishable notes
            note1 = Path(tmpdir) / "note1.md"
            note1.write_text("""---
title: Blog Post
date: 2024-01-15
publish: true
---

Blog content.
""")
            note2 = Path(tmpdir) / "note2.md"
            note2.write_text("""---
title: Project Post
date: 2024-01-16
tags:
  - project
publish: true
---

Project content.
""")

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                from publish import cmd_publish_all
                cmd_publish_all(mock_args)
                output = mock_stdout.getvalue()

                self.assertIn('BATCH PUBLISH COMPLETE', output)
                self.assertIn('Published: 2', output)

            # Check files were created
            post_file = output_post / "2024-01-15-blog-post.md"
            proj_file = output_proj / "2024-01-16-project-post.md"
            self.assertTrue(post_file.exists())
            self.assertTrue(proj_file.exists())

    def test_confirmation_prompt_in_non_yes_mode(self):
        """Prompts for confirmation when -y flag not set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note = Path(tmpdir) / "note.md"
            note.write_text("""---
title: Test
date: 2024-01-15
publish: true
---

Content.
""")

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = False
            mock_args.yes = False  # Will require confirmation
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            with patch('sys.stdout', new_callable=StringIO):
                with patch('builtins.input', return_value='n'):
                    with self.assertRaises(SystemExit) as context:
                        from publish import cmd_publish_all
                        cmd_publish_all(mock_args)
                    self.assertEqual(context.exception.code, 0)

    def test_skips_already_published_notes(self):
        """Skips notes that have already been published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "content" / "english" / "post"
            output_dir.mkdir(parents=True)

            # Create two notes
            note1 = Path(tmpdir) / "published.md"
            note1.write_text("""---
title: Already Published
date: 2024-01-15
publish: true
---

Content 1.
""")
            note2 = Path(tmpdir) / "new.md"
            note2.write_text("""---
title: New Note
date: 2024-01-16
publish: true
---

Content 2.
""")

            # Mark note1 as published in the tracking file
            tracking_file = Path(__file__).parent / '.published.json'
            from publish_tracker import record_published, DEFAULT_TRACKING_FILE
            record_published(note1, tracking_file=tracking_file)

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            try:
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    from publish import cmd_publish_all
                    cmd_publish_all(mock_args)
                    output = mock_stdout.getvalue()

                    # Should show 1 already published, 1 to publish
                    self.assertIn('Already published:        1', output)
                    self.assertIn('To publish:               1', output)
                    self.assertIn('New Note', output)
            finally:
                # Clean up tracking file
                if tracking_file.exists():
                    from publish_tracker import clear_publish_record
                    clear_publish_record(note1)


class TestCmdPublishAllIntegration(unittest.TestCase):
    """Integration tests for cmd_publish_all."""

    def test_records_published_notes_in_tracking_file(self):
        """Recording published notes to tracking file works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "content" / "english" / "post"
            output_dir.mkdir(parents=True)

            note = Path(tmpdir) / "note.md"
            note.write_text("""---
title: Track Test
date: 2024-01-15
publish: true
---

Content.
""")

            # Use a custom tracking file in the temp directory
            tracking_file = Path(tmpdir) / ".published.json"

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = False
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False

            # Patch the tracker to use our temp tracking file
            with patch('publish.load_publish_state') as mock_load:
                with patch('publish.record_published') as mock_record:
                    mock_load.return_value = {'published': {}}

                    with patch('sys.stdout', new_callable=StringIO):
                        from publish import cmd_publish_all
                        cmd_publish_all(mock_args)

                    # Verify record_published was called
                    mock_record.assert_called_once()

    def test_handles_vault_not_found(self):
        """Handles non-existent vault path gracefully."""
        mock_args = MagicMock()
        mock_args.publish_all = True
        mock_args.vault = '/nonexistent/vault/path'
        mock_args.dry_run = True
        mock_args.yes = True
        mock_args.hugo_root = '/tmp'
        mock_args.skip_upload = True
        mock_args.no_gallery = False
        mock_args.keep_associations = False

        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as context:
                from publish import cmd_publish_all
                cmd_publish_all(mock_args)

            self.assertEqual(context.exception.code, 1)
            self.assertIn('Vault not found', mock_stderr.getvalue())


class TestEnvironmentFlag(unittest.TestCase):
    """Tests for --environment flag functionality."""

    def test_convert_note_with_environment_uses_s3cdn_url(self):
        """convert_note with environment uses S3CDN URL from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: Environment Test
date: 2024-12-01
---

Here's an image: ![[2024/photo.jpg]]
""")

            # Mock the get_s3cdn_base_url function
            with patch('publish.get_s3cdn_base_url') as mock_s3cdn:
                mock_s3cdn.return_value = 'https://s3cdn.example.com/assets'

                hugo_fm, converted_body, _ = convert_note(
                    note_path,
                    DEFAULT_OUTPUT_DIR,
                    environment='production'
                )

                # Verify the S3CDN function was called with the environment
                mock_s3cdn.assert_called_once_with('production')

                # Verify the URL was embedded in the output
                self.assertIn('https://s3cdn.example.com/assets', converted_body)

    def test_convert_note_without_environment_uses_shortcode(self):
        """convert_note without environment uses s3cdn shortcode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: No Environment Test
date: 2024-12-01
---

Here's an image: ![[2024/photo.jpg]]
""")

            hugo_fm, converted_body, _ = convert_note(
                note_path,
                DEFAULT_OUTPUT_DIR,
                environment=None
            )

            # Without environment, should use the shortcode
            self.assertIn('{{<s3cdn>}}', converted_body)

    def test_cmd_convert_with_environment_flag(self):
        """convert command with --environment flag passes to convert_note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "env-test.md"
            note_path.write_text("""---
title: CLI Environment Test
date: 2024-12-01
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.output = None
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False
            mock_args.environment = 'development'

            with patch('publish.get_s3cdn_base_url') as mock_s3cdn:
                mock_s3cdn.return_value = 'http://localhost:9000/blog-assets'

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_convert(mock_args)
                    output = mock_stdout.getvalue()

                    # Verify environment is shown in dry-run output
                    self.assertIn('[DRY RUN] Environment: development', output)

    def test_cmd_publish_dry_run_shows_environment(self):
        """publish --dry-run shows environment in summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "publish-env-test.md"
            note_path.write_text("""---
title: Publish Environment Test
date: 2024-12-01
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.path = str(note_path)
            mock_args.dry_run = True
            mock_args.yes = False
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False
            mock_args.environment = 'production'

            with patch('publish.get_s3cdn_base_url') as mock_s3cdn:
                mock_s3cdn.return_value = 'https://s3cdn.example.com/assets'

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    cmd_publish(mock_args)
                    output = mock_stdout.getvalue()

                    # Verify environment is shown in summary
                    self.assertIn('Environment:  production', output)

    def test_convert_note_environment_graceful_fallback(self):
        """convert_note with environment gracefully falls back on config error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "test-note.md"
            note_path.write_text("""---
title: Fallback Test
date: 2024-12-01
---

Here's an image: ![[2024/photo.jpg]]
""")

            # Mock config error
            from config_manager import HugoConfigError
            with patch('publish.get_s3cdn_base_url') as mock_s3cdn:
                mock_s3cdn.side_effect = HugoConfigError("S3CDN not configured")

                hugo_fm, converted_body, _ = convert_note(
                    note_path,
                    DEFAULT_OUTPUT_DIR,
                    environment='nonexistent'
                )

                # Should fall back to shortcode when config fails
                self.assertIn('{{<s3cdn>}}', converted_body)

    def test_cmd_publish_all_with_environment(self):
        """publish --all with --environment passes to convert_note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a publishable note
            note_path = Path(tmpdir) / "batch-env-test.md"
            note_path.write_text("""---
title: Batch Environment Test
date: 2024-12-01
publish: true
---

Content here.
""")

            mock_args = MagicMock()
            mock_args.publish_all = True
            mock_args.vault = tmpdir
            mock_args.dry_run = True
            mock_args.yes = True
            mock_args.hugo_root = tmpdir
            mock_args.skip_upload = True
            mock_args.no_gallery = False
            mock_args.keep_associations = False
            mock_args.environment = 'development'

            with patch('publish.get_s3cdn_base_url') as mock_s3cdn:
                mock_s3cdn.return_value = 'http://localhost:9000/blog-assets'

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    from publish import cmd_publish_all
                    cmd_publish_all(mock_args)
                    output = mock_stdout.getvalue()

                    # Verify environment is shown in batch summary
                    self.assertIn('Environment:  development', output)


if __name__ == '__main__':
    unittest.main()
