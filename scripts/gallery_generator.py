#!/usr/bin/env python3
"""
Gallery Generator for Obsidian Notes

This module handles extracting media references from the ## Pictures section
of Obsidian notes and provides functionality for generating nanogallery2 HTML
galleries matching the existing project page format.
"""

import re
from typing import List, Optional, Tuple

from media_extractor import ALL_MEDIA_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


# Pattern to match the ## Pictures section header (case-insensitive)
PICTURES_SECTION_PATTERN = re.compile(
    r'^##\s+Pictures?\s*$',
    re.IGNORECASE | re.MULTILINE
)

# Pattern to match any level 2 heading (to find the end of Pictures section)
NEXT_SECTION_PATTERN = re.compile(
    r'^##\s+\S',
    re.MULTILINE
)


def extract_pictures_section(content: str) -> Optional[str]:
    """
    Extract the ## Pictures section from Obsidian markdown content.

    Finds the "## Pictures" or "## Picture" header and extracts all content
    until the next level-2 heading or end of document.

    Args:
        content: The full markdown content of the Obsidian note

    Returns:
        The content of the Pictures section (excluding the header itself),
        or None if no Pictures section exists.
    """
    if not content:
        return None

    # Find the Pictures section header
    match = PICTURES_SECTION_PATTERN.search(content)
    if not match:
        return None

    # Start of section content is right after the header
    section_start = match.end()

    # Find the next level-2 heading after the Pictures section
    remaining_content = content[section_start:]
    next_section_match = NEXT_SECTION_PATTERN.search(remaining_content)

    if next_section_match:
        # Extract content up to the next section
        section_content = remaining_content[:next_section_match.start()]
    else:
        # No more sections, take everything to the end
        section_content = remaining_content

    # Strip leading/trailing whitespace but preserve internal structure
    return section_content.strip() if section_content.strip() else None


def extract_media_from_pictures_section(content: str) -> List[str]:
    """
    Extract all media references from the Pictures section of an Obsidian note.

    First extracts the Pictures section, then parses it for all embedded media
    references in Obsidian's ![[...]] syntax.

    Args:
        content: The full markdown content of the Obsidian note

    Returns:
        List of media file paths as they appear in the embed syntax
        (e.g., ['2021/06/image.jpg', 'videos/demo.mp4']).
        Returns empty list if no Pictures section or no media found.
    """
    pictures_section = extract_pictures_section(content)
    if not pictures_section:
        return []

    return find_media_in_section(pictures_section)


def find_media_in_section(section_content: str) -> List[str]:
    """
    Find all media references in a section of markdown content.

    Parses the content for Obsidian embed syntax ![[path/to/file.ext]] and
    returns all media file paths.

    Args:
        section_content: The markdown content to parse

    Returns:
        List of media file paths found in the section
    """
    if not section_content:
        return []

    # Build pattern that matches any media extension
    extensions_pattern = '|'.join(sorted(ALL_MEDIA_EXTENSIONS))

    # Pattern for embedded media: ![[path/to/file.ext]]
    # Allows optional whitespace before/after the path
    embed_pattern = re.compile(
        rf'!\[\[\s*([^\]\s][^\]]*\.({extensions_pattern}))\s*\]\]',
        re.IGNORECASE
    )

    references = []
    for match in embed_pattern.finditer(section_content):
        media_path = match.group(1).strip()
        references.append(media_path)

    return references


def has_pictures_section(content: str) -> bool:
    """
    Check if the markdown content has a Pictures section.

    Args:
        content: The full markdown content to check

    Returns:
        True if a Pictures section exists, False otherwise
    """
    if not content:
        return False
    return PICTURES_SECTION_PATTERN.search(content) is not None


def get_pictures_section_location(content: str) -> Optional[Tuple[int, int]]:
    """
    Get the start and end positions of the Pictures section in the content.

    Useful for removing or replacing the Pictures section during conversion.

    Args:
        content: The full markdown content

    Returns:
        Tuple of (start_index, end_index) for the entire Pictures section
        including the header, or None if no Pictures section exists.
    """
    if not content:
        return None

    match = PICTURES_SECTION_PATTERN.search(content)
    if not match:
        return None

    section_start = match.start()

    # Find the next level-2 heading after the Pictures section
    remaining_content = content[match.end():]
    next_section_match = NEXT_SECTION_PATTERN.search(remaining_content)

    if next_section_match:
        section_end = match.end() + next_section_match.start()
    else:
        section_end = len(content)

    return (section_start, section_end)


def remove_pictures_section(content: str) -> str:
    """
    Remove the Pictures section from markdown content.

    Removes the entire "## Pictures" section including header and all content
    up to the next section or end of document.

    Args:
        content: The full markdown content

    Returns:
        The content with the Pictures section removed.
        Returns original content if no Pictures section exists.
    """
    location = get_pictures_section_location(content)
    if not location:
        return content

    start, end = location
    # Remove the section, preserving content before and after
    before = content[:start].rstrip()
    after = content[end:].lstrip()

    if before and after:
        return before + '\n\n' + after
    elif before:
        return before
    else:
        return after
