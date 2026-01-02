#!/usr/bin/env python3
"""
Tests for the media_extractor module.

Run with: python test_media_extractor.py
Or with pytest: pytest test_media_extractor.py -v
"""

import unittest
from media_extractor import find_media_references, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS


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


if __name__ == '__main__':
    unittest.main()
