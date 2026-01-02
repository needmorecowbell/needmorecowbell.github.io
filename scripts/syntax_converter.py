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
