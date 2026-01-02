#!/usr/bin/env python3
"""
Obsidian to Hugo Publishing CLI Tool

This CLI tool helps publish notes from an Obsidian vault to a Hugo blog.
It handles frontmatter transformation, wikilink conversion, and media embedding.

Usage:
    python publish.py scan          # Find all publishable notes
    python publish.py list          # Show where notes will be published
    python publish.py convert PATH  # Convert a specific note
"""

import argparse
import sys
from pathlib import Path

from obsidian_parser import find_publishable_notes


def format_tags(tags):
    """Format tags list for display."""
    if not tags:
        return "-"
    if isinstance(tags, list):
        return ", ".join(str(t) for t in tags)
    return str(tags)


def format_date(date_val):
    """Format date value for display."""
    if date_val is None:
        return "-"
    # Handle datetime.date objects
    if hasattr(date_val, 'strftime'):
        return date_val.strftime('%Y-%m-%d')
    # Handle string dates
    return str(date_val)


def truncate(text, max_len):
    """Truncate text to max_len, adding ellipsis if needed."""
    text = str(text) if text else "-"
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def print_scan_table(notes):
    """
    Print a formatted table of publishable notes.

    Args:
        notes: List of note dicts with 'path', 'frontmatter', and 'body' keys
    """
    if not notes:
        print("No publishable notes found.")
        return

    # Define column widths
    col_widths = {
        'filename': 30,
        'title': 35,
        'date': 12,
        'tags': 30
    }

    # Print header
    header = (
        f"{'Filename':<{col_widths['filename']}} "
        f"{'Title':<{col_widths['title']}} "
        f"{'Date':<{col_widths['date']}} "
        f"{'Tags':<{col_widths['tags']}}"
    )
    print(header)
    print("-" * len(header))

    # Print each note
    for note in notes:
        fm = note['frontmatter']
        filename = truncate(note['path'].name, col_widths['filename'])
        title = truncate(fm.get('title', '-'), col_widths['title'])
        date = format_date(fm.get('date'))
        tags = truncate(format_tags(fm.get('tags')), col_widths['tags'])

        row = (
            f"{filename:<{col_widths['filename']}} "
            f"{title:<{col_widths['title']}} "
            f"{date:<{col_widths['date']}} "
            f"{tags:<{col_widths['tags']}}"
        )
        print(row)

    # Print summary
    print()
    print(f"Found {len(notes)} publishable note(s).")


def cmd_scan(args):
    """Find and display all notes marked for publishing."""
    vault_path = Path(args.vault) if args.vault else None

    try:
        notes = find_publishable_notes(vault_path=vault_path)
        print_scan_table(notes)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """Show publishable notes with their target Hugo paths."""
    # Will be implemented when obsidian_parser module is created
    print("Listing publishable notes with target paths...")
    print("(Implementation pending: obsidian_parser.find_publishable_notes)")


def cmd_convert(args):
    """Convert a single Obsidian note to Hugo format."""
    note_path = Path(args.path)

    if not note_path.exists():
        print(f"Error: Note not found: {note_path}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[DRY RUN] Would convert: {note_path}")
        print("(Implementation pending: full conversion pipeline)")
    else:
        print(f"Converting: {note_path}")
        print("(Implementation pending: full conversion pipeline)")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="publish",
        description="Publish Obsidian notes to Hugo blog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python publish.py scan
        Scan the Obsidian vault for notes with publish: true

    python publish.py list
        Show all publishable notes and their target paths

    python publish.py convert ~/Notes/Blog/my-post.md
        Convert a specific note to Hugo format

    python publish.py convert ~/Notes/Blog/my-post.md --dry-run
        Preview the conversion without writing files
        """
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
        help="Available commands"
    )

    # scan subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Find all notes marked with publish: true in frontmatter"
    )
    scan_parser.add_argument(
        "--vault",
        help="Path to the Obsidian vault (default: ~/Notes)"
    )
    scan_parser.set_defaults(func=cmd_scan)

    # list subcommand
    list_parser = subparsers.add_parser(
        "list",
        help="Show publishable notes with their target Hugo paths"
    )
    list_parser.set_defaults(func=cmd_list)

    # convert subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert a single Obsidian note to Hugo format"
    )
    convert_parser.add_argument(
        "path",
        help="Path to the Obsidian note to convert"
    )
    convert_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the conversion without writing files"
    )
    convert_parser.set_defaults(func=cmd_convert)

    # Parse arguments and run appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
