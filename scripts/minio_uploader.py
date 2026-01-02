#!/usr/bin/env python3
"""
MinIO Uploader for Blog Media Files

This module handles uploading media files to MinIO object storage.
It provides functions for initializing the MinIO client, uploading
individual files, and batch uploading media referenced in blog posts.

Note: The minio package must be installed to use this module.
Install with: pip install minio
"""

import logging
import mimetypes
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

# Configure module logger
logger = logging.getLogger(__name__)


# Environment variable names for MinIO configuration
MINIO_ENDPOINT_VAR = "MINIO_ENDPOINT"
MINIO_ACCESS_KEY_VAR = "MINIO_ACCESS_KEY"
MINIO_SECRET_KEY_VAR = "MINIO_SECRET_KEY"
MINIO_BUCKET_VAR = "MINIO_BUCKET"
MINIO_SECURE_VAR = "MINIO_SECURE"  # Optional: defaults to True


class MinioConfigError(Exception):
    """Raised when MinIO configuration is missing or invalid."""
    pass


def _get_minio_module():
    """Lazily import the minio module to allow testing without it installed."""
    try:
        import minio
        return minio
    except ImportError:
        raise ImportError(
            "The 'minio' package is required for MinIO operations. "
            "Install it with: pip install minio"
        )


def get_minio_client(
    endpoint: Optional[str] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    secure: Optional[bool] = None
):
    """
    Initialize and return a MinIO client.

    If parameters are not provided, reads from environment variables:
    - MINIO_ENDPOINT: The MinIO server endpoint (e.g., 'minio.example.com:9000')
    - MINIO_ACCESS_KEY: The access key for authentication
    - MINIO_SECRET_KEY: The secret key for authentication
    - MINIO_SECURE: Optional, whether to use HTTPS (default: True)

    Args:
        endpoint: MinIO server endpoint (overrides environment variable)
        access_key: Access key (overrides environment variable)
        secret_key: Secret key (overrides environment variable)
        secure: Use HTTPS connection (overrides environment variable)

    Returns:
        Configured Minio client instance

    Raises:
        MinioConfigError: If required configuration is missing
        ImportError: If the minio package is not installed
    """
    # Get configuration from parameters or environment
    endpoint = endpoint or os.environ.get(MINIO_ENDPOINT_VAR)
    access_key = access_key or os.environ.get(MINIO_ACCESS_KEY_VAR)
    secret_key = secret_key or os.environ.get(MINIO_SECRET_KEY_VAR)

    # Handle secure setting
    if secure is None:
        secure_str = os.environ.get(MINIO_SECURE_VAR, "true").lower()
        secure = secure_str in ("true", "1", "yes")

    # Validate required configuration
    missing = []
    if not endpoint:
        missing.append(MINIO_ENDPOINT_VAR)
    if not access_key:
        missing.append(MINIO_ACCESS_KEY_VAR)
    if not secret_key:
        missing.append(MINIO_SECRET_KEY_VAR)

    if missing:
        raise MinioConfigError(
            f"Missing required MinIO configuration: {', '.join(missing)}. "
            "Set these environment variables or pass them as parameters."
        )

    logger.debug(f"Initializing MinIO client for endpoint: {endpoint}")

    minio_module = _get_minio_module()
    return minio_module.Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )


def get_bucket_name() -> str:
    """
    Get the configured MinIO bucket name from environment.

    Returns:
        The bucket name from MINIO_BUCKET environment variable

    Raises:
        MinioConfigError: If MINIO_BUCKET is not set
    """
    bucket = os.environ.get(MINIO_BUCKET_VAR)
    if not bucket:
        raise MinioConfigError(
            f"Missing required MinIO configuration: {MINIO_BUCKET_VAR}. "
            "Set this environment variable."
        )
    return bucket


def ensure_bucket_exists(client, bucket_name: str) -> bool:
    """
    Ensure the target bucket exists, creating it if necessary.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the bucket to check/create

    Returns:
        True if bucket exists or was created, False on error
    """
    minio_module = _get_minio_module()
    try:
        if not client.bucket_exists(bucket_name):
            logger.info(f"Creating bucket: {bucket_name}")
            client.make_bucket(bucket_name)
        return True
    except minio_module.error.S3Error as e:
        logger.error(f"Error ensuring bucket exists: {e}")
        return False


# Default prefix for uploaded assets in MinIO bucket
DEFAULT_ASSET_PREFIX = "assets"


def upload_file(
    client,
    bucket_name: str,
    local_path: str,
    relative_path: str,
    asset_prefix: str = DEFAULT_ASSET_PREFIX
) -> Optional[str]:
    """
    Upload a single file to MinIO, preserving the relative path structure.

    Uploads a local file to MinIO with a path structure that preserves the
    original relative path. For example, a file at `/home/adam/Media/2021/06/image.jpg`
    with relative_path `2021/06/image.jpg` becomes `assets/2021/06/image.jpg`
    in the bucket.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the target bucket
        local_path: Full local path to the file to upload
        relative_path: The relative path to preserve in MinIO
                      (e.g., '2021/06/image.jpg')
        asset_prefix: Prefix for the object path in MinIO (default: 'assets')

    Returns:
        The object name in MinIO (e.g., 'assets/2021/06/image.jpg') on success,
        None on failure

    Raises:
        FileNotFoundError: If the local file does not exist
        ValueError: If local_path or relative_path is empty
    """
    if not local_path:
        raise ValueError("local_path cannot be empty")
    if not relative_path:
        raise ValueError("relative_path cannot be empty")

    local_file = Path(local_path)
    if not local_file.exists():
        raise FileNotFoundError(f"Local file not found: {local_path}")
    if not local_file.is_file():
        raise ValueError(f"Path is not a file: {local_path}")

    # Normalize the relative path - remove leading slashes
    normalized_relative = relative_path.lstrip('/')

    # Build the object name: prefix/relative/path
    if asset_prefix:
        object_name = f"{asset_prefix.strip('/')}/{normalized_relative}"
    else:
        object_name = normalized_relative

    # Detect content type
    content_type, _ = mimetypes.guess_type(local_path)
    if content_type is None:
        content_type = "application/octet-stream"

    minio_module = _get_minio_module()

    try:
        logger.debug(f"Uploading {local_path} to {bucket_name}/{object_name}")

        # Use fput_object for file uploads
        result = client.fput_object(
            bucket_name,
            object_name,
            local_path,
            content_type=content_type
        )

        logger.info(f"Uploaded {object_name} (etag: {result.etag})")
        return object_name

    except minio_module.error.S3Error as e:
        logger.error(f"Failed to upload {local_path}: {e}")
        return None


def check_existing(
    client,
    bucket_name: str,
    object_name: str
) -> bool:
    """
    Check if an object already exists in MinIO.

    Uses the stat_object API to check for existence, which is efficient
    as it only retrieves metadata without downloading the object.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the bucket to check
        object_name: Object path in the bucket (e.g., 'assets/2021/06/image.jpg')

    Returns:
        True if the object exists, False otherwise
    """
    minio_module = _get_minio_module()

    try:
        client.stat_object(bucket_name, object_name)
        logger.debug(f"Object exists: {bucket_name}/{object_name}")
        return True
    except minio_module.error.S3Error as e:
        if e.code == "NoSuchKey":
            logger.debug(f"Object does not exist: {bucket_name}/{object_name}")
            return False
        # Re-raise for other S3 errors (permissions, network issues, etc.)
        logger.error(f"Error checking object existence: {e}")
        raise


def build_minio_url(
    endpoint: str,
    bucket_name: str,
    object_name: str,
    secure: bool = True
) -> str:
    """
    Build the full URL to access an object in MinIO.

    Args:
        endpoint: MinIO server endpoint (e.g., 'minio.example.com:9000')
        bucket_name: Name of the bucket
        object_name: Object path in the bucket (e.g., 'assets/2021/06/image.jpg')
        secure: Whether HTTPS is used (default: True)

    Returns:
        Full URL to access the object (e.g., 'https://minio.example.com:9000/bucket/assets/2021/06/image.jpg')
    """
    protocol = "https" if secure else "http"
    return f"{protocol}://{endpoint}/{bucket_name}/{object_name}"


def upload_media_batch(
    client,
    bucket_name: str,
    media_items: List[Tuple[str, str]],
    endpoint: Optional[str] = None,
    secure: Optional[bool] = None,
    asset_prefix: str = DEFAULT_ASSET_PREFIX,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, Optional[str]]:
    """
    Upload a batch of media files to MinIO and return URL mappings.

    Takes a list of (obsidian_reference, resolved_local_path) tuples, uploads
    each file to MinIO, and returns a mapping from the original Obsidian
    references to their final MinIO URLs.

    Args:
        client: Initialized Minio client
        bucket_name: Name of the target bucket
        media_items: List of tuples where each tuple contains:
                    - obsidian_reference: The original media reference from ![[...]] syntax
                      (e.g., '2021/06/image.jpg')
                    - resolved_local_path: The full local path to the file
                      (e.g., '/home/adam/Media/2021/06/image.jpg')
        endpoint: MinIO endpoint for URL construction (reads from MINIO_ENDPOINT if not provided)
        secure: Whether HTTPS is used for URLs (reads from MINIO_SECURE if not provided)
        asset_prefix: Prefix for the object path in MinIO (default: 'assets')
        progress_callback: Optional callback function called after each file upload.
                          Receives (filename, current_index, total_count) arguments.
                          Useful for progress bar updates.

    Returns:
        Dictionary mapping Obsidian references to their final MinIO URLs.
        If a file fails to upload, the value will be None for that reference.

    Example:
        >>> media_items = [
        ...     ('2021/06/photo.jpg', '/home/adam/Media/2021/06/photo.jpg'),
        ...     ('videos/demo.mp4', '/home/adam/Media/videos/demo.mp4'),
        ... ]
        >>> url_mapping = upload_media_batch(client, 'my-bucket', media_items)
        >>> url_mapping
        {
            '2021/06/photo.jpg': 'https://minio.example.com/my-bucket/assets/2021/06/photo.jpg',
            'videos/demo.mp4': 'https://minio.example.com/my-bucket/assets/videos/demo.mp4'
        }
    """
    # Get endpoint from environment if not provided
    if endpoint is None:
        endpoint = os.environ.get(MINIO_ENDPOINT_VAR)
        if not endpoint:
            raise MinioConfigError(
                f"Missing MinIO endpoint: provide 'endpoint' parameter or set {MINIO_ENDPOINT_VAR}"
            )

    # Get secure setting from environment if not provided
    if secure is None:
        secure_str = os.environ.get(MINIO_SECURE_VAR, "true").lower()
        secure = secure_str in ("true", "1", "yes")

    url_mapping: Dict[str, Optional[str]] = {}
    total_items = len(media_items)

    for index, (obsidian_ref, local_path) in enumerate(media_items):
        # Use the obsidian reference as the relative path (it already contains the path structure)
        object_name = upload_file(
            client,
            bucket_name,
            local_path,
            obsidian_ref,
            asset_prefix=asset_prefix
        )

        if object_name:
            # Build the full URL for this object
            url = build_minio_url(endpoint, bucket_name, object_name, secure)
            url_mapping[obsidian_ref] = url
            logger.info(f"Uploaded {obsidian_ref} -> {url}")
        else:
            url_mapping[obsidian_ref] = None
            logger.warning(f"Failed to upload {obsidian_ref}")

        # Call progress callback if provided
        if progress_callback:
            progress_callback(obsidian_ref, index + 1, total_items)

    # Log summary
    successful = sum(1 for v in url_mapping.values() if v is not None)
    failed = len(url_mapping) - successful
    logger.info(f"Batch upload complete: {successful} successful, {failed} failed")

    return url_mapping
