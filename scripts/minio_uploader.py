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
import os
from typing import Optional, TYPE_CHECKING

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
