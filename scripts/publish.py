#!/usr/bin/env python3
"""
Obsidian to Hugo Publishing CLI Tool

This CLI tool helps publish notes from an Obsidian vault to a Hugo blog.
It handles frontmatter transformation, wikilink conversion, and media embedding.

Usage:
    python publish.py scan          # Find all publishable notes
    python publish.py list          # Show where notes will be published
    python publish.py media PATH    # List media references in a note
    python publish.py validate PATH # Validate a note before publishing
    python publish.py convert PATH  # Convert a specific note
"""

import argparse
import shutil
import signal
import subprocess
import sys
import tempfile
import webbrowser
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
from syntax_converter import convert_wikilinks, convert_embedded_images, convert_embedded_media, get_s3cdn_base_url
from hugo_writer import write_hugo_post, preview_hugo_post
from config_manager import get_hugo_config, list_environments, HugoConfigError
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
from content_router import determine_content_type, get_hugo_section_path
from hugo_writer import write_hugo_post_routed
from publish_tracker import (
    is_note_published,
    record_published,
    get_unpublished_notes,
    load_publish_state,
)
from validators import (
    validate_frontmatter,
    validate_media_references,
    validate_internal_links,
    is_valid,
    has_warnings,
    format_issues,
    ValidationSeverity,
)
from exceptions import (
    PublishError,
    ValidationError,
    MediaNotFoundError,
    UploadError,
)
from console import (
    console,
    error_console,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_header,
    print_dim,
    print_section_header,
    print_separator,
    print_ok,
    print_skip,
    print_status_line,
    print_publish_complete,
    print_dry_run_banner,
    format_success,
    format_warning,
    format_error,
    format_info,
    format_highlight,
    format_dim,
    format_count,
    set_verbose,
    is_verbose,
    print_verbose,
    print_verbose_step,
    print_verbose_detail,
    print_verbose_list,
    set_quiet,
    is_quiet,
)

# Default Hugo content output directory (relative to blog root)
DEFAULT_OUTPUT_DIR = "content/english/post"

# Default Hugo root directory (for write_hugo_post_routed)
DEFAULT_HUGO_ROOT = Path(__file__).parent.parent.resolve()


def handle_error(error: Exception, context: str = None) -> None:
    """
    Handle an error with user-friendly messaging and exit.

    Provides helpful error messages that explain what went wrong
    and suggest how to fix the issue.

    Args:
        error: The exception that was raised
        context: Optional context about what operation was being performed
    """
    import yaml

    # Build the error message with context if provided
    context_prefix = f"Error during {context}: " if context else "Error: "

    # Handle specific error types with targeted guidance
    if isinstance(error, FileNotFoundError):
        print_error(f"{context_prefix}File not found: {error}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check that the file path is correct")
        console.print("  - Ensure the file exists and is readable")
        console.print("  - Use an absolute path if the relative path isn't working")
        sys.exit(1)

    elif isinstance(error, yaml.YAMLError):
        print_error(f"{context_prefix}Invalid YAML frontmatter")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check your frontmatter syntax between the --- markers")
        console.print("  - Ensure proper YAML formatting (indentation, colons, quotes)")
        console.print("  - Common issues: missing colons, unquoted special characters")
        console.print(f"  - YAML error details: {error}")
        sys.exit(1)

    elif isinstance(error, ValidationError):
        print_error(f"{context_prefix}{error}")
        if error.issues:
            console.print()
            console.print("[dim]Validation issues:[/dim]")
            for issue in error.issues:
                console.print(f"  - {issue}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Ensure all required frontmatter fields are present (title, date, tags)")
        console.print("  - Run 'python publish.py validate <path>' for detailed validation")
        sys.exit(1)

    elif isinstance(error, MediaNotFoundError):
        print_error(f"{context_prefix}{error}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check that the media file exists at the expected path")
        console.print("  - Verify the media reference in your note uses the correct path")
        console.print("  - Ensure your Media folder is configured correctly")
        console.print("  - Run 'python publish.py media <path>' to check all media references")
        sys.exit(1)

    elif isinstance(error, UploadError):
        print_error(f"{context_prefix}{error}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check MinIO connection settings in scripts/.env")
        console.print("  - Verify MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY are set")
        console.print("  - Ensure the MinIO server is running and accessible")
        console.print("  - Check that the bucket exists and you have write permissions")
        if error.original_error:
            console.print(f"  - Underlying error: {error.original_error}")
        sys.exit(1)

    elif isinstance(error, HugoConfigError):
        print_error(f"{context_prefix}{error}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check your Hugo config files in the config/ directory")
        console.print("  - Ensure config/_default/params.toml exists and is valid TOML")
        console.print("  - For environment-specific settings, check config/<environment>/")
        console.print("  - Required settings: S3CDN, mediaBasePath, baseURL")
        sys.exit(1)

    elif isinstance(error, PermissionError):
        print_error(f"{context_prefix}Permission denied: {error}")
        console.print()
        console.print("[dim]How to fix:[/dim]")
        console.print("  - Check file and directory permissions")
        console.print("  - Ensure you have write access to the Hugo content directory")
        console.print("  - Try running with appropriate permissions")
        sys.exit(1)

    elif isinstance(error, PublishError):
        # Generic PublishError - use its message
        print_error(f"{context_prefix}{error}")
        if error.context:
            console.print()
            console.print("[dim]Additional context:[/dim]")
            for key, value in error.context.items():
                console.print(f"  - {key}: {value}")
        sys.exit(1)

    else:
        # Generic error handling for unexpected errors
        print_error(f"{context_prefix}{error}")
        console.print()
        console.print("[dim]This may be an unexpected error. Please check:[/dim]")
        console.print("  - Your file paths and permissions")
        console.print("  - Network connectivity for MinIO operations")
        console.print("  - The error message above for specific details")
        sys.exit(1)


def handle_warning(error: Exception, context: str = None) -> None:
    """
    Handle a non-fatal warning with user-friendly messaging.

    Similar to handle_error but doesn't exit - just prints a warning.

    Args:
        error: The exception that was raised
        context: Optional context about what operation was being performed
    """
    context_prefix = f"Warning ({context}): " if context else "Warning: "

    if isinstance(error, MediaNotFoundError):
        print_warning(f"{context_prefix}Some media files could not be found")
        console.print(f"  [dim]Reference: {error.media_reference}[/dim]")
    elif isinstance(error, UploadError):
        print_warning(f"{context_prefix}Media upload issue")
        console.print(f"  [dim]{error}[/dim]")
    else:
        print_warning(f"{context_prefix}{error}")


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
        print_warning("No publishable notes found.")
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
    console.print(f"[bold]{header}[/bold]")
    console.print("-" * len(header))

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
        console.print(row)

    # Print summary
    console.print()
    print_success(f"Found {len(notes)} publishable note(s).")


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
        print_warning("No publishable notes found.")
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
    console.print(f"[bold]{header}[/bold]")
    console.print("-" * len(header))

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
        console.print(row)

    # Print summary
    console.print()
    print_success(f"Found {len(notes)} publishable note(s).")


def cmd_scan(args):
    """Find and display all notes marked for publishing."""
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)

    vault_path = Path(args.vault) if args.vault else None

    try:
        notes = find_publishable_notes(vault_path=vault_path)
        print_scan_table(notes)
    except FileNotFoundError as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        print_error(f"Error: {e}")
        sys.exit(1)


def cmd_list(args):
    """Show publishable notes with their target Hugo paths."""
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)

    vault_path = Path(args.vault) if args.vault else None
    output_dir = args.output if args.output else DEFAULT_OUTPUT_DIR

    try:
        notes = find_publishable_notes(vault_path=vault_path)
        print_list_table(notes, output_dir)
    except FileNotFoundError as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        print_error(f"Error: {e}")
        sys.exit(1)


def convert_note(
    note_path: Path,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    media_url_map: dict = None,
    generate_gallery: bool = True,
    keep_associations: bool = False,
    environment: str = None
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
        environment: Hugo environment to use for S3CDN URL resolution
                    (e.g., 'development', 'production'). If None, uses the
                    s3cdn shortcode; if specified, embeds the actual URL
                    from Hugo config.

    Returns:
        Tuple of (hugo_frontmatter, converted_body, target_path)

    Raises:
        FileNotFoundError: If the note doesn't exist
    """
    # Step 1: Parse the Obsidian note
    print_verbose_step("PARSE", f"Reading note: {note_path.name}")
    frontmatter, body = parse_obsidian_note(note_path)
    print_verbose_detail("Frontmatter keys", ", ".join(frontmatter.keys()) if frontmatter else "none")
    print_verbose_detail("Body length", f"{len(body)} chars")

    # Step 2: Transform frontmatter to Hugo format
    print_verbose_step("TRANSFORM", "Converting frontmatter to Hugo format")
    hugo_frontmatter = transform_to_hugo(frontmatter, body)
    print_verbose_detail("Title", hugo_frontmatter.get('title', 'N/A'))
    print_verbose_detail("Date", str(hugo_frontmatter.get('date', 'N/A')))
    if hugo_frontmatter.get('tags'):
        print_verbose_detail("Tags", ", ".join(hugo_frontmatter.get('tags', [])))

    # Step 3: Detect Pictures section and prepare gallery generation
    print_verbose_step("GALLERY", "Checking for Pictures section")
    gallery_html = None
    if generate_gallery and has_pictures_section(body):
        # Generate a project slug from the title for the CDN path
        title = hugo_frontmatter.get('title', '')
        project_slug = generate_slug(title, None)  # No date prefix for project slug

        # Determine content type to decide appropriate CDN path
        content_type = determine_content_type(frontmatter)

        print_verbose_detail("Gallery", "Found Pictures section, generating gallery")
        print_verbose_detail("Project slug", project_slug)

        # Generate the gallery HTML using the original body (before syntax conversion)
        gallery_html = generate_gallery_from_obsidian(
            body,
            project_slug,
            cdn_shortcode="{{<s3cdn>}}"
        )

        # Remove the Pictures section from the body before further processing
        body = remove_pictures_section(body)
        print_verbose_detail("Gallery HTML", f"{len(gallery_html)} chars generated")
    else:
        print_verbose_detail("Gallery", "No Pictures section or gallery disabled")

    # Step 4: Handle Associations section
    print_verbose_step("ASSOCIATIONS", "Checking for Associations section")
    if has_associations_section(body):
        if keep_associations:
            # Convert wikilinks to Hugo links and rename header to "## Related"
            print_verbose_detail("Associations", "Converting to Hugo links (Related section)")
            body = convert_associations_to_hugo_links(body)
        else:
            # Remove the entire Associations section
            print_verbose_detail("Associations", "Removing section")
            body = remove_associations_section(body)
    else:
        print_verbose_detail("Associations", "No Associations section found")

    # Step 5: Convert Obsidian syntax to Hugo format
    # Order matters: wikilinks first, then images, then media
    # If environment is specified, get the S3CDN base URL for direct URL output
    print_verbose_step("SYNTAX", "Converting Obsidian syntax to Hugo format")
    s3cdn_base_url = None
    if environment:
        try:
            s3cdn_base_url = get_s3cdn_base_url(environment)
            print_verbose_detail("S3CDN URL", s3cdn_base_url)
        except HugoConfigError:
            # Fall back to shortcode if config is not available
            print_verbose_detail("S3CDN URL", "Config not found, using shortcode")
            pass

    print_verbose("Converting wikilinks...")
    converted_body = convert_wikilinks(body)
    print_verbose("Converting embedded images...")
    converted_body = convert_embedded_images(
        converted_body,
        media_url_map=media_url_map,
        s3cdn_base_url=s3cdn_base_url
    )
    print_verbose("Converting embedded media (video/audio)...")
    converted_body = convert_embedded_media(
        converted_body,
        media_url_map=media_url_map,
        s3cdn_base_url=s3cdn_base_url
    )
    if media_url_map:
        print_verbose_detail("Media URLs mapped", str(len(media_url_map)))

    # Step 6: Append gallery HTML if generated
    if gallery_html:
        print_verbose_step("FINALIZE", "Appending gallery HTML to content")
        # Add gallery at the end of the content with some spacing
        converted_body = converted_body.rstrip() + '\n\n' + gallery_html + '\n'

    # Step 7: Generate the target output path
    print_verbose_step("OUTPUT", "Generating target path")
    slug = generate_slug(hugo_frontmatter.get('title', ''), hugo_frontmatter.get('date'))
    target_path = Path(output_dir) / f"{slug}.md"
    print_verbose_detail("Slug", slug)
    print_verbose_detail("Target path", str(target_path))

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
    print_verbose_step("MEDIA", f"Extracting media from: {note_path.name}")
    # Read the note content to extract media references
    content = note_path.read_text()
    media_refs = find_media_references(content)
    print_verbose_detail("References found", str(len(media_refs)))

    media_items = []
    missing_count = 0

    for ref in media_refs:
        resolved_path = resolve_media_path(ref)
        if resolved_path:
            media_items.append((ref, resolved_path))
            print_verbose(f"Resolved: {ref}")
        else:
            missing_count += 1
            print_verbose(f"Missing: {ref}")

    print_verbose_detail("Resolved", str(len(media_items)))
    print_verbose_detail("Missing", str(missing_count))

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
    print_verbose_step("UPLOAD", "Initializing MinIO client")
    client = get_minio_client()
    bucket_name = get_bucket_name()
    print_verbose_detail("Bucket", bucket_name)

    # Ensure bucket exists
    if not ensure_bucket_exists(client, bucket_name):
        print("Warning: Could not ensure bucket exists, upload may fail",
              file=sys.stderr)

    # Get endpoint and secure settings for URL building
    endpoint = os.environ.get(MINIO_ENDPOINT_VAR)
    secure_str = os.environ.get(MINIO_SECURE_VAR, "true").lower()
    secure = secure_str in ("true", "1", "yes")
    print_verbose_detail("Endpoint", endpoint or "not set")
    print_verbose_detail("Secure", str(secure))

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
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)

    note_path = Path(args.path)

    # Extract and resolve media references
    try:
        media_items, missing_count = extract_and_resolve_media(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note")
    except PermissionError as e:
        handle_error(e, "reading note")

    # Print header
    console.print(f"Media references in: [info]{note_path.name}[/info]")
    console.print("=" * 60)

    if not media_items and missing_count == 0:
        print_info("No media references found in this note.")
        return

    # Print resolved media files
    if media_items:
        console.print(f"\n[success]Resolved ({len(media_items)} file(s)):[/success]")
        for ref, resolved_path in media_items:
            console.print(f"  {ref}")
            console.print(f"    [dim]->[/dim] [info]{resolved_path}[/info]")

    # Print missing media files
    if missing_count > 0:
        console.print(f"\n[error]Missing ({missing_count} file(s)):[/error]")
        # Re-read the note to show which files are missing
        content = note_path.read_text()
        all_refs = find_media_references(content)
        resolved_refs = {ref for ref, _ in media_items}
        for ref in all_refs:
            if ref not in resolved_refs:
                console.print(f"  {ref} [error][NOT FOUND][/error]")

    # Print summary
    console.print()
    total = len(media_items) + missing_count
    if missing_count > 0:
        console.print(f"Summary: {format_count(str(total))} reference(s), {format_success(str(len(media_items)))} resolved, {format_error(str(missing_count))} missing")
    else:
        print_success(f"Summary: {total} reference(s), {len(media_items)} resolved, {missing_count} missing")


def cmd_validate(args):
    """
    Validate an Obsidian note before publishing.

    Runs all validators on a note and displays a formatted report:
    - Frontmatter validation (required fields, types)
    - Media reference validation (embedded files exist)
    - Internal link validation (wikilinks resolve to existing notes)

    Exit codes:
    - 0: All validations passed (no errors or warnings)
    - 1: Validation errors found (note cannot be published as-is)
    - 2: Validation warnings found (note can be published but has issues)
    """
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)

    note_path = Path(args.path)

    # Parse the note to get frontmatter and body
    try:
        frontmatter, body = parse_obsidian_note(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note")
    except Exception as e:
        handle_error(e, "parsing note")

    # Get optional paths from args
    vault_path = Path(args.vault) if hasattr(args, 'vault') and args.vault else None
    hugo_root = Path(args.hugo_root) if hasattr(args, 'hugo_root') and args.hugo_root else DEFAULT_HUGO_ROOT

    # Print header
    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print("[header]VALIDATION REPORT[/header]")
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print(f"Note: [info]{note_path}[/info]")
    console.print(f"Title: [highlight]{frontmatter.get('title', 'Untitled')}[/highlight]")
    console.print()

    # Collect all issues
    all_issues = []

    # Run frontmatter validation
    console.print("Validating frontmatter...")
    fm_issues = validate_frontmatter(frontmatter)
    all_issues.extend(fm_issues)
    if fm_issues:
        error_count = sum(1 for i in fm_issues if i.severity == ValidationSeverity.ERROR)
        warn_count = sum(1 for i in fm_issues if i.severity == ValidationSeverity.WARNING)
        console.print(f"  Found {format_error(str(error_count))} error(s), {format_warning(str(warn_count))} warning(s)")
    else:
        console.print("  [success]OK[/success]")

    # Run media reference validation
    console.print("Validating media references...")
    media_issues = validate_media_references(body)
    all_issues.extend(media_issues)
    if media_issues:
        console.print(f"  Found {format_error(str(len(media_issues)))} missing media file(s)")
    else:
        console.print("  [success]OK[/success]")

    # Run internal link validation
    console.print("Validating internal links...")
    link_issues = validate_internal_links(body, vault_path=vault_path, hugo_root=hugo_root)
    all_issues.extend(link_issues)
    if link_issues:
        console.print(f"  Found {format_error(str(len(link_issues)))} broken link(s)")
    else:
        console.print("  [success]OK[/success]")

    # Print detailed report if there are issues
    console.print()
    if all_issues:
        console.print("-" * 60)
        console.print("[warning]ISSUES FOUND[/warning]")
        console.print("-" * 60)
        console.print(format_issues(all_issues))
        console.print()

    # Print summary and set exit code
    console.print("[header]" + "=" * 60 + "[/header]")
    error_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.ERROR)
    warn_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.WARNING)

    if error_count > 0:
        console.print(f"[error]VALIDATION FAILED:[/error] {error_count} error(s), {warn_count} warning(s)")
        console.print("[header]" + "=" * 60 + "[/header]")
        console.print()
        sys.exit(1)
    elif warn_count > 0:
        console.print(f"[warning]VALIDATION PASSED WITH WARNINGS:[/warning] {warn_count} warning(s)")
        console.print("[header]" + "=" * 60 + "[/header]")
        console.print()
        sys.exit(2)
    else:
        console.print("[success]VALIDATION PASSED:[/success] No issues found")
        console.print("[header]" + "=" * 60 + "[/header]")
        console.print()
        sys.exit(0)


def cmd_convert(args):
    """Convert a single Obsidian note to Hugo format."""
    note_path = Path(args.path)

    # Get output directory from args or use default
    output_dir = args.output if hasattr(args, 'output') and args.output else DEFAULT_OUTPUT_DIR

    # Get verbose flag and enable verbose logging if set
    verbose = getattr(args, 'verbose', False)
    set_verbose(verbose)

    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)

    # Get skip_upload flag
    skip_upload = getattr(args, 'skip_upload', False)

    # Get no_gallery flag (inverted to generate_gallery)
    generate_gallery = not getattr(args, 'no_gallery', False)

    # Get keep_associations flag
    keep_associations = getattr(args, 'keep_associations', False)

    # Get environment flag (ensure we get None if not set, not a MagicMock)
    environment = getattr(args, 'environment', None)
    if environment is not None and not isinstance(environment, str):
        environment = None

    # Step 1: Extract and resolve media references
    try:
        media_items, missing_count = extract_and_resolve_media(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note")
    except PermissionError as e:
        handle_error(e, "reading note")

    # Step 2: Upload media to MinIO (unless --skip-upload)
    media_url_map = None
    if media_items and not skip_upload:
        try:
            print_info(f"Uploading {len(media_items)} media file(s) to MinIO...")
            media_url_map = upload_media_to_minio(media_items)

            # Report upload results
            successful = sum(1 for v in media_url_map.values() if v is not None)
            failed = len(media_url_map) - successful
            if failed > 0:
                print_warning(f"Warning: {failed} file(s) failed to upload")
        except ImportError as e:
            handle_warning(e, "MinIO import")
            console.print("  [dim]Media upload skipped - minio package not installed[/dim]")
            console.print("  [dim]Install with: pip install minio[/dim]")
        except UploadError as e:
            handle_warning(e, "media upload")
        except Exception as e:
            handle_warning(e, "media upload")

    # Step 3: Convert the note (with media URLs if available)
    try:
        hugo_frontmatter, converted_body, target_path = convert_note(
            note_path, output_dir, media_url_map=media_url_map,
            generate_gallery=generate_gallery,
            keep_associations=keep_associations,
            environment=environment
        )
    except FileNotFoundError as e:
        handle_error(e, "converting note")
    except HugoConfigError as e:
        handle_error(e, "converting note")
    except Exception as e:
        handle_error(e, "converting note")

    # Check if note has a Pictures section and Associations section for display purposes
    note_content = note_path.read_text()
    has_gallery = has_pictures_section(note_content)
    gallery_media_count = len(extract_media_from_pictures_section(note_content)) if has_gallery else 0
    has_assoc = has_associations_section(note_content)
    assoc_link_count = len(extract_wikilinks_from_associations(note_content)) if has_assoc else 0

    if args.dry_run:
        console.print(f"[warning][DRY RUN][/warning] Would convert: [info]{note_path}[/info]")
        console.print(f"[warning][DRY RUN][/warning] Target path: [info]{target_path}[/info]")
        if environment:
            console.print(f"[warning][DRY RUN][/warning] Environment: {environment}")
        if media_items:
            console.print(f"[warning][DRY RUN][/warning] Media files found: {len(media_items)}")
            if missing_count > 0:
                console.print(f"[warning][DRY RUN][/warning] Media files missing: [error]{missing_count}[/error]")
        if skip_upload:
            console.print(f"[warning][DRY RUN][/warning] Media upload: [dim]SKIPPED[/dim]")
        if has_gallery:
            if generate_gallery:
                console.print(f"[warning][DRY RUN][/warning] Gallery: [success]YES[/success] ({gallery_media_count} images)")
            else:
                console.print(f"[warning][DRY RUN][/warning] Gallery: [dim]SKIPPED[/dim] ({gallery_media_count} images in Pictures section)")
        if has_assoc:
            if keep_associations:
                console.print(f"[warning][DRY RUN][/warning] Associations: [success]CONVERTED[/success] ({assoc_link_count} links -> Related section)")
            else:
                console.print(f"[warning][DRY RUN][/warning] Associations: [dim]REMOVED[/dim] ({assoc_link_count} links)")
        console.print()
        console.print("[header]--- Preview of converted content ---[/header]")
        console.print()
        preview = preview_hugo_post(hugo_frontmatter, converted_body)
        console.print(preview)
    else:
        # Write the Hugo post
        written_path = write_hugo_post(hugo_frontmatter, converted_body, target_path)
        print_success(f"Converted: {note_path}")
        console.print(f"Written to: [info]{written_path}[/info]")
        if has_gallery:
            if generate_gallery:
                console.print(f"[success]Gallery generated:[/success] {gallery_media_count} images")
            else:
                console.print(f"[dim]Gallery skipped:[/dim] {gallery_media_count} images in Pictures section")
        if has_assoc:
            if keep_associations:
                console.print(f"[success]Associations converted:[/success] {assoc_link_count} links -> Related section")
            else:
                console.print(f"[dim]Associations removed:[/dim] {assoc_link_count} links")


def confirm_prompt(message: str, default: bool = False) -> bool:
    """
    Display a confirmation prompt and return the user's response.

    Args:
        message: The confirmation message to display
        default: Default response if user just presses Enter (True=yes, False=no)

    Returns:
        True if user confirms, False otherwise
    """
    if default:
        prompt = f"{message} [Y/n]: "
    else:
        prompt = f"{message} [y/N]: "

    try:
        response = input(prompt).strip().lower()
    except EOFError:
        # Non-interactive mode, use default
        return default

    if not response:
        return default

    return response in ('y', 'yes')


def cmd_publish(args):
    """
    Publish a single Obsidian note to the Hugo blog.

    This is the main command users will run. It combines:
    1. Scanning for the note and validating it's publishable
    2. Extracting and uploading media to MinIO
    3. Converting Obsidian syntax to Hugo format
    4. Writing the Hugo post to the appropriate content directory

    In non-dry-run mode, prompts for confirmation before making changes.

    Exit codes:
    - 0: Success
    - 1: General error or validation errors
    - 2: Validation warnings (only with --strict flag)
    """
    note_path = Path(args.path)

    # Get flags from args
    dry_run = getattr(args, 'dry_run', False)
    skip_upload = getattr(args, 'skip_upload', False)
    generate_gallery = not getattr(args, 'no_gallery', False)
    keep_associations = getattr(args, 'keep_associations', False)
    yes_flag = getattr(args, 'yes', False)
    strict_mode = getattr(args, 'strict', False)
    hugo_root = Path(args.hugo_root) if hasattr(args, 'hugo_root') and args.hugo_root else DEFAULT_HUGO_ROOT
    # Get verbose flag and enable verbose logging if set
    verbose = getattr(args, 'verbose', False)
    set_verbose(verbose)
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)
    # Get environment flag (ensure we get None if not set, not a MagicMock)
    environment = getattr(args, 'environment', None)
    if environment is not None and not isinstance(environment, str):
        environment = None

    # Step 1: Parse the note and validate it's publishable
    try:
        frontmatter, body = parse_obsidian_note(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note")
    except Exception as e:
        handle_error(e, "parsing note")

    # Check if note is marked for publishing
    is_publishable = frontmatter.get('publish', False)
    if not is_publishable:
        print_warning("Warning: Note is not marked with 'publish: true' in frontmatter.")
        if not dry_run and not yes_flag:
            if not confirm_prompt("Publish anyway?", default=False):
                console.print("[dim]Aborted.[/dim]")
                sys.exit(0)

    # Run validation (respects --strict flag)
    vault_path = Path(args.vault) if hasattr(args, 'vault') and args.vault else None
    all_issues = []

    # Validate frontmatter
    fm_issues = validate_frontmatter(frontmatter)
    all_issues.extend(fm_issues)

    # Validate media references
    media_issues = validate_media_references(body)
    all_issues.extend(media_issues)

    # Validate internal links
    link_issues = validate_internal_links(body, vault_path=vault_path, hugo_root=hugo_root)
    all_issues.extend(link_issues)

    # Check validation results
    error_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.ERROR)
    warn_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.WARNING)

    if error_count > 0 or (strict_mode and warn_count > 0):
        console.print()
        console.print("[error]" + "=" * 60 + "[/error]")
        console.print("[error]VALIDATION FAILED[/error]")
        console.print("[error]" + "=" * 60 + "[/error]")
        console.print(format_issues(all_issues))
        console.print()

        if error_count > 0:
            console.print(f"Found {format_error(str(error_count))} error(s), {format_warning(str(warn_count))} warning(s).")
            print_error("Cannot publish: validation errors must be fixed first.")
            sys.exit(1)
        else:
            # strict_mode and warn_count > 0
            console.print(f"Found {format_warning(str(warn_count))} warning(s).")
            print_error("Cannot publish: --strict mode requires no warnings.")
            sys.exit(2)

    # Show warnings if any (but not blocking without --strict)
    if warn_count > 0 and not strict_mode:
        console.print()
        print_warning(f"Note: {warn_count} validation warning(s) found (use --strict to treat as errors)")

    # Step 2: Determine content type and target path
    content_type = determine_content_type(frontmatter)
    section_path = get_hugo_section_path(content_type)

    # Transform frontmatter to get title/date for slug
    hugo_frontmatter = transform_to_hugo(frontmatter, body)
    slug = generate_slug(hugo_frontmatter.get('title', ''), hugo_frontmatter.get('date'))
    target_path = hugo_root / section_path / f"{slug}.md"

    # Step 3: Extract media references
    media_items, missing_count = extract_and_resolve_media(note_path)

    # Check for Pictures section
    note_content = note_path.read_text()
    has_gallery = has_pictures_section(note_content)
    gallery_media_count = len(extract_media_from_pictures_section(note_content)) if has_gallery else 0

    # Check for Associations section
    has_assoc = has_associations_section(note_content)
    assoc_link_count = len(extract_wikilinks_from_associations(note_content)) if has_assoc else 0

    # Print summary
    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print("[header]PUBLISH SUMMARY[/header]")
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print(f"Source:       [info]{note_path}[/info]")
    console.print(f"Title:        [highlight]{hugo_frontmatter.get('title', 'Untitled')}[/highlight]")
    console.print(f"Date:         {hugo_frontmatter.get('date', 'N/A')}")
    console.print(f"Content Type: [info]{content_type}[/info]")
    console.print(f"Target:       [info]{target_path}[/info]")
    if environment:
        console.print(f"Environment:  {environment}")
    console.print()

    if media_items:
        console.print(f"Media Files:  {format_count(str(len(media_items)))} to upload")
        if missing_count > 0:
            console.print(f"              {format_error(str(missing_count))} missing (will be skipped)")
    else:
        console.print("Media Files:  [dim]None[/dim]")

    if has_gallery:
        if generate_gallery:
            console.print(f"Gallery:      [success]YES[/success] ({gallery_media_count} images)")
        else:
            console.print(f"Gallery:      [dim]SKIPPED[/dim] ({gallery_media_count} images)")

    if has_assoc:
        if keep_associations:
            console.print(f"Associations: [success]CONVERT[/success] ({assoc_link_count} links -> Related)")
        else:
            console.print(f"Associations: [dim]REMOVE[/dim] ({assoc_link_count} links)")

    if skip_upload:
        console.print("Media Upload: [dim]SKIPPED[/dim]")

    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")

    # In dry-run mode, show preview and exit
    if dry_run:
        console.print("[warning][DRY RUN][/warning] No changes will be made.")
        console.print()

        # Run the conversion to show preview
        try:
            _, converted_body, _ = convert_note(
                note_path,
                DEFAULT_OUTPUT_DIR,  # Use default for preview
                media_url_map=None,  # No URLs in dry-run
                generate_gallery=generate_gallery,
                keep_associations=keep_associations,
                environment=environment
            )
        except FileNotFoundError as e:
            handle_error(e, "conversion preview")
        except HugoConfigError as e:
            handle_error(e, "conversion preview")
        except Exception as e:
            handle_error(e, "conversion preview")

        console.print("[header]--- Preview of converted content ---[/header]")
        console.print()
        from hugo_writer import preview_hugo_post
        preview = preview_hugo_post(hugo_frontmatter, converted_body)
        # Limit preview length
        preview_lines = preview.split('\n')
        if len(preview_lines) > 50:
            console.print('\n'.join(preview_lines[:50]))
            console.print(f"\n[dim]... (truncated, {len(preview_lines) - 50} more lines)[/dim]")
        else:
            console.print(preview)
        return

    # Non-dry-run mode: Confirm before proceeding
    if not yes_flag:
        if not confirm_prompt("Proceed with publishing?", default=True):
            console.print("[dim]Aborted.[/dim]")
            sys.exit(0)
        console.print()

    # Step 4: Upload media to MinIO
    media_url_map = None
    if media_items and not skip_upload:
        try:
            print_info(f"Uploading {len(media_items)} media file(s) to MinIO...")
            media_url_map = upload_media_to_minio(media_items)

            # Report upload results
            successful = sum(1 for v in media_url_map.values() if v is not None)
            failed = len(media_url_map) - successful
            print_success(f"Upload complete: {successful} uploaded, {failed} failed")
            if failed > 0:
                print_warning(f"Warning: {failed} file(s) failed to upload")
        except ImportError as e:
            handle_warning(e, "MinIO import")
            console.print("  [dim]Media upload skipped - minio package not installed[/dim]")
            console.print("  [dim]Install with: pip install minio[/dim]")
        except UploadError as e:
            handle_warning(e, "media upload")
            if not yes_flag:
                if not confirm_prompt("Continue without media upload?", default=False):
                    console.print("[dim]Aborted.[/dim]")
                    sys.exit(1)
        except Exception as e:
            handle_warning(e, "media upload")
            if not yes_flag:
                if not confirm_prompt("Continue without media upload?", default=False):
                    console.print("[dim]Aborted.[/dim]")
                    sys.exit(1)

    # Step 5: Convert the note
    print_info("Converting note...")
    try:
        hugo_fm, converted_body, _ = convert_note(
            note_path,
            str(hugo_root / section_path),  # Full path for routing
            media_url_map=media_url_map,
            generate_gallery=generate_gallery,
            keep_associations=keep_associations,
            environment=environment
        )
    except FileNotFoundError as e:
        handle_error(e, "converting note")
    except HugoConfigError as e:
        handle_error(e, "converting note")
    except Exception as e:
        handle_error(e, "converting note")

    # Step 6: Write the Hugo post
    print_info("Writing Hugo post...")
    try:
        written_path = write_hugo_post_routed(
            hugo_fm,
            converted_body,
            f"{slug}.md",
            hugo_root=hugo_root,
            content_type=content_type
        )
        console.print(f"Written to: [info]{written_path}[/info]")
    except PermissionError as e:
        handle_error(e, "writing Hugo post")
    except Exception as e:
        handle_error(e, "writing Hugo post")

    # Step 7: Record the publish in tracking file
    try:
        record_published(note_path, target_path=written_path)
    except Exception as e:
        # Non-fatal: warn but continue
        print_warning(f"Warning: Could not record publish state - {e}")

    # Final summary
    console.print()
    console.print("[success]" + "=" * 60 + "[/success]")
    console.print("[success]PUBLISH COMPLETE[/success]")
    console.print("[success]" + "=" * 60 + "[/success]")
    console.print(f"Source: [info]{note_path.name}[/info]")
    console.print(f"Target: [info]{written_path}[/info]")

    if media_url_map:
        uploaded = sum(1 for v in media_url_map.values() if v is not None)
        console.print(f"Media:  {format_count(str(uploaded))} file(s) uploaded")

    if has_gallery and generate_gallery:
        console.print(f"[success]Gallery:[/success] {gallery_media_count} image(s)")

    if has_assoc:
        if keep_associations:
            console.print(f"[success]Related:[/success] {assoc_link_count} link(s) converted")
        else:
            console.print("[dim]Associations: removed[/dim]")

    console.print()


def cmd_publish_dispatch(args):
    """
    Dispatch to either cmd_publish (single note) or cmd_publish_all (batch).

    This function checks the --all flag to determine which publish mode to use.
    """
    publish_all = getattr(args, 'publish_all', False)

    if publish_all:
        # Batch mode: publish all unpublished notes
        cmd_publish_all(args)
    else:
        # Single note mode: require a path
        if not args.path:
            print_error("Error: Must specify a note path or use --all flag")
            console.print("[dim]Usage: publish <path>  OR  publish --all[/dim]")
            sys.exit(1)
        cmd_publish(args)


def cmd_publish_all(args):
    """
    Publish all unpublished Obsidian notes with publish: true.

    Scans the vault for notes with publish: true in frontmatter,
    filters out notes that have already been published (and haven't
    changed), then publishes each remaining note.

    Uses a tracking file (.published.json) to record which notes have
    been published and their content hashes to detect changes.
    """
    # Get flags from args
    dry_run = getattr(args, 'dry_run', False)
    skip_upload = getattr(args, 'skip_upload', False)
    generate_gallery = not getattr(args, 'no_gallery', False)
    keep_associations = getattr(args, 'keep_associations', False)
    yes_flag = getattr(args, 'yes', False)
    hugo_root = Path(args.hugo_root) if hasattr(args, 'hugo_root') and args.hugo_root else DEFAULT_HUGO_ROOT
    vault_path = Path(args.vault) if hasattr(args, 'vault') and args.vault else None
    # Get verbose flag and enable verbose logging if set
    verbose = getattr(args, 'verbose', False)
    set_verbose(verbose)
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)
    # Get environment flag (ensure we get None if not set, not a MagicMock)
    environment = getattr(args, 'environment', None)
    if environment is not None and not isinstance(environment, str):
        environment = None

    # Step 1: Find all publishable notes
    try:
        all_notes = find_publishable_notes(vault_path=vault_path)
    except FileNotFoundError as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    except NotADirectoryError as e:
        print_error(f"Error: {e}")
        sys.exit(1)

    if not all_notes:
        print_warning("No publishable notes found.")
        return

    # Step 2: Filter to only unpublished notes
    unpublished_notes = get_unpublished_notes(all_notes)

    if not unpublished_notes:
        print_info(f"Found {len(all_notes)} publishable note(s), but all have already been published.")
        console.print("[dim]Use 'publish <path>' to force re-publishing a specific note.[/dim]")
        return

    # Step 3: Display summary
    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print("[header]BATCH PUBLISH SUMMARY[/header]")
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print(f"Vault:        [info]{vault_path or Path.home() / 'Notes'}[/info]")
    console.print(f"Hugo root:    [info]{hugo_root}[/info]")
    if environment:
        console.print(f"Environment:  {environment}")
    console.print()
    console.print(f"Total publishable notes:  {format_count(str(len(all_notes)))}")
    console.print(f"Already published:        {format_dim(str(len(all_notes) - len(unpublished_notes)))}")
    console.print(f"To publish:               {format_success(str(len(unpublished_notes)))}")
    console.print()

    # List notes to be published
    console.print("Notes to publish:")
    for note in unpublished_notes:
        fm = note['frontmatter']
        title = fm.get('title', note['path'].stem)
        content_type = determine_content_type(fm)
        console.print(f"  [dim][{content_type:12}][/dim] [info]{title}[/info]")

    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")

    # In dry-run mode, show what would happen and exit
    if dry_run:
        console.print("[warning][DRY RUN][/warning] No changes will be made.")
        console.print()

        for i, note in enumerate(unpublished_notes, 1):
            note_path = note['path']
            fm = note['frontmatter']
            title = fm.get('title', note_path.stem)
            content_type = determine_content_type(fm)
            section_path = get_hugo_section_path(content_type)

            console.print(f"\n[info][{i}/{len(unpublished_notes)}][/info] {title}")
            console.print(f"  Source:       [info]{note_path}[/info]")
            console.print(f"  Content type: {content_type}")
            console.print(f"  Target:       [info]{hugo_root / section_path}[/info]")

        console.print()
        console.print(f"[warning][DRY RUN][/warning] Would publish {format_count(str(len(unpublished_notes)))} note(s).")
        return

    # Non-dry-run mode: Confirm before proceeding
    if not yes_flag:
        if not confirm_prompt(f"Publish {len(unpublished_notes)} note(s)?", default=True):
            console.print("[dim]Aborted.[/dim]")
            sys.exit(0)
        console.print()

    # Step 4: Publish each note
    published_count = 0
    failed_count = 0
    failed_notes = []

    for i, note in enumerate(unpublished_notes, 1):
        note_path = note['path']
        fm = note['frontmatter']
        title = fm.get('title', note_path.stem)

        console.print(f"\n[info][{i}/{len(unpublished_notes)}][/info] Publishing: [highlight]{title}[/highlight]")
        console.print("-" * 40)

        try:
            # Get content type and section path
            content_type = determine_content_type(fm)
            section_path = get_hugo_section_path(content_type)

            # Transform frontmatter
            body = note['body']
            hugo_fm = transform_to_hugo(fm, body)
            slug = generate_slug(hugo_fm.get('title', ''), hugo_fm.get('date'))

            # Extract and upload media
            media_items, missing_count = extract_and_resolve_media(note_path)
            media_url_map = None

            if media_items and not skip_upload:
                try:
                    console.print(f"  Uploading {len(media_items)} media file(s)...")
                    media_url_map = upload_media_to_minio(media_items, show_progress=False)
                    successful = sum(1 for v in media_url_map.values() if v is not None)
                    console.print(f"  [success]Media uploaded:[/success] {successful}/{len(media_items)}")
                except Exception as e:
                    print_warning(f"  Warning: Media upload failed - {e}")

            # Convert the note
            hugo_fm, converted_body, _ = convert_note(
                note_path,
                str(hugo_root / section_path),
                media_url_map=media_url_map,
                generate_gallery=generate_gallery,
                keep_associations=keep_associations,
                environment=environment
            )

            # Write the Hugo post
            written_path = write_hugo_post_routed(
                hugo_fm,
                converted_body,
                f"{slug}.md",
                hugo_root=hugo_root,
                content_type=content_type
            )

            # Record the publish
            try:
                record_published(note_path, target_path=written_path)
            except Exception as e:
                print_warning(f"  Warning: Could not record publish state - {e}")

            console.print(f"  [success]Written to:[/success] [info]{written_path}[/info]")
            published_count += 1

        except Exception as e:
            print_error(f"  Error: {e}")
            failed_count += 1
            failed_notes.append((note_path, str(e)))

    # Final summary
    console.print()
    if failed_count == 0:
        console.print("[success]" + "=" * 60 + "[/success]")
        console.print("[success]BATCH PUBLISH COMPLETE[/success]")
        console.print("[success]" + "=" * 60 + "[/success]")
    else:
        console.print("[warning]" + "=" * 60 + "[/warning]")
        console.print("[warning]BATCH PUBLISH COMPLETE (with errors)[/warning]")
        console.print("[warning]" + "=" * 60 + "[/warning]")
    console.print(f"Published: {format_success(str(published_count))}")
    console.print(f"Failed:    {format_error(str(failed_count)) if failed_count > 0 else format_dim(str(failed_count))}")

    if failed_notes:
        console.print()
        console.print("[error]Failed notes:[/error]")
        for path, error in failed_notes:
            console.print(f"  [error]{path.name}:[/error] {error}")

    console.print()


def cmd_preview(args):
    """
    Preview a converted note in a local Hugo server.

    This command converts an Obsidian note, writes it to a temporary
    directory within the Hugo site structure, starts a Hugo server,
    and opens the browser to preview the rendered post.

    The server runs until the user presses Ctrl+C, after which the
    temporary content is cleaned up.

    Exit codes:
    - 0: Success (server terminated normally)
    - 1: Error (note not found, conversion failed, or Hugo server error)
    """
    note_path = Path(args.path)

    # Get flags from args
    skip_upload = getattr(args, 'skip_upload', True)  # Default to skip in preview mode
    generate_gallery = not getattr(args, 'no_gallery', False)
    keep_associations = getattr(args, 'keep_associations', False)
    hugo_root = Path(args.hugo_root) if hasattr(args, 'hugo_root') and args.hugo_root else DEFAULT_HUGO_ROOT
    port = getattr(args, 'port', 1313)
    no_browser = getattr(args, 'no_browser', False)
    # Get verbose flag and enable verbose logging if set
    verbose = getattr(args, 'verbose', False)
    set_verbose(verbose)
    # Get quiet flag and enable quiet mode if set
    quiet = getattr(args, 'quiet', False)
    set_quiet(quiet is True)
    # Get environment flag
    environment = getattr(args, 'environment', None)
    if environment is not None and not isinstance(environment, str):
        environment = None

    # Step 1: Parse and convert the note
    print_info(f"Converting note: {note_path.name}")

    try:
        frontmatter, body = parse_obsidian_note(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note")
    except Exception as e:
        handle_error(e, "parsing note")

    # Determine content type for proper routing
    content_type = determine_content_type(frontmatter)
    section_path = get_hugo_section_path(content_type)

    # Transform frontmatter to get the slug
    hugo_fm = transform_to_hugo(frontmatter, body)
    slug = generate_slug(hugo_fm.get('title', ''), hugo_fm.get('date'))

    # Extract and optionally upload media
    try:
        media_items, missing_count = extract_and_resolve_media(note_path)
    except FileNotFoundError as e:
        handle_error(e, "reading note for media extraction")
    except Exception as e:
        handle_error(e, "extracting media references")

    media_url_map = None

    if media_items and not skip_upload:
        try:
            print_info(f"Uploading {len(media_items)} media file(s) to MinIO...")
            media_url_map = upload_media_to_minio(media_items, show_progress=False)
        except ImportError as e:
            handle_warning(e, "MinIO import")
        except UploadError as e:
            handle_warning(e, "media upload")
        except Exception as e:
            handle_warning(e, "media upload")

    # Convert the note
    try:
        hugo_frontmatter, converted_body, _ = convert_note(
            note_path,
            str(hugo_root / section_path),
            media_url_map=media_url_map,
            generate_gallery=generate_gallery,
            keep_associations=keep_associations,
            environment=environment if environment else 'development'
        )
    except FileNotFoundError as e:
        handle_error(e, "converting note")
    except HugoConfigError as e:
        handle_error(e, "converting note")
    except Exception as e:
        handle_error(e, "converting note")

    # Step 2: Write to a temporary file in the Hugo content directory
    # We use a unique prefix to avoid conflicts with real content
    temp_filename = f"_preview_{slug}.md"
    target_path = hugo_root / section_path / temp_filename

    # Determine the URL for this content
    # Hugo URL structure: /section/slug/
    date_str = hugo_frontmatter.get('date', '')
    if date_str and isinstance(date_str, str) and len(date_str) >= 10:
        # For posts with dates, URL is usually /post/YYYY-MM-DD-slug/
        url_path = f"/{content_type}/{slug}/"
    else:
        url_path = f"/{content_type}/{slug}/"

    console.print(f"Writing preview to: [info]{target_path}[/info]")

    try:
        from hugo_writer import write_hugo_post
        written_path = write_hugo_post(hugo_frontmatter, converted_body, target_path)
    except PermissionError as e:
        handle_error(e, "writing preview file")
    except Exception as e:
        handle_error(e, "writing preview file")

    # Step 3: Start Hugo server
    hugo_cmd = [
        'hugo', 'server',
        '--source', str(hugo_root),
        '--port', str(port),
        '--buildDrafts',  # Include drafts
        '--buildFuture',  # Include future posts
        '--navigateToChanged',  # Navigate to changed content
        '--disableFastRender',  # Ensure full rebuild
    ]

    preview_url = f"http://localhost:{port}{url_path}"

    console.print()
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print("[header]PREVIEW SERVER[/header]")
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print(f"Content Type: [info]{content_type}[/info]")
    console.print(f"Preview URL:  [highlight]{preview_url}[/highlight]")
    console.print(f"Hugo Root:    [info]{hugo_root}[/info]")
    console.print()
    console.print("[dim]Press Ctrl+C to stop the server and clean up.[/dim]")
    console.print("[header]" + "=" * 60 + "[/header]")
    console.print()

    hugo_process = None
    try:
        # Start Hugo server
        hugo_process = subprocess.Popen(
            hugo_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(hugo_root)
        )

        # Wait a moment for the server to start, then open browser
        import time
        time.sleep(2)

        if not no_browser:
            print_info(f"Opening browser to: {preview_url}")
            webbrowser.open(preview_url)

        # Stream Hugo server output
        console.print()
        console.print("[header]Hugo server output:[/header]")
        console.print("-" * 40)

        if hugo_process.stdout:
            for line in hugo_process.stdout:
                console.print(line, end='')

        # Wait for the process to complete
        hugo_process.wait()

    except KeyboardInterrupt:
        console.print()
        console.print()
        print_info("Stopping server...")
    except Exception as e:
        print_error(f"Error running Hugo server: {e}")
    finally:
        # Terminate Hugo server if still running
        if hugo_process and hugo_process.poll() is None:
            hugo_process.terminate()
            try:
                hugo_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                hugo_process.kill()

        # Clean up the temporary preview file
        console.print(f"Cleaning up preview file: [info]{written_path}[/info]")
        try:
            written_path.unlink()
            print_success("Preview file removed.")
        except Exception as e:
            print_warning(f"Warning: Could not remove preview file: {e}")

    console.print()
    print_info("Preview session ended.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="publish",
        description="Publish Obsidian notes to Hugo blog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python publish.py publish ~/Notes/Blog/my-post.md
        Publish a single note (with confirmation prompts)

    python publish.py publish ~/Notes/Blog/my-post.md --dry-run
        Preview what would be published without making changes

    python publish.py publish ~/Notes/Blog/my-post.md -y
        Publish without confirmation prompts

    python publish.py publish ~/Notes/Blog/my-post.md -e development
        Publish using development environment S3CDN URLs

    python publish.py publish --all
        Publish all unpublished notes with publish: true

    python publish.py publish --all --dry-run
        Preview batch publishing without making changes

    python publish.py publish --all --vault ~/MyVault
        Publish all from a specific vault

    python publish.py publish --all -e production
        Publish all notes using production environment config

    python publish.py scan
        Scan the Obsidian vault for notes with publish: true

    python publish.py list
        Show all publishable notes and their target paths

    python publish.py convert ~/Notes/Blog/my-post.md
        Convert a specific note to Hugo format (low-level)

    python publish.py convert ~/Notes/Blog/my-post.md -e development
        Convert using development environment S3CDN URLs

    python publish.py preview ~/Notes/Blog/my-post.md
        Preview a note in a local Hugo server

    python publish.py preview ~/Notes/Blog/my-post.md --port 8080 --no-browser
        Preview on a custom port without opening browser
        """
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
        help="Available commands"
    )

    # publish subcommand (main command)
    publish_parser = subparsers.add_parser(
        "publish",
        help="Publish Obsidian note(s) to the Hugo blog (main command)"
    )
    publish_parser.add_argument(
        "path",
        nargs='?',  # Make path optional when using --all
        help="Path to the Obsidian note to publish (not required with --all)"
    )
    publish_parser.add_argument(
        "--all",
        action="store_true",
        dest="publish_all",
        help="Publish all notes with publish: true that haven't been published yet"
    )
    publish_parser.add_argument(
        "--vault",
        help="Path to the Obsidian vault (default: ~/Notes). Only used with --all"
    )
    publish_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the publish without making any changes"
    )
    publish_parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Skip confirmation prompts (non-interactive mode)"
    )
    publish_parser.add_argument(
        "--hugo-root",
        help=f"Path to Hugo site root (default: {DEFAULT_HUGO_ROOT})"
    )
    publish_parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip media upload to MinIO"
    )
    publish_parser.add_argument(
        "--no-gallery",
        action="store_true",
        help="Skip gallery generation even if a Pictures section exists"
    )
    publish_parser.add_argument(
        "--keep-associations",
        action="store_true",
        help="Convert Associations section to Hugo links (default: remove)"
    )
    publish_parser.add_argument(
        "-e", "--environment",
        help="Hugo environment (development/production). Uses environment-specific S3CDN URLs from Hugo config"
    )
    publish_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any validation warnings are present (default: only fail on errors)"
    )
    publish_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed logging of each step in the conversion and upload process"
    )
    publish_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    publish_parser.set_defaults(func=cmd_publish_dispatch)

    # scan subcommand
    scan_parser = subparsers.add_parser(
        "scan",
        help="Find all notes marked with publish: true in frontmatter"
    )
    scan_parser.add_argument(
        "--vault",
        help="Path to the Obsidian vault (default: ~/Notes)"
    )
    scan_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
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
    list_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
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
    media_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    media_parser.set_defaults(func=cmd_media)

    # validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a note before publishing (check frontmatter, media, links)"
    )
    validate_parser.add_argument(
        "path",
        help="Path to the Obsidian note to validate"
    )
    validate_parser.add_argument(
        "--vault",
        help="Path to the Obsidian vault for link validation (default: ~/Notes)"
    )
    validate_parser.add_argument(
        "--hugo-root",
        help=f"Path to Hugo site root for link validation (default: {DEFAULT_HUGO_ROOT})"
    )
    validate_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    validate_parser.set_defaults(func=cmd_validate)

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
    convert_parser.add_argument(
        "-e", "--environment",
        help="Hugo environment (development/production). Uses environment-specific S3CDN URLs from Hugo config"
    )
    convert_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed logging of each step in the conversion and upload process"
    )
    convert_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    convert_parser.set_defaults(func=cmd_convert)

    # preview subcommand
    preview_parser = subparsers.add_parser(
        "preview",
        help="Preview a converted note in a local Hugo server"
    )
    preview_parser.add_argument(
        "path",
        help="Path to the Obsidian note to preview"
    )
    preview_parser.add_argument(
        "--hugo-root",
        help=f"Path to Hugo site root (default: {DEFAULT_HUGO_ROOT})"
    )
    preview_parser.add_argument(
        "--port",
        type=int,
        default=1313,
        help="Port for Hugo server (default: 1313)"
    )
    preview_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )
    preview_parser.add_argument(
        "--skip-upload",
        action="store_true",
        default=True,
        help="Skip media upload to MinIO (default: True for preview)"
    )
    preview_parser.add_argument(
        "--upload",
        action="store_false",
        dest="skip_upload",
        help="Upload media to MinIO before preview"
    )
    preview_parser.add_argument(
        "--no-gallery",
        action="store_true",
        help="Skip gallery generation even if a Pictures section exists"
    )
    preview_parser.add_argument(
        "--keep-associations",
        action="store_true",
        help="Convert Associations section to Hugo links (default: remove)"
    )
    preview_parser.add_argument(
        "-e", "--environment",
        default="development",
        help="Hugo environment for S3CDN URLs (default: development)"
    )
    preview_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed logging of each step in the conversion and upload process"
    )
    preview_parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    preview_parser.set_defaults(func=cmd_preview)

    # Parse arguments and run appropriate command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
