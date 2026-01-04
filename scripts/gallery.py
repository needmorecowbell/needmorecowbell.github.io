#!/usr/bin/env python3
"""
Gallery Management Tool

Helps create and manage gallery manifests for selective image publishing.
Generates .gallery.yaml files that map source files to published names.

Usage:
    python gallery.py init <source_dir> <destination> [--output manifest.gallery.yaml]
    python gallery.py sync <manifest.gallery.yaml> [--dry-run]
    python gallery.py list <manifest.gallery.yaml>
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from console import (
    print_success, print_error, print_warning, print_info,
    print_header, print_dim
)


# Supported media extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def find_media_files(source_dir: Path, recursive: bool = True) -> list[Path]:
    """Find all media files in a directory."""
    files = []
    pattern = '**/*' if recursive else '*'

    for ext in MEDIA_EXTENSIONS:
        files.extend(source_dir.glob(f'{pattern}{ext}'))
        files.extend(source_dir.glob(f'{pattern}{ext.upper()}'))

    return sorted(set(files))


def generate_name(index: int, prefix: str, extension: str) -> str:
    """Generate a sequential filename like prefix_01.jpg"""
    return f"{prefix}_{index:02d}{extension}"


def load_manifest(manifest_path: Path) -> dict:
    """Load a gallery manifest YAML file."""
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)


def save_manifest(manifest: dict, manifest_path: Path) -> None:
    """Save a gallery manifest YAML file."""
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def cmd_init(args) -> int:
    """Initialize a new gallery manifest from a source directory."""
    source_dir = Path(args.source_dir).expanduser().resolve()

    if not source_dir.exists():
        print_error(f"Source directory not found: {source_dir}")
        return 1

    # Find all media files
    files = find_media_files(source_dir, recursive=not args.flat)

    if not files:
        print_warning(f"No media files found in {source_dir}")
        return 1

    print_header(f"Found {len(files)} media files in {source_dir}")
    print()

    # Generate prefix from destination
    prefix = args.prefix or Path(args.destination).name.replace('/', '_').replace('-', '_')

    # Create manifest structure
    manifest = {
        'source_dir': str(source_dir),
        'destination': args.destination,
        'prefix': prefix,
        'images': []
    }

    # List files for selection
    print("Select files to include (enter numbers separated by spaces, 'all' for all, or 'q' to quit):")
    print("-" * 60)

    for i, f in enumerate(files, 1):
        rel_path = f.relative_to(source_dir)
        size_kb = f.stat().st_size / 1024
        print(f"  [{i:3d}] {rel_path} ({size_kb:.1f} KB)")

    print("-" * 60)

    if args.all:
        selection = list(range(len(files)))
        print("Auto-selecting all files (--all flag)")
    else:
        try:
            response = input("\nSelection: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1

        if response == 'q':
            return 0
        elif response == 'all':
            selection = list(range(len(files)))
        else:
            try:
                # Parse space or comma separated numbers
                selection = []
                for part in response.replace(',', ' ').split():
                    if '-' in part:
                        # Handle ranges like 1-5
                        start, end = part.split('-')
                        selection.extend(range(int(start) - 1, int(end)))
                    else:
                        selection.append(int(part) - 1)
            except ValueError:
                print_error("Invalid selection format")
                return 1

    # Build manifest entries
    for idx, file_idx in enumerate(selection, 1):
        if file_idx < 0 or file_idx >= len(files):
            print_warning(f"Skipping invalid index: {file_idx + 1}")
            continue

        source_file = files[file_idx]
        rel_path = source_file.relative_to(source_dir)
        ext = source_file.suffix.lower()

        # Generate destination name
        dest_name = generate_name(idx, prefix, ext)

        manifest['images'].append({
            'src': str(rel_path),
            'name': dest_name,
            'caption': ''
        })

    if not manifest['images']:
        print_warning("No files selected")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"{prefix}.gallery.yaml")

    # Save manifest
    save_manifest(manifest, output_path)
    print_success(f"Created manifest: {output_path}")
    print_info(f"  Source: {source_dir}")
    print_info(f"  Destination: {args.destination}")
    print_info(f"  Files: {len(manifest['images'])}")

    print()
    print_dim("Next steps:")
    print_dim(f"  1. Edit {output_path} to add captions or adjust names")
    print_dim(f"  2. Run: python gallery.py sync {output_path}")

    return 0


def cmd_sync(args) -> int:
    """Sync files from manifest to MinIO."""
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print_error(f"Manifest not found: {manifest_path}")
        return 1

    manifest = load_manifest(manifest_path)
    source_dir = Path(manifest['source_dir']).expanduser()
    destination = manifest['destination']

    print_header(f"Syncing gallery: {destination}")
    print_info(f"Source: {source_dir}")
    print_info(f"Files: {len(manifest['images'])}")
    print()

    if args.dry_run:
        print_warning("[DRY RUN] No files will be uploaded")
        print()

    # Check rclone availability
    import subprocess
    try:
        subprocess.run(['rclone', 'version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("rclone not found. Please install rclone.")
        return 1

    errors = []
    uploaded = 0

    for entry in manifest['images']:
        src_path = source_dir / entry['src']
        dest_name = entry['name']
        dest_full = f"homes3:amblog/assets/{destination}/{dest_name}"

        if not src_path.exists():
            print_error(f"  Source not found: {src_path}")
            errors.append(entry['src'])
            continue

        if args.dry_run:
            print_dim(f"  Would upload: {entry['src']} -> {dest_name}")
        else:
            print_info(f"  Uploading: {entry['src']} -> {dest_name}")
            result = subprocess.run(
                ['rclone', 'copyto', str(src_path), dest_full],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print_error(f"    Failed: {result.stderr}")
                errors.append(entry['src'])
            else:
                uploaded += 1

    print()
    if errors:
        print_warning(f"Completed with {len(errors)} error(s)")
        return 1
    elif args.dry_run:
        print_success(f"Dry run complete: {len(manifest['images'])} file(s) would be uploaded")
    else:
        print_success(f"Uploaded {uploaded} file(s)")

    return 0


def cmd_list(args) -> int:
    """List contents of a manifest."""
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print_error(f"Manifest not found: {manifest_path}")
        return 1

    manifest = load_manifest(manifest_path)

    print_header(f"Gallery: {manifest['destination']}")
    print_info(f"Source: {manifest['source_dir']}")
    print_info(f"Prefix: {manifest.get('prefix', 'N/A')}")
    print()

    print(f"{'Source':<50} {'Published As':<25} Caption")
    print("-" * 90)

    for entry in manifest['images']:
        caption = entry.get('caption', '')[:30]
        print(f"{entry['src']:<50} {entry['name']:<25} {caption}")

    print("-" * 90)
    print(f"Total: {len(manifest['images'])} file(s)")

    return 0


def cmd_html(args) -> int:
    """Generate nanogallery2 HTML from manifest."""
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print_error(f"Manifest not found: {manifest_path}")
        return 1

    manifest = load_manifest(manifest_path)
    destination = manifest['destination']

    # Generate HTML
    lines = [
        f'<div ID="gallery-{manifest.get("prefix", "gallery")}" data-nanogallery2=\'{{',
        f'    "itemsBaseURL": "{{{{<s3cdn>}}}}/{destination}/",',
        '    "thumbnailWidth": "250",',
        '    "thumbnailHeight": "250",',
        '    "thumbnailBorderVertical": 1,',
        '    "thumbnailBorderHorizontal": 1,',
        '    "thumbnailLabel": {',
        '      "position": "overImageOnBottom",',
        '      "displayDescription": true',
        '    },',
        '    "thumbnailHoverEffect2": "labelAppear75|descriptionSlideUp",',
        '    "galleryDisplayMode": "pagination",',
        '    "galleryMaxRows": 2,',
        '    "thumbnailAlignment": "center",',
        '    "thumbnailOpenImage": true,',
        '    "viewerTools": {',
        '      "topLeft": "pageCounter, label",',
        '      "topRight": "playPauseButton, rotateLeft, rotateRight, fullscreenButton, closeButton"',
        '    }',
        "}'>"
    ]

    for entry in manifest['images']:
        name = entry['name']
        caption = entry.get('caption', '')
        title = caption or name.rsplit('.', 1)[0].replace('_', ' ').title()
        lines.append(f'  <a href="{name}" data-ngthumb="{name}" data-ngdesc="{caption}">{title}</a>')

    lines.append('</div>')

    print('\n'.join(lines))

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Gallery management tool for selective image publishing'
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init command
    init_parser = subparsers.add_parser('init', help='Create a new gallery manifest')
    init_parser.add_argument('source_dir', help='Source directory containing media files')
    init_parser.add_argument('destination', help='Destination path in MinIO (e.g., projects/dogwood_bonsai)')
    init_parser.add_argument('--output', '-o', help='Output manifest filename')
    init_parser.add_argument('--prefix', '-p', help='Filename prefix (default: derived from destination)')
    init_parser.add_argument('--flat', action='store_true', help='Do not search subdirectories')
    init_parser.add_argument('--all', '-a', action='store_true', help='Select all files automatically')

    # sync command
    sync_parser = subparsers.add_parser('sync', help='Upload files from manifest to MinIO')
    sync_parser.add_argument('manifest', help='Path to gallery manifest YAML')
    sync_parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be uploaded')

    # list command
    list_parser = subparsers.add_parser('list', help='List manifest contents')
    list_parser.add_argument('manifest', help='Path to gallery manifest YAML')

    # html command
    html_parser = subparsers.add_parser('html', help='Generate nanogallery2 HTML from manifest')
    html_parser.add_argument('manifest', help='Path to gallery manifest YAML')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'init': cmd_init,
        'sync': cmd_sync,
        'list': cmd_list,
        'html': cmd_html,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
