#!/usr/bin/env python3
"""
Obsidian to Hugo Publishing CLI Tool

This CLI tool helps publish notes from an Obsidian vault to a Hugo blog.
It handles frontmatter transformation, wikilink conversion, and media embedding.

Usage:
    python publish.py scan          # Find all publishable notes
    python publish.py list          # Show where notes will be published
    python publish.py media PATH    # List media references in a note
    python publish.py convert PATH  # Convert a specific note
"""

import argparse
import sys
from pathlib import Path

# Load environment variables from .env file if it exists
# This must happen before any modules that read env vars are imported
def load_dotenv():
    """
    Load environment variables from scripts/.env if it exists.

    Uses python-dotenv to load variables from the .env file located
    in the same directory as this script. This enables local development
    without setting system environment variables.

    Returns:
        bool: True if .env file was loaded, False otherwise
    """
    try:
        from dotenv import load_dotenv as dotenv_load
    except ImportError:
        # python-dotenv not installed, skip loading
        return False

    # Find the .env file relative to this script
    script_dir = Path(__file__).parent.resolve()
    env_path = script_dir / '.env'

    if env_path.exists():
        dotenv_load(env_path)
        return True
    return False

# Load .env at module import time
_dotenv_loaded = load_dotenv()

from obsidian_parser import find_publishable_notes, parse_obsidian_note
from frontmatter_transformer import generate_slug, transform_to_hugo
from syntax_converter import convert_wikilinks, convert_embedded_images, convert_embedded_media
from hugo_writer import write_hugo_post, preview_hugo_post
from media_extractor import find_media_references, resolve_media_path
from gallery_generator import (
    has_pictures_section,
    remove_pictures_section,
    generate_gallery_from_obsidian,
    extract_media_from_pictures_section,
    has_associations_section,
    remove_associations_section,
    convert_associations_to_hugo_links,
    extract_wikilinks_from_associations,
)
from content_router import determine_content_type

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


def convert_note(
    note_path: Path,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    media_url_map: dict = None,
    generate_gallery: bool = True,
    keep_associations: bool = False
) -> tuple:
    """
    Run the full conversion pipeline on an Obsidian note.

    Pipeline steps:
    1. Parse the Obsidian note (extract frontmatter and body)
    2. Transform frontmatter to Hugo format
    3. Detect Pictures section and generate gallery (if applicable)
    4. Handle Associations section (convert to Hugo links or remove)
    5. Convert Obsidian syntax (wikilinks, images, media) to Hugo format
    6. Append gallery HTML if generated
    7. Generate the target output path

    Args:
        note_path: Path to the Obsidian note file
        output_dir: Base output directory for Hugo posts
        media_url_map: Optional dict mapping Obsidian media references to their
                      MinIO URLs (e.g., {'2021/06/photo.jpg': 'https://...'}).
                      If provided, embedded images/media will use these URLs
                      instead of the s3cdn shortcode.
        generate_gallery: Whether to generate a gallery from the Pictures section.
                         Set to False to skip gallery generation even if a Pictures
                         section exists. Defaults to True.
        keep_associations: Whether to keep the Associations section. If True,
                          wikilinks in the section are converted to Hugo links
                          and the section header is renamed to "## Related".
                          If False (default), the entire section is removed.

    Returns:
        Tuple of (hugo_frontmatter, converted_body, target_path)

    Raises:
        FileNotFoundError: If the note doesn't exist
    """
    # Step 1: Parse the Obsidian note
    frontmatter, body = parse_obsidian_note(note_path)

    # Step 2: Transform frontmatter to Hugo format
    hugo_frontmatter = transform_to_hugo(frontmatter, body)

    # Step 3: Detect Pictures section and prepare gallery generation
    gallery_html = None
    if generate_gallery and has_pictures_section(body):
        # Generate a project slug from the title for the CDN path
        title = hugo_frontmatter.get('title', '')
        project_slug = generate_slug(title, None)  # No date prefix for project slug

        # Determine content type to decide appropriate CDN path
        content_type = determine_content_type(frontmatter)

        # Generate the gallery HTML using the original body (before syntax conversion)
        gallery_html = generate_gallery_from_obsidian(
            body,
            project_slug,
            cdn_shortcode="{{<s3cdn>}}"
        )

        # Remove the Pictures section from the body before further processing
        body = remove_pictures_section(body)

    # Step 4: Handle Associations section
    if has_associations_section(body):
        if keep_associations:
            # Convert wikilinks to Hugo links and rename header to "## Related"
            body = convert_associations_to_hugo_links(body)
        else:
            # Remove the entire Associations section
            body = remove_associations_section(body)

    # Step 5: Convert Obsidian syntax to Hugo format
    # Order matters: wikilinks first, then images, then media
    converted_body = convert_wikilinks(body)
    converted_body = convert_embedded_images(converted_body, media_url_map=media_url_map)
    converted_body = convert_embedded_media(converted_body, media_url_map=media_url_map)

    # Step 6: Append gallery HTML if generated
    if gallery_html:
        # Add gallery at the end of the content with some spacing
        converted_body = converted_body.rstrip() + '\n\n' + gallery_html + '\n'

    # Step 7: Generate the target output path
    slug = generate_slug(hugo_frontmatter.get('title', ''), hugo_frontmatter.get('date'))
    target_path = Path(output_dir) / f"{slug}.md"

    return hugo_frontmatter, converted_body, target_path


def extract_and_resolve_media(note_path: Path) -> tuple:
    """
    Extract media references from a note and resolve them to local file paths.

    Args:
        note_path: Path to the Obsidian note file

    Returns:
        Tuple of (media_items, missing_count) where:
        - media_items: List of (obsidian_reference, resolved_local_path) tuples
          for files that exist
        - missing_count: Number of referenced files that couldn't be found
    """
    # Read the note content to extract media references
    content = note_path.read_text()
    media_refs = find_media_references(content)

    media_items = []
    missing_count = 0

    for ref in media_refs:
        resolved_path = resolve_media_path(ref)
        if resolved_path:
            media_items.append((ref, resolved_path))
        else:
            missing_count += 1

    return media_items, missing_count


def upload_media_to_minio(media_items: list, show_progress: bool = True) -> dict:
    """
    Upload media files to MinIO and return URL mappings.

    Args:
        media_items: List of (obsidian_reference, resolved_local_path) tuples
        show_progress: Whether to show a progress bar (default: True)

    Returns:
        Dict mapping Obsidian references to their MinIO URLs
        (None for failed uploads)

    Raises:
        ImportError: If minio package is not installed
        MinioConfigError: If MinIO configuration is missing
    """
    # Import here to allow the module to work without minio installed
    # (useful for --skip-upload mode)
    from minio_uploader import (
        get_minio_client,
        get_bucket_name,
        ensure_bucket_exists,
        upload_media_batch,
        check_existing,
        build_minio_url,
        DEFAULT_ASSET_PREFIX,
        MinioConfigError,
        MINIO_ENDPOINT_VAR,
        MINIO_SECURE_VAR
    )
    import os

    # Try to import rich for progress bars
    rich_available = False
    if show_progress:
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
            from rich.console import Console
            rich_available = True
        except ImportError:
            pass  # Fall back to simple output

    # Initialize MinIO client
    client = get_minio_client()
    bucket_name = get_bucket_name()

    # Ensure bucket exists
    if not ensure_bucket_exists(client, bucket_name):
        print("Warning: Could not ensure bucket exists, upload may fail",
              file=sys.stderr)

    # Get endpoint and secure settings for URL building
    endpoint = os.environ.get(MINIO_ENDPOINT_VAR)
    secure_str = os.environ.get(MINIO_SECURE_VAR, "true").lower()
    secure = secure_str in ("true", "1", "yes")

    # Check which files already exist and skip them
    items_to_upload = []
    url_mapping = {}

    if rich_available and show_progress:
        console = Console()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Checking existing files...", total=len(media_items))
            for ref, local_path in media_items:
                # Build the expected object name
                normalized_ref = ref.lstrip('/')
                object_name = f"{DEFAULT_ASSET_PREFIX}/{normalized_ref}"

                if check_existing(client, bucket_name, object_name):
                    # File already exists, build URL without uploading
                    url = build_minio_url(endpoint, bucket_name, object_name, secure)
                    url_mapping[ref] = url
                    console.print(f"  [dim][SKIP][/dim] {ref} [dim](already exists)[/dim]")
                else:
                    items_to_upload.append((ref, local_path))
                progress.advance(task)
    else:
        for ref, local_path in media_items:
            # Build the expected object name
            normalized_ref = ref.lstrip('/')
            object_name = f"{DEFAULT_ASSET_PREFIX}/{normalized_ref}"

            if check_existing(client, bucket_name, object_name):
                # File already exists, build URL without uploading
                url = build_minio_url(endpoint, bucket_name, object_name, secure)
                url_mapping[ref] = url
                print(f"  [SKIP] {ref} (already exists)")
            else:
                items_to_upload.append((ref, local_path))

    # Upload files that don't exist yet
    if items_to_upload:
        if rich_available and show_progress:
            console = Console()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("{task.fields[current_file]}"),
                console=console
            ) as progress:
                task = progress.add_task(
                    "Uploading media...",
                    total=len(items_to_upload),
                    current_file=""
                )

                def update_progress(filename: str, current: int, total: int):
                    # Truncate long filenames for display
                    display_name = filename if len(filename) <= 30 else f"...{filename[-27:]}"
                    progress.update(task, completed=current, current_file=f"[cyan]{display_name}[/cyan]")

                batch_results = upload_media_batch(
                    client,
                    bucket_name,
                    items_to_upload,
                    endpoint=endpoint,
                    secure=secure,
                    progress_callback=update_progress
                )
                url_mapping.update(batch_results)
        else:
            batch_results = upload_media_batch(
                client,
                bucket_name,
                items_to_upload,
                endpoint=endpoint,
                secure=secure
            )
            url_mapping.update(batch_results)

    return url_mapping


def cmd_media(args):
    """List all media files referenced by a note without uploading."""
    note_path = Path(args.path)

    if not note_path.exists():
        print(f"Error: Note not found: {note_path}", file=sys.stderr)
        sys.exit(1)

    # Extract and resolve media references
    media_items, missing_count = extract_and_resolve_media(note_path)

    # Print header
    print(f"Media references in: {note_path.name}")
    print("=" * 60)

    if not media_items and missing_count == 0:
        print("No media references found in this note.")
        return

    # Print resolved media files
    if media_items:
        print(f"\nResolved ({len(media_items)} file(s)):")
        for ref, resolved_path in media_items:
            print(f"  {ref}")
            print(f"    -> {resolved_path}")

    # Print missing media files
    if missing_count > 0:
        print(f"\nMissing ({missing_count} file(s)):")
        # Re-read the note to show which files are missing
        content = note_path.read_text()
        all_refs = find_media_references(content)
        resolved_refs = {ref for ref, _ in media_items}
        for ref in all_refs:
            if ref not in resolved_refs:
                print(f"  {ref} [NOT FOUND]")

    # Print summary
    print()
    total = len(media_items) + missing_count
    print(f"Summary: {total} reference(s), {len(media_items)} resolved, {missing_count} missing")


def cmd_convert(args):
    """Convert a single Obsidian note to Hugo format."""
    note_path = Path(args.path)

    if not note_path.exists():
        print(f"Error: Note not found: {note_path}", file=sys.stderr)
        sys.exit(1)

    # Get output directory from args or use default
    output_dir = args.output if hasattr(args, 'output') and args.output else DEFAULT_OUTPUT_DIR

    # Get skip_upload flag
    skip_upload = getattr(args, 'skip_upload', False)

    # Get no_gallery flag (inverted to generate_gallery)
    generate_gallery = not getattr(args, 'no_gallery', False)

    # Get keep_associations flag
    keep_associations = getattr(args, 'keep_associations', False)

    # Step 1: Extract and resolve media references
    media_items, missing_count = extract_and_resolve_media(note_path)

    # Step 2: Upload media to MinIO (unless --skip-upload)
    media_url_map = None
    if media_items and not skip_upload:
        try:
            print(f"Uploading {len(media_items)} media file(s) to MinIO...")
            media_url_map = upload_media_to_minio(media_items)

            # Report upload results
            successful = sum(1 for v in media_url_map.values() if v is not None)
            failed = len(media_url_map) - successful
            if failed > 0:
                print(f"Warning: {failed} file(s) failed to upload", file=sys.stderr)
        except ImportError as e:
            print(f"Warning: MinIO upload skipped - {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: MinIO upload failed - {e}", file=sys.stderr)

    # Step 3: Convert the note (with media URLs if available)
    try:
        hugo_frontmatter, converted_body, target_path = convert_note(
            note_path, output_dir, media_url_map=media_url_map,
            generate_gallery=generate_gallery,
            keep_associations=keep_associations
        )
    except Exception as e:
        print(f"Error converting note: {e}", file=sys.stderr)
        sys.exit(1)

    # Check if note has a Pictures section and Associations section for display purposes
    note_content = note_path.read_text()
    has_gallery = has_pictures_section(note_content)
    gallery_media_count = len(extract_media_from_pictures_section(note_content)) if has_gallery else 0
    has_assoc = has_associations_section(note_content)
    assoc_link_count = len(extract_wikilinks_from_associations(note_content)) if has_assoc else 0

    if args.dry_run:
        print(f"[DRY RUN] Would convert: {note_path}")
        print(f"[DRY RUN] Target path: {target_path}")
        if media_items:
            print(f"[DRY RUN] Media files found: {len(media_items)}")
            if missing_count > 0:
                print(f"[DRY RUN] Media files missing: {missing_count}")
        if skip_upload:
            print(f"[DRY RUN] Media upload: SKIPPED")
        if has_gallery:
            if generate_gallery:
                print(f"[DRY RUN] Gallery: YES ({gallery_media_count} images)")
            else:
                print(f"[DRY RUN] Gallery: SKIPPED ({gallery_media_count} images in Pictures section)")
        if has_assoc:
            if keep_associations:
                print(f"[DRY RUN] Associations: CONVERTED ({assoc_link_count} links -> Related section)")
            else:
                print(f"[DRY RUN] Associations: REMOVED ({assoc_link_count} links)")
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
        if has_gallery:
            if generate_gallery:
                print(f"Gallery generated: {gallery_media_count} images")
            else:
                print(f"Gallery skipped: {gallery_media_count} images in Pictures section")
        if has_assoc:
            if keep_associations:
                print(f"Associations converted: {assoc_link_count} links -> Related section")
            else:
                print(f"Associations removed: {assoc_link_count} links")


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

    # media subcommand
    media_parser = subparsers.add_parser(
        "media",
        help="List all media files referenced by a note (without uploading)"
    )
    media_parser.add_argument(
        "path",
        help="Path to the Obsidian note to analyze"
    )
    media_parser.set_defaults(func=cmd_media)

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
    convert_parser.add_argument(
        "--no-gallery",
        action="store_true",
        help="Skip gallery generation even if a Pictures section exists"
    )
    convert_parser.add_argument(
        "--keep-associations",
        action="store_true",
        help="Convert Associations section to Hugo links (default: remove the section)"
    )
    convert_parser.set_defaults(func=cmd_convert)

    # Parse arguments and run appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
