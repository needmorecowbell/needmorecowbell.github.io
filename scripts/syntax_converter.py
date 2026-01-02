#!/usr/bin/env python3
"""
Obsidian to Hugo Syntax Converter

This module handles converting Obsidian-specific markdown syntax to Hugo-compatible
formats, including wikilinks, embedded images, and embedded media.
"""

import re
from typing import Callable


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


def convert_embedded_images(content: str, cdn_path: str = '') -> str:
    """
    Convert Obsidian embedded image syntax to Hugo s3cdn shortcode format.

    Transforms ![[path/to/image.jpg]] syntax to markdown images using the s3cdn
    shortcode: ![image]({{<s3cdn>}}/path/to/image.jpg)

    Supports common image formats: jpg, jpeg, png, gif, webp, svg, bmp, tiff, ico

    Args:
        content: The markdown content containing embedded images
        cdn_path: Optional path prefix to prepend to image paths (default: '')

    Returns:
        Content with embedded images converted to Hugo s3cdn shortcode format
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

        # Build the s3cdn path
        if cdn_path:
            full_path = f"{cdn_path.rstrip('/')}/{image_path.lstrip('/')}"
        else:
            full_path = f"/{image_path.lstrip('/')}"

        # Return markdown image with s3cdn shortcode
        # The shortcode {{<s3cdn>}} outputs the CDN base URL
        return f'![{alt_text}]({{{{<s3cdn>}}}}{full_path})'

    return embed_pattern.sub(replace_embedded_image, content)
