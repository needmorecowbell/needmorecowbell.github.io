#!/usr/bin/env python3
"""
Obsidian to Hugo Conversion Script

A streamlined CLI tool for converting Obsidian notes to Hugo-compatible markdown.
This script handles the complete conversion pipeline:

1. Parse Obsidian frontmatter and convert to Hugo format
2. Extract images from ## Pictures section
3. Handle wikilink removal/conversion
4. Upload images to MinIO with proper naming (spaces → underscores)
5. Generate thumbnails for all media (images and videos) for faster gallery loading
6. Create gallery shortcode from Pictures section
7. Output Hugo markdown to correct directory based on content_type

Usage:
    python obsidian_to_hugo.py <obsidian_note_path> [options]

Examples:
    # Convert a note with default settings
    python obsidian_to_hugo.py ~/Notes/Projects/My_Project.md

    # Dry run to preview without writing files
    python obsidian_to_hugo.py ~/Notes/Projects/My_Project.md --dry-run

    # Skip media upload (local testing)
    python obsidian_to_hugo.py ~/Notes/Projects/My_Project.md --skip-upload

    # Specify content type explicitly
    python obsidian_to_hugo.py ~/Notes/Projects/My_Project.md --type project
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Load environment variables from .env file if it exists
def load_dotenv():
    """Load environment variables from scripts/.env if it exists."""
    try:
        from dotenv import load_dotenv as dotenv_load
    except ImportError:
        return False

    script_dir = Path(__file__).parent.resolve()
    env_path = script_dir / '.env'

    if env_path.exists():
        dotenv_load(env_path)
        return True
    return False

# Load .env at module import time
_dotenv_loaded = load_dotenv()

# Import publishing modules
from obsidian_parser import parse_obsidian_note
from frontmatter_transformer import transform_to_hugo, generate_slug
from syntax_converter import convert_wikilinks, convert_embedded_images, convert_embedded_media
from gallery_generator import (
    has_pictures_section,
    extract_pictures_section,
    remove_pictures_section,
    has_associations_section,
    remove_associations_section,
)
from content_router import determine_content_type, get_hugo_section_path
from hugo_writer import write_hugo_post, preview_hugo_post
from media_extractor import (
    resolve_media_path,
    VIDEO_EXTENSIONS,
    IMAGE_EXTENSIONS,
    ALL_MEDIA_EXTENSIONS,
    generate_thumbnail,
    THUMBNAIL_SUPPORTED_EXTENSIONS,
)
from console import (
    print_success,
    print_warning,
    print_error,
    print_info,
    print_header,
    print_dim,
    console,
)

# Default paths
DEFAULT_HUGO_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_MEDIA_BASE = Path.home() / "Notes" / "Media"


def extract_all_media_from_pictures(body: str) -> List[str]:
    """
    Extract all media references from the Pictures section.

    Handles both wikilink syntax [[path/to/file.ext]] and
    embed syntax ![[path/to/file.ext]] used in Obsidian.

    Args:
        body: The markdown body content

    Returns:
        List of media file paths found in the Pictures section
    """
    pictures_section = extract_pictures_section(body)
    if not pictures_section:
        return []

    # Build pattern that matches any media extension
    extensions_pattern = '|'.join(sorted(ALL_MEDIA_EXTENSIONS))

    # Pattern to match both [[...]] and ![[...]] syntax
    # Captures media paths with supported extensions
    pattern = re.compile(
        rf'!?\[\[\s*([^\]\s][^\]]*\.({extensions_pattern}))\s*\]\]',
        re.IGNORECASE
    )

    references = []
    for match in pattern.finditer(pictures_section):
        media_path = match.group(1).strip()
        references.append(media_path)

    return references


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by replacing spaces with underscores.

    Args:
        filename: The original filename

    Returns:
        Sanitized filename with spaces replaced by underscores
    """
    return filename.replace(' ', '_')


def get_project_slug(title: str) -> str:
    """
    Generate a project slug from a title.

    Converts title to lowercase, replaces spaces with underscores,
    and removes special characters.

    Args:
        title: The project title

    Returns:
        URL-safe project slug
    """
    if not title:
        return 'untitled'

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces with underscores
    slug = slug.replace(' ', '_')

    # Remove special characters except underscores and hyphens
    slug = re.sub(r'[^a-z0-9_\-]', '', slug)

    # Replace multiple underscores with single underscore
    slug = re.sub(r'_+', '_', slug)

    # Strip leading/trailing underscores
    slug = slug.strip('_')

    return slug or 'untitled'


def upload_media_to_minio(
    media_files: List[Tuple[str, str]],
    destination_path: str,
    dry_run: bool = False
) -> Dict[str, str]:
    """
    Upload media files to MinIO using rclone.

    Args:
        media_files: List of (obsidian_reference, local_path) tuples
        destination_path: S3 destination path (e.g., 'projects/my_project')
        dry_run: If True, only print what would be uploaded

    Returns:
        Dictionary mapping original filenames to uploaded filenames
    """
    uploaded_files = {}
    remote = os.environ.get('RCLONE_REMOTE', 'homes3:amblog/assets')

    for obsidian_ref, local_path in media_files:
        if not local_path or not Path(local_path).exists():
            print_warning(f"  Media file not found: {obsidian_ref}")
            continue

        # Get sanitized filename
        original_filename = Path(local_path).name
        sanitized_filename = sanitize_filename(original_filename)
        dest_full = f"{remote}/{destination_path}/{sanitized_filename}"

        if dry_run:
            print_dim(f"  Would upload: {original_filename} -> {sanitized_filename}")
            uploaded_files[original_filename] = sanitized_filename
        else:
            print_info(f"  Uploading: {original_filename} -> {sanitized_filename}")
            try:
                # Create temp copy with sanitized name if needed
                if original_filename != sanitized_filename:
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir) / sanitized_filename
                        shutil.copy2(local_path, tmp_path)
                        result = subprocess.run(
                            ['rclone', 'copyto', str(tmp_path), dest_full],
                            capture_output=True,
                            text=True
                        )
                else:
                    result = subprocess.run(
                        ['rclone', 'copyto', local_path, dest_full],
                        capture_output=True,
                        text=True
                    )

                if result.returncode != 0:
                    print_warning(f"    Failed to upload: {result.stderr}")
                else:
                    uploaded_files[original_filename] = sanitized_filename
                    print_success(f"    Uploaded successfully")
            except Exception as e:
                print_warning(f"    Upload error: {e}")

    return uploaded_files


def generate_media_thumbnails(
    media_files: List[Tuple[str, str]],
    destination_path: str,
    dry_run: bool = False
) -> List[str]:
    """
    Generate and upload thumbnails for all media files (images and videos).

    Args:
        media_files: List of (obsidian_reference, local_path) tuples
        destination_path: S3 destination path
        dry_run: If True, only print what would be generated

    Returns:
        List of generated thumbnail filenames
    """
    thumbnails = []
    remote = os.environ.get('RCLONE_REMOTE', 'homes3:amblog/assets')

    for obsidian_ref, local_path in media_files:
        if not local_path or not Path(local_path).exists():
            continue

        ext = Path(local_path).suffix.lower().lstrip('.')
        original_filename = Path(local_path).name
        sanitized_basename = sanitize_filename(Path(local_path).stem)
        thumb_name = f"{sanitized_basename}.thumb.jpg"

        # Determine if this is a video or image
        is_video = ext in VIDEO_EXTENSIONS
        is_image = ext in THUMBNAIL_SUPPORTED_EXTENSIONS

        if not is_video and not is_image:
            continue

        if dry_run:
            print_dim(f"  Would generate thumbnail: {thumb_name}")
            thumbnails.append(thumb_name)
            continue

        print_info(f"  Generating thumbnail for: {original_filename}")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_thumb = Path(tmp_dir) / thumb_name

                if is_video:
                    # Use ffmpeg for video thumbnails
                    # Try to extract frame at 1 second, fall back to first frame
                    result = subprocess.run(
                        ['ffmpeg', '-y', '-i', local_path, '-ss', '00:00:01',
                         '-vframes', '1', '-vf', 'scale=400:-1', '-q:v', '2', str(tmp_thumb)],
                        capture_output=True,
                        text=True
                    )

                    if result.returncode != 0:
                        # Fallback to first frame
                        result = subprocess.run(
                            ['ffmpeg', '-y', '-i', local_path,
                             '-vframes', '1', '-vf', 'scale=400:-1', '-q:v', '2', str(tmp_thumb)],
                            capture_output=True,
                            text=True
                        )

                    if not tmp_thumb.exists():
                        print_warning(f"    Failed to generate video thumbnail")
                        continue

                else:
                    # Use Pillow for image thumbnails
                    thumb_result = generate_thumbnail(
                        local_path,
                        str(tmp_thumb),
                        width=400,
                        quality=85
                    )

                    if not thumb_result:
                        # If thumbnail generation returned None, the image might be
                        # smaller than target width - copy original as "thumbnail"
                        shutil.copy2(local_path, tmp_thumb)
                        # Convert to JPEG if needed
                        if ext not in ('jpg', 'jpeg'):
                            from PIL import Image
                            with Image.open(tmp_thumb) as img:
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    if img.mode in ('RGBA', 'LA'):
                                        background.paste(img, mask=img.split()[-1])
                                        img = background
                                    else:
                                        img = img.convert('RGB')
                                img.save(tmp_thumb, 'JPEG', quality=85, optimize=True)

                if tmp_thumb.exists():
                    # Upload thumbnail
                    dest_full = f"{remote}/{destination_path}/{thumb_name}"
                    upload_result = subprocess.run(
                        ['rclone', 'copyto', str(tmp_thumb), dest_full],
                        capture_output=True,
                        text=True
                    )
                    if upload_result.returncode == 0:
                        thumbnails.append(thumb_name)
                        print_success(f"    Generated and uploaded thumbnail")
                    else:
                        print_warning(f"    Failed to upload thumbnail")
                else:
                    print_warning(f"    Failed to generate thumbnail")

        except FileNotFoundError as e:
            if 'ffmpeg' in str(e):
                print_warning(f"    ffmpeg not found, skipping video thumbnail")
            else:
                print_warning(f"    Thumbnail error: {e}")
        except Exception as e:
            print_warning(f"    Thumbnail error: {e}")

    return thumbnails


# Keep old function name for backwards compatibility
def generate_video_thumbnails(
    media_files: List[Tuple[str, str]],
    destination_path: str,
    dry_run: bool = False
) -> List[str]:
    """Deprecated: Use generate_media_thumbnails instead."""
    return generate_media_thumbnails(media_files, destination_path, dry_run)


def generate_gallery_shortcode(
    uploaded_files: Dict[str, str],
    destination_path: str,
    max_rows: int = 1
) -> str:
    """
    Generate a Hugo gallery shortcode from uploaded files.

    Args:
        uploaded_files: Dict mapping original to sanitized filenames
        destination_path: S3 path for the gallery
        max_rows: Number of rows per page in gallery

    Returns:
        Hugo gallery shortcode string
    """
    if not uploaded_files:
        return ""

    # Get the sanitized filenames
    image_files = list(uploaded_files.values())
    images_str = ", ".join(image_files)

    return f'{{{{< gallery path="{destination_path}" maxRows="{max_rows}" images="{images_str}" />}}}}'


def convert_obsidian_to_hugo(
    note_path: Path,
    hugo_root: Optional[Path] = None,
    content_type: Optional[str] = None,
    dry_run: bool = False,
    skip_upload: bool = False,
    skip_video_thumbs: bool = False,
    media_base: Optional[Path] = None,
) -> Optional[Path]:
    """
    Convert an Obsidian note to Hugo format.

    This is the main conversion function that handles the complete pipeline:
    1. Parse Obsidian note
    2. Transform frontmatter to Hugo format
    3. Extract and upload media from Pictures section
    4. Generate video thumbnails
    5. Convert syntax (wikilinks, embeds)
    6. Create gallery shortcode
    7. Write Hugo markdown

    Args:
        note_path: Path to the Obsidian note
        hugo_root: Path to Hugo site root (defaults to parent of scripts/)
        content_type: Override content type (post/project/photography)
        dry_run: Preview changes without writing files
        skip_upload: Skip media upload (useful for testing)
        skip_video_thumbs: Skip video thumbnail generation
        media_base: Base path for resolving media references

    Returns:
        Path to the written Hugo file, or None if dry_run
    """
    note_path = Path(note_path).expanduser().resolve()
    hugo_root = hugo_root or DEFAULT_HUGO_ROOT
    media_base = media_base or DEFAULT_MEDIA_BASE

    if not note_path.exists():
        print_error(f"Note not found: {note_path}")
        return None

    print_header(f"Converting: {note_path.name}")
    console.print()

    # Step 1: Parse Obsidian note
    print_info("Parsing Obsidian note...")
    try:
        frontmatter, body = parse_obsidian_note(note_path)
    except Exception as e:
        print_error(f"Failed to parse note: {e}")
        return None

    # Step 2: Extract metadata from body if not in frontmatter
    # Obsidian often uses **Key**:: Value format in the body
    if 'description' not in frontmatter:
        desc_match = re.search(r'\*\*Description\*\*::\s*(.+?)$', body, re.MULTILINE)
        if desc_match:
            frontmatter['description'] = desc_match.group(1).strip()

    # Extract date from **Created**:: if not in frontmatter
    if 'date' not in frontmatter or not frontmatter['date']:
        date_match = re.search(r'\*\*Created\*\*::\s*(\d{1,2}-\d{1,2}-\d{4})', body)
        if date_match:
            # Convert MM-DD-YYYY to YYYY-MM-DD
            parts = date_match.group(1).split('-')
            if len(parts) == 3:
                frontmatter['date'] = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"

    # Step 2: Transform frontmatter
    print_info("Transforming frontmatter...")
    hugo_frontmatter = transform_to_hugo(frontmatter, body, content_type)

    # Determine content type for routing
    effective_content_type = content_type or determine_content_type(frontmatter)
    print_dim(f"  Content type: {effective_content_type}")

    # Get project/post slug for media paths
    title = hugo_frontmatter.get('title', 'untitled')
    project_slug = get_project_slug(title)
    print_dim(f"  Slug: {project_slug}")

    # Determine S3 destination path based on content type
    if effective_content_type == 'project':
        s3_path = f"projects/{project_slug}"
    elif effective_content_type == 'photography':
        s3_path = f"img/gallery/{project_slug}"
    else:
        s3_path = f"img/posts/{project_slug}"

    print_dim(f"  S3 path: {s3_path}")

    # Step 3: Extract media from Pictures section
    uploaded_files = {}
    has_gallery = False

    if has_pictures_section(body):
        print_info("Processing Pictures section...")
        media_refs = extract_all_media_from_pictures(body)
        print_dim(f"  Found {len(media_refs)} media reference(s)")

        if media_refs:
            has_gallery = True
            # Resolve media paths
            media_files = []
            for ref in media_refs:
                resolved = resolve_media_path(ref, media_base, validate=True)
                media_files.append((ref, resolved))

            # Step 4: Upload media
            if not skip_upload:
                print_info("Uploading media to MinIO...")
                uploaded_files = upload_media_to_minio(
                    media_files, s3_path, dry_run
                )

                # Step 5: Generate thumbnails for all media (images and videos)
                if not skip_video_thumbs:
                    print_info("Generating thumbnails...")
                    generate_media_thumbnails(
                        media_files, s3_path, dry_run
                    )
            else:
                print_dim("  Skipping media upload (--skip-upload)")
                # Still create the mapping for shortcode generation
                for ref, local_path in media_files:
                    if local_path:
                        original = Path(local_path).name
                        uploaded_files[original] = sanitize_filename(original)

    # Step 6: Convert body content
    print_info("Converting body content...")

    # Remove Pictures section (will be replaced with gallery)
    if has_pictures_section(body):
        body = remove_pictures_section(body)

    # Remove Associations section (Obsidian-specific)
    if has_associations_section(body):
        body = remove_associations_section(body)

    # Convert wikilinks to regular markdown links
    body = convert_wikilinks(body)

    # Convert any remaining embedded images/media
    body = convert_embedded_images(body)
    body = convert_embedded_media(body)

    # Remove the H1 title if it matches the frontmatter title
    # (Hugo uses frontmatter title, so duplicate H1 is unnecessary)
    title_pattern = re.compile(
        rf'^#\s+{re.escape(title)}\s*$',
        re.MULTILINE | re.IGNORECASE
    )
    body = title_pattern.sub('', body)

    # Clean up any metadata lines commonly used in Obsidian
    # (e.g., **Created**:: date, **Author**:: name)
    metadata_pattern = re.compile(r'^\*\*\w+\*\*::\s*.*$', re.MULTILINE)
    body = metadata_pattern.sub('', body)

    # Remove empty bold markers (****)
    body = re.sub(r'^\*{4}\s*$', '', body, flags=re.MULTILINE)

    # Remove horizontal rules (-----, *****, etc.) that are used as separators
    body = re.sub(r'^-{3,}\s*$', '', body, flags=re.MULTILINE)
    body = re.sub(r'^\*{3,}\s*$', '', body, flags=re.MULTILINE)

    # Remove Collaborators and References sections if empty or have just placeholder
    for section in ['Collaborators', 'References']:
        # Match section header followed by empty list items or numbered placeholders
        section_pattern = re.compile(
            rf'^##\s+{section}\s*\n(-\s*\n?|1\.\s*\n?)*$',
            re.MULTILINE | re.IGNORECASE
        )
        body = section_pattern.sub('', body)

    # Clean up excessive blank lines
    body = re.sub(r'\n{3,}', '\n\n', body)
    body = body.strip()

    # Step 7: Add gallery shortcode if we have media
    if has_gallery and uploaded_files:
        print_info("Adding gallery shortcode...")
        gallery_shortcode = generate_gallery_shortcode(
            uploaded_files, s3_path
        )
        if gallery_shortcode:
            body = f"{body}\n\n{gallery_shortcode}"

    # Step 8: Determine output path
    section_path = get_hugo_section_path(effective_content_type)
    date_str = hugo_frontmatter.get('date', '')
    filename = generate_slug(title, date_str if effective_content_type == 'post' else None)
    output_path = hugo_root / section_path / f"{filename}.md"

    print_info(f"Output path: {output_path.relative_to(hugo_root)}")

    # Step 9: Write or preview
    if dry_run:
        console.print()
        print_header("=== DRY RUN PREVIEW ===")
        console.print()
        preview = preview_hugo_post(hugo_frontmatter, body)
        # Use markup=False to prevent Rich from interpreting [...] as style tags
        console.print(preview, markup=False)
        console.print()
        print_header("=== END PREVIEW ===")
        return None
    else:
        print_info("Writing Hugo post...")
        try:
            written_path = write_hugo_post(
                hugo_frontmatter,
                body,
                output_path,
                create_dirs=True
            )
            print_success(f"Successfully wrote: {written_path}")
            return written_path
        except Exception as e:
            print_error(f"Failed to write post: {e}")
            return None


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Convert Obsidian notes to Hugo-compatible markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a note with default settings
  python obsidian_to_hugo.py "~/Notes/Projects/My Project.md"

  # Dry run to preview without writing files
  python obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --dry-run

  # Skip media upload (local testing)
  python obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --skip-upload

  # Specify content type explicitly
  python obsidian_to_hugo.py "~/Notes/Projects/My Project.md" --type project
"""
    )

    parser.add_argument(
        'note_path',
        type=str,
        help='Path to the Obsidian markdown note'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview changes without writing files or uploading'
    )

    parser.add_argument(
        '--type', '-t',
        choices=['post', 'project', 'photography'],
        default=None,
        help='Override content type (default: inferred from frontmatter/tags)'
    )

    parser.add_argument(
        '--hugo-root',
        type=str,
        default=None,
        help='Hugo site root directory (default: parent of scripts/)'
    )

    parser.add_argument(
        '--media-base',
        type=str,
        default=None,
        help='Base path for media files (default: ~/Notes/Media)'
    )

    parser.add_argument(
        '--skip-upload',
        action='store_true',
        help='Skip uploading media to MinIO'
    )

    parser.add_argument(
        '--skip-thumbs',
        '--skip-video-thumbs',  # Keep old flag for backwards compatibility
        dest='skip_video_thumbs',
        action='store_true',
        help='Skip thumbnail generation for images and videos'
    )

    args = parser.parse_args()

    # Resolve paths
    note_path = Path(args.note_path).expanduser()
    hugo_root = Path(args.hugo_root).expanduser() if args.hugo_root else None
    media_base = Path(args.media_base).expanduser() if args.media_base else None

    # Run conversion
    result = convert_obsidian_to_hugo(
        note_path=note_path,
        hugo_root=hugo_root,
        content_type=args.type,
        dry_run=args.dry_run,
        skip_upload=args.skip_upload,
        skip_video_thumbs=args.skip_video_thumbs,
        media_base=media_base,
    )

    if args.dry_run:
        console.print()
        print_info("Dry run complete. No files were written.")
        sys.exit(0)
    elif result:
        console.print()
        print_success("Conversion complete!")
        print_dim(f"  Output: {result}")
        print_dim("  Next: Run 'hugo server' to preview, then commit changes")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
