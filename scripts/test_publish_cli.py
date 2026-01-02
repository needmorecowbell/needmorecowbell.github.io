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
    cmd_scan
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


if __name__ == '__main__':
    unittest.main()
