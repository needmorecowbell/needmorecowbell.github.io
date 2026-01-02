#!/usr/bin/env python3
"""
Media Reference Extractor for Obsidian Notes

This module handles extracting and resolving media references from Obsidian
markdown content. It parses the ![[...]] embedding syntax to find all
referenced media files (images, videos, audio). Also provides thumbnail
generation for gallery images using Pillow.
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

# Configure module logger
logger = logging.getLogger(__name__)


# Supported image extensions
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'tif', 'ico'}

# Supported video extensions
VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'ogv', 'mov', 'avi', 'mkv', 'm4v'}

# Supported audio extensions
AUDIO_EXTENSIONS = {'mp3', 'wav', 'oga', 'm4a', 'flac', 'aac', 'wma'}

# All supported media extensions
ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS


def find_media_references(content: str) -> List[str]:
    """
    Parse Obsidian markdown content and extract all embedded media paths.

    Finds all occurrences of the ![[path/to/file.ext]] syntax and returns
    the media paths. Only includes files with recognized media extensions
    (images, videos, audio).

    Args:
        content: The markdown content to parse

    Returns:
        List of media file paths as they appear in the embed syntax
        (e.g., ['2021/06/image.jpg', 'videos/demo.mp4'])
    """
    # Build pattern that matches any media extension
    extensions_pattern = '|'.join(sorted(ALL_MEDIA_EXTENSIONS))

    # Pattern for embedded media: ![[path/to/file.ext]]
    # Captures the full path including filename
    # Allows optional whitespace before/after the path
    embed_pattern = re.compile(
        rf'!\[\[\s*([^\]\s][^\]]*\.({extensions_pattern}))\s*\]\]',
        re.IGNORECASE
    )

    references = []
    for match in embed_pattern.finditer(content):
        media_path = match.group(1).strip()
        references.append(media_path)

    return references


# Default media base path (symlinked from ~/Notes/Media -> ~/Media)
DEFAULT_MEDIA_BASE = Path.home() / "Notes" / "Media"


def resolve_media_path(
    media_reference: str,
    media_base: Optional[Path] = None,
    validate: bool = True
) -> Optional[str]:
    """
    Resolve an Obsidian media reference to an actual file path.

    Takes a media reference from ![[...]] syntax and resolves it to the full
    file path via the Media folder symlink. By default, validates that the
    resolved file exists.

    Args:
        media_reference: The media path as it appears in Obsidian embed syntax
                        (e.g., '2021/06/image.jpg')
        media_base: Base path for media files. Defaults to ~/Notes/Media
                   which is typically symlinked to ~/Media
        validate: If True, checks if the file exists and logs a warning if not.
                 If False, returns the path without validation.

    Returns:
        The full absolute path to the media file (e.g., '/home/adam/Media/2021/06/image.jpg'),
        or None if validate=True and the file doesn't exist.
    """
    if media_base is None:
        media_base = DEFAULT_MEDIA_BASE

    # Normalize the reference - remove any leading slashes
    normalized_ref = media_reference.lstrip('/')

    # Resolve the full path
    # First resolve the media_base to follow any symlinks, then join with the reference
    resolved_base = media_base.resolve()
    full_path = resolved_base / normalized_ref

    # Convert to absolute path string
    full_path_str = str(full_path.resolve())

    if validate:
        if not full_path.exists():
            logger.warning(f"Media file not found: {full_path_str} (reference: {media_reference})")
            return None
        if not full_path.is_file():
            logger.warning(f"Media path is not a file: {full_path_str} (reference: {media_reference})")
            return None

    return full_path_str


# Default thumbnail width in pixels
DEFAULT_THUMBNAIL_WIDTH = 400

# Extensions that support thumbnailing (raster images only, not SVG)
THUMBNAIL_SUPPORTED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'tif'}


def generate_thumbnail(
    source_path: str,
    output_path: Optional[str] = None,
    width: int = DEFAULT_THUMBNAIL_WIDTH,
    quality: int = 85,
) -> Optional[str]:
    """
    Generate a thumbnail version of an image file.

    Creates a width-constrained thumbnail while maintaining aspect ratio.
    The height is automatically calculated to preserve the original proportions.

    Args:
        source_path: Path to the source image file
        output_path: Path for the output thumbnail. If not provided, the thumbnail
                     will be saved in the same directory with '_thumb' suffix
                     (e.g., 'image.jpg' -> 'image_thumb.jpg')
        width: Target width in pixels for the thumbnail. Default is 400px.
               Height is calculated automatically to maintain aspect ratio.
        quality: JPEG/WebP quality setting (1-100). Default is 85.
                 Only applies to lossy formats.

    Returns:
        The path to the generated thumbnail file, or None if generation failed.
        Returns None if:
        - The source file doesn't exist
        - The source file is not a supported image format
        - The image is already smaller than the target width (no thumbnail needed)
        - Any error occurs during processing

    Raises:
        No exceptions are raised; errors are logged and None is returned.
    """
    source = Path(source_path)

    # Validate source file exists
    if not source.exists():
        logger.warning(f"Source file does not exist: {source_path}")
        return None

    if not source.is_file():
        logger.warning(f"Source path is not a file: {source_path}")
        return None

    # Check if extension is supported for thumbnailing
    ext = source.suffix.lower().lstrip('.')
    if ext not in THUMBNAIL_SUPPORTED_EXTENSIONS:
        logger.warning(f"Unsupported image format for thumbnailing: {ext} (file: {source_path})")
        return None

    # Determine output path
    if output_path is None:
        # Generate default output path with _thumb suffix
        stem = source.stem
        suffix = source.suffix
        output_path = str(source.parent / f"{stem}_thumb{suffix}")

    output = Path(output_path)

    try:
        # Open and process the image
        with Image.open(source) as img:
            original_width, original_height = img.size

            # Skip if image is already smaller than target width
            if original_width <= width:
                logger.info(
                    f"Image already smaller than target width ({original_width}px <= {width}px), "
                    f"skipping thumbnail generation: {source_path}"
                )
                return None

            # Calculate new height maintaining aspect ratio
            aspect_ratio = original_height / original_width
            new_height = int(width * aspect_ratio)

            # Use LANCZOS for high-quality downsampling
            resized = img.resize((width, new_height), Image.Resampling.LANCZOS)

            # Determine output format from output path extension
            output_ext = output.suffix.lower().lstrip('.')

            # Handle different image modes for saving
            # Convert RGBA to RGB for JPEG (which doesn't support transparency)
            save_kwargs = {}
            if output_ext in ('jpg', 'jpeg'):
                if resized.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB, using white background for transparency
                    background = Image.new('RGB', resized.size, (255, 255, 255))
                    if resized.mode == 'P':
                        resized = resized.convert('RGBA')
                    if resized.mode in ('RGBA', 'LA'):
                        background.paste(resized, mask=resized.split()[-1])  # Use alpha channel as mask
                        resized = background
                    else:
                        resized = resized.convert('RGB')
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_ext == 'webp':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_ext == 'png':
                save_kwargs['optimize'] = True
            elif output_ext == 'gif':
                # For GIFs, just save the first frame as thumbnail
                pass

            # Ensure output directory exists
            output.parent.mkdir(parents=True, exist_ok=True)

            # Save the thumbnail
            resized.save(output, **save_kwargs)

            logger.info(
                f"Generated thumbnail: {output_path} "
                f"({original_width}x{original_height} -> {width}x{new_height})"
            )

            return str(output)

    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {source_path}: {e}")
        return None


def get_thumbnail_path(
    original_path: str,
    thumbnail_suffix: str = "_thumb"
) -> str:
    """
    Generate the expected thumbnail path for a given original image path.

    This is a utility function to determine where a thumbnail would be saved
    without actually generating it.

    Args:
        original_path: Path to the original image file
        thumbnail_suffix: Suffix to add before the file extension. Default is "_thumb"

    Returns:
        The expected thumbnail path (e.g., 'image.jpg' -> 'image_thumb.jpg')
    """
    path = Path(original_path)
    return str(path.parent / f"{path.stem}{thumbnail_suffix}{path.suffix}")
