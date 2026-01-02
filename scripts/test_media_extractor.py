#!/usr/bin/env python3
"""
Tests for the media_extractor module.

Run with: python test_media_extractor.py
Or with pytest: pytest test_media_extractor.py -v
"""

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from media_extractor import (
    find_media_references,
    resolve_media_path,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DEFAULT_MEDIA_BASE,
)


class TestFindMediaReferences(unittest.TestCase):
    """Tests for the find_media_references function."""

    def test_finds_single_image(self):
        """Should find a single embedded image."""
        content = "Here is an image: ![[photos/sunset.jpg]]"
        result = find_media_references(content)
        self.assertEqual(result, ['photos/sunset.jpg'])

    def test_finds_multiple_images(self):
        """Should find multiple embedded images."""
        content = """
        First image: ![[2021/06/photo1.jpg]]
        Second image: ![[2022/01/photo2.png]]
        Third image: ![[gallery/image.webp]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['2021/06/photo1.jpg', '2022/01/photo2.png', 'gallery/image.webp'])

    def test_finds_videos(self):
        """Should find embedded videos."""
        content = """
        Check out this video: ![[videos/demo.mp4]]
        And this one: ![[clips/example.webm]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['videos/demo.mp4', 'clips/example.webm'])

    def test_finds_audio_files(self):
        """Should find embedded audio files."""
        content = """
        Listen to this: ![[audio/song.mp3]]
        Also this: ![[music/track.wav]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['audio/song.mp3', 'music/track.wav'])

    def test_finds_mixed_media_types(self):
        """Should find images, videos, and audio in the same content."""
        content = """
        Image: ![[photos/pic.jpg]]
        Video: ![[videos/clip.mp4]]
        Audio: ![[music/song.mp3]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['photos/pic.jpg', 'videos/clip.mp4', 'music/song.mp3'])

    def test_ignores_wikilinks(self):
        """Should not match regular wikilinks (without !)."""
        content = """
        Link to page: [[Some Page]]
        Image: ![[photo.jpg]]
        Another link: [[Another Page|Display Text]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['photo.jpg'])

    def test_ignores_non_media_extensions(self):
        """Should not match files with non-media extensions."""
        content = """
        Document: ![[docs/file.pdf]]
        Text: ![[notes/readme.txt]]
        Code: ![[scripts/app.py]]
        Image: ![[photo.jpg]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['photo.jpg'])

    def test_handles_whitespace_in_embed(self):
        """Should handle whitespace inside the embed syntax."""
        content = "![[  photos/image.jpg  ]]"
        result = find_media_references(content)
        self.assertEqual(result, ['photos/image.jpg'])

    def test_handles_simple_filename(self):
        """Should handle filenames without paths."""
        content = "![[sunset.jpg]]"
        result = find_media_references(content)
        self.assertEqual(result, ['sunset.jpg'])

    def test_handles_deep_paths(self):
        """Should handle deeply nested paths."""
        content = "![[media/2021/vacation/hawaii/beach/sunset.jpg]]"
        result = find_media_references(content)
        self.assertEqual(result, ['media/2021/vacation/hawaii/beach/sunset.jpg'])

    def test_case_insensitive_extensions(self):
        """Should match extensions case-insensitively."""
        content = """
        ![[photo.JPG]]
        ![[image.PNG]]
        ![[video.MP4]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['photo.JPG', 'image.PNG', 'video.MP4'])

    def test_empty_content(self):
        """Should return empty list for empty content."""
        result = find_media_references("")
        self.assertEqual(result, [])

    def test_no_embeds(self):
        """Should return empty list when no embeds are present."""
        content = "This is just plain text without any embeds."
        result = find_media_references(content)
        self.assertEqual(result, [])

    def test_preserves_order(self):
        """Should preserve the order of media references as they appear."""
        content = """
        ![[c.jpg]]
        ![[a.png]]
        ![[b.mp4]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['c.jpg', 'a.png', 'b.mp4'])

    def test_handles_filenames_with_special_chars(self):
        """Should handle filenames with hyphens and underscores."""
        content = """
        ![[my-vacation-photo.jpg]]
        ![[screen_shot_2021.png]]
        """
        result = find_media_references(content)
        self.assertEqual(result, ['my-vacation-photo.jpg', 'screen_shot_2021.png'])

    def test_all_image_extensions(self):
        """Should recognize all supported image extensions."""
        for ext in IMAGE_EXTENSIONS:
            content = f"![[test.{ext}]]"
            result = find_media_references(content)
            self.assertEqual(result, [f'test.{ext}'], f"Failed for extension: {ext}")

    def test_all_video_extensions(self):
        """Should recognize all supported video extensions."""
        for ext in VIDEO_EXTENSIONS:
            content = f"![[test.{ext}]]"
            result = find_media_references(content)
            self.assertEqual(result, [f'test.{ext}'], f"Failed for extension: {ext}")

    def test_all_audio_extensions(self):
        """Should recognize all supported audio extensions."""
        for ext in AUDIO_EXTENSIONS:
            content = f"![[test.{ext}]]"
            result = find_media_references(content)
            self.assertEqual(result, [f'test.{ext}'], f"Failed for extension: {ext}")

    def test_realistic_obsidian_content(self):
        """Should correctly parse realistic Obsidian note content."""
        content = """---
title: My Vacation
date: 2021-06-15
---

# My Trip to Hawaii

Last summer I went on an amazing trip!

![[2021/06/beach-sunset.jpg]]

The beach was incredible. Here's a video:

![[2021/06/waves.mp4]]

I also recorded some sounds:

![[2021/06/ocean-sounds.mp3]]

Check out my notes on [[Travel Tips]] for more info.

![[2021/06/final-group-photo.png]]
"""
        result = find_media_references(content)
        self.assertEqual(result, [
            '2021/06/beach-sunset.jpg',
            '2021/06/waves.mp4',
            '2021/06/ocean-sounds.mp3',
            '2021/06/final-group-photo.png'
        ])


class TestResolveMediaPath(unittest.TestCase):
    """Tests for the resolve_media_path function."""

    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.media_base = Path(self.temp_dir)

        # Create test directory structure
        (self.media_base / "2021" / "06").mkdir(parents=True)
        (self.media_base / "photos" / "vacation").mkdir(parents=True)

        # Create test files
        (self.media_base / "2021" / "06" / "image.jpg").touch()
        (self.media_base / "2021" / "06" / "video.mp4").touch()
        (self.media_base / "photos" / "vacation" / "sunset.png").touch()
        (self.media_base / "simple.jpg").touch()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_resolves_simple_path(self):
        """Should resolve a simple media reference to full path."""
        result = resolve_media_path("simple.jpg", media_base=self.media_base)
        expected = str(self.media_base / "simple.jpg")
        self.assertEqual(result, expected)

    def test_resolves_nested_path(self):
        """Should resolve nested path references."""
        result = resolve_media_path("2021/06/image.jpg", media_base=self.media_base)
        expected = str(self.media_base / "2021" / "06" / "image.jpg")
        self.assertEqual(result, expected)

    def test_resolves_deeply_nested_path(self):
        """Should resolve deeply nested path references."""
        result = resolve_media_path("photos/vacation/sunset.png", media_base=self.media_base)
        expected = str(self.media_base / "photos" / "vacation" / "sunset.png")
        self.assertEqual(result, expected)

    def test_strips_leading_slash(self):
        """Should strip leading slashes from reference."""
        result = resolve_media_path("/2021/06/image.jpg", media_base=self.media_base)
        expected = str(self.media_base / "2021" / "06" / "image.jpg")
        self.assertEqual(result, expected)

    def test_returns_none_for_missing_file_with_validation(self):
        """Should return None when file doesn't exist and validation is enabled."""
        result = resolve_media_path("nonexistent.jpg", media_base=self.media_base, validate=True)
        self.assertIsNone(result)

    def test_returns_path_for_missing_file_without_validation(self):
        """Should return path even when file doesn't exist if validation is disabled."""
        result = resolve_media_path("nonexistent.jpg", media_base=self.media_base, validate=False)
        expected = str(self.media_base / "nonexistent.jpg")
        self.assertEqual(result, expected)

    def test_logs_warning_for_missing_file(self):
        """Should log warning when file doesn't exist."""
        with self.assertLogs('media_extractor', level='WARNING') as cm:
            result = resolve_media_path("missing.jpg", media_base=self.media_base, validate=True)

        self.assertIsNone(result)
        self.assertTrue(any("Media file not found" in msg for msg in cm.output))
        self.assertTrue(any("missing.jpg" in msg for msg in cm.output))

    def test_returns_none_for_directory(self):
        """Should return None when path is a directory, not a file."""
        with self.assertLogs('media_extractor', level='WARNING') as cm:
            result = resolve_media_path("2021/06", media_base=self.media_base, validate=True)

        self.assertIsNone(result)
        self.assertTrue(any("not a file" in msg for msg in cm.output))

    def test_returns_directory_path_without_validation(self):
        """Should return directory path if validation is disabled."""
        result = resolve_media_path("2021/06", media_base=self.media_base, validate=False)
        expected = str(self.media_base / "2021" / "06")
        self.assertEqual(result, expected)

    def test_uses_default_media_base(self):
        """Should use DEFAULT_MEDIA_BASE when no base is provided."""
        # We can't easily test the actual default path, but we can verify it's used
        self.assertEqual(DEFAULT_MEDIA_BASE, Path.home() / "Notes" / "Media")

    def test_resolves_symlink_in_base_path(self):
        """Should resolve symlinks in the media base path."""
        # Create a symlink to the media base
        symlink_path = Path(self.temp_dir) / "symlink_media"
        actual_media = Path(self.temp_dir) / "actual_media"
        actual_media.mkdir()
        (actual_media / "test.jpg").touch()
        symlink_path.symlink_to(actual_media)

        result = resolve_media_path("test.jpg", media_base=symlink_path)
        # The result should be the resolved (actual) path
        expected = str(actual_media / "test.jpg")
        self.assertEqual(result, expected)

    def test_handles_multiple_leading_slashes(self):
        """Should handle multiple leading slashes."""
        result = resolve_media_path("///2021/06/image.jpg", media_base=self.media_base)
        expected = str(self.media_base / "2021" / "06" / "image.jpg")
        self.assertEqual(result, expected)

    def test_validation_default_is_true(self):
        """Should validate by default (validate=True)."""
        result = resolve_media_path("nonexistent.jpg", media_base=self.media_base)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
