#!/usr/bin/env python3
"""
Tests for the Hugo configuration manager module.

Run with: python test_config_manager.py
Or with pytest: pytest test_config_manager.py -v
"""

import os
import tempfile
import unittest
from pathlib import Path

from config_manager import (
    get_hugo_config,
    get_s3cdn_url,
    get_media_base_path,
    get_base_url,
    list_environments,
    HugoConfigError,
    _load_toml_file,
    _merge_configs,
    DEFAULT_ENVIRONMENT,
)


class TestLoadTomlFile(unittest.TestCase):
    """Tests for _load_toml_file() function."""

    def test_loads_valid_toml(self):
        """Loads and parses a valid TOML file."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            f.write(b'key = "value"\nnumber = 42\n')
            temp_path = Path(f.name)

        try:
            result = _load_toml_file(temp_path)
            self.assertEqual(result, {'key': 'value', 'number': 42})
        finally:
            temp_path.unlink()

    def test_raises_on_missing_file(self):
        """Raises HugoConfigError for missing file."""
        with self.assertRaises(HugoConfigError) as ctx:
            _load_toml_file(Path('/nonexistent/path/config.toml'))
        self.assertIn('not found', str(ctx.exception))

    def test_raises_on_invalid_toml(self):
        """Raises HugoConfigError for invalid TOML syntax."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            f.write(b'invalid = [unclosed\n')
            temp_path = Path(f.name)

        try:
            with self.assertRaises(HugoConfigError) as ctx:
                _load_toml_file(temp_path)
            self.assertIn('Invalid TOML', str(ctx.exception))
        finally:
            temp_path.unlink()

    def test_loads_nested_config(self):
        """Loads TOML with nested tables."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.toml', delete=False) as f:
            f.write(b'''
[section]
key = "value"

[section.nested]
deep = true
''')
            temp_path = Path(f.name)

        try:
            result = _load_toml_file(temp_path)
            self.assertEqual(result['section']['key'], 'value')
            self.assertEqual(result['section']['nested']['deep'], True)
        finally:
            temp_path.unlink()


class TestMergeConfigs(unittest.TestCase):
    """Tests for _merge_configs() function."""

    def test_merges_flat_dicts(self):
        """Merges two flat dictionaries."""
        base = {'a': 1, 'b': 2}
        override = {'b': 3, 'c': 4}
        result = _merge_configs(base, override)
        self.assertEqual(result, {'a': 1, 'b': 3, 'c': 4})

    def test_does_not_mutate_base(self):
        """Does not modify the base dictionary."""
        base = {'a': 1, 'b': 2}
        override = {'b': 3}
        _merge_configs(base, override)
        self.assertEqual(base, {'a': 1, 'b': 2})

    def test_deep_merges_nested_dicts(self):
        """Deep merges nested dictionaries."""
        base = {
            'section': {
                'key1': 'value1',
                'key2': 'value2'
            }
        }
        override = {
            'section': {
                'key2': 'overridden',
                'key3': 'value3'
            }
        }
        result = _merge_configs(base, override)
        self.assertEqual(result['section'], {
            'key1': 'value1',
            'key2': 'overridden',
            'key3': 'value3'
        })

    def test_replaces_non_dict_with_dict(self):
        """Replaces non-dict value with dict."""
        base = {'key': 'string'}
        override = {'key': {'nested': 'value'}}
        result = _merge_configs(base, override)
        self.assertEqual(result, {'key': {'nested': 'value'}})

    def test_replaces_dict_with_non_dict(self):
        """Replaces dict value with non-dict."""
        base = {'key': {'nested': 'value'}}
        override = {'key': 'string'}
        result = _merge_configs(base, override)
        self.assertEqual(result, {'key': 'string'})

    def test_handles_empty_base(self):
        """Handles empty base dictionary."""
        result = _merge_configs({}, {'key': 'value'})
        self.assertEqual(result, {'key': 'value'})

    def test_handles_empty_override(self):
        """Handles empty override dictionary."""
        result = _merge_configs({'key': 'value'}, {})
        self.assertEqual(result, {'key': 'value'})


class TestGetHugoConfig(unittest.TestCase):
    """Tests for get_hugo_config() function."""

    def setUp(self):
        """Set up a temporary config directory structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.default_dir = self.config_dir / '_default'
        self.dev_dir = self.config_dir / 'development'

        # Create directory structure
        self.default_dir.mkdir(parents=True)
        self.dev_dir.mkdir(parents=True)

        # Create default config.toml
        (self.default_dir / 'config.toml').write_text('''
baseURL = "https://example.com"
title = "Test Site"
''')

        # Create default params.toml
        (self.default_dir / 'params.toml').write_text('''
S3CDN = "https://cdn.example.com/assets"
mediaBasePath = "production/assets"
author = "Test Author"
''')

        # Create development params.toml
        (self.dev_dir / 'params.toml').write_text('''
S3CDN = "http://localhost:9000/dev-bucket"
mediaBasePath = "dev-bucket"
''')

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_loads_production_config_by_default(self):
        """Loads production (default) config when no environment specified."""
        config = get_hugo_config(config_dir=self.config_dir)
        self.assertEqual(config['baseURL'], 'https://example.com')
        self.assertEqual(config['S3CDN'], 'https://cdn.example.com/assets')

    def test_merges_multiple_toml_files(self):
        """Merges config.toml and params.toml from _default."""
        config = get_hugo_config(config_dir=self.config_dir)
        self.assertEqual(config['baseURL'], 'https://example.com')
        self.assertEqual(config['title'], 'Test Site')
        self.assertEqual(config['author'], 'Test Author')

    def test_loads_development_config(self):
        """Loads development environment overrides."""
        config = get_hugo_config(environment='development', config_dir=self.config_dir)
        # Should have development S3CDN
        self.assertEqual(config['S3CDN'], 'http://localhost:9000/dev-bucket')
        self.assertEqual(config['mediaBasePath'], 'dev-bucket')
        # Should still have base config values
        self.assertEqual(config['baseURL'], 'https://example.com')
        self.assertEqual(config['author'], 'Test Author')

    def test_raises_on_missing_config_dir(self):
        """Raises HugoConfigError when config directory doesn't exist."""
        with self.assertRaises(HugoConfigError) as ctx:
            get_hugo_config(config_dir=Path('/nonexistent/config'))
        self.assertIn('Config directory not found', str(ctx.exception))

    def test_raises_on_missing_default_dir(self):
        """Raises HugoConfigError when _default directory doesn't exist."""
        empty_config = Path(self.temp_dir) / 'empty_config'
        empty_config.mkdir()

        with self.assertRaises(HugoConfigError) as ctx:
            get_hugo_config(config_dir=empty_config)
        self.assertIn('Default config directory not found', str(ctx.exception))

    def test_ignores_missing_environment_dir(self):
        """Uses only _default when environment directory doesn't exist."""
        config = get_hugo_config(environment='staging', config_dir=self.config_dir)
        # Should fall back to production values
        self.assertEqual(config['S3CDN'], 'https://cdn.example.com/assets')

    def test_production_environment_uses_default_only(self):
        """Production environment uses _default without looking for overrides."""
        config = get_hugo_config(environment='production', config_dir=self.config_dir)
        self.assertEqual(config['S3CDN'], 'https://cdn.example.com/assets')


class TestGetS3cdnUrl(unittest.TestCase):
    """Tests for get_s3cdn_url() function."""

    def setUp(self):
        """Set up a temporary config directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.default_dir = self.config_dir / '_default'
        self.dev_dir = self.config_dir / 'development'

        self.default_dir.mkdir(parents=True)
        self.dev_dir.mkdir(parents=True)

        (self.default_dir / 'params.toml').write_text('''
S3CDN = "https://cdn.example.com/prod"
''')

        (self.dev_dir / 'params.toml').write_text('''
S3CDN = "http://localhost:9000/dev"
''')

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_returns_production_url_by_default(self):
        """Returns production S3CDN URL when no environment specified."""
        url = get_s3cdn_url(config_dir=self.config_dir)
        self.assertEqual(url, 'https://cdn.example.com/prod')

    def test_returns_development_url(self):
        """Returns development S3CDN URL when development environment specified."""
        url = get_s3cdn_url(environment='development', config_dir=self.config_dir)
        self.assertEqual(url, 'http://localhost:9000/dev')

    def test_raises_when_not_configured(self):
        """Raises HugoConfigError when S3CDN is not configured."""
        # Create config without S3CDN
        (self.default_dir / 'params.toml').write_text('author = "test"\n')

        with self.assertRaises(HugoConfigError) as ctx:
            get_s3cdn_url(config_dir=self.config_dir)
        self.assertIn('S3CDN not configured', str(ctx.exception))


class TestGetMediaBasePath(unittest.TestCase):
    """Tests for get_media_base_path() function."""

    def setUp(self):
        """Set up a temporary config directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.default_dir = self.config_dir / '_default'
        self.dev_dir = self.config_dir / 'development'

        self.default_dir.mkdir(parents=True)
        self.dev_dir.mkdir(parents=True)

        (self.default_dir / 'params.toml').write_text('''
mediaBasePath = "prod/assets"
''')

        (self.dev_dir / 'params.toml').write_text('''
mediaBasePath = "dev-bucket"
''')

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_returns_production_path_by_default(self):
        """Returns production media path when no environment specified."""
        path = get_media_base_path(config_dir=self.config_dir)
        self.assertEqual(path, 'prod/assets')

    def test_returns_development_path(self):
        """Returns development media path when development environment specified."""
        path = get_media_base_path(environment='development', config_dir=self.config_dir)
        self.assertEqual(path, 'dev-bucket')

    def test_raises_when_not_configured(self):
        """Raises HugoConfigError when mediaBasePath is not configured."""
        # Create config without mediaBasePath
        (self.default_dir / 'params.toml').write_text('author = "test"\n')

        with self.assertRaises(HugoConfigError) as ctx:
            get_media_base_path(config_dir=self.config_dir)
        self.assertIn('mediaBasePath not configured', str(ctx.exception))


class TestGetBaseUrl(unittest.TestCase):
    """Tests for get_base_url() function."""

    def setUp(self):
        """Set up a temporary config directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.default_dir = self.config_dir / '_default'

        self.default_dir.mkdir(parents=True)

        (self.default_dir / 'config.toml').write_text('''
baseURL = "https://example.com"
''')

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_returns_base_url(self):
        """Returns the Hugo site base URL."""
        url = get_base_url(config_dir=self.config_dir)
        self.assertEqual(url, 'https://example.com')

    def test_raises_when_not_configured(self):
        """Raises HugoConfigError when baseURL is not configured."""
        (self.default_dir / 'config.toml').write_text('title = "test"\n')

        with self.assertRaises(HugoConfigError) as ctx:
            get_base_url(config_dir=self.config_dir)
        self.assertIn('baseURL not configured', str(ctx.exception))


class TestListEnvironments(unittest.TestCase):
    """Tests for list_environments() function."""

    def setUp(self):
        """Set up a temporary config directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / 'config'
        self.config_dir.mkdir(parents=True)
        (self.config_dir / '_default').mkdir()
        (self.config_dir / 'development').mkdir()
        (self.config_dir / 'staging').mkdir()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_lists_all_environments(self):
        """Lists all available environments including production."""
        envs = list_environments(config_dir=self.config_dir)
        self.assertIn('production', envs)
        self.assertIn('development', envs)
        self.assertIn('staging', envs)

    def test_always_includes_production(self):
        """Always includes production even if only _default exists."""
        # Remove non-default directories
        import shutil
        shutil.rmtree(self.config_dir / 'development')
        shutil.rmtree(self.config_dir / 'staging')

        envs = list_environments(config_dir=self.config_dir)
        self.assertEqual(envs, ['production'])

    def test_excludes_default_from_list(self):
        """Does not include '_default' in the list."""
        envs = list_environments(config_dir=self.config_dir)
        self.assertNotIn('_default', envs)

    def test_returns_sorted_list(self):
        """Returns environments in sorted order."""
        envs = list_environments(config_dir=self.config_dir)
        self.assertEqual(envs, sorted(envs))

    def test_handles_missing_config_dir(self):
        """Returns only production for missing config dir."""
        envs = list_environments(config_dir=Path('/nonexistent'))
        self.assertEqual(envs, ['production'])


class TestDefaultEnvironment(unittest.TestCase):
    """Tests for default environment constant."""

    def test_default_is_production(self):
        """Default environment is 'production'."""
        self.assertEqual(DEFAULT_ENVIRONMENT, 'production')


class TestRealConfig(unittest.TestCase):
    """Integration tests using the real Hugo config files."""

    def test_reads_real_production_config(self):
        """Reads the actual production configuration."""
        try:
            config = get_hugo_config()
            # Verify expected production values exist
            self.assertIn('S3CDN', config)
            self.assertIn('mediaBasePath', config)
            self.assertTrue(config['S3CDN'].startswith('https://'))
        except HugoConfigError:
            self.skipTest("Real config not available")

    def test_reads_real_development_config(self):
        """Reads the actual development configuration."""
        try:
            config = get_hugo_config(environment='development')
            # Development should have S3CDN configured
            self.assertIn('S3CDN', config)
            # Development typically uses HTTP (not HTTPS) for local/LAN resources
            # Accept http:// URLs (localhost, LAN IPs, or docker hostnames)
            self.assertTrue(
                config['S3CDN'].startswith('http://'),
                f"Development S3CDN should use HTTP for local resources: {config['S3CDN']}"
            )
        except HugoConfigError:
            self.skipTest("Real config not available")

    def test_real_s3cdn_url(self):
        """Gets the real S3CDN URL."""
        try:
            url = get_s3cdn_url()
            self.assertTrue(url.startswith('http'))
        except HugoConfigError:
            self.skipTest("Real config not available")

    def test_real_media_base_path(self):
        """Gets the real media base path."""
        try:
            path = get_media_base_path()
            self.assertTrue(len(path) > 0)
        except HugoConfigError:
            self.skipTest("Real config not available")

    def test_list_real_environments(self):
        """Lists real environments."""
        envs = list_environments()
        self.assertIn('production', envs)
        # Development should exist based on the config we saw
        self.assertIn('development', envs)


if __name__ == "__main__":
    unittest.main()
