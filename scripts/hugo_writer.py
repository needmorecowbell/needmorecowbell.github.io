#!/usr/bin/env python3
"""
Hugo Post Writer

This module handles writing properly formatted Hugo markdown files
from transformed frontmatter and converted body content.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


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
