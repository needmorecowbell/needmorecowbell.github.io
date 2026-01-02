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


# Default nanogallery2 configuration matching existing project pages
DEFAULT_NANOGALLERY_CONFIG = {
    "thumbnailWidth": "250",
    "thumbnailHeight": "250",
    "thumbnailBorderVertical": 1,
    "thumbnailBorderHorizontal": 1,
    "thumbnailLabel": {
        "position": "overImageOnBottom",
        "displayDescription": True
    },
    "thumbnailHoverEffect2": "labelAppear75|descriptionSlideUp",
    "galleryDisplayMode": "pagination",
    "galleryMaxRows": 1,
    "thumbnailAlignment": "center",
    "thumbnailOpenImage": True,
    "viewerTools": {
        "topLeft": "pageCounter, label",
        "topRight": "playPauseButton, rotateLeft, rotateRight, fullscreenButton, closeButton"
    }
}


def generate_nanogallery_html(
    media_files: List[str],
    base_url: str,
    thumbnail_suffix: Optional[str] = None,
    descriptions: Optional[List[str]] = None,
    config: Optional[dict] = None
) -> str:
    """
    Generate nanogallery2 HTML structure for a list of media files.

    Creates the HTML div and anchor tags matching the format used in existing
    project pages on the blog. Supports both images and videos.

    Args:
        media_files: List of media filenames (e.g., ['image1.jpg', 'video.mp4']).
                    These should be just the filenames, not full paths.
        base_url: The base URL for the media files. Use Hugo shortcode syntax
                 like '{{<s3cdn>}}/projects/my_project/' for S3 CDN URLs.
        thumbnail_suffix: Optional suffix to add to thumbnail filenames.
                         If None, thumbnails use the same filename as full images.
                         E.g., '_thumb' would make 'image.jpg' -> 'image_thumb.jpg'
        descriptions: Optional list of descriptions for each media file.
                     Must match length of media_files if provided.
        config: Optional custom nanogallery2 configuration dict.
               Merged with defaults (custom values override defaults).

    Returns:
        The complete HTML string for the nanogallery2 gallery.
        Returns empty string if media_files is empty.

    Raises:
        ValueError: If descriptions is provided but has different length than media_files.
    """
    import json
    import os

    if not media_files:
        return ""

    if descriptions is not None and len(descriptions) != len(media_files):
        raise ValueError(
            f"descriptions length ({len(descriptions)}) must match "
            f"media_files length ({len(media_files)})"
        )

    # Build the configuration
    gallery_config = DEFAULT_NANOGALLERY_CONFIG.copy()

    # Deep merge the nested dicts
    if config:
        for key, value in config.items():
            if isinstance(value, dict) and key in gallery_config and isinstance(gallery_config[key], dict):
                gallery_config[key] = {**gallery_config[key], **value}
            else:
                gallery_config[key] = value

    # Add the base URL to config
    gallery_config["itemsBaseURL"] = base_url

    # Format config as JSON with proper indentation
    # Using a custom approach to match the existing format in project files
    config_json = json.dumps(gallery_config, indent=4)

    # Build the anchor tags for each media file
    anchors = []
    for i, media_file in enumerate(media_files):
        # Get just the filename if a path was provided
        filename = os.path.basename(media_file)

        # Determine thumbnail filename
        if thumbnail_suffix:
            name, ext = os.path.splitext(filename)
            thumb_filename = f"{name}{thumbnail_suffix}{ext}"
        else:
            thumb_filename = filename

        # Get description
        desc = descriptions[i] if descriptions else ""

        # Build anchor tag
        anchor = f'    <a href="{filename}" data-ngthumb="{thumb_filename}" data-ngdesc="{desc}"></a>'
        anchors.append(anchor)

    # Build the complete HTML
    anchors_html = "\n".join(anchors)

    html = f"""<div ID="gallery" data-nanogallery2='{config_json}'>
{anchors_html}
</div>"""

    return html


def generate_gallery_from_obsidian(
    content: str,
    project_slug: str,
    cdn_shortcode: str = "{{<s3cdn>}}"
) -> Optional[str]:
    """
    Generate nanogallery2 HTML from an Obsidian note's Pictures section.

    Convenience function that extracts media from the Pictures section
    and generates the gallery HTML with the standard project URL structure.

    Args:
        content: The full markdown content of the Obsidian note.
        project_slug: The project identifier used in the URL path
                     (e.g., 'wood_zippo_lighter' -> /projects/wood_zippo_lighter/).
        cdn_shortcode: The Hugo shortcode for the CDN base URL.
                      Defaults to '{{<s3cdn>}}' for the blog's S3 CDN.

    Returns:
        The nanogallery2 HTML string, or None if no Pictures section
        or no media files found.
    """
    import os

    # Extract media from Pictures section
    media_refs = extract_media_from_pictures_section(content)
    if not media_refs:
        return None

    # Extract just the filenames from the paths
    filenames = [os.path.basename(ref) for ref in media_refs]

    # Build the base URL
    base_url = f"{cdn_shortcode}/projects/{project_slug}/"

    return generate_nanogallery_html(filenames, base_url)
