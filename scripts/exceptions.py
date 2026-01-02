#!/usr/bin/env python3
"""
Custom Exception Classes for Obsidian-to-Hugo Publishing Pipeline

This module provides a hierarchy of custom exceptions for better error handling
throughout the publishing pipeline. These exceptions provide more specific
information about what went wrong and can include context to help users
understand and fix issues.

Exception Hierarchy:
    PublishError (base class)
    ├── ValidationError
    │   └── (for frontmatter, content, and link validation failures)
    ├── MediaNotFoundError
    │   └── (for missing media files referenced in notes)
    └── UploadError
        └── (for MinIO/S3 upload failures)
"""

from pathlib import Path
from typing import List, Optional, Any


class PublishError(Exception):
    """
    Base exception for all publishing pipeline errors.

    All custom exceptions in this module inherit from PublishError,
    making it easy to catch any publishing-related error with a single
    except clause while still allowing specific error handling.

    Attributes:
        message: Human-readable error description
        context: Optional dict with additional context about the error

    Example:
        try:
            publish_note(note_path)
        except PublishError as e:
            print(f"Publishing failed: {e}")
    """

    def __init__(self, message: str, context: Optional[dict] = None):
        """
        Initialize a PublishError.

        Args:
            message: Human-readable description of the error
            context: Optional dict with additional context (paths, field names, etc.)
        """
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    def __repr__(self) -> str:
        """Return a detailed representation of the error."""
        if self.context:
            return f"{self.__class__.__name__}({self.message!r}, context={self.context!r})"
        return f"{self.__class__.__name__}({self.message!r})"


class ValidationError(PublishError):
    """
    Exception raised when note validation fails.

    This exception is used when frontmatter is invalid, required fields
    are missing, or content validation (like internal link checks) fails.

    Attributes:
        message: Human-readable error description
        field: The specific field that failed validation (optional)
        issues: List of validation issues found (optional)
        context: Optional dict with additional context

    Example:
        if not frontmatter.get('title'):
            raise ValidationError(
                "Missing required field",
                field="title",
                issues=["title is required for Hugo posts"]
            )
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        issues: Optional[List[str]] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize a ValidationError.

        Args:
            message: Human-readable description of the validation failure
            field: The specific frontmatter/content field that failed (optional)
            issues: List of specific validation issues found (optional)
            context: Optional dict with additional context
        """
        self.field = field
        self.issues = issues or []

        # Build context dict including field and issues
        full_context = context or {}
        if field:
            full_context['field'] = field
        if issues:
            full_context['issues'] = issues

        super().__init__(message, full_context)

    def __str__(self) -> str:
        """Return a formatted error message including field if available."""
        if self.field:
            return f"{self.field}: {self.message}"
        return self.message


class MediaNotFoundError(PublishError):
    """
    Exception raised when a referenced media file cannot be found.

    This exception is used when an Obsidian embed (![[media.jpg]]) references
    a file that doesn't exist in the expected location. It provides helpful
    information about what was expected and where.

    Attributes:
        message: Human-readable error description
        media_reference: The original media reference from the note (e.g., '2021/06/photo.jpg')
        expected_path: The resolved path where the file was expected
        note_path: Path to the note containing the reference (optional)
        context: Optional dict with additional context

    Example:
        raise MediaNotFoundError(
            "Media file not found",
            media_reference="2021/06/photo.jpg",
            expected_path=Path("/home/user/Media/2021/06/photo.jpg"),
            note_path=Path("/home/user/Notes/my-post.md")
        )
    """

    def __init__(
        self,
        message: str,
        media_reference: Optional[str] = None,
        expected_path: Optional[Path] = None,
        note_path: Optional[Path] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize a MediaNotFoundError.

        Args:
            message: Human-readable description of the error
            media_reference: The original reference from ![[...]] syntax
            expected_path: Where the file was expected to be found
            note_path: The note containing the broken reference
            context: Optional dict with additional context
        """
        self.media_reference = media_reference
        self.expected_path = expected_path
        self.note_path = note_path

        # Build context dict
        full_context = context or {}
        if media_reference:
            full_context['media_reference'] = media_reference
        if expected_path:
            full_context['expected_path'] = str(expected_path)
        if note_path:
            full_context['note_path'] = str(note_path)

        super().__init__(message, full_context)

    def __str__(self) -> str:
        """Return a formatted error message with reference details."""
        parts = [self.message]
        if self.media_reference:
            parts.append(f"Reference: {self.media_reference}")
        if self.expected_path:
            parts.append(f"Expected at: {self.expected_path}")
        return " | ".join(parts)


class UploadError(PublishError):
    """
    Exception raised when media upload to MinIO/S3 fails.

    This exception is used when uploading media files to object storage
    fails, whether due to connection issues, authentication problems,
    or storage errors.

    Attributes:
        message: Human-readable error description
        file_path: Path to the local file that failed to upload (optional)
        bucket: Target bucket name (optional)
        object_name: Target object name in the bucket (optional)
        original_error: The underlying exception that caused the failure (optional)
        context: Optional dict with additional context

    Example:
        try:
            client.fput_object(bucket, object_name, local_path)
        except S3Error as e:
            raise UploadError(
                "Failed to upload media file",
                file_path=Path(local_path),
                bucket=bucket,
                object_name=object_name,
                original_error=e
            )
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        bucket: Optional[str] = None,
        object_name: Optional[str] = None,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize an UploadError.

        Args:
            message: Human-readable description of the upload failure
            file_path: Local path of the file that failed to upload
            bucket: Target bucket name
            object_name: Target object path in the bucket
            original_error: The underlying exception (for chaining)
            context: Optional dict with additional context
        """
        self.file_path = file_path
        self.bucket = bucket
        self.object_name = object_name
        self.original_error = original_error

        # Build context dict
        full_context = context or {}
        if file_path:
            full_context['file_path'] = str(file_path)
        if bucket:
            full_context['bucket'] = bucket
        if object_name:
            full_context['object_name'] = object_name
        if original_error:
            full_context['original_error'] = str(original_error)

        super().__init__(message, full_context)

    def __str__(self) -> str:
        """Return a formatted error message with upload details."""
        parts = [self.message]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.bucket and self.object_name:
            parts.append(f"Target: {self.bucket}/{self.object_name}")
        if self.original_error:
            parts.append(f"Cause: {self.original_error}")
        return " | ".join(parts)
