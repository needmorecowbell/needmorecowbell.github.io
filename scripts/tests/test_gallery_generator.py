#!/usr/bin/env python3
"""
Tests for the gallery_generator module.

Tests Pictures section extraction, media reference parsing, nanogallery2 HTML generation,
and Associations section handling.
"""

import json
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gallery_generator import (
    # Pictures section functions
    extract_pictures_section,
    extract_media_from_pictures_section,
    find_media_in_section,
    has_pictures_section,
    get_pictures_section_location,
    remove_pictures_section,
    # Nanogallery HTML generation
    generate_nanogallery_html,
    generate_gallery_from_obsidian,
    # Associations section functions
    has_associations_section,
    extract_associations_section,
    get_associations_section_location,
    remove_associations_section,
    extract_wikilinks_from_associations,
    find_wikilinks_in_section,
    convert_associations_to_hugo_links,
    _slugify_for_hugo,
    # Constants
    PICTURES_SECTION_PATTERN,
    ASSOCIATIONS_SECTION_PATTERN,
    DEFAULT_NANOGALLERY_CONFIG,
)


# =============================================================================
# Pictures Section Extraction Tests
# =============================================================================


class TestExtractPicturesSection(unittest.TestCase):
    """Tests for the extract_pictures_section function."""

    def test_simple_pictures_section(self):
        """Test extracting a simple Pictures section."""
        content = """# My Project

Some intro text.

## Pictures

![[2021/06/image1.jpg]]
![[2021/06/image2.png]]

## Notes

Some notes here.
"""
        result = extract_pictures_section(content)
        self.assertIn('![[2021/06/image1.jpg]]', result)
        self.assertIn('![[2021/06/image2.png]]', result)
        self.assertNotIn('Some intro text', result)
        self.assertNotIn('## Notes', result)

    def test_pictures_section_at_end(self):
        """Test extracting Pictures section at end of document."""
        content = """# My Project

## Description

Some text.

## Pictures

![[photos/final.jpg]]
"""
        result = extract_pictures_section(content)
        self.assertIn('![[photos/final.jpg]]', result)

    def test_pictures_section_case_insensitive(self):
        """Test that Pictures header is case-insensitive."""
        content = """## PICTURES

![[image.jpg]]
"""
        result = extract_pictures_section(content)
        self.assertIn('![[image.jpg]]', result)

        content2 = """## pictures

![[image.jpg]]
"""
        result2 = extract_pictures_section(content2)
        self.assertIn('![[image.jpg]]', result2)

    def test_picture_singular(self):
        """Test that 'Picture' (singular) is also recognized."""
        content = """## Picture

![[image.jpg]]
"""
        result = extract_pictures_section(content)
        self.assertIn('![[image.jpg]]', result)

    def test_no_pictures_section(self):
        """Test when there's no Pictures section."""
        content = """# My Project

## Description

Some text here.

## Notes

More text.
"""
        result = extract_pictures_section(content)
        self.assertIsNone(result)

    def test_empty_pictures_section(self):
        """Test when Pictures section is empty."""
        content = """## Pictures

## Next Section
"""
        result = extract_pictures_section(content)
        self.assertIsNone(result)

    def test_empty_content(self):
        """Test with empty content."""
        result = extract_pictures_section('')
        self.assertIsNone(result)

    def test_none_content(self):
        """Test with None content."""
        result = extract_pictures_section(None)
        self.assertIsNone(result)

    def test_pictures_section_with_text(self):
        """Test Pictures section containing both text and media."""
        content = """## Pictures

Here are some photos from the project:

![[photo1.jpg]]

This one shows the final result:

![[photo2.jpg]]
"""
        result = extract_pictures_section(content)
        self.assertIn('Here are some photos', result)
        self.assertIn('![[photo1.jpg]]', result)
        self.assertIn('![[photo2.jpg]]', result)

    def test_pictures_with_extra_whitespace_in_header(self):
        """Test Pictures header with extra whitespace."""
        content = """##   Pictures

![[image.jpg]]
"""
        result = extract_pictures_section(content)
        self.assertIn('![[image.jpg]]', result)

    def test_only_pictures_section(self):
        """Test document with only a Pictures section."""
        content = """## Pictures

![[image.jpg]]
![[video.mp4]]
"""
        result = extract_pictures_section(content)
        self.assertIn('![[image.jpg]]', result)
        self.assertIn('![[video.mp4]]', result)

    def test_pictures_section_preserves_formatting(self):
        """Test that internal formatting is preserved."""
        content = """## Pictures

- ![[image1.jpg]]
- ![[image2.jpg]]

### Subsection

![[image3.jpg]]

## Next
"""
        result = extract_pictures_section(content)
        self.assertIn('- ![[image1.jpg]]', result)
        self.assertIn('### Subsection', result)


class TestExtractMediaFromPicturesSection(unittest.TestCase):
    """Tests for the extract_media_from_pictures_section function."""

    def test_extract_images(self):
        """Test extracting image references."""
        content = """## Pictures

![[2021/06/photo1.jpg]]
![[2021/06/photo2.png]]
![[gallery/sunset.webp]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 3)
        self.assertIn('2021/06/photo1.jpg', result)
        self.assertIn('2021/06/photo2.png', result)
        self.assertIn('gallery/sunset.webp', result)

    def test_extract_videos(self):
        """Test extracting video references."""
        content = """## Pictures

![[videos/demo.mp4]]
![[clips/test.webm]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 2)
        self.assertIn('videos/demo.mp4', result)
        self.assertIn('clips/test.webm', result)

    def test_extract_mixed_media(self):
        """Test extracting mixed image and video references."""
        content = """## Pictures

![[photo.jpg]]
![[video.mp4]]
![[audio.mp3]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 3)
        self.assertIn('photo.jpg', result)
        self.assertIn('video.mp4', result)
        self.assertIn('audio.mp3', result)

    def test_no_pictures_section_returns_empty(self):
        """Test that missing Pictures section returns empty list."""
        content = """## Description

Some text with ![[image.jpg]] embedded.
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(result, [])

    def test_empty_pictures_section_returns_empty(self):
        """Test that empty Pictures section returns empty list."""
        content = """## Pictures

## Next
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(result, [])

    def test_pictures_section_no_media_returns_empty(self):
        """Test Pictures section with no media references."""
        content = """## Pictures

Just some text here, no images.
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(result, [])

    def test_ignores_non_media_embeds(self):
        """Test that non-media embeds are ignored."""
        content = """## Pictures

![[note.md]]
![[document.pdf]]
![[real-image.jpg]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 1)
        self.assertIn('real-image.jpg', result)

    def test_preserves_order(self):
        """Test that media references are returned in order."""
        content = """## Pictures

![[first.jpg]]
![[second.jpg]]
![[third.jpg]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(result, ['first.jpg', 'second.jpg', 'third.jpg'])

    def test_handles_whitespace_in_embeds(self):
        """Test handling whitespace in embed syntax."""
        content = """## Pictures

![[  image1.jpg  ]]
![[ path/to/image2.png ]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 2)
        self.assertIn('image1.jpg', result)
        self.assertIn('path/to/image2.png', result)

    def test_case_insensitive_extensions(self):
        """Test that extensions are matched case-insensitively."""
        content = """## Pictures

![[image.JPG]]
![[photo.PNG]]
![[video.MP4]]
"""
        result = extract_media_from_pictures_section(content)
        self.assertEqual(len(result), 3)


class TestFindMediaInSection(unittest.TestCase):
    """Tests for the find_media_in_section function."""

    def test_find_multiple_images(self):
        """Test finding multiple image references."""
        section = """
![[photos/001.jpg]]
![[photos/002.png]]
![[photos/003.gif]]
"""
        result = find_media_in_section(section)
        self.assertEqual(len(result), 3)

    def test_empty_section(self):
        """Test with empty section."""
        result = find_media_in_section('')
        self.assertEqual(result, [])

    def test_none_section(self):
        """Test with None section."""
        result = find_media_in_section(None)
        self.assertEqual(result, [])

    def test_section_with_text_and_media(self):
        """Test section with mixed text and media."""
        section = """Here is the first image:

![[first.jpg]]

And here's another:

![[second.jpg]]
"""
        result = find_media_in_section(section)
        self.assertEqual(result, ['first.jpg', 'second.jpg'])

    def test_inline_media_references(self):
        """Test inline media references."""
        section = "Check out ![[image1.jpg]] and ![[image2.png]] here."
        result = find_media_in_section(section)
        self.assertEqual(len(result), 2)

    def test_all_supported_image_formats(self):
        """Test all supported image extensions."""
        section = """
![[test.jpg]]
![[test.jpeg]]
![[test.png]]
![[test.gif]]
![[test.webp]]
![[test.svg]]
![[test.bmp]]
![[test.tiff]]
![[test.tif]]
![[test.ico]]
"""
        result = find_media_in_section(section)
        self.assertEqual(len(result), 10)

    def test_all_supported_video_formats(self):
        """Test all supported video extensions."""
        section = """
![[test.mp4]]
![[test.webm]]
![[test.ogg]]
![[test.ogv]]
![[test.mov]]
![[test.avi]]
![[test.mkv]]
![[test.m4v]]
"""
        result = find_media_in_section(section)
        self.assertEqual(len(result), 8)

    def test_paths_with_subdirectories(self):
        """Test media paths with subdirectories."""
        section = """
![[2021/06/15/photo.jpg]]
![[projects/woodworking/final_result.png]]
"""
        result = find_media_in_section(section)
        self.assertEqual(result, [
            '2021/06/15/photo.jpg',
            'projects/woodworking/final_result.png'
        ])


class TestHasPicturesSection(unittest.TestCase):
    """Tests for the has_pictures_section function."""

    def test_has_pictures_section_true(self):
        """Test detection of Pictures section."""
        content = """# Title

## Pictures

Some content.
"""
        self.assertTrue(has_pictures_section(content))

    def test_has_pictures_section_false(self):
        """Test when no Pictures section exists."""
        content = """# Title

## Description

Some content.
"""
        self.assertFalse(has_pictures_section(content))

    def test_empty_content(self):
        """Test with empty content."""
        self.assertFalse(has_pictures_section(''))

    def test_none_content(self):
        """Test with None content."""
        self.assertFalse(has_pictures_section(None))

    def test_case_variations(self):
        """Test various case variations of Pictures header."""
        self.assertTrue(has_pictures_section('## Pictures\n'))
        self.assertTrue(has_pictures_section('## PICTURES\n'))
        self.assertTrue(has_pictures_section('## pictures\n'))
        self.assertTrue(has_pictures_section('## Picture\n'))

    def test_similar_but_not_matching(self):
        """Test headers that are similar but shouldn't match."""
        self.assertFalse(has_pictures_section('## My Pictures\n'))
        self.assertFalse(has_pictures_section('### Pictures\n'))  # Level 3
        self.assertFalse(has_pictures_section('##Pictures\n'))  # No space


class TestGetPicturesSectionLocation(unittest.TestCase):
    """Tests for the get_pictures_section_location function."""

    def test_get_location_simple(self):
        """Test getting location of Pictures section."""
        content = """# Title

## Pictures

![[image.jpg]]

## End
"""
        result = get_pictures_section_location(content)
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(content[start:start+12], '## Pictures\n')
        self.assertNotIn('## End', content[start:end])

    def test_get_location_at_end(self):
        """Test location when Pictures is the last section."""
        content = """# Title

## Pictures

![[image.jpg]]
"""
        result = get_pictures_section_location(content)
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(end, len(content))

    def test_get_location_no_section(self):
        """Test when no Pictures section exists."""
        content = """# Title

## Description

Some text.
"""
        result = get_pictures_section_location(content)
        self.assertIsNone(result)

    def test_empty_content(self):
        """Test with empty content."""
        result = get_pictures_section_location('')
        self.assertIsNone(result)

    def test_none_content(self):
        """Test with None content."""
        result = get_pictures_section_location(None)
        self.assertIsNone(result)


class TestRemovePicturesSection(unittest.TestCase):
    """Tests for the remove_pictures_section function."""

    def test_remove_middle_section(self):
        """Test removing Pictures section from the middle."""
        content = """# Title

## Description

Some text.

## Pictures

![[image.jpg]]

## Notes

More text.
"""
        result = remove_pictures_section(content)
        self.assertIn('## Description', result)
        self.assertIn('## Notes', result)
        self.assertNotIn('## Pictures', result)
        self.assertNotIn('![[image.jpg]]', result)

    def test_remove_end_section(self):
        """Test removing Pictures section at the end."""
        content = """# Title

## Description

Some text.

## Pictures

![[image.jpg]]
"""
        result = remove_pictures_section(content)
        self.assertIn('## Description', result)
        self.assertNotIn('## Pictures', result)
        self.assertNotIn('![[image.jpg]]', result)

    def test_remove_only_section(self):
        """Test removing when Pictures is the only section."""
        content = """## Pictures

![[image.jpg]]
"""
        result = remove_pictures_section(content)
        self.assertEqual(result, '')

    def test_no_pictures_section(self):
        """Test when there's no Pictures section to remove."""
        content = """# Title

## Description

Some text.
"""
        result = remove_pictures_section(content)
        self.assertEqual(result, content)

    def test_empty_content(self):
        """Test with empty content."""
        result = remove_pictures_section('')
        self.assertEqual(result, '')

    def test_preserves_formatting(self):
        """Test that formatting around removed section is clean."""
        content = """# Title

## Pictures

![[image.jpg]]

## Notes

Text here.
"""
        result = remove_pictures_section(content)
        # Should not have excessive blank lines
        self.assertNotIn('\n\n\n', result)
        self.assertIn('# Title', result)
        self.assertIn('## Notes', result)


class TestPicturesSectionPattern(unittest.TestCase):
    """Tests for the PICTURES_SECTION_PATTERN regex."""

    def test_matches_pictures(self):
        """Test that pattern matches '## Pictures'."""
        match = PICTURES_SECTION_PATTERN.search('## Pictures')
        self.assertIsNotNone(match)

    def test_matches_picture_singular(self):
        """Test that pattern matches '## Picture'."""
        match = PICTURES_SECTION_PATTERN.search('## Picture')
        self.assertIsNotNone(match)

    def test_matches_with_trailing_whitespace(self):
        """Test matching with trailing whitespace."""
        match = PICTURES_SECTION_PATTERN.search('## Pictures   ')
        self.assertIsNotNone(match)

    def test_case_insensitive(self):
        """Test case insensitivity."""
        self.assertIsNotNone(PICTURES_SECTION_PATTERN.search('## PICTURES'))
        self.assertIsNotNone(PICTURES_SECTION_PATTERN.search('## pictures'))
        self.assertIsNotNone(PICTURES_SECTION_PATTERN.search('## PiCtUrEs'))

    def test_no_match_level_3(self):
        """Test that level 3 heading doesn't match."""
        match = PICTURES_SECTION_PATTERN.search('### Pictures')
        self.assertIsNone(match)

    def test_no_match_without_space(self):
        """Test that ##Pictures (no space) doesn't match."""
        match = PICTURES_SECTION_PATTERN.search('##Pictures')
        self.assertIsNone(match)


# =============================================================================
# Nanogallery HTML Generation Tests
# =============================================================================


class TestGenerateNanogalleryHtml(unittest.TestCase):
    """Tests for the generate_nanogallery_html function."""

    def test_basic_gallery_with_images(self):
        """Test generating gallery with basic image list."""
        media_files = ['image1.jpg', 'image2.png', 'image3.webp']
        base_url = '{{<s3cdn>}}/projects/test_project/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('<div ID="gallery"', result)
        self.assertIn('data-nanogallery2=', result)
        self.assertIn('image1.jpg', result)
        self.assertIn('image2.png', result)
        self.assertIn('image3.webp', result)
        self.assertIn(base_url, result)

    def test_empty_media_list_returns_empty_string(self):
        """Test that empty media list returns empty string."""
        result = generate_nanogallery_html([], 'http://example.com/')
        self.assertEqual(result, '')

    def test_includes_default_config(self):
        """Test that default config values are included."""
        media_files = ['test.jpg']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        # Check for key config values
        self.assertIn('"thumbnailWidth": "250"', result)
        self.assertIn('"thumbnailHeight": "250"', result)
        self.assertIn('"galleryDisplayMode": "pagination"', result)
        self.assertIn('"thumbnailAlignment": "center"', result)

    def test_includes_base_url_in_config(self):
        """Test that base URL is added to config as itemsBaseURL."""
        media_files = ['test.jpg']
        base_url = '{{<s3cdn>}}/projects/my_project/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('"itemsBaseURL":', result)
        self.assertIn(base_url, result)

    def test_anchor_tags_format(self):
        """Test that anchor tags have correct format."""
        media_files = ['photo.jpg']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('<a href="photo.jpg"', result)
        self.assertIn('data-ngthumb="photo.jpg"', result)
        self.assertIn('data-ngdesc=""', result)

    def test_thumbnail_suffix(self):
        """Test thumbnail suffix is applied correctly."""
        media_files = ['photo.jpg', 'video.mp4']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(
            media_files, base_url, thumbnail_suffix='_thumb'
        )

        self.assertIn('data-ngthumb="photo_thumb.jpg"', result)
        self.assertIn('data-ngthumb="video_thumb.mp4"', result)
        # Full size should remain unchanged
        self.assertIn('href="photo.jpg"', result)
        self.assertIn('href="video.mp4"', result)

    def test_descriptions(self):
        """Test that descriptions are included in anchor tags."""
        media_files = ['photo1.jpg', 'photo2.jpg']
        descriptions = ['First photo', 'Second photo']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(
            media_files, base_url, descriptions=descriptions
        )

        self.assertIn('data-ngdesc="First photo"', result)
        self.assertIn('data-ngdesc="Second photo"', result)

    def test_descriptions_length_mismatch_raises_error(self):
        """Test that mismatched descriptions length raises ValueError."""
        media_files = ['photo1.jpg', 'photo2.jpg']
        descriptions = ['Only one description']

        with self.assertRaises(ValueError) as context:
            generate_nanogallery_html(
                media_files, 'http://example.com/', descriptions=descriptions
            )

        self.assertIn('length', str(context.exception))

    def test_custom_config_override(self):
        """Test that custom config overrides defaults."""
        media_files = ['test.jpg']
        base_url = 'http://example.com/'
        custom_config = {
            'thumbnailWidth': '300',
            'galleryMaxRows': 2
        }

        result = generate_nanogallery_html(
            media_files, base_url, config=custom_config
        )

        self.assertIn('"thumbnailWidth": "300"', result)
        self.assertIn('"galleryMaxRows": 2', result)
        # Other defaults should still be present
        self.assertIn('"thumbnailHeight": "250"', result)

    def test_custom_config_nested_merge(self):
        """Test that nested config values are properly merged."""
        media_files = ['test.jpg']
        base_url = 'http://example.com/'
        custom_config = {
            'thumbnailLabel': {
                'position': 'onBottom'  # Override one nested value
            }
        }

        result = generate_nanogallery_html(
            media_files, base_url, config=custom_config
        )

        self.assertIn('"position": "onBottom"', result)
        # Other nested value should be preserved
        self.assertIn('"displayDescription": true', result)

    def test_mixed_media_types(self):
        """Test gallery with mixed images and videos."""
        media_files = ['photo.jpg', 'video.mp4', 'animation.gif', 'clip.webm']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('href="photo.jpg"', result)
        self.assertIn('href="video.mp4"', result)
        self.assertIn('href="animation.gif"', result)
        self.assertIn('href="clip.webm"', result)

    def test_strips_paths_from_filenames(self):
        """Test that paths are stripped, keeping only filenames."""
        media_files = ['2024/01/photo.jpg', 'projects/video.mp4']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('href="photo.jpg"', result)
        self.assertIn('href="video.mp4"', result)
        self.assertNotIn('2024/01/', result.split('data-nanogallery2')[1])
        self.assertNotIn('projects/', result.split('data-nanogallery2')[1])

    def test_output_is_valid_html_structure(self):
        """Test that output has valid HTML div structure."""
        media_files = ['test.jpg']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertTrue(result.startswith('<div ID="gallery"'))
        self.assertTrue(result.endswith('</div>'))

    def test_preserves_order_of_media_files(self):
        """Test that media files appear in order."""
        media_files = ['first.jpg', 'second.jpg', 'third.jpg']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        first_pos = result.find('first.jpg')
        second_pos = result.find('second.jpg')
        third_pos = result.find('third.jpg')

        self.assertLess(first_pos, second_pos)
        self.assertLess(second_pos, third_pos)

    def test_single_media_file(self):
        """Test gallery with a single media file."""
        media_files = ['only_image.jpg']
        base_url = 'http://example.com/'

        result = generate_nanogallery_html(media_files, base_url)

        self.assertIn('only_image.jpg', result)
        # Should still have full structure
        self.assertIn('<div ID="gallery"', result)
        self.assertIn('</div>', result)

    def test_hugo_shortcode_base_url(self):
        """Test with Hugo shortcode syntax in base URL."""
        media_files = ['test.jpg']
        base_url = '{{<s3cdn>}}/projects/wood_zippo_lighter/'

        result = generate_nanogallery_html(media_files, base_url)

        # The shortcode should be preserved as-is
        self.assertIn('{{<s3cdn>}}', result)
        self.assertIn('/projects/wood_zippo_lighter/', result)


class TestGenerateGalleryFromObsidian(unittest.TestCase):
    """Tests for the generate_gallery_from_obsidian function."""

    def test_basic_obsidian_note(self):
        """Test extracting gallery from typical Obsidian note."""
        content = """---
title: My Project
---

# My Project

Description here.

## Pictures

![[2024/01/photo1.jpg]]
![[2024/01/photo2.jpg]]
![[2024/01/video.mp4]]
"""
        result = generate_gallery_from_obsidian(content, 'my_project')

        self.assertIsNotNone(result)
        self.assertIn('photo1.jpg', result)
        self.assertIn('photo2.jpg', result)
        self.assertIn('video.mp4', result)
        self.assertIn('/projects/my_project/', result)
        self.assertIn('{{<s3cdn>}}', result)

    def test_no_pictures_section_returns_none(self):
        """Test that notes without Pictures section return None."""
        content = """# My Post

Just some text, no pictures section.
"""
        result = generate_gallery_from_obsidian(content, 'my_project')

        self.assertIsNone(result)

    def test_empty_pictures_section_returns_none(self):
        """Test that empty Pictures section returns None."""
        content = """## Pictures

## Next Section
"""
        result = generate_gallery_from_obsidian(content, 'my_project')

        self.assertIsNone(result)

    def test_custom_cdn_shortcode(self):
        """Test with custom CDN shortcode."""
        content = """## Pictures

![[image.jpg]]
"""
        result = generate_gallery_from_obsidian(
            content, 'my_project', cdn_shortcode='{{<mycdn>}}'
        )

        self.assertIn('{{<mycdn>}}', result)
        self.assertNotIn('{{<s3cdn>}}', result)

    def test_project_slug_in_url(self):
        """Test that project slug is properly included in URL."""
        content = """## Pictures

![[test.jpg]]
"""
        result = generate_gallery_from_obsidian(content, 'stained_glass_window')

        self.assertIn('/projects/stained_glass_window/', result)

    def test_extracts_only_filenames(self):
        """Test that only filenames (not full paths) appear in anchors."""
        content = """## Pictures

![[2024/january/deep/path/photo.jpg]]
"""
        result = generate_gallery_from_obsidian(content, 'test')

        # The anchor should have just the filename
        self.assertIn('href="photo.jpg"', result)
        # But not the path in the anchor (path is in the base URL via itemsBaseURL)
        anchor_section = result.split('data-nanogallery2')[1]
        self.assertNotIn('2024/january', anchor_section)


class TestDefaultNanogalleryConfig(unittest.TestCase):
    """Tests for the DEFAULT_NANOGALLERY_CONFIG constant."""

    def test_config_has_required_keys(self):
        """Test that default config has all required keys."""
        required_keys = [
            'thumbnailWidth', 'thumbnailHeight',
            'thumbnailBorderVertical', 'thumbnailBorderHorizontal',
            'thumbnailLabel', 'thumbnailHoverEffect2',
            'galleryDisplayMode', 'galleryMaxRows',
            'thumbnailAlignment', 'thumbnailOpenImage',
            'viewerTools'
        ]
        for key in required_keys:
            self.assertIn(key, DEFAULT_NANOGALLERY_CONFIG)

    def test_thumbnail_label_has_required_keys(self):
        """Test that thumbnailLabel has position and displayDescription."""
        self.assertIn('position', DEFAULT_NANOGALLERY_CONFIG['thumbnailLabel'])
        self.assertIn('displayDescription', DEFAULT_NANOGALLERY_CONFIG['thumbnailLabel'])

    def test_viewer_tools_has_required_keys(self):
        """Test that viewerTools has topLeft and topRight."""
        self.assertIn('topLeft', DEFAULT_NANOGALLERY_CONFIG['viewerTools'])
        self.assertIn('topRight', DEFAULT_NANOGALLERY_CONFIG['viewerTools'])

    def test_config_matches_existing_projects(self):
        """Test that config values match existing project format."""
        self.assertEqual(DEFAULT_NANOGALLERY_CONFIG['thumbnailWidth'], '250')
        self.assertEqual(DEFAULT_NANOGALLERY_CONFIG['thumbnailHeight'], '250')
        self.assertEqual(DEFAULT_NANOGALLERY_CONFIG['galleryDisplayMode'], 'pagination')
        self.assertEqual(DEFAULT_NANOGALLERY_CONFIG['galleryMaxRows'], 1)
        self.assertEqual(DEFAULT_NANOGALLERY_CONFIG['thumbnailAlignment'], 'center')
        self.assertTrue(DEFAULT_NANOGALLERY_CONFIG['thumbnailOpenImage'])


# =============================================================================
# Associations Section Tests
# =============================================================================


class TestHasAssociationsSection(unittest.TestCase):
    """Tests for the has_associations_section function."""

    def test_has_associations_section(self):
        """Test detecting an Associations section."""
        content = """# My Post

## Associations

[[Related Post]]
[[Another Post|See this]]
"""
        self.assertTrue(has_associations_section(content))

    def test_no_associations_section(self):
        """Test when there's no Associations section."""
        content = """# My Post

## Description

Some text here.
"""
        self.assertFalse(has_associations_section(content))

    def test_singular_association(self):
        """Test that 'Association' (singular) is recognized."""
        content = """## Association

[[Related]]
"""
        self.assertTrue(has_associations_section(content))

    def test_case_insensitive(self):
        """Test case insensitivity."""
        self.assertTrue(has_associations_section("## ASSOCIATIONS\n[[Link]]"))
        self.assertTrue(has_associations_section("## associations\n[[Link]]"))
        self.assertTrue(has_associations_section("## Associations\n[[Link]]"))

    def test_empty_content(self):
        """Test with empty content."""
        self.assertFalse(has_associations_section(''))
        self.assertFalse(has_associations_section(None))


class TestExtractAssociationsSection(unittest.TestCase):
    """Tests for the extract_associations_section function."""

    def test_simple_associations_section(self):
        """Test extracting a simple Associations section."""
        content = """# My Post

## Description

Some text.

## Associations

[[Related Post]]
[[Another Post|See this]]

## Notes

More text.
"""
        result = extract_associations_section(content)
        self.assertIn('[[Related Post]]', result)
        self.assertIn('[[Another Post|See this]]', result)
        self.assertNotIn('## Notes', result)
        self.assertNotIn('Some text', result)

    def test_associations_at_end(self):
        """Test extracting Associations section at end of document."""
        content = """# My Post

## Description

Text.

## Associations

[[Link 1]]
[[Link 2]]
"""
        result = extract_associations_section(content)
        self.assertIn('[[Link 1]]', result)
        self.assertIn('[[Link 2]]', result)

    def test_no_associations_section(self):
        """Test when there's no Associations section."""
        content = """# My Post

## Description

Text.
"""
        result = extract_associations_section(content)
        self.assertIsNone(result)

    def test_empty_associations_section(self):
        """Test extracting empty Associations section."""
        content = """## Associations

## Next Section
"""
        result = extract_associations_section(content)
        self.assertIsNone(result)


class TestGetAssociationsSectionLocation(unittest.TestCase):
    """Tests for the get_associations_section_location function."""

    def test_get_location_simple(self):
        """Test getting location of Associations section."""
        content = """# Title

## Associations

[[Link]]

## End
"""
        result = get_associations_section_location(content)
        self.assertIsNotNone(result)
        start, end = result
        self.assertIn('## Associations', content[start:end])
        self.assertNotIn('## End', content[start:end])

    def test_get_location_at_end(self):
        """Test location when Associations is the last section."""
        content = """# Title

## Associations

[[Link]]
"""
        result = get_associations_section_location(content)
        self.assertIsNotNone(result)
        start, end = result
        self.assertEqual(end, len(content))

    def test_get_location_no_section(self):
        """Test when no Associations section exists."""
        content = """# Title

## Description

Some text.
"""
        result = get_associations_section_location(content)
        self.assertIsNone(result)

    def test_empty_content(self):
        """Test with empty content."""
        result = get_associations_section_location('')
        self.assertIsNone(result)

    def test_none_content(self):
        """Test with None content."""
        result = get_associations_section_location(None)
        self.assertIsNone(result)


class TestRemoveAssociationsSection(unittest.TestCase):
    """Tests for the remove_associations_section function."""

    def test_remove_middle_section(self):
        """Test removing Associations section from middle of document."""
        content = """# Title

## Description

Some text.

## Associations

[[Link 1]]
[[Link 2]]

## Notes

More text.
"""
        result = remove_associations_section(content)
        self.assertIn('## Description', result)
        self.assertIn('## Notes', result)
        self.assertNotIn('## Associations', result)
        self.assertNotIn('[[Link 1]]', result)

    def test_remove_end_section(self):
        """Test removing Associations section at end."""
        content = """# Title

## Description

Text.

## Associations

[[Link]]
"""
        result = remove_associations_section(content)
        self.assertIn('## Description', result)
        self.assertNotIn('## Associations', result)
        self.assertNotIn('[[Link]]', result)

    def test_no_associations_section(self):
        """Test when there's no Associations section to remove."""
        content = """# Title

## Description

Text.
"""
        result = remove_associations_section(content)
        self.assertEqual(result, content)

    def test_empty_content(self):
        """Test with empty content."""
        result = remove_associations_section('')
        self.assertEqual(result, '')


class TestExtractWikilinksFromAssociations(unittest.TestCase):
    """Tests for the extract_wikilinks_from_associations function."""

    def test_simple_wikilinks(self):
        """Test extracting simple wikilinks."""
        content = """## Associations

[[First Link]]
[[Second Link]]
"""
        result = extract_wikilinks_from_associations(content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ('First Link', None))
        self.assertEqual(result[1], ('Second Link', None))

    def test_aliased_wikilinks(self):
        """Test extracting aliased wikilinks."""
        content = """## Associations

[[Page Name|Display Text]]
[[Another Page|Different Text]]
"""
        result = extract_wikilinks_from_associations(content)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ('Page Name', 'Display Text'))
        self.assertEqual(result[1], ('Another Page', 'Different Text'))

    def test_mixed_wikilinks(self):
        """Test extracting a mix of simple and aliased wikilinks."""
        content = """## Associations

[[Simple Link]]
[[Complex Link|With Alias]]
[[Another Simple]]
"""
        result = extract_wikilinks_from_associations(content)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ('Simple Link', None))
        self.assertEqual(result[1], ('Complex Link', 'With Alias'))
        self.assertEqual(result[2], ('Another Simple', None))

    def test_no_associations_section(self):
        """Test when there's no Associations section."""
        content = """## Description

Some text with [[A Link]].
"""
        result = extract_wikilinks_from_associations(content)
        self.assertEqual(result, [])


class TestFindWikilinksInSection(unittest.TestCase):
    """Tests for the find_wikilinks_in_section function."""

    def test_find_simple_wikilinks(self):
        """Test finding simple wikilinks."""
        section = """
[[Link One]]
[[Link Two]]
[[Link Three]]
"""
        result = find_wikilinks_in_section(section)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], 'Link One')
        self.assertEqual(result[1][0], 'Link Two')
        self.assertEqual(result[2][0], 'Link Three')

    def test_find_aliased_wikilinks(self):
        """Test finding aliased wikilinks."""
        section = "[[Page|Display]]"
        result = find_wikilinks_in_section(section)
        self.assertEqual(result, [('Page', 'Display')])

    def test_inline_wikilinks(self):
        """Test finding wikilinks inline with text."""
        section = "See [[Related Page]] and [[Another|Also this]] for more."
        result = find_wikilinks_in_section(section)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ('Related Page', None))
        self.assertEqual(result[1], ('Another', 'Also this'))

    def test_empty_section(self):
        """Test with empty section."""
        self.assertEqual(find_wikilinks_in_section(''), [])
        self.assertEqual(find_wikilinks_in_section(None), [])


class TestConvertAssociationsToHugoLinks(unittest.TestCase):
    """Tests for the convert_associations_to_hugo_links function."""

    def test_simple_conversion(self):
        """Test converting simple wikilinks to Hugo links."""
        content = """# My Post

## Associations

[[Related Post]]
[[Another Post]]
"""
        result = convert_associations_to_hugo_links(content)
        self.assertIn('[Related Post](/post/related-post/)', result)
        self.assertIn('[Another Post](/post/another-post/)', result)
        # Header should be renamed to Related
        self.assertIn('## Related', result)
        self.assertNotIn('## Associations', result)

    def test_aliased_links_conversion(self):
        """Test converting aliased wikilinks."""
        content = """## Associations

[[Page Name|Click Here]]
"""
        result = convert_associations_to_hugo_links(content)
        self.assertIn('[Click Here](/post/page-name/)', result)
        self.assertNotIn('[[Page Name|Click Here]]', result)

    def test_custom_base_path(self):
        """Test conversion with custom base path."""
        content = """## Associations

[[My Project]]
"""
        result = convert_associations_to_hugo_links(content, base_path='/projects/')
        self.assertIn('[My Project](/projects/my-project/)', result)

    def test_preserves_other_content(self):
        """Test that other content is preserved."""
        content = """# Title

## Description

Some important text here.

## Associations

[[Related]]

## Notes

Final notes.
"""
        result = convert_associations_to_hugo_links(content)
        self.assertIn('# Title', result)
        self.assertIn('## Description', result)
        self.assertIn('Some important text here.', result)
        self.assertIn('## Notes', result)
        self.assertIn('Final notes.', result)
        self.assertIn('## Related', result)
        self.assertIn('[Related](/post/related/)', result)

    def test_no_associations_section(self):
        """Test that content without Associations is unchanged."""
        content = """# Title

## Description

Text.
"""
        result = convert_associations_to_hugo_links(content)
        self.assertEqual(result, content)

    def test_slug_generation(self):
        """Test that slugs are properly generated."""
        content = """## Associations

[[My Fancy Page Name!]]
[[Page With   Multiple   Spaces]]
[[Page-With-Hyphens]]
"""
        result = convert_associations_to_hugo_links(content)
        self.assertIn('/post/my-fancy-page-name/', result)
        self.assertIn('/post/page-with-multiple-spaces/', result)
        self.assertIn('/post/page-with-hyphens/', result)


class TestSlugifyForHugo(unittest.TestCase):
    """Tests for the _slugify_for_hugo function."""

    def test_basic_slug(self):
        """Test basic slug generation."""
        self.assertEqual(_slugify_for_hugo('My Page'), 'my-page')

    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        self.assertEqual(_slugify_for_hugo('Hello, World!'), 'hello-world')
        self.assertEqual(_slugify_for_hugo("It's a test"), 'its-a-test')

    def test_handles_multiple_spaces(self):
        """Test handling of multiple spaces."""
        self.assertEqual(_slugify_for_hugo('Too   Many   Spaces'), 'too-many-spaces')

    def test_preserves_underscores(self):
        """Test that underscores are preserved."""
        self.assertEqual(_slugify_for_hugo('my_page_name'), 'my_page_name')

    def test_strips_leading_trailing_hyphens(self):
        """Test stripping of leading/trailing hyphens."""
        self.assertEqual(_slugify_for_hugo('--test--'), 'test')
        self.assertEqual(_slugify_for_hugo('!@#test!@#'), 'test')

    def test_handles_numbers(self):
        """Test handling of numbers in slugs."""
        self.assertEqual(_slugify_for_hugo('Page 123'), 'page-123')
        self.assertEqual(_slugify_for_hugo('2024 Project'), '2024-project')


# =============================================================================
# Integration Tests
# =============================================================================


class TestPicturesSectionIntegration(unittest.TestCase):
    """Integration tests simulating real-world Pictures section usage."""

    def test_typical_project_note(self):
        """Test a typical Obsidian project note."""
        content = """---
title: Wooden Bookshelf
tags: [woodworking, project]
publish: true
---

# Wooden Bookshelf

I built this bookshelf using reclaimed wood.

## Materials

- Oak planks
- Wood screws
- Finish

## Process

Started by cutting the planks to size...

## Pictures

![[2024/01/bookshelf_01.jpg]]
![[2024/01/bookshelf_02.jpg]]
![[2024/01/bookshelf_process.mp4]]
![[2024/01/bookshelf_final.jpg]]

## Associations

[[Woodworking Projects]]
[[Home Improvement]]
"""
        # Should find Pictures section
        self.assertTrue(has_pictures_section(content))

        # Should extract the Pictures section content
        section = extract_pictures_section(content)
        self.assertIsNotNone(section)
        self.assertIn('bookshelf_01.jpg', section)
        self.assertNotIn('## Associations', section)

        # Should extract all media references
        media = extract_media_from_pictures_section(content)
        self.assertEqual(len(media), 4)
        self.assertEqual(media[0], '2024/01/bookshelf_01.jpg')
        self.assertEqual(media[2], '2024/01/bookshelf_process.mp4')

        # Should be able to remove the Pictures section
        without_pictures = remove_pictures_section(content)
        self.assertNotIn('## Pictures', without_pictures)
        self.assertIn('## Materials', without_pictures)
        self.assertIn('## Associations', without_pictures)

    def test_note_without_pictures(self):
        """Test a note without a Pictures section."""
        content = """---
title: My Blog Post
tags: [python, coding]
publish: true
---

# My Blog Post

Here's some content about Python.

## Code Examples

```python
print("Hello World")
```
"""
        self.assertFalse(has_pictures_section(content))
        self.assertIsNone(extract_pictures_section(content))
        self.assertEqual(extract_media_from_pictures_section(content), [])

    def test_note_with_inline_images_but_no_pictures_section(self):
        """Test note with inline images but no Pictures section."""
        content = """# My Post

Here's an image ![[inline_image.jpg]] in the text.

And another ![[photo.png]] here.
"""
        # Should not detect a Pictures section
        self.assertFalse(has_pictures_section(content))

        # extract_media_from_pictures_section should return empty
        media = extract_media_from_pictures_section(content)
        self.assertEqual(media, [])

    def test_pictures_section_with_descriptions(self):
        """Test Pictures section with image descriptions."""
        content = """## Pictures

The initial mockup:
![[mockup.jpg]]

Work in progress:
![[wip.jpg]]

The finished piece:
![[final.jpg]]
"""
        media = extract_media_from_pictures_section(content)
        self.assertEqual(len(media), 3)
        self.assertEqual(media, ['mockup.jpg', 'wip.jpg', 'final.jpg'])


class TestGalleryGenerationIntegration(unittest.TestCase):
    """Integration tests for gallery generation end-to-end."""

    def test_complete_project_workflow(self):
        """Test complete workflow matching existing project pages."""
        content = """---
title: Wooden Bookshelf
tags: [woodworking, project]
publish: true
---

# Wooden Bookshelf

I built this bookshelf using reclaimed wood.

## Materials

- Oak planks
- Wood screws

## Pictures

![[2024/01/bookshelf_01.jpg]]
![[2024/01/bookshelf_02.jpg]]
![[2024/01/bookshelf_video.mp4]]
![[2024/01/bookshelf_final.jpg]]

## Associations

[[Woodworking Projects]]
"""
        result = generate_gallery_from_obsidian(content, 'wooden_bookshelf')

        # Should have gallery div
        self.assertIn('<div ID="gallery"', result)

        # Should have all media files
        self.assertIn('bookshelf_01.jpg', result)
        self.assertIn('bookshelf_02.jpg', result)
        self.assertIn('bookshelf_video.mp4', result)
        self.assertIn('bookshelf_final.jpg', result)

        # Should have correct base URL
        self.assertIn('{{<s3cdn>}}/projects/wooden_bookshelf/', result)

        # Should have correct anchor structure for each file
        self.assertIn('<a href="bookshelf_01.jpg" data-ngthumb="bookshelf_01.jpg" data-ngdesc="">', result)

    def test_output_matches_existing_format(self):
        """Test that output format matches existing project pages."""
        media_files = ['zippo_01.jpg', 'zippo_02.mp4']
        base_url = '{{<s3cdn>}}/projects/wood_zippo_lighter/'

        result = generate_nanogallery_html(media_files, base_url)

        # Parse out the JSON config to verify structure
        import re
        config_match = re.search(r"data-nanogallery2='(\{.*?\})'", result, re.DOTALL)
        self.assertIsNotNone(config_match)

        config = json.loads(config_match.group(1))

        # Verify itemsBaseURL is set
        self.assertEqual(config['itemsBaseURL'], base_url)

        # Verify key config values match existing format
        self.assertEqual(config['thumbnailWidth'], '250')
        self.assertEqual(config['galleryMaxRows'], 1)

    def test_gallery_with_descriptions_workflow(self):
        """Test gallery generation with custom descriptions."""
        media_files = ['before.jpg', 'during.jpg', 'after.jpg']
        descriptions = ['Before starting', 'Work in progress', 'Final result']
        base_url = 'http://example.com/assets/'

        result = generate_nanogallery_html(
            media_files, base_url, descriptions=descriptions
        )

        self.assertIn('data-ngdesc="Before starting"', result)
        self.assertIn('data-ngdesc="Work in progress"', result)
        self.assertIn('data-ngdesc="Final result"', result)


class TestAssociationsIntegration(unittest.TestCase):
    """Integration tests for Associations section handling."""

    def test_complete_note_with_associations(self):
        """Test processing a complete note with Associations section."""
        content = """---
title: My Blog Post
tags: [coding, python]
publish: true
---

# My Blog Post

This is a great post about Python programming.

## Code Example

```python
print("Hello, world!")
```

## Associations

[[Python Tutorials]]
[[Getting Started with Programming|Programming Guide]]
[[My Other Post]]

## References

Some references here.
"""
        # Test detection
        self.assertTrue(has_associations_section(content))

        # Test extraction
        links = extract_wikilinks_from_associations(content)
        self.assertEqual(len(links), 3)
        self.assertEqual(links[0], ('Python Tutorials', None))
        self.assertEqual(links[1], ('Getting Started with Programming', 'Programming Guide'))
        self.assertEqual(links[2], ('My Other Post', None))

        # Test removal
        removed = remove_associations_section(content)
        self.assertNotIn('## Associations', removed)
        self.assertNotIn('[[Python Tutorials]]', removed)
        self.assertIn('## Code Example', removed)
        self.assertIn('## References', removed)

        # Test conversion
        converted = convert_associations_to_hugo_links(content)
        self.assertIn('## Related', converted)
        self.assertIn('[Python Tutorials](/post/python-tutorials/)', converted)
        self.assertIn('[Programming Guide](/post/getting-started-with-programming/)', converted)
        self.assertIn('[My Other Post](/post/my-other-post/)', converted)
        self.assertIn('## Code Example', converted)
        self.assertIn('## References', converted)

    def test_note_with_both_pictures_and_associations(self):
        """Test note with both Pictures and Associations sections."""
        content = """# My Project

## Description

A project description.

## Pictures

![[image1.jpg]]
![[image2.jpg]]

## Associations

[[Related Project]]
[[Another Project|See also]]

## Notes

Some notes.
"""
        # Both sections should be detected
        self.assertTrue(has_pictures_section(content))
        self.assertTrue(has_associations_section(content))

        # Remove both
        result = remove_pictures_section(content)
        result = remove_associations_section(result)
        self.assertNotIn('## Pictures', result)
        self.assertNotIn('## Associations', result)
        self.assertIn('## Description', result)
        self.assertIn('## Notes', result)

        # Or convert associations and remove pictures
        result2 = remove_pictures_section(content)
        result2 = convert_associations_to_hugo_links(result2)
        self.assertNotIn('## Pictures', result2)
        self.assertIn('## Related', result2)
        self.assertIn('[Related Project](/post/related-project/)', result2)


class TestAssociationsSectionPattern(unittest.TestCase):
    """Tests for the ASSOCIATIONS_SECTION_PATTERN regex."""

    def test_matches_associations(self):
        """Test that pattern matches '## Associations'."""
        match = ASSOCIATIONS_SECTION_PATTERN.search('## Associations')
        self.assertIsNotNone(match)

    def test_matches_association_singular(self):
        """Test that pattern matches '## Association'."""
        match = ASSOCIATIONS_SECTION_PATTERN.search('## Association')
        self.assertIsNotNone(match)

    def test_matches_with_trailing_whitespace(self):
        """Test matching with trailing whitespace."""
        match = ASSOCIATIONS_SECTION_PATTERN.search('## Associations   ')
        self.assertIsNotNone(match)

    def test_case_insensitive(self):
        """Test case insensitivity."""
        self.assertIsNotNone(ASSOCIATIONS_SECTION_PATTERN.search('## ASSOCIATIONS'))
        self.assertIsNotNone(ASSOCIATIONS_SECTION_PATTERN.search('## associations'))
        self.assertIsNotNone(ASSOCIATIONS_SECTION_PATTERN.search('## AssOcIaTiOnS'))

    def test_no_match_level_3(self):
        """Test that level 3 heading doesn't match."""
        match = ASSOCIATIONS_SECTION_PATTERN.search('### Associations')
        self.assertIsNone(match)

    def test_no_match_without_space(self):
        """Test that ##Associations (no space) doesn't match."""
        match = ASSOCIATIONS_SECTION_PATTERN.search('##Associations')
        self.assertIsNone(match)


if __name__ == '__main__':
    unittest.main()
