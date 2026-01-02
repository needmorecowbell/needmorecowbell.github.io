#!/usr/bin/env python3
"""
Validators for Obsidian-to-Hugo Publishing Pipeline

This module provides validation functions for notes being published from
Obsidian to Hugo. It checks frontmatter fields, media references, and
internal links to ensure content is complete and valid before publishing.
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from media_extractor import find_media_references, resolve_media_path, DEFAULT_MEDIA_BASE, ALL_MEDIA_EXTENSIONS
from syntax_converter import slugify


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


# Default vault path for Obsidian notes
DEFAULT_VAULT_PATH = Path.home() / "Notes"

# Default Hugo root path
DEFAULT_HUGO_ROOT = Path(__file__).parent.parent


def find_wikilinks(content: str) -> List[str]:
    """
    Extract all internal wikilinks (non-media) from markdown content.

    Finds all occurrences of [[Page Name]] or [[Page Name|Alias]] syntax,
    excluding embedded media (which start with !).

    Args:
        content: The markdown content to parse

    Returns:
        List of page names (without aliases) as they appear in the wikilinks.
        For example, [[My Page|Display Text]] returns 'My Page'.
    """
    # Build pattern to exclude media extensions
    extensions_pattern = '|'.join(sorted(ALL_MEDIA_EXTENSIONS))

    # Pattern for wikilinks: [[Page Name]] or [[Page Name|Display Text]]
    # Must NOT start with ! (that's an embed)
    # Must NOT end with a media file extension
    wikilink_pattern = re.compile(
        rf'(?<!!)\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    )

    links = []
    for match in wikilink_pattern.finditer(content):
        page_name = match.group(1).strip()
        # Skip if this is a media file reference
        ext = page_name.rsplit('.', 1)[-1].lower() if '.' in page_name else ''
        if ext not in ALL_MEDIA_EXTENSIONS:
            links.append(page_name)

    return links


def find_note_in_vault(
    page_name: str,
    vault_path: Optional[Path] = None
) -> Optional[Path]:
    """
    Search for a note by name in the Obsidian vault.

    Obsidian allows linking to notes by their filename (without path or extension).
    This function searches the vault for a matching .md file.

    Args:
        page_name: The page name from a wikilink (e.g., "My Note" or "folder/My Note")
        vault_path: Path to the Obsidian vault. Defaults to ~/Notes

    Returns:
        Path to the matching note file if found, None otherwise
    """
    if vault_path is None:
        vault_path = DEFAULT_VAULT_PATH

    vault_path = Path(vault_path)

    if not vault_path.exists() or not vault_path.is_dir():
        return None

    # If page_name includes a path, check for exact match first
    if '/' in page_name:
        exact_path = vault_path / f"{page_name}.md"
        if exact_path.exists() and exact_path.is_file():
            return exact_path

    # Extract just the note name (without path)
    note_name = page_name.split('/')[-1] if '/' in page_name else page_name

    # Search for any .md file matching the note name (case-insensitive)
    note_name_lower = note_name.lower()

    for md_file in vault_path.rglob('*.md'):
        if md_file.stem.lower() == note_name_lower:
            return md_file

    return None


def find_note_in_hugo(
    page_name: str,
    hugo_root: Optional[Path] = None
) -> Optional[Path]:
    """
    Search for a published note in Hugo content directories.

    Checks if a note with the given name has been published to Hugo.
    The check is based on the slugified version of the page name.

    Args:
        page_name: The page name from a wikilink
        hugo_root: Path to the Hugo site root. Defaults to project root.

    Returns:
        Path to the matching Hugo post if found, None otherwise
    """
    if hugo_root is None:
        hugo_root = DEFAULT_HUGO_ROOT

    hugo_root = Path(hugo_root)

    # Hugo content directories to search
    content_dirs = [
        hugo_root / 'content' / 'english' / 'post',
        hugo_root / 'content' / 'english' / 'projects',
        hugo_root / 'content' / 'english' / 'photography',
    ]

    # Generate the slug for the page name
    slug = slugify(page_name)

    # Common filename patterns for Hugo posts
    potential_filenames = [
        f"{slug}.md",
        f"{slug}.markdown",
    ]

    for content_dir in content_dirs:
        if not content_dir.exists():
            continue

        for filename in potential_filenames:
            post_path = content_dir / filename
            if post_path.exists() and post_path.is_file():
                return post_path

        # Also check for files containing the slug (for dated filenames like 2017-01-04-my-post.md)
        for md_file in content_dir.glob('*.md'):
            # Check if the slug is contained in the filename
            file_slug = md_file.stem.lower()
            if slug in file_slug or file_slug.endswith(slug):
                return md_file

    return None


def validate_internal_links(
    content: str,
    vault_path: Optional[Path] = None,
    hugo_root: Optional[Path] = None
) -> List[ValidationIssue]:
    """
    Validate that all internal wikilinks point to existing notes.

    Checks each wikilink in the content to verify it references either:
    1. A note that exists in the Obsidian vault, OR
    2. A note that has already been published to Hugo

    Args:
        content: The markdown content to validate
        vault_path: Path to the Obsidian vault. Defaults to ~/Notes
        hugo_root: Path to the Hugo site root. Defaults to project root.

    Returns:
        List of ValidationIssue objects for any broken links.
        Each broken link is reported as an ERROR-level issue.
        Empty list means all internal links are valid.

    Examples:
        >>> content = "See also [[My Other Post]] for more details."
        >>> issues = validate_internal_links(content)
        >>> # If "My Other Post" doesn't exist in vault or Hugo:
        >>> len(issues)
        1
        >>> issues[0].field
        'internal_link'
    """
    if vault_path is None:
        vault_path = DEFAULT_VAULT_PATH

    if hugo_root is None:
        hugo_root = DEFAULT_HUGO_ROOT

    issues: List[ValidationIssue] = []

    # Extract all wikilinks from the content
    wikilinks = find_wikilinks(content)

    # Check each link
    for link in wikilinks:
        # First check if it exists in the vault
        vault_note = find_note_in_vault(link, vault_path=vault_path)
        if vault_note is not None:
            continue

        # Then check if it exists in Hugo
        hugo_note = find_note_in_hugo(link, hugo_root=hugo_root)
        if hugo_note is not None:
            continue

        # Link is broken - neither in vault nor published
        issues.append(ValidationIssue(
            field='internal_link',
            message=f'Broken link: "{link}" - note not found in vault or Hugo content',
            severity=ValidationSeverity.ERROR
        ))

    return issues
