#!/usr/bin/env python3
"""
Tests for the MinIO uploader module.

Run with: python test_minio_uploader.py
Or with pytest: pytest test_minio_uploader.py -v
"""

import os
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from minio_uploader import (
    get_minio_client,
    get_bucket_name,
    ensure_bucket_exists,
    MinioConfigError,
    MINIO_ENDPOINT_VAR,
    MINIO_ACCESS_KEY_VAR,
    MINIO_SECRET_KEY_VAR,
    MINIO_BUCKET_VAR,
    MINIO_SECURE_VAR,
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


if __name__ == "__main__":
    unittest.main()
