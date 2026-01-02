#!/usr/bin/env python3
"""
Tests for the publish_tracker module.

Tests cover file hashing, publish state tracking, and filtering of unpublished notes.
"""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from publish_tracker import (
    compute_file_hash,
    load_publish_state,
    save_publish_state,
    is_note_published,
    record_published,
    get_unpublished_notes,
    clear_publish_record,
    get_publish_info,
    DEFAULT_TRACKING_FILE,
)


class TestComputeFileHash(unittest.TestCase):
    """Tests for compute_file_hash function."""

    def test_computes_sha256_hash(self):
        """Returns SHA-256 hash of file contents."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("Hello, World!")
            f.flush()
            file_path = Path(f.name)

        try:
            result = compute_file_hash(file_path)
            # SHA-256 hash of "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            self.assertEqual(result, expected)
        finally:
            file_path.unlink()

    def test_different_content_different_hash(self):
        """Different file contents produce different hashes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.md"
            file2 = Path(tmpdir) / "file2.md"

            file1.write_text("Content A")
            file2.write_text("Content B")

            hash1 = compute_file_hash(file1)
            hash2 = compute_file_hash(file2)

            self.assertNotEqual(hash1, hash2)

    def test_same_content_same_hash(self):
        """Same file contents produce same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.md"
            file2 = Path(tmpdir) / "file2.md"

            file1.write_text("Same content")
            file2.write_text("Same content")

            hash1 = compute_file_hash(file1)
            hash2 = compute_file_hash(file2)

            self.assertEqual(hash1, hash2)

    def test_file_not_found_raises_error(self):
        """Raises FileNotFoundError for non-existent file."""
        with self.assertRaises(FileNotFoundError):
            compute_file_hash(Path("/nonexistent/file.md"))

    def test_handles_binary_content(self):
        """Can hash files with binary content."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            f.flush()
            file_path = Path(f.name)

        try:
            result = compute_file_hash(file_path)
            self.assertEqual(len(result), 64)  # SHA-256 hex length
        finally:
            file_path.unlink()

    def test_handles_empty_file(self):
        """Can hash empty files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            file_path = Path(f.name)

        try:
            result = compute_file_hash(file_path)
            # SHA-256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            self.assertEqual(result, expected)
        finally:
            file_path.unlink()


class TestLoadPublishState(unittest.TestCase):
    """Tests for load_publish_state function."""

    def test_returns_empty_state_for_nonexistent_file(self):
        """Returns empty state when tracking file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / "nonexistent.json"
            result = load_publish_state(tracking_file)
            self.assertEqual(result, {'published': {}})

    def test_loads_existing_state(self):
        """Loads and parses existing tracking file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            state = {
                'published': {
                    '/path/to/note.md': {
                        'hash': 'abc123',
                        'published_at': '2024-01-15T10:30:00'
                    }
                }
            }
            tracking_file.write_text(json.dumps(state))

            result = load_publish_state(tracking_file)
            self.assertEqual(result, state)

    def test_handles_corrupted_json(self):
        """Returns empty state for corrupted JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            tracking_file.write_text("not valid json {{{")

            result = load_publish_state(tracking_file)
            self.assertEqual(result, {'published': {}})

    def test_adds_published_key_if_missing(self):
        """Adds 'published' key if not present in file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            tracking_file.write_text('{"other_key": "value"}')

            result = load_publish_state(tracking_file)
            self.assertIn('published', result)
            self.assertEqual(result['published'], {})


class TestSavePublishState(unittest.TestCase):
    """Tests for save_publish_state function."""

    def test_saves_state_to_file(self):
        """Saves state dict to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            state = {
                'published': {
                    '/path/to/note.md': {
                        'hash': 'abc123'
                    }
                }
            }

            save_publish_state(state, tracking_file)

            content = tracking_file.read_text()
            loaded = json.loads(content)
            self.assertEqual(loaded, state)

    def test_creates_parent_directory(self):
        """Creates parent directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / "subdir" / ".published.json"
            state = {'published': {}}

            save_publish_state(state, tracking_file)

            self.assertTrue(tracking_file.exists())

    def test_overwrites_existing_file(self):
        """Overwrites existing tracking file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            tracking_file.write_text('{"old": "data"}')

            new_state = {'published': {'new': 'data'}}
            save_publish_state(new_state, tracking_file)

            content = tracking_file.read_text()
            loaded = json.loads(content)
            self.assertEqual(loaded, new_state)


class TestIsNotePublished(unittest.TestCase):
    """Tests for is_note_published function."""

    def test_returns_false_for_untracked_note(self):
        """Returns False for notes not in tracking file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Note content")

            result = is_note_published(note_path, tracking_file)
            self.assertFalse(result)

    def test_returns_true_for_unchanged_published_note(self):
        """Returns True for published notes with matching hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Note content")

            # Get actual hash and save state
            note_hash = compute_file_hash(note_path)
            state = {
                'published': {
                    str(note_path.resolve()): {
                        'hash': note_hash,
                        'published_at': '2024-01-15T10:30:00'
                    }
                }
            }
            tracking_file.write_text(json.dumps(state))

            result = is_note_published(note_path, tracking_file)
            self.assertTrue(result)

    def test_returns_false_for_modified_published_note(self):
        """Returns False for published notes with changed content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Original content")

            # Save state with old hash
            state = {
                'published': {
                    str(note_path.resolve()): {
                        'hash': 'old_hash_value',
                        'published_at': '2024-01-15T10:30:00'
                    }
                }
            }
            tracking_file.write_text(json.dumps(state))

            result = is_note_published(note_path, tracking_file)
            self.assertFalse(result)

    def test_returns_false_for_deleted_note(self):
        """Returns False for notes that were published but no longer exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "deleted.md"

            state = {
                'published': {
                    str(note_path.resolve()): {
                        'hash': 'some_hash',
                        'published_at': '2024-01-15T10:30:00'
                    }
                }
            }
            tracking_file.write_text(json.dumps(state))

            # Note doesn't exist
            result = is_note_published(note_path, tracking_file)
            self.assertFalse(result)

    def test_uses_provided_state(self):
        """Uses provided state dict instead of loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Note content")

            note_hash = compute_file_hash(note_path)
            state = {
                'published': {
                    str(note_path.resolve()): {
                        'hash': note_hash
                    }
                }
            }

            # No tracking file exists, but we provide state
            result = is_note_published(note_path, state=state)
            self.assertTrue(result)


class TestRecordPublished(unittest.TestCase):
    """Tests for record_published function."""

    def test_records_new_publish(self):
        """Records a newly published note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Note content")

            result = record_published(note_path, tracking_file=tracking_file)

            self.assertIn('published', result)
            note_key = str(note_path.resolve())
            self.assertIn(note_key, result['published'])
            self.assertIn('hash', result['published'][note_key])
            self.assertIn('published_at', result['published'][note_key])

    def test_saves_to_file(self):
        """Saves updated state to tracking file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Note content")

            record_published(note_path, tracking_file=tracking_file)

            self.assertTrue(tracking_file.exists())
            content = tracking_file.read_text()
            loaded = json.loads(content)
            self.assertIn('published', loaded)

    def test_includes_target_path(self):
        """Records target path when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            target_path = Path(tmpdir) / "output" / "note.md"
            note_path.write_text("Note content")

            result = record_published(
                note_path,
                target_path=target_path,
                tracking_file=tracking_file
            )

            note_key = str(note_path.resolve())
            self.assertEqual(
                result['published'][note_key]['target'],
                str(target_path)
            )

    def test_updates_existing_record(self):
        """Updates record when note is re-published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note_path = Path(tmpdir) / "note.md"
            note_path.write_text("Original content")

            # First publish
            record_published(note_path, tracking_file=tracking_file)

            # Modify and re-publish
            note_path.write_text("Modified content")
            result = record_published(note_path, tracking_file=tracking_file)

            # Should have updated hash
            note_key = str(note_path.resolve())
            new_hash = compute_file_hash(note_path)
            self.assertEqual(result['published'][note_key]['hash'], new_hash)

    def test_preserves_other_records(self):
        """Preserves existing records for other notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note1 = Path(tmpdir) / "note1.md"
            note2 = Path(tmpdir) / "note2.md"
            note1.write_text("Note 1")
            note2.write_text("Note 2")

            record_published(note1, tracking_file=tracking_file)
            record_published(note2, tracking_file=tracking_file)

            # Load and check both are present
            state = load_publish_state(tracking_file)
            self.assertEqual(len(state['published']), 2)


class TestGetUnpublishedNotes(unittest.TestCase):
    """Tests for get_unpublished_notes function."""

    def test_returns_all_notes_when_none_published(self):
        """Returns all notes when tracking file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note1 = Path(tmpdir) / "note1.md"
            note2 = Path(tmpdir) / "note2.md"
            note1.write_text("Note 1")
            note2.write_text("Note 2")

            notes = [
                {'path': note1, 'frontmatter': {}},
                {'path': note2, 'frontmatter': {}}
            ]

            result = get_unpublished_notes(notes, tracking_file)
            self.assertEqual(len(result), 2)

    def test_filters_out_published_notes(self):
        """Excludes notes that have been published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note1 = Path(tmpdir) / "note1.md"
            note2 = Path(tmpdir) / "note2.md"
            note1.write_text("Note 1")
            note2.write_text("Note 2")

            # Publish note1
            record_published(note1, tracking_file=tracking_file)

            notes = [
                {'path': note1, 'frontmatter': {}},
                {'path': note2, 'frontmatter': {}}
            ]

            result = get_unpublished_notes(notes, tracking_file)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['path'], note2)

    def test_includes_modified_notes(self):
        """Includes notes that have been modified since publishing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            note.write_text("Original content")

            # Publish
            record_published(note, tracking_file=tracking_file)

            # Modify
            note.write_text("Modified content")

            notes = [{'path': note, 'frontmatter': {}}]

            result = get_unpublished_notes(notes, tracking_file)
            self.assertEqual(len(result), 1)

    def test_returns_empty_when_all_published(self):
        """Returns empty list when all notes are published."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            note.write_text("Content")

            record_published(note, tracking_file=tracking_file)

            notes = [{'path': note, 'frontmatter': {}}]

            result = get_unpublished_notes(notes, tracking_file)
            self.assertEqual(len(result), 0)


class TestClearPublishRecord(unittest.TestCase):
    """Tests for clear_publish_record function."""

    def test_removes_existing_record(self):
        """Removes published record for a note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            note.write_text("Content")

            record_published(note, tracking_file=tracking_file)

            # Clear the record
            result = clear_publish_record(note, tracking_file)
            self.assertTrue(result)

            # Verify it's gone
            self.assertFalse(is_note_published(note, tracking_file))

    def test_returns_false_for_untracked_note(self):
        """Returns False when note wasn't tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            note.write_text("Content")

            result = clear_publish_record(note, tracking_file)
            self.assertFalse(result)

    def test_preserves_other_records(self):
        """Preserves records for other notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note1 = Path(tmpdir) / "note1.md"
            note2 = Path(tmpdir) / "note2.md"
            note1.write_text("Note 1")
            note2.write_text("Note 2")

            record_published(note1, tracking_file=tracking_file)
            record_published(note2, tracking_file=tracking_file)

            # Clear only note1
            clear_publish_record(note1, tracking_file)

            # note2 should still be published
            self.assertTrue(is_note_published(note2, tracking_file))


class TestGetPublishInfo(unittest.TestCase):
    """Tests for get_publish_info function."""

    def test_returns_none_for_untracked_note(self):
        """Returns None for notes not in tracking file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            note.write_text("Content")

            result = get_publish_info(note, tracking_file)
            self.assertIsNone(result)

    def test_returns_info_for_published_note(self):
        """Returns publish info dict for tracked notes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracking_file = Path(tmpdir) / ".published.json"
            note = Path(tmpdir) / "note.md"
            target = Path(tmpdir) / "output.md"
            note.write_text("Content")

            record_published(note, target_path=target, tracking_file=tracking_file)

            result = get_publish_info(note, tracking_file)
            self.assertIsNotNone(result)
            self.assertIn('hash', result)
            self.assertIn('published_at', result)
            self.assertIn('target', result)


if __name__ == '__main__':
    unittest.main()
