#!/usr/bin/env python3
"""
Media Reference Extractor for Obsidian Notes

This module handles extracting and resolving media references from Obsidian
markdown content. It parses the ![[...]] embedding syntax to find all
referenced media files (images, videos, audio).
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional

# Configure module logger
logger = logging.getLogger(__name__)


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


# Default media base path (symlinked from ~/Notes/Media -> ~/Media)
DEFAULT_MEDIA_BASE = Path.home() / "Notes" / "Media"


def resolve_media_path(
    media_reference: str,
    media_base: Optional[Path] = None,
    validate: bool = True
) -> Optional[str]:
    """
    Resolve an Obsidian media reference to an actual file path.

    Takes a media reference from ![[...]] syntax and resolves it to the full
    file path via the Media folder symlink. By default, validates that the
    resolved file exists.

    Args:
        media_reference: The media path as it appears in Obsidian embed syntax
                        (e.g., '2021/06/image.jpg')
        media_base: Base path for media files. Defaults to ~/Notes/Media
                   which is typically symlinked to ~/Media
        validate: If True, checks if the file exists and logs a warning if not.
                 If False, returns the path without validation.

    Returns:
        The full absolute path to the media file (e.g., '/home/adam/Media/2021/06/image.jpg'),
        or None if validate=True and the file doesn't exist.
    """
    if media_base is None:
        media_base = DEFAULT_MEDIA_BASE

    # Normalize the reference - remove any leading slashes
    normalized_ref = media_reference.lstrip('/')

    # Resolve the full path
    # First resolve the media_base to follow any symlinks, then join with the reference
    resolved_base = media_base.resolve()
    full_path = resolved_base / normalized_ref

    # Convert to absolute path string
    full_path_str = str(full_path.resolve())

    if validate:
        if not full_path.exists():
            logger.warning(f"Media file not found: {full_path_str} (reference: {media_reference})")
            return None
        if not full_path.is_file():
            logger.warning(f"Media path is not a file: {full_path_str} (reference: {media_reference})")
            return None

    return full_path_str
