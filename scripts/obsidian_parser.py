#!/usr/bin/env python3
"""
Obsidian Markdown Parser

This module handles parsing Obsidian markdown files, extracting YAML frontmatter
and separating it from the body content.
"""

import re
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import yaml


# Regex to match YAML frontmatter block (--- delimited)
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n?', re.DOTALL)


def parse_obsidian_note(file_path: Path) -> Tuple[Dict[str, Any], str]:
    """
    Parse an Obsidian markdown file and extract frontmatter and body content.

    Args:
        file_path: Path to the Obsidian markdown file

    Returns:
        A tuple of (frontmatter_dict, body_content)
        - frontmatter_dict: Python dict of the YAML frontmatter (empty dict if none)
        - body_content: The markdown body after the frontmatter

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the frontmatter is invalid YAML
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Note not found: {file_path}")

    content = file_path.read_text(encoding='utf-8')

    return parse_frontmatter(content)


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter from markdown content.

    Args:
        content: Raw markdown content as a string

    Returns:
        A tuple of (frontmatter_dict, body_content)
        - frontmatter_dict: Python dict of the YAML frontmatter (empty dict if none)
        - body_content: The markdown body after the frontmatter
    """
    match = FRONTMATTER_PATTERN.match(content)

    if match:
        yaml_content = match.group(1)
        frontmatter = yaml.safe_load(yaml_content) or {}
        body = content[match.end():]
    else:
        frontmatter = {}
        body = content

    return frontmatter, body


def has_publish_flag(frontmatter: Dict[str, Any]) -> bool:
    """
    Check if frontmatter contains publish: true.

    Args:
        frontmatter: Dict of parsed frontmatter

    Returns:
        True if publish flag is set to true, False otherwise
    """
    return frontmatter.get('publish', False) is True


def find_publishable_notes(
    vault_path: Optional[Path] = None,
    skip_dirs: Optional[list] = None
) -> list:
    """
    Recursively scan an Obsidian vault for notes with publish: true frontmatter.

    Args:
        vault_path: Path to the Obsidian vault. Defaults to ~/Notes
        skip_dirs: List of directory names to skip. Defaults to ['People']

    Returns:
        List of dicts, each containing:
            - path: Path to the note file
            - frontmatter: Dict of the parsed frontmatter
            - body: The markdown body content
    """
    if vault_path is None:
        vault_path = Path.home() / 'Notes'

    if skip_dirs is None:
        skip_dirs = ['People']

    vault_path = Path(vault_path)

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault not found: {vault_path}")

    if not vault_path.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {vault_path}")

    publishable_notes = []

    for md_file in vault_path.rglob('*.md'):
        # Skip files in excluded directories
        if any(skip_dir in md_file.parts for skip_dir in skip_dirs):
            continue

        try:
            frontmatter, body = parse_obsidian_note(md_file)

            if has_publish_flag(frontmatter):
                publishable_notes.append({
                    'path': md_file,
                    'frontmatter': frontmatter,
                    'body': body
                })
        except yaml.YAMLError:
            # Skip files with invalid YAML frontmatter
            continue
        except Exception:
            # Skip files that can't be read for any reason
            continue

    return publishable_notes
