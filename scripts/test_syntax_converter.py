#!/usr/bin/env python3
"""
Tests for the syntax_converter module.

Uses unittest (standard library) for compatibility.
"""

import unittest
from syntax_converter import slugify, convert_wikilinks, convert_embedded_images, convert_embedded_media


class TestSlugify(unittest.TestCase):
    """Tests for the slugify function."""

    def test_simple_text(self):
        """Test slugifying simple text."""
        self.assertEqual(slugify('Hello World'), 'hello-world')

    def test_already_lowercase(self):
        """Test text that's already lowercase."""
        self.assertEqual(slugify('hello world'), 'hello-world')

    def test_mixed_case(self):
        """Test mixed case text."""
        self.assertEqual(slugify('HeLLo WoRLd'), 'hello-world')

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        self.assertEqual(slugify("Hello, World! How's it going?"), 'hello-world-hows-it-going')

    def test_multiple_spaces(self):
        """Test multiple spaces become single hyphen."""
        self.assertEqual(slugify('Hello    World'), 'hello-world')

    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        self.assertEqual(slugify('Post 123'), 'post-123')

    def test_underscores_preserved(self):
        """Test that underscores are preserved."""
        self.assertEqual(slugify('my_post_title'), 'my_post_title')

    def test_hyphens_preserved(self):
        """Test that existing hyphens are preserved."""
        self.assertEqual(slugify('my-post-title'), 'my-post-title')

    def test_leading_trailing_spaces(self):
        """Test leading/trailing spaces are handled."""
        self.assertEqual(slugify('  Hello World  '), 'hello-world')

    def test_empty_string(self):
        """Test empty string returns empty string."""
        self.assertEqual(slugify(''), '')

    def test_unicode_characters(self):
        """Test that unicode characters are removed (for URL safety)."""
        self.assertEqual(slugify('Café Résumé'), 'caf-rsum')


class TestConvertWikilinks(unittest.TestCase):
    """Tests for the convert_wikilinks function."""

    def test_simple_wikilink(self):
        """Test converting a simple wikilink."""
        content = 'Check out [[My Page]] for more info.'
        expected = 'Check out [My Page](/post/my-page/) for more info.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_multiple_wikilinks(self):
        """Test converting multiple wikilinks in same content."""
        content = 'See [[Page One]] and [[Page Two]] for details.'
        expected = 'See [Page One](/post/page-one/) and [Page Two](/post/page-two/) for details.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_aliased_wikilink(self):
        """Test converting wikilink with display text alias."""
        content = 'Check out [[My Long Page Name|this page]] for more.'
        expected = 'Check out [this page](/post/my-long-page-name/) for more.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_mixed_aliased_and_simple(self):
        """Test mix of aliased and simple wikilinks."""
        content = '[[Simple Link]] and [[Complex Page|easy link]] here.'
        expected = '[Simple Link](/post/simple-link/) and [easy link](/post/complex-page/) here.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_at_line_start(self):
        """Test wikilink at the start of a line."""
        content = '[[My Page]] is interesting.'
        expected = '[My Page](/post/my-page/) is interesting.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_at_line_end(self):
        """Test wikilink at the end of a line."""
        content = 'See more at [[My Page]]'
        expected = 'See more at [My Page](/post/my-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_alone_on_line(self):
        """Test wikilink as entire line content."""
        content = '[[Standalone Page]]'
        expected = '[Standalone Page](/post/standalone-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_preserves_regular_markdown_links(self):
        """Test that standard markdown links are not affected."""
        content = 'Regular [link](https://example.com) stays the same.'
        expected = 'Regular [link](https://example.com) stays the same.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_does_not_match_embedded_images(self):
        """Test that embedded images ![[image.jpg]] are NOT converted."""
        content = 'Here is an image: ![[my-image.jpg]]'
        expected = 'Here is an image: ![[my-image.jpg]]'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_mixed_wikilinks_and_embeds(self):
        """Test content with both wikilinks and embeds."""
        content = 'See [[My Page]] and look at ![[image.png]] for reference.'
        expected = 'See [My Page](/post/my-page/) and look at ![[image.png]] for reference.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_custom_base_path(self):
        """Test using a custom base path."""
        content = 'Check out [[My Project]].'
        expected = 'Check out [My Project](/projects/my-project/).'
        self.assertEqual(convert_wikilinks(content, base_path='/projects/'), expected)

    def test_base_path_without_trailing_slash(self):
        """Test base path without trailing slash."""
        content = '[[My Page]]'
        expected = '[My Page](/post/my-page/)'
        self.assertEqual(convert_wikilinks(content, base_path='/post'), expected)

    def test_whitespace_in_link_text(self):
        """Test that extra whitespace in link text is handled."""
        content = '[[  Spaced Page  ]]'
        expected = '[Spaced Page](/post/spaced-page/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_whitespace_in_alias(self):
        """Test that extra whitespace in alias is handled."""
        content = '[[Page Name |  Display Text  ]]'
        expected = '[Display Text](/post/page-name/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_no_wikilinks(self):
        """Test content with no wikilinks returns unchanged."""
        content = 'Just regular markdown text with no special links.'
        expected = 'Just regular markdown text with no special links.'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_empty_content(self):
        """Test empty content returns empty string."""
        self.assertEqual(convert_wikilinks(''), '')

    def test_multiline_content(self):
        """Test wikilinks across multiple lines."""
        content = """First line with [[Link One]].

Second paragraph has [[Link Two|custom text]].

And [[Link Three]] at the end."""
        expected = """First line with [Link One](/post/link-one/).

Second paragraph has [custom text](/post/link-two/).

And [Link Three](/post/link-three/) at the end."""
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_with_numbers(self):
        """Test wikilink containing numbers."""
        content = '[[2024 Goals]]'
        expected = '[2024 Goals](/post/2024-goals/)'
        self.assertEqual(convert_wikilinks(content), expected)

    def test_wikilink_with_special_chars_in_name(self):
        """Test wikilink with special characters in page name."""
        content = "[[What's New?]]"
        expected = "[What's New?](/post/whats-new/)"
        self.assertEqual(convert_wikilinks(content), expected)


class TestConvertEmbeddedImages(unittest.TestCase):
    """Tests for the convert_embedded_images function."""

    def test_simple_image(self):
        """Test converting a simple embedded image."""
        content = 'Here is an image: ![[my-photo.jpg]]'
        expected = 'Here is an image: ![my photo]({{<s3cdn>}}/my-photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_with_path(self):
        """Test converting embedded image with subdirectory path."""
        content = '![[assets/images/photo.png]]'
        expected = '![photo]({{<s3cdn>}}/assets/images/photo.png)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_multiple_images(self):
        """Test converting multiple embedded images."""
        content = '![[image1.jpg]] and ![[folder/image2.png]]'
        expected = '![image1]({{<s3cdn>}}/image1.jpg) and ![image2]({{<s3cdn>}}/folder/image2.png)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_jpg(self):
        """Test jpg extension."""
        content = '![[photo.jpg]]'
        expected = '![photo]({{<s3cdn>}}/photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_jpeg(self):
        """Test jpeg extension."""
        content = '![[photo.jpeg]]'
        expected = '![photo]({{<s3cdn>}}/photo.jpeg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_png(self):
        """Test png extension."""
        content = '![[photo.png]]'
        expected = '![photo]({{<s3cdn>}}/photo.png)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_gif(self):
        """Test gif extension."""
        content = '![[animation.gif]]'
        expected = '![animation]({{<s3cdn>}}/animation.gif)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_webp(self):
        """Test webp extension."""
        content = '![[modern.webp]]'
        expected = '![modern]({{<s3cdn>}}/modern.webp)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_svg(self):
        """Test svg extension."""
        content = '![[icon.svg]]'
        expected = '![icon]({{<s3cdn>}}/icon.svg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_bmp(self):
        """Test bmp extension."""
        content = '![[legacy.bmp]]'
        expected = '![legacy]({{<s3cdn>}}/legacy.bmp)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_tiff(self):
        """Test tiff extension."""
        content = '![[scan.tiff]]'
        expected = '![scan]({{<s3cdn>}}/scan.tiff)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_tif(self):
        """Test tif extension (short form)."""
        content = '![[scan.tif]]'
        expected = '![scan]({{<s3cdn>}}/scan.tif)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_image_extensions_ico(self):
        """Test ico extension."""
        content = '![[favicon.ico]]'
        expected = '![favicon]({{<s3cdn>}}/favicon.ico)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_case_insensitive_extension(self):
        """Test that extensions are case insensitive."""
        content = '![[photo.JPG]] and ![[other.PNG]]'
        expected = '![photo]({{<s3cdn>}}/photo.JPG) and ![other]({{<s3cdn>}}/other.PNG)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_does_not_match_video(self):
        """Test that video files are NOT converted (handled by separate function)."""
        content = '![[video.mp4]]'
        expected = '![[video.mp4]]'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_does_not_match_audio(self):
        """Test that audio files are NOT converted."""
        content = '![[audio.mp3]]'
        expected = '![[audio.mp3]]'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_does_not_match_pdf(self):
        """Test that PDF files are NOT converted."""
        content = '![[document.pdf]]'
        expected = '![[document.pdf]]'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_does_not_match_wikilinks(self):
        """Test that wikilinks (without !) are NOT converted."""
        content = '[[My Page]] should stay as wikilink'
        expected = '[[My Page]] should stay as wikilink'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_alt_text_from_filename(self):
        """Test that alt text is derived from filename."""
        content = '![[my_awesome_photo.jpg]]'
        expected = '![my awesome photo]({{<s3cdn>}}/my_awesome_photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_alt_text_with_hyphens(self):
        """Test alt text conversion removes hyphens."""
        content = '![[my-cool-image.png]]'
        expected = '![my cool image]({{<s3cdn>}}/my-cool-image.png)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_custom_cdn_path(self):
        """Test using a custom CDN path prefix."""
        content = '![[photo.jpg]]'
        expected = '![photo]({{<s3cdn>}}/images/blog/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, cdn_path='/images/blog'), expected)

    def test_custom_cdn_path_with_trailing_slash(self):
        """Test custom CDN path with trailing slash is normalized."""
        content = '![[photo.jpg]]'
        expected = '![photo]({{<s3cdn>}}/assets/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, cdn_path='/assets/'), expected)

    def test_image_path_with_leading_slash(self):
        """Test image path with leading slash is normalized."""
        content = '![[/images/photo.jpg]]'
        expected = '![photo]({{<s3cdn>}}/images/photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_no_embedded_images(self):
        """Test content with no embedded images returns unchanged."""
        content = 'Just regular text with no images.'
        expected = 'Just regular text with no images.'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_empty_content(self):
        """Test empty content returns empty string."""
        self.assertEqual(convert_embedded_images(''), '')

    def test_multiline_content(self):
        """Test embedded images across multiple lines."""
        content = """First image: ![[photo1.jpg]]

Second paragraph with ![[folder/photo2.png]].

End of content."""
        expected = """First image: ![photo1]({{<s3cdn>}}/photo1.jpg)

Second paragraph with ![photo2]({{<s3cdn>}}/folder/photo2.png).

End of content."""
        self.assertEqual(convert_embedded_images(content), expected)

    def test_mixed_images_and_wikilinks(self):
        """Test content with both embedded images and wikilinks."""
        content = 'See [[My Page]] and look at ![[image.png]] for reference.'
        expected = 'See [[My Page]] and look at ![image]({{<s3cdn>}}/image.png) for reference.'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_deeply_nested_path(self):
        """Test image with deeply nested path."""
        content = '![[a/b/c/d/e/photo.jpg]]'
        expected = '![photo]({{<s3cdn>}}/a/b/c/d/e/photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)

    def test_whitespace_in_embed(self):
        """Test handling of whitespace in embed syntax."""
        content = '![[  photo.jpg  ]]'
        expected = '![photo]({{<s3cdn>}}/photo.jpg)'
        self.assertEqual(convert_embedded_images(content), expected)


class TestConvertEmbeddedMedia(unittest.TestCase):
    """Tests for the convert_embedded_media function."""

    # =====================
    # Video Tests
    # =====================

    def test_simple_video_mp4(self):
        """Test converting a simple mp4 video embed."""
        content = 'Check out this video: ![[my-video.mp4]]'
        expected = 'Check out this video: <video controls><source src="{{<s3cdn>}}/my-video.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_webm(self):
        """Test webm video format."""
        content = '![[clip.webm]]'
        expected = '<video controls><source src="{{<s3cdn>}}/clip.webm" type="video/webm"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_ogg(self):
        """Test ogg video format."""
        content = '![[video.ogg]]'
        expected = '<video controls><source src="{{<s3cdn>}}/video.ogg" type="video/ogg"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_ogv(self):
        """Test ogv video format."""
        content = '![[video.ogv]]'
        expected = '<video controls><source src="{{<s3cdn>}}/video.ogv" type="video/ogg"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_mov(self):
        """Test mov video format."""
        content = '![[recording.mov]]'
        expected = '<video controls><source src="{{<s3cdn>}}/recording.mov" type="video/quicktime"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_avi(self):
        """Test avi video format."""
        content = '![[old-video.avi]]'
        expected = '<video controls><source src="{{<s3cdn>}}/old-video.avi" type="video/x-msvideo"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_mkv(self):
        """Test mkv video format."""
        content = '![[movie.mkv]]'
        expected = '<video controls><source src="{{<s3cdn>}}/movie.mkv" type="video/x-matroska"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_m4v(self):
        """Test m4v video format."""
        content = '![[clip.m4v]]'
        expected = '<video controls><source src="{{<s3cdn>}}/clip.m4v" type="video/x-m4v"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_with_path(self):
        """Test video with subdirectory path."""
        content = '![[media/videos/tutorial.mp4]]'
        expected = '<video controls><source src="{{<s3cdn>}}/media/videos/tutorial.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_video_case_insensitive(self):
        """Test that video extensions are case insensitive."""
        content = '![[video.MP4]] and ![[other.WebM]]'
        expected = '<video controls><source src="{{<s3cdn>}}/video.MP4" type="video/mp4"></video> and <video controls><source src="{{<s3cdn>}}/other.WebM" type="video/webm"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    # =====================
    # Audio Tests
    # =====================

    def test_simple_audio_mp3(self):
        """Test converting a simple mp3 audio embed."""
        content = 'Listen to this: ![[song.mp3]]'
        expected = 'Listen to this: <audio controls><source src="{{<s3cdn>}}/song.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_wav(self):
        """Test wav audio format."""
        content = '![[sound.wav]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/sound.wav" type="audio/wav"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_oga(self):
        """Test oga (ogg audio) format."""
        content = '![[audio.oga]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/audio.oga" type="audio/ogg"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_m4a(self):
        """Test m4a audio format."""
        content = '![[podcast.m4a]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/podcast.m4a" type="audio/mp4"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_flac(self):
        """Test flac audio format."""
        content = '![[lossless.flac]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/lossless.flac" type="audio/flac"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_aac(self):
        """Test aac audio format."""
        content = '![[track.aac]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/track.aac" type="audio/aac"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_wma(self):
        """Test wma audio format."""
        content = '![[legacy.wma]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/legacy.wma" type="audio/x-ms-wma"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_with_path(self):
        """Test audio with subdirectory path."""
        content = '![[music/albums/track.mp3]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/music/albums/track.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_audio_case_insensitive(self):
        """Test that audio extensions are case insensitive."""
        content = '![[song.MP3]] and ![[other.FLAC]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/song.MP3" type="audio/mpeg"></audio> and <audio controls><source src="{{<s3cdn>}}/other.FLAC" type="audio/flac"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    # =====================
    # Mixed and Edge Cases
    # =====================

    def test_multiple_videos(self):
        """Test converting multiple video embeds."""
        content = '![[video1.mp4]] and ![[video2.webm]]'
        expected = '<video controls><source src="{{<s3cdn>}}/video1.mp4" type="video/mp4"></video> and <video controls><source src="{{<s3cdn>}}/video2.webm" type="video/webm"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_multiple_audio(self):
        """Test converting multiple audio embeds."""
        content = '![[song1.mp3]] and ![[song2.wav]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/song1.mp3" type="audio/mpeg"></audio> and <audio controls><source src="{{<s3cdn>}}/song2.wav" type="audio/wav"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_mixed_video_and_audio(self):
        """Test converting mixed video and audio embeds."""
        content = 'Watch ![[tutorial.mp4]] and listen to ![[intro.mp3]]'
        expected = 'Watch <video controls><source src="{{<s3cdn>}}/tutorial.mp4" type="video/mp4"></video> and listen to <audio controls><source src="{{<s3cdn>}}/intro.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_custom_cdn_path(self):
        """Test using a custom CDN path prefix."""
        content = '![[video.mp4]]'
        expected = '<video controls><source src="{{<s3cdn>}}/media/videos/video.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content, cdn_path='/media/videos'), expected)

    def test_custom_cdn_path_with_trailing_slash(self):
        """Test custom CDN path with trailing slash is normalized."""
        content = '![[song.mp3]]'
        expected = '<audio controls><source src="{{<s3cdn>}}/audio/song.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content, cdn_path='/audio/'), expected)

    def test_media_path_with_leading_slash(self):
        """Test media path with leading slash is normalized."""
        content = '![[/videos/clip.mp4]]'
        expected = '<video controls><source src="{{<s3cdn>}}/videos/clip.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_whitespace_in_embed(self):
        """Test handling of whitespace in embed syntax."""
        content = '![[  video.mp4  ]]'
        expected = '<video controls><source src="{{<s3cdn>}}/video.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_does_not_match_images(self):
        """Test that image files are NOT converted (handled by separate function)."""
        content = '![[photo.jpg]] and ![[image.png]]'
        expected = '![[photo.jpg]] and ![[image.png]]'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_does_not_match_pdf(self):
        """Test that PDF files are NOT converted."""
        content = '![[document.pdf]]'
        expected = '![[document.pdf]]'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_does_not_match_wikilinks(self):
        """Test that wikilinks (without !) are NOT converted."""
        content = '[[My Page]] should stay as wikilink'
        expected = '[[My Page]] should stay as wikilink'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_no_embedded_media(self):
        """Test content with no embedded media returns unchanged."""
        content = 'Just regular text with no media.'
        expected = 'Just regular text with no media.'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_empty_content(self):
        """Test empty content returns empty string."""
        self.assertEqual(convert_embedded_media(''), '')

    def test_multiline_content(self):
        """Test embedded media across multiple lines."""
        content = """First video: ![[clip1.mp4]]

Second paragraph with ![[folder/clip2.webm]].

And some audio: ![[song.mp3]]"""
        expected = """First video: <video controls><source src="{{<s3cdn>}}/clip1.mp4" type="video/mp4"></video>

Second paragraph with <video controls><source src="{{<s3cdn>}}/folder/clip2.webm" type="video/webm"></video>.

And some audio: <audio controls><source src="{{<s3cdn>}}/song.mp3" type="audio/mpeg"></audio>"""
        self.assertEqual(convert_embedded_media(content), expected)

    def test_mixed_media_images_wikilinks(self):
        """Test content with media, images, and wikilinks."""
        content = 'See [[My Page]] and watch ![[video.mp4]] and view ![[photo.jpg]]'
        # Only video should be converted, image and wikilink should remain
        expected = 'See [[My Page]] and watch <video controls><source src="{{<s3cdn>}}/video.mp4" type="video/mp4"></video> and view ![[photo.jpg]]'
        self.assertEqual(convert_embedded_media(content), expected)

    def test_deeply_nested_path(self):
        """Test media with deeply nested path."""
        content = '![[a/b/c/d/e/video.mp4]]'
        expected = '<video controls><source src="{{<s3cdn>}}/a/b/c/d/e/video.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content), expected)


class TestMediaUrlMapImages(unittest.TestCase):
    """Tests for convert_embedded_images with media_url_map parameter."""

    def test_uses_minio_url_when_available(self):
        """Test that MinIO URL is used when present in mapping."""
        content = '![[2021/06/photo.jpg]]'
        media_url_map = {
            '2021/06/photo.jpg': 'https://minio.example.com/bucket/assets/2021/06/photo.jpg'
        }
        expected = '![photo](https://minio.example.com/bucket/assets/2021/06/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_falls_back_to_s3cdn_when_not_in_map(self):
        """Test fallback to s3cdn shortcode when image not in mapping."""
        content = '![[photo.jpg]]'
        media_url_map = {
            'other/image.jpg': 'https://minio.example.com/bucket/assets/other/image.jpg'
        }
        expected = '![photo]({{<s3cdn>}}/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_falls_back_when_url_is_none(self):
        """Test fallback to s3cdn when mapping value is None (failed upload)."""
        content = '![[failed/photo.jpg]]'
        media_url_map = {
            'failed/photo.jpg': None
        }
        expected = '![photo]({{<s3cdn>}}/failed/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_normalizes_leading_slash_in_content(self):
        """Test that leading slash in content is normalized for lookup."""
        content = '![[/2021/06/photo.jpg]]'
        media_url_map = {
            '2021/06/photo.jpg': 'https://minio.example.com/bucket/assets/2021/06/photo.jpg'
        }
        expected = '![photo](https://minio.example.com/bucket/assets/2021/06/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_multiple_images_mixed_mapping(self):
        """Test multiple images where some are in map and some are not."""
        content = '![[mapped.jpg]] and ![[unmapped.png]]'
        media_url_map = {
            'mapped.jpg': 'https://minio.example.com/bucket/assets/mapped.jpg'
        }
        expected = '![mapped](https://minio.example.com/bucket/assets/mapped.jpg) and ![unmapped]({{<s3cdn>}}/unmapped.png)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_empty_media_url_map(self):
        """Test with empty media_url_map (falls back to s3cdn)."""
        content = '![[photo.jpg]]'
        media_url_map = {}
        expected = '![photo]({{<s3cdn>}}/photo.jpg)'
        self.assertEqual(convert_embedded_images(content, media_url_map=media_url_map), expected)

    def test_cdn_path_ignored_when_minio_url_available(self):
        """Test that cdn_path is ignored when MinIO URL is available."""
        content = '![[photo.jpg]]'
        media_url_map = {
            'photo.jpg': 'https://minio.example.com/bucket/assets/photo.jpg'
        }
        # cdn_path should be ignored since we have a MinIO URL
        expected = '![photo](https://minio.example.com/bucket/assets/photo.jpg)'
        self.assertEqual(
            convert_embedded_images(content, cdn_path='/custom/path', media_url_map=media_url_map),
            expected
        )

    def test_cdn_path_used_when_not_in_map(self):
        """Test that cdn_path is used for images not in the mapping."""
        content = '![[photo.jpg]]'
        media_url_map = {}
        expected = '![photo]({{<s3cdn>}}/custom/path/photo.jpg)'
        self.assertEqual(
            convert_embedded_images(content, cdn_path='/custom/path', media_url_map=media_url_map),
            expected
        )


class TestMediaUrlMapMedia(unittest.TestCase):
    """Tests for convert_embedded_media with media_url_map parameter."""

    def test_video_uses_minio_url_when_available(self):
        """Test that MinIO URL is used for video when present in mapping."""
        content = '![[videos/demo.mp4]]'
        media_url_map = {
            'videos/demo.mp4': 'https://minio.example.com/bucket/assets/videos/demo.mp4'
        }
        expected = '<video controls><source src="https://minio.example.com/bucket/assets/videos/demo.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_audio_uses_minio_url_when_available(self):
        """Test that MinIO URL is used for audio when present in mapping."""
        content = '![[music/song.mp3]]'
        media_url_map = {
            'music/song.mp3': 'https://minio.example.com/bucket/assets/music/song.mp3'
        }
        expected = '<audio controls><source src="https://minio.example.com/bucket/assets/music/song.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_video_falls_back_to_s3cdn_when_not_in_map(self):
        """Test fallback to s3cdn shortcode for video not in mapping."""
        content = '![[video.mp4]]'
        media_url_map = {
            'other/video.webm': 'https://minio.example.com/bucket/assets/other/video.webm'
        }
        expected = '<video controls><source src="{{<s3cdn>}}/video.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_audio_falls_back_when_url_is_none(self):
        """Test fallback to s3cdn for audio when mapping value is None."""
        content = '![[failed/audio.mp3]]'
        media_url_map = {
            'failed/audio.mp3': None
        }
        expected = '<audio controls><source src="{{<s3cdn>}}/failed/audio.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_normalizes_leading_slash_for_video(self):
        """Test that leading slash is normalized for video lookup."""
        content = '![[/videos/clip.mp4]]'
        media_url_map = {
            'videos/clip.mp4': 'https://minio.example.com/bucket/assets/videos/clip.mp4'
        }
        expected = '<video controls><source src="https://minio.example.com/bucket/assets/videos/clip.mp4" type="video/mp4"></video>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_mixed_video_audio_with_mapping(self):
        """Test mixed video and audio with partial mapping."""
        content = '![[video.mp4]] and ![[song.mp3]]'
        media_url_map = {
            'video.mp4': 'https://minio.example.com/bucket/assets/video.mp4'
            # song.mp3 not in mapping
        }
        expected = (
            '<video controls><source src="https://minio.example.com/bucket/assets/video.mp4" type="video/mp4"></video>'
            ' and '
            '<audio controls><source src="{{<s3cdn>}}/song.mp3" type="audio/mpeg"></audio>'
        )
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_empty_media_url_map_for_video(self):
        """Test with empty media_url_map for video (falls back to s3cdn)."""
        content = '![[clip.webm]]'
        media_url_map = {}
        expected = '<video controls><source src="{{<s3cdn>}}/clip.webm" type="video/webm"></video>'
        self.assertEqual(convert_embedded_media(content, media_url_map=media_url_map), expected)

    def test_cdn_path_ignored_when_minio_url_available_for_audio(self):
        """Test that cdn_path is ignored for audio when MinIO URL is available."""
        content = '![[podcast.mp3]]'
        media_url_map = {
            'podcast.mp3': 'https://minio.example.com/bucket/assets/podcast.mp3'
        }
        expected = '<audio controls><source src="https://minio.example.com/bucket/assets/podcast.mp3" type="audio/mpeg"></audio>'
        self.assertEqual(
            convert_embedded_media(content, cdn_path='/audio/files', media_url_map=media_url_map),
            expected
        )

    def test_cdn_path_used_when_video_not_in_map(self):
        """Test that cdn_path is used for video not in the mapping."""
        content = '![[clip.mp4]]'
        media_url_map = {}
        expected = '<video controls><source src="{{<s3cdn>}}/videos/clip.mp4" type="video/mp4"></video>'
        self.assertEqual(
            convert_embedded_media(content, cdn_path='/videos', media_url_map=media_url_map),
            expected
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
