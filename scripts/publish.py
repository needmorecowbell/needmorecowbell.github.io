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

from obsidian_parser import find_publishable_notes, parse_obsidian_note
from frontmatter_transformer import generate_slug, transform_to_hugo
from syntax_converter import convert_wikilinks, convert_embedded_images, convert_embedded_media
from hugo_writer import write_hugo_post, preview_hugo_post

# Default Hugo content output directory (relative to blog root)
DEFAULT_OUTPUT_DIR = "content/english/post"


def get_target_path(frontmatter, body, output_dir=DEFAULT_OUTPUT_DIR):
    """
    Compute the target Hugo path for a note.

    Uses transform_to_hugo to get normalized frontmatter, then generates
    a slug from the title and date for the output filename.

    Args:
        frontmatter: Dict of Obsidian frontmatter
        body: Body content (used for title extraction if needed)
        output_dir: Base output directory for Hugo posts

    Returns:
        Target path as a string (e.g., 'content/english/post/2024-01-15-my-post.md')
    """
    hugo_fm = transform_to_hugo(frontmatter, body)
    slug = generate_slug(hugo_fm.get('title', ''), hugo_fm.get('date'))
    return f"{output_dir}/{slug}.md"


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


def print_list_table(notes, output_dir=DEFAULT_OUTPUT_DIR):
    """
    Print a formatted table of publishable notes with their target paths.

    Similar to print_scan_table but includes an additional column showing
    where each note will be published in the Hugo content directory.

    Args:
        notes: List of note dicts with 'path', 'frontmatter', and 'body' keys
        output_dir: Base output directory for Hugo posts
    """
    if not notes:
        print("No publishable notes found.")
        return

    # Define column widths
    col_widths = {
        'filename': 25,
        'title': 30,
        'date': 12,
        'target': 55
    }

    # Print header
    header = (
        f"{'Filename':<{col_widths['filename']}} "
        f"{'Title':<{col_widths['title']}} "
        f"{'Date':<{col_widths['date']}} "
        f"{'Target Path':<{col_widths['target']}}"
    )
    print(header)
    print("-" * len(header))

    # Print each note
    for note in notes:
        fm = note['frontmatter']
        body = note.get('body', '')
        filename = truncate(note['path'].name, col_widths['filename'])
        title = truncate(fm.get('title', '-'), col_widths['title'])
        date = format_date(fm.get('date'))
        target = truncate(get_target_path(fm, body, output_dir), col_widths['target'])

        row = (
            f"{filename:<{col_widths['filename']}} "
            f"{title:<{col_widths['title']}} "
            f"{date:<{col_widths['date']}} "
            f"{target:<{col_widths['target']}}"
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
    vault_path = Path(args.vault) if args.vault else None
    output_dir = args.output if args.output else DEFAULT_OUTPUT_DIR

    try:
        notes = find_publishable_notes(vault_path=vault_path)
        print_list_table(notes, output_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except NotADirectoryError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def convert_note(note_path: Path, output_dir: str = DEFAULT_OUTPUT_DIR) -> tuple:
    """
    Run the full conversion pipeline on an Obsidian note.

    Pipeline steps:
    1. Parse the Obsidian note (extract frontmatter and body)
    2. Transform frontmatter to Hugo format
    3. Convert Obsidian syntax (wikilinks, images, media) to Hugo format
    4. Generate the target output path

    Args:
        note_path: Path to the Obsidian note file
        output_dir: Base output directory for Hugo posts

    Returns:
        Tuple of (hugo_frontmatter, converted_body, target_path)

    Raises:
        FileNotFoundError: If the note doesn't exist
    """
    # Step 1: Parse the Obsidian note
    frontmatter, body = parse_obsidian_note(note_path)

    # Step 2: Transform frontmatter to Hugo format
    hugo_frontmatter = transform_to_hugo(frontmatter, body)

    # Step 3: Convert Obsidian syntax to Hugo format
    # Order matters: wikilinks first, then images, then media
    converted_body = convert_wikilinks(body)
    converted_body = convert_embedded_images(converted_body)
    converted_body = convert_embedded_media(converted_body)

    # Step 4: Generate the target output path
    slug = generate_slug(hugo_frontmatter.get('title', ''), hugo_frontmatter.get('date'))
    target_path = Path(output_dir) / f"{slug}.md"

    return hugo_frontmatter, converted_body, target_path


def cmd_convert(args):
    """Convert a single Obsidian note to Hugo format."""
    note_path = Path(args.path)

    if not note_path.exists():
        print(f"Error: Note not found: {note_path}", file=sys.stderr)
        sys.exit(1)

    # Get output directory from args or use default
    output_dir = args.output if hasattr(args, 'output') and args.output else DEFAULT_OUTPUT_DIR

    # Get skip_upload flag (will be used for media upload integration)
    skip_upload = getattr(args, 'skip_upload', False)

    try:
        hugo_frontmatter, converted_body, target_path = convert_note(note_path, output_dir)
    except Exception as e:
        print(f"Error converting note: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[DRY RUN] Would convert: {note_path}")
        print(f"[DRY RUN] Target path: {target_path}")
        if skip_upload:
            print(f"[DRY RUN] Media upload: SKIPPED")
        print()
        print("--- Preview of converted content ---")
        print()
        preview = preview_hugo_post(hugo_frontmatter, converted_body)
        print(preview)
    else:
        # Write the Hugo post
        written_path = write_hugo_post(hugo_frontmatter, converted_body, target_path)
        print(f"Converted: {note_path}")
        print(f"Written to: {written_path}")


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
    list_parser.add_argument(
        "--vault",
        help="Path to the Obsidian vault (default: ~/Notes)"
    )
    list_parser.add_argument(
        "--output",
        help="Hugo output directory (default: content/english/post)"
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
    convert_parser.add_argument(
        "--output",
        help="Hugo output directory (default: content/english/post)"
    )
    convert_parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip media upload to MinIO (useful for testing media extraction)"
    )
    convert_parser.set_defaults(func=cmd_convert)

    # Parse arguments and run appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
