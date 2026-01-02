#!/usr/bin/env python3
"""
Media Reference Extractor for Obsidian Notes

This module handles extracting and resolving media references from Obsidian
markdown content. It parses the ![[...]] embedding syntax to find all
referenced media files (images, videos, audio).
"""

import re
from typing import List


# Supported image extensions
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'tif', 'ico'}

# Supported video extensions
VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'ogv', 'mov', 'avi', 'mkv', 'm4v'}

# Supported audio extensions
AUDIO_EXTENSIONS = {'mp3', 'wav', 'oga', 'm4a', 'flac', 'aac', 'wma'}

# All supported media extensions
ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def find_media_references(content: str) -> List[str]:
    """
    Parse Obsidian markdown content and extract all embedded media paths.

    Finds all occurrences of the ![[path/to/file.ext]] syntax and returns
    the media paths. Only includes files with recognized media extensions
    (images, videos, audio).

    Args:
        content: The markdown content to parse

    Returns:
        List of media file paths as they appear in the embed syntax
        (e.g., ['2021/06/image.jpg', 'videos/demo.mp4'])
    """
    # Build pattern that matches any media extension
    extensions_pattern = '|'.join(sorted(ALL_MEDIA_EXTENSIONS))

    # Pattern for embedded media: ![[path/to/file.ext]]
    # Captures the full path including filename
    # Allows optional whitespace before/after the path
    embed_pattern = re.compile(
        rf'!\[\[\s*([^\]\s][^\]]*\.({extensions_pattern}))\s*\]\]',
        re.IGNORECASE
    )

    references = []
    for match in embed_pattern.finditer(content):
        media_path = match.group(1).strip()
        references.append(media_path)

    return references
