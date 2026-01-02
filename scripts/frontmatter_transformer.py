#!/usr/bin/env python3
"""
Frontmatter Transformer

This module handles converting Obsidian frontmatter to Hugo-compatible format,
ensuring all required fields are present and properly formatted.
"""

import re
from datetime import datetime, date
from typing import Dict, Any, Optional


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


def transform_to_hugo(frontmatter: Dict[str, Any], body: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert Obsidian frontmatter to Hugo-compatible format.

    Ensures required Hugo fields are present:
    - title: extracted from frontmatter, or from first H1 heading in body if not present
    - date: normalized to ISO format string (YYYY-MM-DD)
    - draft: boolean, defaults to False
    - tags: list of strings, defaults to empty list

    The 'publish' field from Obsidian is removed as it's not needed in Hugo.

    Args:
        frontmatter: Dict of parsed Obsidian frontmatter
        body: Optional markdown body content for extracting title from H1 heading

    Returns:
        Dict with Hugo-compatible frontmatter fields
    """
    hugo_frontmatter = {}

    # Title: required field - try frontmatter first, then body H1 heading
    title = frontmatter.get('title', '')
    if not title and body:
        extracted_title = extract_title_from_body(body)
        if extracted_title:
            title = extracted_title
    hugo_frontmatter['title'] = title

    # Date: required field, normalize to string
    hugo_frontmatter['date'] = _normalize_date(frontmatter.get('date'))

    # Draft: required field, defaults to False
    hugo_frontmatter['draft'] = _normalize_draft(frontmatter.get('draft'))

    # Tags: required field, normalize to list
    hugo_frontmatter['tags'] = _normalize_tags(frontmatter.get('tags'))

    # Copy over other common Hugo fields if present
    optional_fields = [
        'author', 'description', 'categories', 'series',
        'layout', 'subtitle', 'headerimg', 'aliases',
        'weight', 'featured', 'toc'
    ]

    for field in optional_fields:
        if field in frontmatter:
            hugo_frontmatter[field] = frontmatter[field]

    # Explicitly do NOT copy 'publish' as it's Obsidian-specific
    # and not needed in Hugo output

    return hugo_frontmatter


def _normalize_date(date_value: Any) -> str:
    """
    Normalize a date value to ISO format string (YYYY-MM-DD).

    Handles:
    - datetime objects
    - date objects
    - String dates in various formats
    - None/missing dates (defaults to today)

    Args:
        date_value: The date value to normalize

    Returns:
        Date string in YYYY-MM-DD format
    """
    if date_value is None:
        return datetime.now().strftime('%Y-%m-%d')

    if isinstance(date_value, datetime):
        return date_value.strftime('%Y-%m-%d')

    if isinstance(date_value, date):
        return date_value.strftime('%Y-%m-%d')

    if isinstance(date_value, str):
        date_str = date_value.strip().strip('"').strip("'")
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

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
