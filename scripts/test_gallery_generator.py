#!/usr/bin/env python3
"""
Tests for the gallery_generator module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from gallery_generator import (
    extract_pictures_section,
    extract_media_from_pictures_section,
    find_media_in_section,
    has_pictures_section,
    get_pictures_section_location,
    remove_pictures_section,
    PICTURES_SECTION_PATTERN,
)


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


class TestIntegration(unittest.TestCase):
    """Integration tests simulating real-world usage."""

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


if __name__ == '__main__':
    unittest.main()
