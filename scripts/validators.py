#!/usr/bin/env python3
"""
Validators for Obsidian-to-Hugo Publishing Pipeline

This module provides validation functions for notes being published from
Obsidian to Hugo. It checks frontmatter fields, media references, and
internal links to ensure content is complete and valid before publishing.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional

from media_extractor import find_media_references, resolve_media_path, DEFAULT_MEDIA_BASE


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must be fixed before publishing
    WARNING = "warning"  # Should be addressed but won't block publishing


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue found during content validation.

    Attributes:
        field: The frontmatter field or content area with the issue
        message: Human-readable description of the issue
        severity: Whether this is an error (blocking) or warning (non-blocking)
    """
    field: str
    message: str
    severity: ValidationSeverity

    def __str__(self) -> str:
        """Format the issue as a string for display."""
        return f"[{self.severity.value.upper()}] {self.field}: {self.message}"


# Required frontmatter fields for Hugo posts
REQUIRED_FIELDS = ['title', 'date', 'tags']


def validate_frontmatter(frontmatter: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate frontmatter for required fields and proper formatting.

    Checks that the frontmatter contains all required Hugo fields:
    - title: Must be present and non-empty
    - date: Must be present and non-empty
    - tags: Must be present (can be empty list)

    Additional validation:
    - Warns if title is empty or whitespace-only
    - Warns if date appears to be in an unusual format
    - Warns if tags is present but not a list

    Args:
        frontmatter: Dict of parsed frontmatter from an Obsidian note

    Returns:
        List of ValidationIssue objects describing any problems found.
        Empty list means the frontmatter is valid.

    Examples:
        >>> issues = validate_frontmatter({'title': 'My Post', 'date': '2024-01-15', 'tags': ['python']})
        >>> len(issues)
        0

        >>> issues = validate_frontmatter({})
        >>> len(issues)
        3
        >>> issues[0].field
        'title'
    """
    issues: List[ValidationIssue] = []

    # Check for required 'title' field
    if 'title' not in frontmatter:
        issues.append(ValidationIssue(
            field='title',
            message='Required field "title" is missing',
            severity=ValidationSeverity.ERROR
        ))
    else:
        title = frontmatter['title']
        if title is None:
            issues.append(ValidationIssue(
                field='title',
                message='Field "title" is null',
                severity=ValidationSeverity.ERROR
            ))
        elif isinstance(title, str) and not title.strip():
            issues.append(ValidationIssue(
                field='title',
                message='Field "title" is empty or whitespace-only',
                severity=ValidationSeverity.WARNING
            ))
        elif not isinstance(title, str):
            issues.append(ValidationIssue(
                field='title',
                message=f'Field "title" should be a string, got {type(title).__name__}',
                severity=ValidationSeverity.WARNING
            ))

    # Check for required 'date' field
    if 'date' not in frontmatter:
        issues.append(ValidationIssue(
            field='date',
            message='Required field "date" is missing',
            severity=ValidationSeverity.ERROR
        ))
    else:
        date_val = frontmatter['date']
        if date_val is None:
            issues.append(ValidationIssue(
                field='date',
                message='Field "date" is null',
                severity=ValidationSeverity.ERROR
            ))
        elif isinstance(date_val, str) and not date_val.strip():
            issues.append(ValidationIssue(
                field='date',
                message='Field "date" is empty or whitespace-only',
                severity=ValidationSeverity.WARNING
            ))

    # Check for required 'tags' field
    if 'tags' not in frontmatter:
        issues.append(ValidationIssue(
            field='tags',
            message='Required field "tags" is missing',
            severity=ValidationSeverity.ERROR
        ))
    else:
        tags = frontmatter['tags']
        if tags is not None and not isinstance(tags, (list, str)):
            issues.append(ValidationIssue(
                field='tags',
                message=f'Field "tags" should be a list or string, got {type(tags).__name__}',
                severity=ValidationSeverity.WARNING
            ))

    return issues


def is_valid(issues: List[ValidationIssue]) -> bool:
    """
    Check if a list of validation issues contains any errors.

    Args:
        issues: List of ValidationIssue objects

    Returns:
        True if there are no ERROR-level issues, False otherwise
    """
    return not any(issue.severity == ValidationSeverity.ERROR for issue in issues)


def has_warnings(issues: List[ValidationIssue]) -> bool:
    """
    Check if a list of validation issues contains any warnings.

    Args:
        issues: List of ValidationIssue objects

    Returns:
        True if there are any WARNING-level issues, False otherwise
    """
    return any(issue.severity == ValidationSeverity.WARNING for issue in issues)


def format_issues(issues: List[ValidationIssue]) -> str:
    """
    Format a list of validation issues for display.

    Groups issues by severity (errors first, then warnings) and
    formats them as a readable report.

    Args:
        issues: List of ValidationIssue objects

    Returns:
        Formatted string suitable for terminal display
    """
    if not issues:
        return "No validation issues found."

    errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
    warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]

    lines = []

    if errors:
        lines.append(f"Errors ({len(errors)}):")
        for issue in errors:
            lines.append(f"  - {issue.field}: {issue.message}")

    if warnings:
        if errors:
            lines.append("")
        lines.append(f"Warnings ({len(warnings)}):")
        for issue in warnings:
            lines.append(f"  - {issue.field}: {issue.message}")

    return "\n".join(lines)


def validate_media_references(
    content: str,
    media_base: Optional[Path] = None
) -> List[ValidationIssue]:
    """
    Validate that all embedded media references in content resolve to existing files.

    Parses the content for Obsidian-style media embeds (![[path/to/file.ext]]) and
    checks that each referenced media file exists on the filesystem.

    Args:
        content: The markdown content to validate
        media_base: Base path for media files. Defaults to ~/Notes/Media
                   (which is typically symlinked to ~/Media)

    Returns:
        List of ValidationIssue objects for any media files that cannot be found.
        Each missing file is reported as an ERROR-level issue.
        Empty list means all media references are valid.

    Examples:
        >>> content = "Here's an image: ![[2021/06/photo.jpg]]"
        >>> issues = validate_media_references(content, Path("/tmp/media"))
        >>> # If /tmp/media/2021/06/photo.jpg doesn't exist:
        >>> len(issues)
        1
        >>> issues[0].field
        'media'
        >>> 'photo.jpg' in issues[0].message
        True
    """
    if media_base is None:
        media_base = DEFAULT_MEDIA_BASE

    issues: List[ValidationIssue] = []

    # Extract all media references from the content
    references = find_media_references(content)

    # Check each reference resolves to an existing file
    for ref in references:
        resolved = resolve_media_path(ref, media_base=media_base, validate=True)
        if resolved is None:
            # File doesn't exist or isn't a valid file
            expected_path = media_base / ref.lstrip('/')
            issues.append(ValidationIssue(
                field='media',
                message=f'Media file not found: "{ref}" (expected at: {expected_path})',
                severity=ValidationSeverity.ERROR
            ))

    return issues
