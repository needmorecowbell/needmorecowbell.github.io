#!/usr/bin/env python3
"""
Tests for the syntax_converter module.

Tests wikilink conversion, image embedding, and video/audio embedding functionality.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from syntax_converter import (
    slugify,
    convert_wikilinks,
    convert_embedded_images,
    convert_embedded_media,
)


class TestSlugify(unittest.TestCase):
    """Tests for slugify function."""

    def test_simple_text(self):
        """Test slugifying simple text."""
        self.assertEqual(slugify('Hello World'), 'hello-world')

    def test_already_lowercase(self):
        """Test text that's already lowercase."""
        self.assertEqual(slugify('hello world'), 'hello-world')

    def test_mixed_case(self):
        """Test mixed case text."""
        self.assertEqual(slugify('Hello WORLD Test'), 'hello-world-test')

    def test_special_characters(self):
        """Test removal of special characters."""
        self.assertEqual(slugify("Hello, World! What's Up?"), 'hello-world-whats-up')

    def test_multiple_spaces(self):
        """Test handling of multiple consecutive spaces."""
        self.assertEqual(slugify('Hello   World'), 'hello-world')

    def test_leading_trailing_spaces(self):
        """Test stripping of leading and trailing hyphens."""
        self.assertEqual(slugify('  Hello World  '), 'hello-world')

    def test_numbers(self):
        """Test that numbers are preserved."""
        self.assertEqual(slugify('Post 123 Title'), 'post-123-title')

    def test_underscores(self):
        """Test that underscores are preserved."""
        self.assertEqual(slugify('my_special_post'), 'my_special_post')

    def test_unicode_characters(self):
        """Test that unicode characters are removed and hyphens normalized."""
        # Unicode chars are removed, multiple spaces become hyphens which get normalized
        self.assertEqual(slugify('Hello 日本語 World'), 'hello-world')

    def test_hyphens_preserved(self):
        """Test that hyphens in original text are preserved."""
        self.assertEqual(slugify('my-existing-slug'), 'my-existing-slug')

    def test_empty_string(self):
        """Test empty string input."""
        self.assertEqual(slugify(''), '')

    def test_only_special_chars(self):
        """Test string with only special characters."""
        self.assertEqual(slugify('!@#$%^&*()'), '')


class TestConvertWikilinks(unittest.TestCase):
    """Tests for convert_wikilinks function."""

    def test_simple_wikilink(self):
        """Test converting a simple wikilink."""
        content = 'Check out [[My Page]] for more info.'
        result = convert_wikilinks(content)
        self.assertEqual(result, 'Check out [My Page](/post/my-page/) for more info.')

    def test_wikilink_with_alias(self):
        """Test converting a wikilink with display text alias."""
        content = 'See [[My Long Page Name|this page]] for details.'
        result = convert_wikilinks(content)
        self.assertEqual(result, 'See [this page](/post/my-long-page-name/) for details.')

    def test_multiple_wikilinks(self):
        """Test converting multiple wikilinks in same content."""
        content = 'Link to [[Page One]] and [[Page Two]] here.'
        result = convert_wikilinks(content)
        self.assertEqual(
            result,
            'Link to [Page One](/post/page-one/) and [Page Two](/post/page-two/) here.'
        )

    def test_custom_base_path(self):
        """Test using a custom base path."""
        content = 'Check [[My Page]] here.'
        result = convert_wikilinks(content, base_path='/blog/')
        self.assertEqual(result, 'Check [My Page](/blog/my-page/) here.')

    def test_base_path_trailing_slash_normalization(self):
        """Test that base path trailing slashes are handled."""
        content = '[[Test Page]]'
        result1 = convert_wikilinks(content, base_path='/posts')
        result2 = convert_wikilinks(content, base_path='/posts/')
        self.assertEqual(result1, '[Test Page](/posts/test-page/)')
        self.assertEqual(result2, '[Test Page](/posts/test-page/)')

    def test_does_not_match_embedded_images(self):
        """Test that embedded images (with !) are not converted."""
        content = '![[image.png]] and [[Regular Link]]'
        result = convert_wikilinks(content)
        # The embedded image syntax should remain unchanged
        self.assertIn('![[image.png]]', result)
        self.assertIn('[Regular Link](/post/regular-link/)', result)

    def test_wikilink_with_special_characters(self):
        """Test wikilink page names with special characters."""
        content = "[[What's New in 2024?]]"
        result = convert_wikilinks(content)
        self.assertEqual(result, "[What's New in 2024?](/post/whats-new-in-2024/)")

    def test_wikilink_with_whitespace_in_brackets(self):
        """Test wikilinks with extra whitespace."""
        content = '[[  My Page  ]] and [[ Another Page | Display Text ]]'
        result = convert_wikilinks(content)
        self.assertIn('[My Page](/post/my-page/)', result)
        self.assertIn('[Display Text](/post/another-page/)', result)

    def test_no_wikilinks(self):
        """Test content with no wikilinks."""
        content = 'This is regular markdown with [normal links](http://example.com).'
        result = convert_wikilinks(content)
        self.assertEqual(result, content)

    def test_adjacent_wikilinks(self):
        """Test wikilinks next to each other."""
        content = '[[Page A]][[Page B]]'
        result = convert_wikilinks(content)
        self.assertEqual(result, '[Page A](/post/page-a/)[Page B](/post/page-b/)')

    def test_wikilink_in_list(self):
        """Test wikilinks within markdown lists."""
        content = """- [[First Item]]
- [[Second Item]]
- [[Third Item]]"""
        result = convert_wikilinks(content)
        self.assertIn('[First Item](/post/first-item/)', result)
        self.assertIn('[Second Item](/post/second-item/)', result)
        self.assertIn('[Third Item](/post/third-item/)', result)


class TestConvertEmbeddedImages(unittest.TestCase):
    """Tests for convert_embedded_images function."""

    def test_simple_image_embed(self):
        """Test converting a simple embedded image."""
        content = 'Here is an image: ![[photos/sunset.jpg]]'
        result = convert_embedded_images(content)
        self.assertEqual(
            result,
            'Here is an image: ![sunset]({{<s3cdn>}}/photos/sunset.jpg)'
        )

    def test_image_with_cdn_path(self):
        """Test embedded image with custom CDN path."""
        content = '![[my-image.png]]'
        result = convert_embedded_images(content, cdn_path='/assets')
        self.assertEqual(result, '![my image]({{<s3cdn>}}/assets/my-image.png)')

    def test_image_with_s3cdn_base_url(self):
        """Test embedded image with direct S3CDN URL."""
        content = '![[photos/beach.jpg]]'
        result = convert_embedded_images(
            content,
            s3cdn_base_url='https://s3cdn.example.com/blog/assets'
        )
        self.assertEqual(
            result,
            '![beach](https://s3cdn.example.com/blog/assets/photos/beach.jpg)'
        )

    def test_image_with_media_url_map(self):
        """Test embedded image with media URL mapping."""
        content = '![[2024/vacation/photo.jpg]]'
        url_map = {
            '2024/vacation/photo.jpg': 'https://minio.example.com/bucket/photo.jpg'
        }
        result = convert_embedded_images(content, media_url_map=url_map)
        self.assertEqual(result, '![photo](https://minio.example.com/bucket/photo.jpg)')

    def test_multiple_image_formats(self):
        """Test various image format extensions."""
        formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'ico']
        for fmt in formats:
            content = f'![[image.{fmt}]]'
            result = convert_embedded_images(content)
            self.assertIn(f'/image.{fmt})', result, f"Failed for format: {fmt}")

    def test_case_insensitive_extension(self):
        """Test that image extensions are case insensitive."""
        content = '![[photo.JPG]] and ![[image.PNG]]'
        result = convert_embedded_images(content)
        self.assertIn('/photo.JPG)', result)
        self.assertIn('/image.PNG)', result)

    def test_alt_text_generation(self):
        """Test that alt text is generated from filename."""
        content = '![[my-awesome-photo.jpg]]'
        result = convert_embedded_images(content)
        self.assertIn('![my awesome photo]', result)

    def test_alt_text_with_underscores(self):
        """Test that underscores in filename become spaces in alt text."""
        content = '![[my_cool_image.png]]'
        result = convert_embedded_images(content)
        self.assertIn('![my cool image]', result)

    def test_nested_path_image(self):
        """Test deeply nested image path."""
        content = '![[2024/01/travel/paris/eiffel-tower.jpg]]'
        result = convert_embedded_images(content)
        self.assertEqual(
            result,
            '![eiffel tower]({{<s3cdn>}}/2024/01/travel/paris/eiffel-tower.jpg)'
        )

    def test_does_not_match_non_images(self):
        """Test that non-image extensions are not converted."""
        content = '![[document.pdf]] and ![[video.mp4]]'
        result = convert_embedded_images(content)
        # Non-image embeds should remain unchanged by this function
        self.assertIn('![[document.pdf]]', result)
        self.assertIn('![[video.mp4]]', result)

    def test_whitespace_in_embed_syntax(self):
        """Test handling of whitespace in embed syntax."""
        content = '![[ photos/sunset.jpg ]]'
        result = convert_embedded_images(content)
        self.assertIn('/photos/sunset.jpg)', result)

    def test_multiple_images_in_content(self):
        """Test multiple embedded images in same content."""
        content = """Check out these photos:
![[photo1.jpg]]
![[photo2.png]]
![[photo3.gif]]"""
        result = convert_embedded_images(content)
        self.assertIn('![photo1]({{<s3cdn>}}/photo1.jpg)', result)
        self.assertIn('![photo2]({{<s3cdn>}}/photo2.png)', result)
        self.assertIn('![photo3]({{<s3cdn>}}/photo3.gif)', result)

    def test_image_with_leading_slash(self):
        """Test image path with leading slash is normalized."""
        content = '![[/assets/image.jpg]]'
        result = convert_embedded_images(content)
        # Leading slash should be normalized
        self.assertIn('/assets/image.jpg)', result)

    def test_cdn_path_and_s3cdn_url_priority(self):
        """Test that s3cdn_base_url takes precedence over shortcode."""
        content = '![[image.jpg]]'
        result = convert_embedded_images(
            content,
            cdn_path='/custom',
            s3cdn_base_url='https://cdn.example.com'
        )
        self.assertIn('https://cdn.example.com/custom/image.jpg', result)
        self.assertNotIn('{{<s3cdn>}}', result)

    def test_media_url_map_takes_priority(self):
        """Test that media_url_map takes priority over s3cdn_base_url."""
        content = '![[photo.jpg]]'
        url_map = {'photo.jpg': 'https://direct.url/photo.jpg'}
        result = convert_embedded_images(
            content,
            s3cdn_base_url='https://cdn.example.com',
            media_url_map=url_map
        )
        self.assertEqual(result, '![photo](https://direct.url/photo.jpg)')

    def test_media_url_map_with_empty_value(self):
        """Test that empty values in media_url_map fall back to shortcode."""
        content = '![[photo.jpg]]'
        url_map = {'photo.jpg': ''}  # Empty value
        result = convert_embedded_images(content, media_url_map=url_map)
        self.assertIn('{{<s3cdn>}}', result)


class TestConvertEmbeddedMedia(unittest.TestCase):
    """Tests for convert_embedded_media function."""

    # Video tests

    def test_simple_video_embed(self):
        """Test converting a simple embedded video."""
        content = 'Watch this: ![[videos/demo.mp4]]'
        result = convert_embedded_media(content)
        self.assertIn('<video controls>', result)
        self.assertIn('{{<s3cdn>}}/videos/demo.mp4', result)
        self.assertIn('type="video/mp4"', result)
        self.assertIn('</video>', result)

    def test_video_formats(self):
        """Test various video format extensions and MIME types."""
        test_cases = [
            ('mp4', 'video/mp4'),
            ('webm', 'video/webm'),
            ('ogg', 'video/ogg'),
            ('ogv', 'video/ogg'),
            ('mov', 'video/quicktime'),
            ('avi', 'video/x-msvideo'),
            ('mkv', 'video/x-matroska'),
            ('m4v', 'video/x-m4v'),
        ]
        for ext, mime in test_cases:
            content = f'![[video.{ext}]]'
            result = convert_embedded_media(content)
            self.assertIn('<video controls>', result, f"Failed for {ext}")
            self.assertIn(f'type="{mime}"', result, f"Failed MIME for {ext}")

    def test_video_with_cdn_path(self):
        """Test video embed with custom CDN path."""
        content = '![[clip.mp4]]'
        result = convert_embedded_media(content, cdn_path='/media')
        self.assertIn('{{<s3cdn>}}/media/clip.mp4', result)

    def test_video_with_s3cdn_base_url(self):
        """Test video embed with direct S3CDN URL."""
        content = '![[demo.mp4]]'
        result = convert_embedded_media(
            content,
            s3cdn_base_url='https://cdn.example.com/assets'
        )
        self.assertIn('https://cdn.example.com/assets/demo.mp4', result)
        self.assertNotIn('{{<s3cdn>}}', result)

    def test_video_with_media_url_map(self):
        """Test video embed with media URL mapping."""
        content = '![[clips/intro.mp4]]'
        url_map = {'clips/intro.mp4': 'https://minio.example.com/videos/intro.mp4'}
        result = convert_embedded_media(content, media_url_map=url_map)
        self.assertIn('https://minio.example.com/videos/intro.mp4', result)

    # Audio tests

    def test_simple_audio_embed(self):
        """Test converting a simple embedded audio."""
        content = 'Listen: ![[sounds/podcast.mp3]]'
        result = convert_embedded_media(content)
        self.assertIn('<audio controls>', result)
        self.assertIn('{{<s3cdn>}}/sounds/podcast.mp3', result)
        self.assertIn('type="audio/mpeg"', result)
        self.assertIn('</audio>', result)

    def test_audio_formats(self):
        """Test various audio format extensions and MIME types."""
        test_cases = [
            ('mp3', 'audio/mpeg'),
            ('wav', 'audio/wav'),
            ('oga', 'audio/ogg'),
            ('m4a', 'audio/mp4'),
            ('flac', 'audio/flac'),
            ('aac', 'audio/aac'),
            ('wma', 'audio/x-ms-wma'),
        ]
        for ext, mime in test_cases:
            content = f'![[audio.{ext}]]'
            result = convert_embedded_media(content)
            self.assertIn('<audio controls>', result, f"Failed for {ext}")
            self.assertIn(f'type="{mime}"', result, f"Failed MIME for {ext}")

    def test_audio_with_cdn_path(self):
        """Test audio embed with custom CDN path."""
        content = '![[song.mp3]]'
        result = convert_embedded_media(content, cdn_path='/audio')
        self.assertIn('{{<s3cdn>}}/audio/song.mp3', result)

    def test_audio_with_s3cdn_base_url(self):
        """Test audio embed with direct S3CDN URL."""
        content = '![[podcast.mp3]]'
        result = convert_embedded_media(
            content,
            s3cdn_base_url='https://cdn.example.com'
        )
        self.assertIn('https://cdn.example.com/podcast.mp3', result)

    # Mixed content tests

    def test_multiple_media_types(self):
        """Test mixed video and audio embeds in same content."""
        content = """Here's a video: ![[video.mp4]]
And some audio: ![[audio.mp3]]"""
        result = convert_embedded_media(content)
        self.assertIn('<video controls>', result)
        self.assertIn('<audio controls>', result)
        self.assertIn('type="video/mp4"', result)
        self.assertIn('type="audio/mpeg"', result)

    def test_does_not_match_images(self):
        """Test that image extensions are not converted by this function."""
        content = '![[photo.jpg]] and ![[image.png]]'
        result = convert_embedded_media(content)
        # Images should remain unchanged
        self.assertIn('![[photo.jpg]]', result)
        self.assertIn('![[image.png]]', result)

    def test_case_insensitive_extension(self):
        """Test that media extensions are case insensitive."""
        content = '![[Video.MP4]] and ![[Audio.MP3]]'
        result = convert_embedded_media(content)
        self.assertIn('<video controls>', result)
        self.assertIn('<audio controls>', result)

    def test_nested_path_media(self):
        """Test deeply nested media path."""
        content = '![[2024/01/recordings/interview.mp4]]'
        result = convert_embedded_media(content)
        self.assertIn('/2024/01/recordings/interview.mp4', result)

    def test_whitespace_in_embed_syntax(self):
        """Test handling of whitespace in embed syntax."""
        content = '![[ videos/demo.mp4 ]]'
        result = convert_embedded_media(content)
        self.assertIn('/videos/demo.mp4', result)

    def test_no_media_embeds(self):
        """Test content with no media embeds."""
        content = 'Just regular text with [[wikilink]] and ![[image.jpg]]'
        result = convert_embedded_media(content)
        # Should be unchanged (wikilinks and images are not media)
        self.assertEqual(result, content)

    def test_media_with_leading_slash(self):
        """Test media path with leading slash is normalized."""
        content = '![[/videos/clip.mp4]]'
        result = convert_embedded_media(content)
        self.assertIn('/videos/clip.mp4', result)

    def test_media_url_map_empty_value_fallback(self):
        """Test that empty values in media_url_map fall back to shortcode."""
        content = '![[video.mp4]]'
        url_map = {'video.mp4': ''}  # Empty value
        result = convert_embedded_media(content, media_url_map=url_map)
        self.assertIn('{{<s3cdn>}}', result)


class TestIntegration(unittest.TestCase):
    """Integration tests for combined conversion functions."""

    def test_full_obsidian_content_conversion(self):
        """Test converting a complete Obsidian note with all syntax types."""
        content = """# My Blog Post

Check out [[Related Post]] for more details.

Here's an image:
![[photos/sunset.jpg]]

And a video:
![[videos/demo.mp4]]

Also see [[Another Page|this link]] for reference.
"""
        # Apply all conversions
        result = convert_wikilinks(content)
        result = convert_embedded_images(result)
        result = convert_embedded_media(result)

        # Verify all conversions happened
        self.assertIn('[Related Post](/post/related-post/)', result)
        self.assertIn('[this link](/post/another-page/)', result)
        self.assertIn('![sunset]({{<s3cdn>}}/photos/sunset.jpg)', result)
        self.assertIn('<video controls>', result)
        self.assertIn('{{<s3cdn>}}/videos/demo.mp4', result)

    def test_wikilinks_dont_match_embeds(self):
        """Test that wikilink conversion doesn't affect embedded content."""
        content = '![[image.jpg]] and [[Normal Link]]'

        # Apply wikilink conversion first
        result = convert_wikilinks(content)

        # Embedded image should be untouched
        self.assertIn('![[image.jpg]]', result)
        # Normal link should be converted
        self.assertIn('[Normal Link](/post/normal-link/)', result)

    def test_order_of_operations_doesnt_matter(self):
        """Test that conversion order doesn't affect final result."""
        content = '![[image.png]] and ![[video.mp4]] and [[Wiki Link]]'

        # Order 1: wikilinks -> images -> media
        result1 = convert_wikilinks(content)
        result1 = convert_embedded_images(result1)
        result1 = convert_embedded_media(result1)

        # Order 2: media -> images -> wikilinks
        result2 = convert_embedded_media(content)
        result2 = convert_embedded_images(result2)
        result2 = convert_wikilinks(result2)

        self.assertEqual(result1, result2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
