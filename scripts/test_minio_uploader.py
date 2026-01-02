#!/usr/bin/env python3
"""
Tests for the MinIO uploader module.

Run with: python test_minio_uploader.py
Or with pytest: pytest test_minio_uploader.py -v
"""

import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import tempfile

from minio_uploader import (
    get_minio_client,
    get_bucket_name,
    ensure_bucket_exists,
    upload_file,
    check_existing,
    build_minio_url,
    upload_media_batch,
    MinioConfigError,
    MINIO_ENDPOINT_VAR,
    MINIO_ACCESS_KEY_VAR,
    MINIO_SECRET_KEY_VAR,
    MINIO_BUCKET_VAR,
    MINIO_SECURE_VAR,
    DEFAULT_ASSET_PREFIX,
    _get_minio_module,
)


class TestGetMinioClient(unittest.TestCase):
    """Tests for get_minio_client() function."""

    def test_with_all_parameters(self):
        """Returns Minio client when all parameters provided."""
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            client = get_minio_client(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                secure=False
            )
            mock_minio.Minio.assert_called_once_with(
                "localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                secure=False
            )
            self.assertIsNotNone(client)

    def test_with_environment_variables(self):
        """Reads configuration from environment variables."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "minio.example.com:9000",
            MINIO_ACCESS_KEY_VAR: "envkey",
            MINIO_SECRET_KEY_VAR: "envsecret",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                client = get_minio_client()
                mock_minio.Minio.assert_called_once_with(
                    "minio.example.com:9000",
                    access_key="envkey",
                    secret_key="envsecret",
                    secure=True  # Default
                )
                self.assertIsNotNone(client)

    def test_parameters_override_environment(self):
        """Parameters take precedence over environment variables."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "env-endpoint:9000",
            MINIO_ACCESS_KEY_VAR: "envkey",
            MINIO_SECRET_KEY_VAR: "envsecret",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                client = get_minio_client(
                    endpoint="param-endpoint:9000",
                    access_key="paramkey"
                )
                mock_minio.Minio.assert_called_once_with(
                    "param-endpoint:9000",
                    access_key="paramkey",
                    secret_key="envsecret",  # From env
                    secure=True
                )
                self.assertIsNotNone(client)

    def test_missing_endpoint_raises_error(self):
        """Raises MinioConfigError when endpoint is missing."""
        env_vars = {
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
        }
        # Clear MINIO_ENDPOINT_VAR if it exists
        clean_env = {k: v for k, v in os.environ.items() if k != MINIO_ENDPOINT_VAR}
        with patch.dict(os.environ, {**clean_env, **env_vars}, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                get_minio_client()
            self.assertIn(MINIO_ENDPOINT_VAR, str(ctx.exception))

    def test_missing_access_key_raises_error(self):
        """Raises MinioConfigError when access key is missing."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_SECRET_KEY_VAR: "secret",
        }
        clean_env = {k: v for k, v in os.environ.items() if k != MINIO_ACCESS_KEY_VAR}
        with patch.dict(os.environ, {**clean_env, **env_vars}, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                get_minio_client()
            self.assertIn(MINIO_ACCESS_KEY_VAR, str(ctx.exception))

    def test_missing_secret_key_raises_error(self):
        """Raises MinioConfigError when secret key is missing."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
        }
        clean_env = {k: v for k, v in os.environ.items() if k != MINIO_SECRET_KEY_VAR}
        with patch.dict(os.environ, {**clean_env, **env_vars}, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                get_minio_client()
            self.assertIn(MINIO_SECRET_KEY_VAR, str(ctx.exception))

    def test_missing_multiple_vars_lists_all(self):
        """Error message lists all missing configuration."""
        # Clear all minio env vars
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in [MINIO_ENDPOINT_VAR, MINIO_ACCESS_KEY_VAR, MINIO_SECRET_KEY_VAR]}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                get_minio_client()
            error_msg = str(ctx.exception)
            self.assertIn(MINIO_ENDPOINT_VAR, error_msg)
            self.assertIn(MINIO_ACCESS_KEY_VAR, error_msg)
            self.assertIn(MINIO_SECRET_KEY_VAR, error_msg)

    def test_secure_defaults_to_true(self):
        """HTTPS is enabled by default."""
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            get_minio_client(
                endpoint="localhost:9000",
                access_key="key",
                secret_key="secret"
            )
            _, kwargs = mock_minio.Minio.call_args
            self.assertTrue(kwargs['secure'])

    def test_secure_from_environment_true(self):
        """MINIO_SECURE=true enables HTTPS."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
            MINIO_SECURE_VAR: "true",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                get_minio_client()
                _, kwargs = mock_minio.Minio.call_args
                self.assertTrue(kwargs['secure'])

    def test_secure_from_environment_false(self):
        """MINIO_SECURE=false disables HTTPS."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
            MINIO_SECURE_VAR: "false",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                get_minio_client()
                _, kwargs = mock_minio.Minio.call_args
                self.assertFalse(kwargs['secure'])

    def test_secure_accepts_yes_value(self):
        """MINIO_SECURE accepts 'yes' value."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
            MINIO_SECURE_VAR: "yes",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                get_minio_client()
                _, kwargs = mock_minio.Minio.call_args
                self.assertTrue(kwargs['secure'])

    def test_secure_accepts_1_value(self):
        """MINIO_SECURE accepts '1' value."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
            MINIO_SECURE_VAR: "1",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                get_minio_client()
                _, kwargs = mock_minio.Minio.call_args
                self.assertTrue(kwargs['secure'])

    def test_secure_parameter_overrides_env(self):
        """secure parameter overrides MINIO_SECURE environment variable."""
        env_vars = {
            MINIO_ENDPOINT_VAR: "localhost:9000",
            MINIO_ACCESS_KEY_VAR: "key",
            MINIO_SECRET_KEY_VAR: "secret",
            MINIO_SECURE_VAR: "true",
        }
        mock_minio = MagicMock()
        mock_minio.Minio.return_value = MagicMock()

        with patch.dict(os.environ, env_vars, clear=False):
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                get_minio_client(secure=False)
                _, kwargs = mock_minio.Minio.call_args
                self.assertFalse(kwargs['secure'])


class TestGetBucketName(unittest.TestCase):
    """Tests for get_bucket_name() function."""

    def test_returns_bucket_from_environment(self):
        """Returns bucket name from environment variable."""
        with patch.dict(os.environ, {MINIO_BUCKET_VAR: "my-bucket"}):
            self.assertEqual(get_bucket_name(), "my-bucket")

    def test_missing_bucket_raises_error(self):
        """Raises MinioConfigError when bucket name is missing."""
        clean_env = {k: v for k, v in os.environ.items() if k != MINIO_BUCKET_VAR}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                get_bucket_name()
            self.assertIn(MINIO_BUCKET_VAR, str(ctx.exception))


class TestEnsureBucketExists(unittest.TestCase):
    """Tests for ensure_bucket_exists() function."""

    def test_returns_true_when_bucket_exists(self):
        """Returns True when bucket already exists."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = ensure_bucket_exists(mock_client, "existing-bucket")

        self.assertTrue(result)
        mock_client.bucket_exists.assert_called_once_with("existing-bucket")
        mock_client.make_bucket.assert_not_called()

    def test_creates_bucket_when_missing(self):
        """Creates bucket when it doesn't exist."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_minio = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = ensure_bucket_exists(mock_client, "new-bucket")

        self.assertTrue(result)
        mock_client.bucket_exists.assert_called_once_with("new-bucket")
        mock_client.make_bucket.assert_called_once_with("new-bucket")

    def test_returns_false_on_s3_error(self):
        """Returns False when S3Error occurs."""
        mock_client = MagicMock()

        # Create a mock S3Error class
        mock_s3_error = Exception("Access Denied")
        mock_minio = MagicMock()
        mock_minio.error.S3Error = type(mock_s3_error)

        mock_client.bucket_exists.side_effect = mock_s3_error

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = ensure_bucket_exists(mock_client, "new-bucket")

        self.assertFalse(result)


class TestGetMinioModule(unittest.TestCase):
    """Tests for the lazy minio module loader."""

    def test_raises_import_error_when_minio_not_installed(self):
        """Raises ImportError with helpful message when minio is not installed."""
        # Since minio is not installed, _get_minio_module should raise ImportError
        with self.assertRaises(ImportError) as ctx:
            _get_minio_module()
        self.assertIn("pip install minio", str(ctx.exception))


class TestUploadFile(unittest.TestCase):
    """Tests for upload_file() function."""

    def test_upload_file_success(self):
        """Successfully uploads a file and returns the object name."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "2021/06/image.jpg"
                )

            self.assertEqual(result, "assets/2021/06/image.jpg")
            mock_client.fput_object.assert_called_once()
            call_args = mock_client.fput_object.call_args
            self.assertEqual(call_args[0][0], "my-bucket")
            self.assertEqual(call_args[0][1], "assets/2021/06/image.jpg")
            self.assertEqual(call_args[0][2], temp_path)
            self.assertEqual(call_args[1]['content_type'], "image/jpeg")
        finally:
            os.unlink(temp_path)

    def test_upload_file_with_custom_prefix(self):
        """Uses custom asset prefix when provided."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "2021/06/photo.png",
                    asset_prefix="media"
                )

            self.assertEqual(result, "media/2021/06/photo.png")
        finally:
            os.unlink(temp_path)

    def test_upload_file_with_empty_prefix(self):
        """Uses no prefix when asset_prefix is empty."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "2021/06/animation.gif",
                    asset_prefix=""
                )

            self.assertEqual(result, "2021/06/animation.gif")
        finally:
            os.unlink(temp_path)

    def test_upload_file_strips_leading_slashes(self):
        """Strips leading slashes from relative path."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "/2021/06/image.jpg"
                )

            self.assertEqual(result, "assets/2021/06/image.jpg")
        finally:
            os.unlink(temp_path)

    def test_upload_file_raises_on_empty_local_path(self):
        """Raises ValueError when local_path is empty."""
        mock_client = MagicMock()
        with self.assertRaises(ValueError) as ctx:
            upload_file(mock_client, "bucket", "", "2021/image.jpg")
        self.assertIn("local_path cannot be empty", str(ctx.exception))

    def test_upload_file_raises_on_empty_relative_path(self):
        """Raises ValueError when relative_path is empty."""
        mock_client = MagicMock()
        with self.assertRaises(ValueError) as ctx:
            upload_file(mock_client, "bucket", "/some/path.jpg", "")
        self.assertIn("relative_path cannot be empty", str(ctx.exception))

    def test_upload_file_raises_on_missing_file(self):
        """Raises FileNotFoundError when local file doesn't exist."""
        mock_client = MagicMock()
        with self.assertRaises(FileNotFoundError) as ctx:
            upload_file(
                mock_client,
                "bucket",
                "/nonexistent/path/image.jpg",
                "image.jpg"
            )
        self.assertIn("Local file not found", str(ctx.exception))

    def test_upload_file_raises_on_directory(self):
        """Raises ValueError when local_path is a directory."""
        mock_client = MagicMock()
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError) as ctx:
                upload_file(mock_client, "bucket", temp_dir, "somepath")
            self.assertIn("not a file", str(ctx.exception))

    def test_upload_file_returns_none_on_s3_error(self):
        """Returns None when S3Error occurs during upload."""
        mock_client = MagicMock()
        mock_s3_error = Exception("Access Denied")
        mock_minio = MagicMock()
        mock_minio.error.S3Error = type(mock_s3_error)
        mock_client.fput_object.side_effect = mock_s3_error

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "2021/06/image.jpg"
                )

            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)

    def test_upload_file_detects_content_type(self):
        """Correctly detects content type for various file types."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        test_cases = [
            ('.png', 'image/png'),
            ('.gif', 'image/gif'),
            ('.mp4', 'video/mp4'),
            ('.webm', 'video/webm'),
        ]

        for suffix, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
                f.write(b'fake data')
                temp_path = f.name

            try:
                mock_client.reset_mock()
                with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                    upload_file(mock_client, "bucket", temp_path, f"file{suffix}")

                call_kwargs = mock_client.fput_object.call_args[1]
                self.assertEqual(
                    call_kwargs['content_type'],
                    expected_type,
                    f"Wrong content type for {suffix}"
                )
            finally:
                os.unlink(temp_path)

    def test_upload_file_uses_default_content_type_for_unknown(self):
        """Uses application/octet-stream for unknown file types."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.xyz123', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                upload_file(mock_client, "bucket", temp_path, "file.xyz123")

            call_kwargs = mock_client.fput_object.call_args[1]
            self.assertEqual(call_kwargs['content_type'], "application/octet-stream")
        finally:
            os.unlink(temp_path)

    def test_upload_file_strips_slashes_from_prefix(self):
        """Strips leading and trailing slashes from asset prefix."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name

        try:
            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                result = upload_file(
                    mock_client,
                    "my-bucket",
                    temp_path,
                    "2021/image.jpg",
                    asset_prefix="/custom/prefix/"
                )

            self.assertEqual(result, "custom/prefix/2021/image.jpg")
        finally:
            os.unlink(temp_path)


class TestCheckExisting(unittest.TestCase):
    """Tests for check_existing() function."""

    def test_returns_true_when_object_exists(self):
        """Returns True when object exists in bucket."""
        mock_client = MagicMock()
        mock_stat = MagicMock()
        mock_stat.size = 12345
        mock_stat.etag = "abc123"
        mock_client.stat_object.return_value = mock_stat
        mock_minio = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = check_existing(
                mock_client,
                "my-bucket",
                "assets/2021/06/image.jpg"
            )

        self.assertTrue(result)
        mock_client.stat_object.assert_called_once_with(
            "my-bucket",
            "assets/2021/06/image.jpg"
        )

    def test_returns_false_when_object_does_not_exist(self):
        """Returns False when object does not exist (NoSuchKey error)."""
        mock_client = MagicMock()
        mock_minio = MagicMock()

        # Create a custom exception class that simulates S3Error with code attribute
        class MockS3Error(Exception):
            def __init__(self, code):
                self.code = code
                super().__init__(f"S3Error: {code}")

        mock_minio.error.S3Error = MockS3Error
        mock_client.stat_object.side_effect = MockS3Error("NoSuchKey")

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = check_existing(
                mock_client,
                "my-bucket",
                "assets/nonexistent.jpg"
            )

        self.assertFalse(result)

    def test_raises_on_other_s3_errors(self):
        """Re-raises S3Error for non-NoSuchKey errors (e.g., permissions)."""
        mock_client = MagicMock()
        mock_minio = MagicMock()

        # Create a custom exception class that simulates S3Error with code attribute
        class MockS3Error(Exception):
            def __init__(self, code):
                self.code = code
                super().__init__(f"S3Error: {code}")

        mock_minio.error.S3Error = MockS3Error
        mock_client.stat_object.side_effect = MockS3Error("AccessDenied")

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            with self.assertRaises(MockS3Error):
                check_existing(
                    mock_client,
                    "my-bucket",
                    "assets/forbidden.jpg"
                )

    def test_handles_nested_paths(self):
        """Correctly handles deeply nested object paths."""
        mock_client = MagicMock()
        mock_client.stat_object.return_value = MagicMock()
        mock_minio = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = check_existing(
                mock_client,
                "my-bucket",
                "assets/2021/06/subfolder/deep/image.jpg"
            )

        self.assertTrue(result)
        mock_client.stat_object.assert_called_once_with(
            "my-bucket",
            "assets/2021/06/subfolder/deep/image.jpg"
        )

    def test_handles_root_level_object(self):
        """Correctly handles objects at bucket root level."""
        mock_client = MagicMock()
        mock_client.stat_object.return_value = MagicMock()
        mock_minio = MagicMock()

        with patch('minio_uploader._get_minio_module', return_value=mock_minio):
            result = check_existing(
                mock_client,
                "my-bucket",
                "file.jpg"
            )

        self.assertTrue(result)
        mock_client.stat_object.assert_called_once_with("my-bucket", "file.jpg")


class TestBuildMinioUrl(unittest.TestCase):
    """Tests for build_minio_url() function."""

    def test_builds_https_url_by_default(self):
        """Builds HTTPS URL when secure=True (default)."""
        url = build_minio_url(
            "minio.example.com:9000",
            "my-bucket",
            "assets/2021/06/image.jpg"
        )
        self.assertEqual(
            url,
            "https://minio.example.com:9000/my-bucket/assets/2021/06/image.jpg"
        )

    def test_builds_http_url_when_not_secure(self):
        """Builds HTTP URL when secure=False."""
        url = build_minio_url(
            "localhost:9000",
            "my-bucket",
            "assets/photo.png",
            secure=False
        )
        self.assertEqual(
            url,
            "http://localhost:9000/my-bucket/assets/photo.png"
        )

    def test_handles_endpoint_without_port(self):
        """Handles endpoint without port number."""
        url = build_minio_url(
            "minio.example.com",
            "bucket",
            "file.jpg"
        )
        self.assertEqual(url, "https://minio.example.com/bucket/file.jpg")

    def test_handles_nested_object_path(self):
        """Correctly handles deeply nested object paths."""
        url = build_minio_url(
            "s3.example.com",
            "media",
            "assets/2021/06/subfolder/image.jpg"
        )
        self.assertEqual(
            url,
            "https://s3.example.com/media/assets/2021/06/subfolder/image.jpg"
        )


class TestUploadMediaBatch(unittest.TestCase):
    """Tests for upload_media_batch() function."""

    def test_uploads_multiple_files_successfully(self):
        """Uploads multiple files and returns URL mapping."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        # Create temporary test files
        temp_files = []
        try:
            for i, ext in enumerate(['.jpg', '.png']):
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(b'fake data')
                    temp_files.append(f.name)

            media_items = [
                ('2021/06/photo.jpg', temp_files[0]),
                ('2021/07/image.png', temp_files[1]),
            ]

            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                url_mapping = upload_media_batch(
                    mock_client,
                    "my-bucket",
                    media_items,
                    endpoint="minio.example.com:9000",
                    secure=True
                )

            self.assertEqual(len(url_mapping), 2)
            self.assertEqual(
                url_mapping['2021/06/photo.jpg'],
                "https://minio.example.com:9000/my-bucket/assets/2021/06/photo.jpg"
            )
            self.assertEqual(
                url_mapping['2021/07/image.png'],
                "https://minio.example.com:9000/my-bucket/assets/2021/07/image.png"
            )
        finally:
            for path in temp_files:
                os.unlink(path)

    def test_returns_none_for_failed_uploads(self):
        """Returns None in mapping for files that fail to upload."""
        mock_client = MagicMock()
        mock_s3_error = Exception("Access Denied")
        mock_minio = MagicMock()
        mock_minio.error.S3Error = type(mock_s3_error)
        mock_client.fput_object.side_effect = mock_s3_error

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            media_items = [('2021/06/photo.jpg', temp_path)]

            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                url_mapping = upload_media_batch(
                    mock_client,
                    "my-bucket",
                    media_items,
                    endpoint="minio.example.com:9000"
                )

            self.assertIsNone(url_mapping['2021/06/photo.jpg'])
        finally:
            os.unlink(temp_path)

    def test_reads_endpoint_from_environment(self):
        """Reads endpoint from MINIO_ENDPOINT when not provided."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            media_items = [('photo.jpg', temp_path)]
            env_vars = {MINIO_ENDPOINT_VAR: "env-minio.example.com:9000"}

            with patch.dict(os.environ, env_vars, clear=False):
                with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                    url_mapping = upload_media_batch(
                        mock_client,
                        "my-bucket",
                        media_items
                    )

            self.assertEqual(
                url_mapping['photo.jpg'],
                "https://env-minio.example.com:9000/my-bucket/assets/photo.jpg"
            )
        finally:
            os.unlink(temp_path)

    def test_raises_error_when_endpoint_missing(self):
        """Raises MinioConfigError when endpoint not provided and not in env."""
        mock_client = MagicMock()
        media_items = [('photo.jpg', '/some/path.jpg')]

        clean_env = {k: v for k, v in os.environ.items() if k != MINIO_ENDPOINT_VAR}
        with patch.dict(os.environ, clean_env, clear=True):
            with self.assertRaises(MinioConfigError) as ctx:
                upload_media_batch(mock_client, "bucket", media_items)
            self.assertIn(MINIO_ENDPOINT_VAR, str(ctx.exception))

    def test_reads_secure_from_environment(self):
        """Reads secure setting from MINIO_SECURE when not provided."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            media_items = [('photo.jpg', temp_path)]
            env_vars = {
                MINIO_ENDPOINT_VAR: "minio.example.com",
                MINIO_SECURE_VAR: "false"
            }

            with patch.dict(os.environ, env_vars, clear=False):
                with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                    url_mapping = upload_media_batch(
                        mock_client,
                        "my-bucket",
                        media_items
                    )

            # Should use http:// since MINIO_SECURE=false
            self.assertTrue(url_mapping['photo.jpg'].startswith("http://"))
        finally:
            os.unlink(temp_path)

    def test_uses_custom_asset_prefix(self):
        """Uses custom asset prefix when provided."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            media_items = [('photo.jpg', temp_path)]

            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                url_mapping = upload_media_batch(
                    mock_client,
                    "my-bucket",
                    media_items,
                    endpoint="minio.example.com",
                    asset_prefix="media"
                )

            self.assertEqual(
                url_mapping['photo.jpg'],
                "https://minio.example.com/my-bucket/media/photo.jpg"
            )
        finally:
            os.unlink(temp_path)

    def test_handles_empty_batch(self):
        """Handles empty media_items list gracefully."""
        mock_client = MagicMock()

        url_mapping = upload_media_batch(
            mock_client,
            "my-bucket",
            [],
            endpoint="minio.example.com"
        )

        self.assertEqual(url_mapping, {})

    def test_handles_mixed_success_and_failure(self):
        """Correctly handles batch with mixed success and failure."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_s3_error = Exception("Access Denied")
        mock_minio = MagicMock()
        mock_minio.error.S3Error = type(mock_s3_error)

        # First call succeeds, second fails
        mock_client.fput_object.side_effect = [mock_result, mock_s3_error]

        temp_files = []
        try:
            for ext in ['.jpg', '.png']:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(b'fake data')
                    temp_files.append(f.name)

            media_items = [
                ('success.jpg', temp_files[0]),
                ('fail.png', temp_files[1]),
            ]

            with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                url_mapping = upload_media_batch(
                    mock_client,
                    "my-bucket",
                    media_items,
                    endpoint="minio.example.com"
                )

            self.assertEqual(
                url_mapping['success.jpg'],
                "https://minio.example.com/my-bucket/assets/success.jpg"
            )
            self.assertIsNone(url_mapping['fail.png'])
        finally:
            for path in temp_files:
                os.unlink(path)

    def test_secure_parameter_overrides_environment(self):
        """secure parameter overrides MINIO_SECURE environment variable."""
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.etag = "abc123"
        mock_client.fput_object.return_value = mock_result
        mock_minio = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake data')
            temp_path = f.name

        try:
            media_items = [('photo.jpg', temp_path)]
            env_vars = {
                MINIO_ENDPOINT_VAR: "minio.example.com",
                MINIO_SECURE_VAR: "true"  # Environment says HTTPS
            }

            with patch.dict(os.environ, env_vars, clear=False):
                with patch('minio_uploader._get_minio_module', return_value=mock_minio):
                    url_mapping = upload_media_batch(
                        mock_client,
                        "my-bucket",
                        media_items,
                        secure=False  # But we override to HTTP
                    )

            # Should use http:// despite env saying true
            self.assertTrue(url_mapping['photo.jpg'].startswith("http://"))
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
