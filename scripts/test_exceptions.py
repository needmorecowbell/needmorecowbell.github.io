#!/usr/bin/env python3
"""
Tests for custom exception classes in the publishing pipeline.
"""

import pytest
from pathlib import Path

from exceptions import (
    PublishError,
    ValidationError,
    MediaNotFoundError,
    UploadError,
)


class TestPublishError:
    """Tests for the base PublishError exception."""

    def test_basic_message(self):
        """Test creating a PublishError with just a message."""
        error = PublishError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.context == {}

    def test_with_context(self):
        """Test creating a PublishError with context dict."""
        error = PublishError("Failed to process", context={"path": "/some/path", "code": 42})
        assert str(error) == "Failed to process"
        assert error.context == {"path": "/some/path", "code": 42}

    def test_repr_without_context(self):
        """Test repr format without context."""
        error = PublishError("Test error")
        assert repr(error) == "PublishError('Test error')"

    def test_repr_with_context(self):
        """Test repr format with context."""
        error = PublishError("Test error", context={"key": "value"})
        assert repr(error) == "PublishError('Test error', context={'key': 'value'})"

    def test_is_exception(self):
        """Test that PublishError is a proper Exception."""
        error = PublishError("Test")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Test that PublishError can be raised and caught."""
        with pytest.raises(PublishError) as exc_info:
            raise PublishError("Test error")
        assert str(exc_info.value) == "Test error"

    def test_catch_as_exception(self):
        """Test that PublishError can be caught as generic Exception."""
        with pytest.raises(Exception):
            raise PublishError("Test error")


class TestValidationError:
    """Tests for the ValidationError exception."""

    def test_basic_message(self):
        """Test creating a ValidationError with just a message."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.field is None
        assert error.issues == []

    def test_with_field(self):
        """Test creating a ValidationError with a field name."""
        error = ValidationError("is required", field="title")
        assert str(error) == "title: is required"
        assert error.field == "title"
        assert error.context.get("field") == "title"

    def test_with_issues(self):
        """Test creating a ValidationError with a list of issues."""
        issues = ["must be a string", "cannot be empty"]
        error = ValidationError("Multiple issues found", issues=issues)
        assert error.issues == issues
        assert error.context.get("issues") == issues

    def test_with_field_and_issues(self):
        """Test creating a ValidationError with both field and issues."""
        issues = ["must be YYYY-MM-DD format"]
        error = ValidationError("Invalid format", field="date", issues=issues)
        assert str(error) == "date: Invalid format"
        assert error.field == "date"
        assert error.issues == issues

    def test_inherits_from_publish_error(self):
        """Test that ValidationError inherits from PublishError."""
        error = ValidationError("Test")
        assert isinstance(error, PublishError)

    def test_can_catch_as_publish_error(self):
        """Test that ValidationError can be caught as PublishError."""
        with pytest.raises(PublishError):
            raise ValidationError("Invalid field")

    def test_additional_context(self):
        """Test that additional context is preserved."""
        error = ValidationError(
            "Validation failed",
            field="tags",
            context={"note_path": "/path/to/note.md"}
        )
        assert error.context.get("field") == "tags"
        assert error.context.get("note_path") == "/path/to/note.md"


class TestMediaNotFoundError:
    """Tests for the MediaNotFoundError exception."""

    def test_basic_message(self):
        """Test creating a MediaNotFoundError with just a message."""
        error = MediaNotFoundError("Media file not found")
        assert "Media file not found" in str(error)
        assert error.media_reference is None
        assert error.expected_path is None
        assert error.note_path is None

    def test_with_media_reference(self):
        """Test creating a MediaNotFoundError with media reference."""
        error = MediaNotFoundError("Not found", media_reference="2021/06/photo.jpg")
        assert "2021/06/photo.jpg" in str(error)
        assert error.media_reference == "2021/06/photo.jpg"
        assert error.context.get("media_reference") == "2021/06/photo.jpg"

    def test_with_expected_path(self):
        """Test creating a MediaNotFoundError with expected path."""
        expected = Path("/home/user/Media/2021/06/photo.jpg")
        error = MediaNotFoundError("Not found", expected_path=expected)
        assert str(expected) in str(error)
        assert error.expected_path == expected
        assert error.context.get("expected_path") == str(expected)

    def test_with_note_path(self):
        """Test creating a MediaNotFoundError with note path."""
        note = Path("/home/user/Notes/my-post.md")
        error = MediaNotFoundError("Not found", note_path=note)
        assert error.note_path == note
        assert error.context.get("note_path") == str(note)

    def test_full_error_message(self):
        """Test the full formatted error message."""
        error = MediaNotFoundError(
            "Media file not found",
            media_reference="2021/06/photo.jpg",
            expected_path=Path("/home/user/Media/2021/06/photo.jpg")
        )
        error_str = str(error)
        assert "Media file not found" in error_str
        assert "2021/06/photo.jpg" in error_str
        assert "/home/user/Media/2021/06/photo.jpg" in error_str

    def test_inherits_from_publish_error(self):
        """Test that MediaNotFoundError inherits from PublishError."""
        error = MediaNotFoundError("Test")
        assert isinstance(error, PublishError)

    def test_can_catch_as_publish_error(self):
        """Test that MediaNotFoundError can be caught as PublishError."""
        with pytest.raises(PublishError):
            raise MediaNotFoundError("Missing file")

    def test_additional_context(self):
        """Test that additional context is preserved."""
        error = MediaNotFoundError(
            "Not found",
            media_reference="photo.jpg",
            context={"line_number": 42}
        )
        assert error.context.get("media_reference") == "photo.jpg"
        assert error.context.get("line_number") == 42


class TestUploadError:
    """Tests for the UploadError exception."""

    def test_basic_message(self):
        """Test creating an UploadError with just a message."""
        error = UploadError("Upload failed")
        assert "Upload failed" in str(error)
        assert error.file_path is None
        assert error.bucket is None
        assert error.object_name is None
        assert error.original_error is None

    def test_with_file_path(self):
        """Test creating an UploadError with file path."""
        path = Path("/home/user/Media/photo.jpg")
        error = UploadError("Failed", file_path=path)
        assert str(path) in str(error)
        assert error.file_path == path
        assert error.context.get("file_path") == str(path)

    def test_with_bucket_and_object_name(self):
        """Test creating an UploadError with bucket and object name."""
        error = UploadError("Failed", bucket="my-bucket", object_name="assets/photo.jpg")
        error_str = str(error)
        assert "my-bucket" in error_str or "assets/photo.jpg" in error_str
        assert error.bucket == "my-bucket"
        assert error.object_name == "assets/photo.jpg"

    def test_with_original_error(self):
        """Test creating an UploadError with original exception."""
        original = ValueError("Connection refused")
        error = UploadError("Upload failed", original_error=original)
        assert "Connection refused" in str(error)
        assert error.original_error == original
        assert "Connection refused" in error.context.get("original_error", "")

    def test_full_error_message(self):
        """Test the full formatted error message."""
        original = IOError("Network error")
        error = UploadError(
            "Failed to upload",
            file_path=Path("/tmp/photo.jpg"),
            bucket="blog-assets",
            object_name="assets/2021/photo.jpg",
            original_error=original
        )
        error_str = str(error)
        assert "Failed to upload" in error_str
        assert "/tmp/photo.jpg" in error_str
        assert "blog-assets" in error_str
        assert "assets/2021/photo.jpg" in error_str
        assert "Network error" in error_str

    def test_inherits_from_publish_error(self):
        """Test that UploadError inherits from PublishError."""
        error = UploadError("Test")
        assert isinstance(error, PublishError)

    def test_can_catch_as_publish_error(self):
        """Test that UploadError can be caught as PublishError."""
        with pytest.raises(PublishError):
            raise UploadError("Upload failed")

    def test_additional_context(self):
        """Test that additional context is preserved."""
        error = UploadError(
            "Upload failed",
            bucket="my-bucket",
            context={"retry_count": 3}
        )
        assert error.context.get("bucket") == "my-bucket"
        assert error.context.get("retry_count") == 3

    def test_exception_chaining(self):
        """Test that original_error enables exception chaining."""
        try:
            try:
                raise ValueError("Root cause")
            except ValueError as e:
                raise UploadError("Upload failed", original_error=e)
        except UploadError as upload_error:
            assert upload_error.original_error is not None
            assert isinstance(upload_error.original_error, ValueError)
            assert str(upload_error.original_error) == "Root cause"


class TestExceptionHierarchy:
    """Tests for the exception hierarchy and polymorphism."""

    def test_catch_all_with_publish_error(self):
        """Test catching all custom exceptions with PublishError."""
        exceptions = [
            ValidationError("Validation failed"),
            MediaNotFoundError("Media not found"),
            UploadError("Upload failed"),
        ]

        for exc in exceptions:
            with pytest.raises(PublishError):
                raise exc

    def test_specific_handling(self):
        """Test handling specific exception types differently."""
        def process_error(error):
            if isinstance(error, ValidationError):
                return "validation"
            elif isinstance(error, MediaNotFoundError):
                return "media"
            elif isinstance(error, UploadError):
                return "upload"
            elif isinstance(error, PublishError):
                return "publish"
            return "unknown"

        assert process_error(ValidationError("test")) == "validation"
        assert process_error(MediaNotFoundError("test")) == "media"
        assert process_error(UploadError("test")) == "upload"
        assert process_error(PublishError("test")) == "publish"

    def test_all_have_message_and_context(self):
        """Test that all exception types have message and context attributes."""
        exceptions = [
            PublishError("msg1", context={"a": 1}),
            ValidationError("msg2", field="f"),
            MediaNotFoundError("msg3", media_reference="ref"),
            UploadError("msg4", bucket="b"),
        ]

        for exc in exceptions:
            assert hasattr(exc, 'message')
            assert hasattr(exc, 'context')
            assert isinstance(exc.context, dict)
