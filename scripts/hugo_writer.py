#!/usr/bin/env python3
"""
Hugo Post Writer

This module handles writing properly formatted Hugo markdown files
from transformed frontmatter and converted body content.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

from content_router import get_hugo_section_path, determine_content_type


def format_frontmatter(frontmatter: Dict[str, Any]) -> str:
    """
    Format a frontmatter dictionary as a YAML-style Hugo frontmatter block.

    Creates a properly formatted frontmatter block with --- delimiters,
    suitable for Hugo markdown files.

    Args:
        frontmatter: Dictionary containing Hugo frontmatter fields

    Returns:
        A string with the formatted frontmatter block including --- delimiters
    """
    lines = ['---']

    # Define the preferred order of fields
    field_order = [
        'layout', 'title', 'subtitle', 'author', 'date', 'draft',
        'description', 'headerimg', 'tags', 'categories', 'series',
        'aliases', 'weight', 'featured', 'toc'
    ]

    # Track which fields we've already processed
    processed = set()

    # Add fields in preferred order
    for field in field_order:
        if field in frontmatter:
            lines.append(_format_field(field, frontmatter[field]))
            processed.add(field)

    # Add any remaining fields not in the preferred order
    for field, value in frontmatter.items():
        if field not in processed:
            lines.append(_format_field(field, value))

    lines.append('---')
    return '\n'.join(lines)


def _format_field(key: str, value: Any) -> str:
    """
    Format a single frontmatter field as a YAML line.

    Args:
        key: The field name
        value: The field value

    Returns:
        Formatted YAML line (e.g., 'title: "My Post"')
    """
    if value is None:
        return f'{key}:'

    if isinstance(value, bool):
        return f'{key}: {str(value).lower()}'

    if isinstance(value, (int, float)):
        return f'{key}: {value}'

    if isinstance(value, list):
        if not value:
            return f'{key}: []'
        # Format as inline YAML list
        formatted_items = [_quote_if_needed(str(item)) for item in value]
        return f'{key}: [{", ".join(formatted_items)}]'

    # String value - quote if needed
    str_value = str(value)
    return f'{key}: {_quote_if_needed(str_value)}'


def _quote_if_needed(value: str) -> str:
    """
    Add quotes around a string value if it contains special YAML characters.

    Args:
        value: The string value to potentially quote

    Returns:
        The value, quoted if necessary
    """
    # Always quote if empty
    if not value:
        return '""'

    # Check if value starts/ends with whitespace
    if value != value.strip():
        return f'"{value}"'

    # Characters that require quoting in YAML (when present anywhere in string)
    # Note: '-' only needs quoting at start or when it looks like a list
    always_quote_chars = [':', '#', '[', ']', '{', '}', ',', '&', '*', '?', '|',
                          '<', '>', '=', '!', '%', '@', '`', '"', "'", '\n']

    # Check for characters that always need quoting
    needs_quotes = any(char in value for char in always_quote_chars)

    # Check if starts with hyphen followed by space (list item syntax)
    if value.startswith('- '):
        needs_quotes = True

    # Also quote if it looks like a number or boolean
    if value.lower() in ('true', 'false', 'yes', 'no', 'null', 'none'):
        needs_quotes = True

    # Check if it looks like a number
    try:
        float(value)
        needs_quotes = True
    except ValueError:
        pass

    if needs_quotes:
        # Escape any existing double quotes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'

    return value


def get_output_path(
    filename: str,
    content_type: str,
    hugo_root: Optional[Path] = None
) -> Path:
    """
    Determine the full output path for a Hugo post based on content type.

    Uses content_router to determine the appropriate Hugo section directory,
    then constructs the full path including the hugo root and filename.

    Args:
        filename: The filename for the post (with or without .md extension)
        content_type: The content type ('post', 'project', or 'photography')
        hugo_root: The root directory of the Hugo site. Defaults to current directory.

    Returns:
        The full Path where the Hugo post should be written

    Raises:
        ValueError: If content_type is not valid
    """
    if hugo_root is None:
        hugo_root = Path.cwd()
    else:
        hugo_root = Path(hugo_root)

    # Get the section path from content_router
    section_path = get_hugo_section_path(content_type)

    # Ensure filename has .md extension
    if not filename.endswith('.md'):
        filename = f"{filename}.md"

    return hugo_root / section_path / filename


def write_hugo_post(
    frontmatter: Dict[str, Any],
    body: str,
    output_path: Path,
    create_dirs: bool = True
) -> Path:
    """
    Write a properly formatted Hugo markdown file.

    Takes transformed frontmatter and converted body content,
    combines them into a valid Hugo post format, and writes
    to the specified output path.

    Args:
        frontmatter: Dictionary containing Hugo-compatible frontmatter fields
        body: The markdown body content (already converted from Obsidian syntax)
        output_path: Path where the Hugo markdown file should be written
        create_dirs: If True, create parent directories if they don't exist

    Returns:
        The Path where the file was written

    Raises:
        ValueError: If output_path is not a valid path
        OSError: If the file cannot be written
    """
    output_path = Path(output_path)

    if not output_path.suffix:
        output_path = output_path.with_suffix('.md')

    # Create parent directories if needed
    if create_dirs:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Format the frontmatter block
    frontmatter_block = format_frontmatter(frontmatter)

    # Combine frontmatter and body with proper spacing
    # Ensure body starts with a blank line after frontmatter
    body = body.lstrip('\n') if body else ''

    content = f"{frontmatter_block}\n\n{body}"

    # Ensure file ends with a newline
    if not content.endswith('\n'):
        content += '\n'

    # Write the file
    output_path.write_text(content, encoding='utf-8')

    return output_path


def write_hugo_post_routed(
    frontmatter: Dict[str, Any],
    body: str,
    filename: str,
    hugo_root: Optional[Path] = None,
    content_type: Optional[str] = None,
    create_dirs: bool = True
) -> Path:
    """
    Write a Hugo post to the appropriate section based on content type.

    Combines content type determination with writing. If content_type is not
    explicitly provided, it is determined from the frontmatter (explicit
    content_type field or inferred from tags).

    Args:
        frontmatter: Dictionary containing Hugo-compatible frontmatter fields
        body: The markdown body content (already converted from Obsidian syntax)
        filename: The filename for the post (with or without .md extension)
        hugo_root: The root directory of the Hugo site. Defaults to current directory.
        content_type: Explicit content type. If None, determined from frontmatter.
        create_dirs: If True, create parent directories if they don't exist

    Returns:
        The Path where the file was written

    Raises:
        ValueError: If an explicit content_type is provided but is invalid
        OSError: If the file cannot be written
    """
    # Determine content type if not explicitly provided
    if content_type is None:
        content_type = determine_content_type(frontmatter)

    # Get the output path for the determined content type
    output_path = get_output_path(filename, content_type, hugo_root)

    # Write the post
    return write_hugo_post(frontmatter, body, output_path, create_dirs)


def preview_hugo_post(frontmatter: Dict[str, Any], body: str) -> str:
    """
    Generate a preview of the Hugo post content without writing to disk.

    Useful for --dry-run functionality to show what would be written.

    Args:
        frontmatter: Dictionary containing Hugo-compatible frontmatter fields
        body: The markdown body content

    Returns:
        The complete Hugo post content as a string
    """
    frontmatter_block = format_frontmatter(frontmatter)

    body = body.lstrip('\n') if body else ''

    content = f"{frontmatter_block}\n\n{body}"

    if not content.endswith('\n'):
        content += '\n'

    return content
