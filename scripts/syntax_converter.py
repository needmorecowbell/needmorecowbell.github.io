#!/usr/bin/env python3
"""
Obsidian to Hugo Syntax Converter

This module handles converting Obsidian-specific markdown syntax to Hugo-compatible
formats, including wikilinks, embedded images, and embedded media.

Supports two modes for S3CDN URLs:
1. Shortcode mode (default): Outputs {{<s3cdn>}} shortcodes that Hugo expands at render time
2. Direct URL mode: Uses the actual S3CDN URL from Hugo config via config_manager

Usage with config_manager:
    from syntax_converter import convert_embedded_images, get_s3cdn_base_url

    # Get the S3CDN URL for the current environment
    s3cdn_url = get_s3cdn_base_url('production')  # or 'development'

    # Convert images using direct URLs
    content = convert_embedded_images(content, s3cdn_base_url=s3cdn_url)
"""

import re
from typing import Callable, Dict, Optional

# Lazy import for config_manager to avoid circular imports and allow
# syntax_converter to work standalone without config_manager
_config_manager = None


def _get_config_manager():
    """Lazily import config_manager module."""
    global _config_manager
    if _config_manager is None:
        try:
            from . import config_manager as cm
            _config_manager = cm
        except ImportError:
            # Handle direct script execution
            import config_manager as cm
            _config_manager = cm
    return _config_manager


def get_s3cdn_base_url(environment: str = 'production') -> str:
    """
    Get the S3CDN base URL from Hugo configuration.

    This is a convenience wrapper around config_manager.get_s3cdn_url()
    for use in content conversion pipelines.

    Args:
        environment: Hugo environment name ('production' or 'development')

    Returns:
        The S3CDN base URL string (e.g., 'https://s3cdn.617a.net/amblog/assets')

    Raises:
        config_manager.HugoConfigError: If S3CDN is not configured
    """
    cm = _get_config_manager()
    return cm.get_s3cdn_url(environment)


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Args:
        text: The text to slugify (e.g., page title)

    Returns:
        A lowercase, hyphen-separated slug
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    # Remove any characters that aren't alphanumeric, hyphens, or underscores
    slug = re.sub(r'[^a-z0-9\-_]', '', slug)
    # Replace multiple consecutive hyphens with a single hyphen
    slug = re.sub(r'-+', '-', slug)
    # Strip leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def convert_wikilinks(content: str, base_path: str = '/post/') -> str:
    """
    Convert Obsidian wikilinks to standard markdown links.

    Transforms [[Page Name]] syntax to [Page Name](/post/page-name/) links.
    Also handles aliased links: [[Page Name|Display Text]] becomes
    [Display Text](/post/page-name/).

    Args:
        content: The markdown content containing wikilinks
        base_path: The base URL path for links (default: '/post/')

    Returns:
        Content with wikilinks converted to standard markdown links
    """
    # Pattern for wikilinks: [[Page Name]] or [[Page Name|Display Text]]
    # Does NOT match embedded content (which starts with !)
    wikilink_pattern = re.compile(r'(?<!!)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

    def replace_wikilink(match: re.Match) -> str:
        page_name = match.group(1).strip()
        display_text = match.group(2)

        if display_text:
            display_text = display_text.strip()
        else:
            display_text = page_name

        slug = slugify(page_name)
        url = f"{base_path.rstrip('/')}/{slug}/"

        return f'[{display_text}]({url})'

    return wikilink_pattern.sub(replace_wikilink, content)


def convert_embedded_images(
    content: str,
    cdn_path: str = '',
    media_url_map: Optional[Dict[str, str]] = None,
    s3cdn_base_url: Optional[str] = None
) -> str:
    """
    Convert Obsidian embedded image syntax to Hugo s3cdn shortcode format.

    Transforms ![[path/to/image.jpg]] syntax to markdown images using the s3cdn
    shortcode: ![image]({{<s3cdn>}}/path/to/image.jpg)

    If a media_url_map is provided and contains the image path, the full MinIO URL
    is used instead of the s3cdn shortcode path.

    If s3cdn_base_url is provided, the actual URL is used instead of the {{<s3cdn>}}
    shortcode. This is useful when generating content that needs resolved URLs
    (e.g., for previews or non-Hugo rendering).

    Supports common image formats: jpg, jpeg, png, gif, webp, svg, bmp, tiff, ico

    Args:
        content: The markdown content containing embedded images
        cdn_path: Optional path prefix to prepend to image paths (default: '')
        media_url_map: Optional dict mapping Obsidian media references to their
                      MinIO URLs (e.g., {'2021/06/photo.jpg': 'https://...'})
        s3cdn_base_url: Optional S3CDN base URL from Hugo config. If provided,
                       uses this URL instead of {{<s3cdn>}} shortcode.
                       Get this value using get_s3cdn_base_url() or
                       config_manager.get_s3cdn_url().

    Returns:
        Content with embedded images converted to Hugo s3cdn shortcode format
        or direct URLs if media_url_map or s3cdn_base_url is provided
    """
    # Pattern for embedded images: ![[path/to/image.ext]]
    # Only matches common image extensions
    # Allows optional whitespace before/after the path
    image_extensions = r'\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff?|ico)'
    embed_pattern = re.compile(
        rf'!\[\[\s*([^\]\s][^\]]*{image_extensions})\s*\]\]',
        re.IGNORECASE
    )

    def replace_embedded_image(match: re.Match) -> str:
        image_path = match.group(1).strip()

        # Extract just the filename for alt text (without extension)
        # Handle both forward slashes and backslashes
        filename = image_path.replace('\\', '/').split('/')[-1]
        alt_text = re.sub(r'\.[^.]+$', '', filename)  # Remove extension
        # Clean up alt text: replace hyphens/underscores with spaces
        alt_text = alt_text.replace('-', ' ').replace('_', ' ')

        # Check if we have a MinIO URL for this image
        if media_url_map is not None:
            # Try to find the image in the mapping (normalize leading slashes)
            normalized_path = image_path.lstrip('/')
            if normalized_path in media_url_map and media_url_map[normalized_path]:
                return f'![{alt_text}]({media_url_map[normalized_path]})'

        # Build the path suffix
        if cdn_path:
            full_path = f"{cdn_path.rstrip('/')}/{image_path.lstrip('/')}"
        else:
            full_path = f"/{image_path.lstrip('/')}"

        # Use direct S3CDN URL if provided, otherwise use shortcode
        if s3cdn_base_url:
            # Use the actual S3CDN URL from Hugo config
            base_url = s3cdn_base_url.rstrip('/')
            return f'![{alt_text}]({base_url}{full_path})'
        else:
            # Return markdown image with s3cdn shortcode
            # The shortcode {{<s3cdn>}} outputs the CDN base URL
            return f'![{alt_text}]({{{{<s3cdn>}}}}{full_path})'

    return embed_pattern.sub(replace_embedded_image, content)


def convert_embedded_media(
    content: str,
    cdn_path: str = '',
    media_url_map: Optional[Dict[str, str]] = None,
    s3cdn_base_url: Optional[str] = None
) -> str:
    """
    Convert Obsidian embedded video/audio syntax to HTML5 media tags with s3cdn paths.

    Transforms ![[path/to/video.mp4]] syntax to HTML5 video tags:
    <video controls><source src="{{<s3cdn>}}/path/to/video.mp4" type="video/mp4"></video>

    Transforms ![[path/to/audio.mp3]] syntax to HTML5 audio tags:
    <audio controls><source src="{{<s3cdn>}}/path/to/audio.mp3" type="audio/mpeg"></audio>

    If a media_url_map is provided and contains the media path, the full MinIO URL
    is used instead of the s3cdn shortcode path.

    If s3cdn_base_url is provided, the actual URL is used instead of the {{<s3cdn>}}
    shortcode. This is useful when generating content that needs resolved URLs
    (e.g., for previews or non-Hugo rendering).

    Supported video formats: mp4, webm, ogg, mov, avi, mkv, m4v
    Supported audio formats: mp3, wav, ogg, m4a, flac, aac, wma

    Args:
        content: The markdown content containing embedded media
        cdn_path: Optional path prefix to prepend to media paths (default: '')
        media_url_map: Optional dict mapping Obsidian media references to their
                      MinIO URLs (e.g., {'videos/demo.mp4': 'https://...'})
        s3cdn_base_url: Optional S3CDN base URL from Hugo config. If provided,
                       uses this URL instead of {{<s3cdn>}} shortcode.
                       Get this value using get_s3cdn_base_url() or
                       config_manager.get_s3cdn_url().

    Returns:
        Content with embedded media converted to HTML5 tags with s3cdn shortcodes
        or direct URLs if media_url_map or s3cdn_base_url is provided
    """
    # Video extensions and their MIME types
    video_types = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'ogg': 'video/ogg',
        'ogv': 'video/ogg',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'm4v': 'video/x-m4v',
    }

    # Audio extensions and their MIME types
    audio_types = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'oga': 'audio/ogg',
        'm4a': 'audio/mp4',
        'flac': 'audio/flac',
        'aac': 'audio/aac',
        'wma': 'audio/x-ms-wma',
    }

    # Build regex patterns for video and audio extensions
    video_extensions = '|'.join(video_types.keys())
    audio_extensions = '|'.join(audio_types.keys())
    media_extensions = f'({video_extensions}|{audio_extensions})'

    # Pattern for embedded media: ![[path/to/file.ext]]
    embed_pattern = re.compile(
        rf'!\[\[\s*([^\]\s][^\]]*\.({media_extensions}))\s*\]\]',
        re.IGNORECASE
    )

    def replace_embedded_media(match: re.Match) -> str:
        media_path = match.group(1).strip()
        extension = match.group(2).lower()

        # Check if we have a MinIO URL for this media
        src_url = None
        if media_url_map is not None:
            # Try to find the media in the mapping (normalize leading slashes)
            normalized_path = media_path.lstrip('/')
            if normalized_path in media_url_map and media_url_map[normalized_path]:
                src_url = media_url_map[normalized_path]

        # Fall back to s3cdn URL or shortcode if no URL found
        if src_url is None:
            if cdn_path:
                full_path = f"{cdn_path.rstrip('/')}/{media_path.lstrip('/')}"
            else:
                full_path = f"/{media_path.lstrip('/')}"

            # Use direct S3CDN URL if provided, otherwise use shortcode
            if s3cdn_base_url:
                base_url = s3cdn_base_url.rstrip('/')
                src_url = f"{base_url}{full_path}"
            else:
                src_url = f"{{{{<s3cdn>}}}}{full_path}"

        # Determine if this is video or audio and get MIME type
        if extension in video_types:
            mime_type = video_types[extension]
            return (
                f'<video controls>'
                f'<source src="{src_url}" type="{mime_type}">'
                f'</video>'
            )
        elif extension in audio_types:
            mime_type = audio_types[extension]
            return (
                f'<audio controls>'
                f'<source src="{src_url}" type="{mime_type}">'
                f'</audio>'
            )
        else:
            # Should not reach here, but return original if unknown
            return match.group(0)

    return embed_pattern.sub(replace_embedded_media, content)
