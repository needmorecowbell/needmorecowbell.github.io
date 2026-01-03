#!/usr/bin/env python3
"""
Tests for the media_extractor module.

Tests media reference extraction, path resolution, and thumbnail generation.
"""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from media_extractor import (
    find_media_references,
    resolve_media_path,
    generate_thumbnail,
    get_thumbnail_path,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    ALL_MEDIA_EXTENSIONS,
    DEFAULT_MEDIA_BASE,
    DEFAULT_THUMBNAIL_WIDTH,
    THUMBNAIL_SUPPORTED_EXTENSIONS,
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

    def test_all_media_extensions_set(self):
        """Should have ALL_MEDIA_EXTENSIONS as union of all extension sets."""
        expected = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
        self.assertEqual(ALL_MEDIA_EXTENSIONS, expected)

    def test_filenames_with_numbers(self):
        """Should handle filenames that contain numbers."""
        content = "![[IMG_20210615_123456.jpg]]"
        result = find_media_references(content)
        self.assertEqual(result, ['IMG_20210615_123456.jpg'])

    def test_handles_dot_in_path(self):
        """Should handle paths with dots in directory names."""
        content = "![[v1.0/screenshots/demo.png]]"
        result = find_media_references(content)
        self.assertEqual(result, ['v1.0/screenshots/demo.png'])


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

    def test_handles_video_file(self):
        """Should resolve video file paths correctly."""
        result = resolve_media_path("2021/06/video.mp4", media_base=self.media_base)
        expected = str(self.media_base / "2021" / "06" / "video.mp4")
        self.assertEqual(result, expected)

    def test_path_with_spaces_without_validation(self):
        """Should handle paths with spaces when validation is disabled."""
        result = resolve_media_path("my photos/vacation.jpg", media_base=self.media_base, validate=False)
        expected = str(self.media_base / "my photos" / "vacation.jpg")
        self.assertEqual(result, expected)


class TestGenerateThumbnail(unittest.TestCase):
    """Tests for the generate_thumbnail function."""

    def setUp(self):
        """Create a temporary directory with test images."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def _create_test_image(self, filename: str, width: int = 800, height: int = 600, mode: str = 'RGB') -> str:
        """Helper to create a test image with specified dimensions."""
        path = Path(self.temp_dir) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new(mode, (width, height), color='blue')
        img.save(path)
        return str(path)

    def test_generates_thumbnail_with_default_width(self):
        """Should generate a 400px wide thumbnail by default."""
        source = self._create_test_image('test.jpg', 800, 600)
        result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        self.assertTrue(Path(result).exists())

        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)
            # Height should maintain aspect ratio: 400 * (600/800) = 300
            self.assertEqual(thumb.height, 300)

    def test_generates_thumbnail_with_custom_width(self):
        """Should generate thumbnail with specified width."""
        source = self._create_test_image('test.jpg', 1000, 500)
        result = generate_thumbnail(source, width=200)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 200)
            # Height should maintain aspect ratio: 200 * (500/1000) = 100
            self.assertEqual(thumb.height, 100)

    def test_maintains_aspect_ratio(self):
        """Should maintain original aspect ratio in thumbnail."""
        source = self._create_test_image('test.jpg', 1600, 900)  # 16:9 ratio
        result = generate_thumbnail(source, width=400)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)
            self.assertEqual(thumb.height, 225)  # 400 * (9/16) = 225

    def test_default_output_path_has_thumb_suffix(self):
        """Should add _thumb suffix when no output path specified."""
        source = self._create_test_image('photo.jpg', 800, 600)
        result = generate_thumbnail(source)

        expected = str(Path(self.temp_dir) / 'photo_thumb.jpg')
        self.assertEqual(result, expected)

    def test_custom_output_path(self):
        """Should use specified output path."""
        source = self._create_test_image('source.jpg', 800, 600)
        output = str(Path(self.temp_dir) / 'thumbnails' / 'custom.jpg')
        result = generate_thumbnail(source, output_path=output)

        self.assertEqual(result, output)
        self.assertTrue(Path(output).exists())

    def test_creates_output_directory_if_missing(self):
        """Should create output directory structure if it doesn't exist."""
        source = self._create_test_image('source.jpg', 800, 600)
        output = str(Path(self.temp_dir) / 'nested' / 'dirs' / 'thumb.jpg')
        result = generate_thumbnail(source, output_path=output)

        self.assertEqual(result, output)
        self.assertTrue(Path(output).exists())

    def test_returns_none_for_nonexistent_file(self):
        """Should return None when source file doesn't exist."""
        result = generate_thumbnail('/nonexistent/path/image.jpg')
        self.assertIsNone(result)

    def test_returns_none_for_directory(self):
        """Should return None when source is a directory."""
        dir_path = Path(self.temp_dir) / 'subdir'
        dir_path.mkdir()
        result = generate_thumbnail(str(dir_path))
        self.assertIsNone(result)

    def test_returns_none_for_unsupported_format(self):
        """Should return None for unsupported image formats like SVG."""
        svg_path = Path(self.temp_dir) / 'image.svg'
        svg_path.write_text('<svg></svg>')
        result = generate_thumbnail(str(svg_path))
        self.assertIsNone(result)

    def test_returns_none_for_image_smaller_than_target(self):
        """Should return None if image is already smaller than target width."""
        source = self._create_test_image('small.jpg', 300, 200)
        result = generate_thumbnail(source, width=400)
        self.assertIsNone(result)

    def test_returns_none_for_image_equal_to_target(self):
        """Should return None if image width equals target width."""
        source = self._create_test_image('exact.jpg', 400, 300)
        result = generate_thumbnail(source, width=400)
        self.assertIsNone(result)

    def test_handles_png_format(self):
        """Should correctly generate PNG thumbnails."""
        source = self._create_test_image('test.png', 800, 600)
        result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.png'))
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)

    def test_handles_webp_format(self):
        """Should correctly generate WebP thumbnails."""
        source = self._create_test_image('test.webp', 800, 600)
        result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.webp'))
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)

    def test_handles_gif_format(self):
        """Should correctly generate GIF thumbnails."""
        source = self._create_test_image('test.gif', 800, 600)
        result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.gif'))
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)

    def test_handles_rgba_to_jpeg_conversion(self):
        """Should convert RGBA images to RGB when saving as JPEG."""
        # Create an RGBA PNG first
        png_path = Path(self.temp_dir) / 'rgba_source.png'
        img = Image.new('RGBA', (800, 600), color=(0, 0, 255, 128))
        img.save(png_path)

        # Generate thumbnail to JPG output
        output_jpg = str(Path(self.temp_dir) / 'output.jpg')
        result = generate_thumbnail(str(png_path), output_path=output_jpg)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.mode, 'RGB')

    def test_preserves_transparency_in_png(self):
        """Should preserve RGBA mode in PNG thumbnails."""
        source = self._create_test_image('transparent.png', 800, 600, mode='RGBA')
        result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.mode, 'RGBA')

    def test_quality_parameter(self):
        """Should accept quality parameter for JPEG compression."""
        source = self._create_test_image('test.jpg', 800, 600)
        result_low = generate_thumbnail(source, quality=20,
                                        output_path=str(Path(self.temp_dir) / 'low.jpg'))
        result_high = generate_thumbnail(source, quality=95,
                                         output_path=str(Path(self.temp_dir) / 'high.jpg'))

        self.assertIsNotNone(result_low)
        self.assertIsNotNone(result_high)
        # Higher quality should generally produce larger file
        low_size = Path(result_low).stat().st_size
        high_size = Path(result_high).stat().st_size
        self.assertLess(low_size, high_size)

    def test_all_supported_extensions(self):
        """Should support all extensions in THUMBNAIL_SUPPORTED_EXTENSIONS."""
        for ext in THUMBNAIL_SUPPORTED_EXTENSIONS:
            with self.subTest(ext=ext):
                source = self._create_test_image(f'test.{ext}', 800, 600)
                result = generate_thumbnail(source)
                self.assertIsNotNone(result, f"Failed to generate thumbnail for .{ext}")

    def test_logs_warning_for_missing_file(self):
        """Should log warning when source file doesn't exist."""
        with self.assertLogs('media_extractor', level='WARNING') as cm:
            result = generate_thumbnail('/nonexistent/image.jpg')

        self.assertIsNone(result)
        self.assertTrue(any("does not exist" in msg for msg in cm.output))

    def test_logs_warning_for_unsupported_format(self):
        """Should log warning for unsupported image formats."""
        svg_path = Path(self.temp_dir) / 'image.svg'
        svg_path.write_text('<svg></svg>')

        with self.assertLogs('media_extractor', level='WARNING') as cm:
            result = generate_thumbnail(str(svg_path))

        self.assertIsNone(result)
        self.assertTrue(any("Unsupported" in msg for msg in cm.output))

    def test_logs_info_when_skipping_small_image(self):
        """Should log info when skipping image smaller than target."""
        source = self._create_test_image('small.jpg', 300, 200)

        with self.assertLogs('media_extractor', level='INFO') as cm:
            result = generate_thumbnail(source)

        self.assertIsNone(result)
        self.assertTrue(any("already smaller" in msg for msg in cm.output))

    def test_logs_info_on_success(self):
        """Should log info message when thumbnail is generated successfully."""
        source = self._create_test_image('test.jpg', 800, 600)

        with self.assertLogs('media_extractor', level='INFO') as cm:
            result = generate_thumbnail(source)

        self.assertIsNotNone(result)
        self.assertTrue(any("Generated thumbnail" in msg for msg in cm.output))

    def test_default_thumbnail_width_is_400(self):
        """Should have default thumbnail width of 400 pixels."""
        self.assertEqual(DEFAULT_THUMBNAIL_WIDTH, 400)

    def test_handles_corrupted_image_gracefully(self):
        """Should return None and log error for corrupted images."""
        corrupted_path = Path(self.temp_dir) / 'corrupted.jpg'
        corrupted_path.write_bytes(b'not an image')

        with self.assertLogs('media_extractor', level='ERROR') as cm:
            result = generate_thumbnail(str(corrupted_path))

        self.assertIsNone(result)
        self.assertTrue(any("Failed to generate" in msg for msg in cm.output))

    def test_portrait_image_aspect_ratio(self):
        """Should correctly maintain aspect ratio for portrait images."""
        source = self._create_test_image('portrait.jpg', 600, 900)  # Portrait (2:3)
        result = generate_thumbnail(source, width=400)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)
            self.assertEqual(thumb.height, 600)  # 400 * (900/600) = 600

    def test_square_image_aspect_ratio(self):
        """Should correctly maintain aspect ratio for square images."""
        source = self._create_test_image('square.jpg', 800, 800)
        result = generate_thumbnail(source, width=400)

        self.assertIsNotNone(result)
        with Image.open(result) as thumb:
            self.assertEqual(thumb.width, 400)
            self.assertEqual(thumb.height, 400)


class TestGetThumbnailPath(unittest.TestCase):
    """Tests for the get_thumbnail_path utility function."""

    def test_simple_filename(self):
        """Should add _thumb suffix before extension."""
        result = get_thumbnail_path('image.jpg')
        self.assertEqual(result, 'image_thumb.jpg')

    def test_path_with_directory(self):
        """Should preserve directory structure."""
        result = get_thumbnail_path('/path/to/image.jpg')
        self.assertEqual(result, '/path/to/image_thumb.jpg')

    def test_custom_suffix(self):
        """Should use custom suffix when provided."""
        result = get_thumbnail_path('image.jpg', thumbnail_suffix='_small')
        self.assertEqual(result, 'image_small.jpg')

    def test_preserves_extension(self):
        """Should preserve the original file extension."""
        self.assertEqual(get_thumbnail_path('photo.png'), 'photo_thumb.png')
        self.assertEqual(get_thumbnail_path('pic.webp'), 'pic_thumb.webp')
        self.assertEqual(get_thumbnail_path('img.gif'), 'img_thumb.gif')

    def test_complex_filename(self):
        """Should handle filenames with multiple dots."""
        result = get_thumbnail_path('photo.backup.2024.jpg')
        self.assertEqual(result, 'photo.backup.2024_thumb.jpg')

    def test_relative_path(self):
        """Should handle relative paths."""
        result = get_thumbnail_path('photos/2021/sunset.jpg')
        self.assertEqual(result, 'photos/2021/sunset_thumb.jpg')

    def test_empty_suffix(self):
        """Should handle empty suffix."""
        result = get_thumbnail_path('image.jpg', thumbnail_suffix='')
        self.assertEqual(result, 'image.jpg')

    def test_different_extensions(self):
        """Should work with all thumbnail-supported extensions."""
        for ext in THUMBNAIL_SUPPORTED_EXTENSIONS:
            result = get_thumbnail_path(f'test.{ext}')
            self.assertEqual(result, f'test_thumb.{ext}')


class TestExtensionSets(unittest.TestCase):
    """Tests for extension set definitions."""

    def test_image_extensions_are_lowercase(self):
        """All image extensions should be lowercase."""
        for ext in IMAGE_EXTENSIONS:
            self.assertEqual(ext, ext.lower())

    def test_video_extensions_are_lowercase(self):
        """All video extensions should be lowercase."""
        for ext in VIDEO_EXTENSIONS:
            self.assertEqual(ext, ext.lower())

    def test_audio_extensions_are_lowercase(self):
        """All audio extensions should be lowercase."""
        for ext in AUDIO_EXTENSIONS:
            self.assertEqual(ext, ext.lower())

    def test_thumbnail_supported_is_subset_of_images(self):
        """Thumbnail supported extensions should be a subset of image extensions."""
        self.assertTrue(THUMBNAIL_SUPPORTED_EXTENSIONS.issubset(IMAGE_EXTENSIONS))

    def test_svg_not_in_thumbnail_supported(self):
        """SVG should not be in thumbnail supported extensions."""
        self.assertNotIn('svg', THUMBNAIL_SUPPORTED_EXTENSIONS)

    def test_common_image_formats_included(self):
        """Common image formats should be in IMAGE_EXTENSIONS."""
        common = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        self.assertTrue(common.issubset(IMAGE_EXTENSIONS))

    def test_common_video_formats_included(self):
        """Common video formats should be in VIDEO_EXTENSIONS."""
        common = {'mp4', 'webm', 'mov'}
        self.assertTrue(common.issubset(VIDEO_EXTENSIONS))

    def test_common_audio_formats_included(self):
        """Common audio formats should be in AUDIO_EXTENSIONS."""
        common = {'mp3', 'wav', 'm4a'}
        self.assertTrue(common.issubset(AUDIO_EXTENSIONS))

    def test_no_overlap_between_extension_sets(self):
        """There should be no overlap between image, video, and audio extensions."""
        self.assertEqual(len(IMAGE_EXTENSIONS & VIDEO_EXTENSIONS), 0)
        self.assertEqual(len(IMAGE_EXTENSIONS & AUDIO_EXTENSIONS), 0)
        self.assertEqual(len(VIDEO_EXTENSIONS & AUDIO_EXTENSIONS), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for media extraction workflows."""

    def setUp(self):
        """Set up temporary directory for integration tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.media_base = Path(self.temp_dir)

        # Create a realistic directory structure
        (self.media_base / "2021" / "06" / "vacation").mkdir(parents=True)
        (self.media_base / "gallery").mkdir(parents=True)

        # Create test files
        self._create_test_image('2021/06/vacation/beach.jpg', 1200, 800)
        self._create_test_image('2021/06/vacation/sunset.png', 1600, 900)
        (self.media_base / "2021" / "06" / "vacation" / "waves.mp4").touch()
        (self.media_base / "2021" / "06" / "vacation" / "ocean.mp3").touch()
        self._create_test_image('gallery/landscape.jpg', 2000, 1500)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def _create_test_image(self, relative_path: str, width: int, height: int):
        """Helper to create a test image."""
        path = self.media_base / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', (width, height), color='green')
        img.save(path)

    def test_full_workflow_extract_and_resolve(self):
        """Test extracting references from content and resolving to paths."""
        content = """
        # My Vacation

        Here are some photos from my trip:

        ![[2021/06/vacation/beach.jpg]]
        ![[2021/06/vacation/sunset.png]]

        And a video:

        ![[2021/06/vacation/waves.mp4]]
        """

        # Extract references
        references = find_media_references(content)
        self.assertEqual(len(references), 3)

        # Resolve all references
        resolved = []
        for ref in references:
            path = resolve_media_path(ref, media_base=self.media_base)
            self.assertIsNotNone(path)
            resolved.append(path)

        self.assertEqual(len(resolved), 3)
        self.assertTrue(all(Path(p).exists() for p in resolved))

    def test_extract_resolve_and_thumbnail(self):
        """Test full workflow: extract, resolve, and generate thumbnails."""
        content = "![[gallery/landscape.jpg]]"

        # Extract
        references = find_media_references(content)
        self.assertEqual(references, ['gallery/landscape.jpg'])

        # Resolve
        source_path = resolve_media_path(references[0], media_base=self.media_base)
        self.assertIsNotNone(source_path)

        # Generate thumbnail
        thumb_output = str(Path(self.temp_dir) / 'thumbs' / 'landscape_thumb.jpg')
        thumb_path = generate_thumbnail(source_path, output_path=thumb_output, width=300)

        self.assertIsNotNone(thumb_path)
        self.assertTrue(Path(thumb_path).exists())

        with Image.open(thumb_path) as thumb:
            self.assertEqual(thumb.width, 300)

    def test_missing_media_in_workflow(self):
        """Test handling of missing media files in workflow."""
        content = "![[nonexistent/photo.jpg]]"

        references = find_media_references(content)
        self.assertEqual(references, ['nonexistent/photo.jpg'])

        path = resolve_media_path(references[0], media_base=self.media_base, validate=True)
        self.assertIsNone(path)

    def test_mixed_media_types_workflow(self):
        """Test workflow with mixed media types (only images can be thumbnailed)."""
        content = """
        ![[2021/06/vacation/beach.jpg]]
        ![[2021/06/vacation/waves.mp4]]
        ![[2021/06/vacation/ocean.mp3]]
        """

        references = find_media_references(content)
        self.assertEqual(len(references), 3)

        # Only the image should be thumbnailable
        for ref in references:
            path = resolve_media_path(ref, media_base=self.media_base)
            self.assertIsNotNone(path)

            if ref.endswith('.jpg'):
                thumb = generate_thumbnail(path)
                self.assertIsNotNone(thumb)
            else:
                # Non-images won't have thumbnails generated
                # (they're not in THUMBNAIL_SUPPORTED_EXTENSIONS)
                ext = Path(ref).suffix.lower().lstrip('.')
                self.assertNotIn(ext, THUMBNAIL_SUPPORTED_EXTENSIONS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
