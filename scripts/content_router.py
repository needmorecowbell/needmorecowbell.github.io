#!/usr/bin/env python3
"""
Content Router

This module handles routing content to the appropriate Hugo section based on
explicit content_type frontmatter or inferred from tags.
"""

from typing import Dict, Any, Optional, List

from frontmatter_transformer import VALID_CONTENT_TYPES, validate_content_type


# Tags that indicate content should be routed to the projects section
PROJECT_TAGS = frozenset({
    'project',
    'projects',
    'woodworking',
    'diy',
    'maker',
    'build',
    'craft',
    'crafts',
})

# Tags that indicate content should be routed to the photography section
PHOTOGRAPHY_TAGS = frozenset({
    'photography',
    'photos',
    'photo',
    'travel',
    'trip',
    'gallery',
})

# Default content type when no explicit type or matching tags are found
DEFAULT_CONTENT_TYPE = 'post'


def determine_content_type(
    frontmatter: Dict[str, Any],
    explicit_only: bool = False
) -> str:
    """
    Determine the content type for routing to the appropriate Hugo section.

    The content type determines which Hugo section the content is published to:
    - 'post': Published to content/english/post/
    - 'project': Published to content/english/projects/
    - 'photography': Published to content/english/photography/

    Resolution order:
    1. Explicit content_type field in frontmatter (if valid)
    2. Inferred from tags (project/photography keywords)
    3. Default to 'post'

    Args:
        frontmatter: Dict of parsed frontmatter from the Obsidian note
        explicit_only: If True, only use explicit content_type (don't infer from tags)

    Returns:
        The content type string ('post', 'project', or 'photography')
    """
    # First, check for explicit content_type in frontmatter
    explicit_type = validate_content_type(frontmatter.get('content_type'))
    if explicit_type:
        return explicit_type

    # If explicit_only mode, return default without tag inference
    if explicit_only:
        return DEFAULT_CONTENT_TYPE

    # Try to infer content type from tags
    inferred_type = infer_content_type_from_tags(frontmatter.get('tags'))
    if inferred_type:
        return inferred_type

    # Default to post
    return DEFAULT_CONTENT_TYPE


def infer_content_type_from_tags(tags: Any) -> Optional[str]:
    """
    Infer the content type from a list of tags.

    Checks if any tag matches known project or photography keywords.
    Project tags are checked first, then photography tags.

    Args:
        tags: List of tags (or None/other types)

    Returns:
        The inferred content type ('project' or 'photography'), or None if no match
    """
    if tags is None:
        return None

    # Normalize tags to a list of lowercase strings
    normalized_tags = _normalize_tags_for_matching(tags)

    if not normalized_tags:
        return None

    # Check for project tags first
    if normalized_tags & PROJECT_TAGS:
        return 'project'

    # Check for photography tags
    if normalized_tags & PHOTOGRAPHY_TAGS:
        return 'photography'

    return None


def _normalize_tags_for_matching(tags: Any) -> frozenset:
    """
    Normalize tags to a frozenset of lowercase strings for matching.

    Args:
        tags: List of tags, comma-separated string, or other types

    Returns:
        Frozenset of lowercase tag strings
    """
    if isinstance(tags, list):
        return frozenset(
            str(tag).strip().lower()
            for tag in tags
            if tag is not None and str(tag).strip()
        )

    if isinstance(tags, str):
        if ',' in tags:
            return frozenset(
                tag.strip().lower()
                for tag in tags.split(',')
                if tag.strip()
            )
        tag = tags.strip().lower()
        return frozenset([tag]) if tag else frozenset()

    return frozenset()


def get_hugo_section_path(content_type: str) -> str:
    """
    Get the Hugo section directory path for a given content type.

    Args:
        content_type: The content type ('post', 'project', or 'photography')

    Returns:
        The relative path to the Hugo section directory

    Raises:
        ValueError: If content_type is not valid
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(
            f"Invalid content type: {content_type}. "
            f"Must be one of: {', '.join(VALID_CONTENT_TYPES)}"
        )

    # Map content types to their Hugo section paths
    section_paths = {
        'post': 'content/english/post',
        'project': 'content/english/projects',
        'photography': 'content/english/photography',
    }

    return section_paths[content_type]
