#!/usr/bin/env python3
"""
Frontmatter Transformer

This module handles converting Obsidian frontmatter to Hugo-compatible format,
ensuring all required fields are present and properly formatted.
"""

import re
import unicodedata
from datetime import datetime, date
from typing import Dict, Any, Optional, Literal

# Valid content types for routing to Hugo sections
VALID_CONTENT_TYPES = ('post', 'project', 'photography')

# Optional fields that are specific to each content type
# These are fields that are commonly used in each section but may not apply to others
CONTENT_TYPE_FIELDS = {
    'post': [
        'author', 'description', 'categories', 'series',
        'layout', 'subtitle', 'headerimg', 'aliases',
        'weight', 'featured', 'toc'
    ],
    'project': [
        'author', 'description', 'aliases', 'weight', 'featured'
    ],
    'photography': [
        'author', 'description', 'aliases', 'weight', 'location'
    ],
}

# Common fields that apply to all content types
COMMON_OPTIONAL_FIELDS = [
    'author', 'description', 'categories', 'series',
    'layout', 'subtitle', 'headerimg', 'aliases',
    'weight', 'featured', 'toc', 'location'
]


def get_optional_fields_for_content_type(content_type: Optional[str] = None) -> list:
    """
    Get the list of optional frontmatter fields for a given content type.

    Args:
        content_type: The content type ('post', 'project', or 'photography')

    Returns:
        List of optional field names appropriate for the content type
    """
    if content_type and content_type in CONTENT_TYPE_FIELDS:
        return CONTENT_TYPE_FIELDS[content_type].copy()
    return COMMON_OPTIONAL_FIELDS.copy()


def validate_content_type(content_type: Any) -> Optional[str]:
    """
    Validate and normalize a content_type value.

    The content_type field controls which Hugo section the content is published to:
    - 'post': Published to content/english/post/
    - 'project': Published to content/english/projects/
    - 'photography': Published to content/english/photography/

    Args:
        content_type: The content_type value to validate (can be string or None)

    Returns:
        The validated content type string if valid, None if not provided or invalid
    """
    if content_type is None:
        return None

    if isinstance(content_type, str):
        normalized = content_type.strip().lower()
        if normalized in VALID_CONTENT_TYPES:
            return normalized

    return None


def generate_slug(title: str, date_str: Optional[str] = None) -> str:
    """
    Generate a URL-friendly slug from a title for use as an output filename.

    The slug is formatted as 'YYYY-MM-DD-title-slug' when a date is provided,
    or just 'title-slug' when no date is given.

    Args:
        title: The title to convert to a slug
        date_str: Optional date string in YYYY-MM-DD format to prepend

    Returns:
        A URL-friendly slug suitable for use as a filename (without extension)
    """
    if not title:
        slug = 'untitled'
    else:
        # Normalize unicode characters (convert accented chars to ASCII equivalents)
        slug = unicodedata.normalize('NFKD', title)
        slug = slug.encode('ascii', 'ignore').decode('ascii')

        # Convert to lowercase
        slug = slug.lower()

        # Replace common separators with hyphens
        slug = slug.replace(' ', '-')
        slug = slug.replace('_', '-')

        # Remove any characters that aren't alphanumeric or hyphens
        slug = re.sub(r'[^a-z0-9\-]', '', slug)

        # Replace multiple consecutive hyphens with a single hyphen
        slug = re.sub(r'-+', '-', slug)

        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        # Handle edge case of empty slug after processing
        if not slug:
            slug = 'untitled'

    # Prepend date if provided
    if date_str:
        return f"{date_str}-{slug}"

    return slug


def extract_title_from_body(body: str) -> Optional[str]:
    """
    Extract the first H1 heading from markdown body content.

    Looks for the first line that starts with a single '#' followed by space
    and extracts the heading text.

    Args:
        body: The markdown body content

    Returns:
        The H1 heading text if found, None otherwise
    """
    if not body:
        return None

    # Match lines that start with exactly one '#' followed by space and text
    # This excludes ## (H2), ### (H3), etc.
    pattern = r'^#\s+(.+?)$'

    for line in body.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            return match.group(1).strip()

    return None


def transform_to_hugo(
    frontmatter: Dict[str, Any],
    body: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert Obsidian frontmatter to Hugo-compatible format.

    Ensures required Hugo fields are present:
    - title: extracted from frontmatter, or from first H1 heading in body if not present
    - date: normalized to ISO format string (YYYY-MM-DD), or with timezone for posts
    - draft: boolean, defaults to False
    - tags: list of strings, defaults to empty list

    Optionally includes:
    - content_type: if valid ('post', 'project', or 'photography'), controls which
      Hugo section the content is published to

    The 'publish' field from Obsidian is removed as it's not needed in Hugo.

    Args:
        frontmatter: Dict of parsed Obsidian frontmatter
        body: Optional markdown body content for extracting title from H1 heading
        content_type: Optional content type to use for formatting (overrides frontmatter)

    Returns:
        Dict with Hugo-compatible frontmatter fields
    """
    hugo_frontmatter = {}

    # Determine content type - parameter overrides frontmatter
    effective_content_type = content_type
    if not effective_content_type:
        effective_content_type = validate_content_type(frontmatter.get('content_type'))

    # Title: required field - try frontmatter first, then body H1 heading
    title = frontmatter.get('title', '')
    if not title and body:
        extracted_title = extract_title_from_body(body)
        if extracted_title:
            title = extracted_title
    hugo_frontmatter['title'] = title

    # Date: required field, normalize based on content type
    hugo_frontmatter['date'] = _normalize_date(
        frontmatter.get('date'),
        content_type=effective_content_type
    )

    # Draft: required field, defaults to False
    hugo_frontmatter['draft'] = _normalize_draft(frontmatter.get('draft'))

    # Tags: required field, normalize to list
    hugo_frontmatter['tags'] = _normalize_tags(frontmatter.get('tags'))

    # Content type: optional field for routing to Hugo sections
    # Only include if explicitly set and valid
    if effective_content_type:
        hugo_frontmatter['content_type'] = effective_content_type

    # Copy over optional Hugo fields based on content type
    # Use content-type-specific fields if available, otherwise use common fields
    if effective_content_type and effective_content_type in CONTENT_TYPE_FIELDS:
        optional_fields = CONTENT_TYPE_FIELDS[effective_content_type]
    else:
        optional_fields = COMMON_OPTIONAL_FIELDS

    for field in optional_fields:
        if field in frontmatter:
            hugo_frontmatter[field] = frontmatter[field]

    # Explicitly do NOT copy 'publish' as it's Obsidian-specific
    # and not needed in Hugo output

    return hugo_frontmatter


def _normalize_date(date_value: Any, content_type: Optional[str] = None) -> str:
    """
    Normalize a date value to ISO format string.

    Handles:
    - datetime objects
    - date objects
    - String dates in various formats
    - None/missing dates (defaults to today)

    Date formatting varies by content type:
    - 'post': Preserves timezone info if present (e.g., 2024-01-15T10:30:00-05:00)
    - 'project' and 'photography': Uses simple YYYY-MM-DD format

    Args:
        date_value: The date value to normalize
        content_type: Optional content type for content-specific formatting

    Returns:
        Date string in appropriate format for the content type
    """
    if date_value is None:
        return datetime.now().strftime('%Y-%m-%d')

    if isinstance(date_value, datetime):
        # For posts, preserve timezone info if present
        if content_type == 'post' and date_value.tzinfo is not None:
            return date_value.isoformat()
        return date_value.strftime('%Y-%m-%d')

    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')

    if isinstance(date_value, str):
        date_str = date_value.strip().strip('"').strip("'")
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        # For posts, preserve ISO 8601 strings with timezone info
        if content_type == 'post':
            # Check if it's already a valid ISO 8601 string with timezone
            iso_tz_patterns = [
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$',  # 2024-01-15T10:30:00-05:00
                r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$',                # 2024-01-15T10:30:00Z
            ]
            for pattern in iso_tz_patterns:
                if re.match(pattern, date_str):
                    return date_str

        # Try parsing various date formats
        date_formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%Y/%m/%d',           # 2024/01/15
            '%Y-%m-%dT%H:%M:%S',  # 2024-01-15T10:30:00
            '%Y-%m-%d %H:%M:%S',  # 2024-01-15 10:30:00
            '%B %d, %Y',          # January 15, 2024
            '%b %d, %Y',          # Jan 15, 2024
            '%d %B %Y',           # 15 January 2024
            '%d %b %Y',           # 15 Jan 2024
            '%m/%d/%Y',           # 01/15/2024
            '%d/%m/%Y',           # 15/01/2024
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If no format matched, return as-is (might already be correct format)
        return date_str

    # Fallback for unexpected types
    return datetime.now().strftime('%Y-%m-%d')


def _normalize_draft(draft_value: Any) -> bool:
    """
    Normalize a draft value to boolean.

    Args:
        draft_value: The draft value to normalize

    Returns:
        Boolean indicating if the post is a draft
    """
    if draft_value is None:
        return False

    if isinstance(draft_value, bool):
        return draft_value

    if isinstance(draft_value, str):
        return draft_value.lower() in ('true', 'yes', '1')

    return bool(draft_value)


def _normalize_tags(tags_value: Any) -> list:
    """
    Normalize tags to a list of strings.

    Handles:
    - List of tags
    - Single tag string
    - Comma-separated string
    - None/missing tags

    Args:
        tags_value: The tags value to normalize

    Returns:
        List of tag strings
    """
    if tags_value is None:
        return []

    if isinstance(tags_value, list):
        # Ensure all items are strings and stripped
        return [str(tag).strip() for tag in tags_value if tag]

    if isinstance(tags_value, str):
        # Handle comma-separated tags
        if ',' in tags_value:
            return [tag.strip() for tag in tags_value.split(',') if tag.strip()]
        # Single tag
        return [tags_value.strip()] if tags_value.strip() else []

    return []
