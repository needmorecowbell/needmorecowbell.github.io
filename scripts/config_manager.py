#!/usr/bin/env python3
"""
Hugo Configuration Manager

This module reads Hugo configuration files and provides access to S3CDN settings
and media upload paths. It supports environment switching (development/production)
by reading from the appropriate config directories.

Usage:
    from config_manager import get_hugo_config, get_s3cdn_url, get_media_base_path

    # Get all config for production (default)
    config = get_hugo_config()

    # Get config for development environment
    config = get_hugo_config(environment='development')

    # Get just the S3CDN URL
    s3cdn_url = get_s3cdn_url()

    # Get the media upload path
    media_path = get_media_base_path()
"""

import tomllib
from pathlib import Path
from typing import Optional


class HugoConfigError(Exception):
    """Exception raised when Hugo configuration cannot be read or is invalid."""
    pass


# Default Hugo config directory relative to this script
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / 'config'

# Default environment
DEFAULT_ENVIRONMENT = 'production'


def _load_toml_file(path: Path) -> dict:
    """
    Load and parse a TOML file.

    Args:
        path: Path to the TOML file

    Returns:
        Dict containing parsed TOML data

    Raises:
        HugoConfigError: If file cannot be read or parsed
    """
    try:
        with open(path, 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise HugoConfigError(f"Config file not found: {path}")
    except tomllib.TOMLDecodeError as e:
        raise HugoConfigError(f"Invalid TOML in {path}: {e}")


def _merge_configs(base: dict, override: dict) -> dict:
    """
    Deep merge two config dictionaries.

    Values in override take precedence over base. Nested dicts are merged
    recursively; other values are replaced.

    Args:
        base: Base configuration dict
        override: Override configuration dict

    Returns:
        Merged configuration dict
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = _merge_configs(result[key], value)
        else:
            # Override value
            result[key] = value

    return result


def get_hugo_config(
    environment: str = DEFAULT_ENVIRONMENT,
    config_dir: Optional[Path] = None
) -> dict:
    """
    Load Hugo configuration for the specified environment.

    Reads the base configuration from config/_default/ and overlays
    environment-specific settings from config/<environment>/ if they exist.

    Args:
        environment: The Hugo environment name (default: 'production')
        config_dir: Optional path to the Hugo config directory
                   (default: <repo_root>/config)

    Returns:
        Dict containing merged Hugo configuration

    Raises:
        HugoConfigError: If configuration cannot be loaded
    """
    if config_dir is None:
        config_dir = DEFAULT_CONFIG_DIR

    config_dir = Path(config_dir)

    if not config_dir.exists():
        raise HugoConfigError(f"Config directory not found: {config_dir}")

    # Load base configuration from _default
    default_dir = config_dir / '_default'
    if not default_dir.exists():
        raise HugoConfigError(f"Default config directory not found: {default_dir}")

    merged_config = {}

    # Load all TOML files from _default
    for toml_file in sorted(default_dir.glob('*.toml')):
        file_config = _load_toml_file(toml_file)
        merged_config = _merge_configs(merged_config, file_config)

    # Load environment-specific overrides if not production
    # (production uses _default as-is)
    if environment != 'production':
        env_dir = config_dir / environment
        if env_dir.exists():
            for toml_file in sorted(env_dir.glob('*.toml')):
                file_config = _load_toml_file(toml_file)
                merged_config = _merge_configs(merged_config, file_config)

    return merged_config


def get_s3cdn_url(
    environment: str = DEFAULT_ENVIRONMENT,
    config_dir: Optional[Path] = None
) -> str:
    """
    Get the S3CDN base URL for the specified environment.

    This is the public URL prefix used in Hugo templates for media files.
    For production, this typically points to the CDN. For development,
    it points to a local MinIO instance.

    Args:
        environment: The Hugo environment name (default: 'production')
        config_dir: Optional path to the Hugo config directory

    Returns:
        The S3CDN base URL string

    Raises:
        HugoConfigError: If S3CDN is not configured
    """
    config = get_hugo_config(environment, config_dir)

    s3cdn = config.get('S3CDN')
    if not s3cdn:
        raise HugoConfigError(
            f"S3CDN not configured in Hugo config for environment '{environment}'. "
            f"Add 'S3CDN = \"https://...\"' to config/_default/params.toml or "
            f"config/{environment}/params.toml"
        )

    return s3cdn


def get_media_base_path(
    environment: str = DEFAULT_ENVIRONMENT,
    config_dir: Optional[Path] = None
) -> str:
    """
    Get the media upload base path for the specified environment.

    This is the path prefix used when uploading media files to MinIO/S3.
    It corresponds to the bucket path where assets are stored.

    Args:
        environment: The Hugo environment name (default: 'production')
        config_dir: Optional path to the Hugo config directory

    Returns:
        The media base path string

    Raises:
        HugoConfigError: If mediaBasePath is not configured
    """
    config = get_hugo_config(environment, config_dir)

    media_path = config.get('mediaBasePath')
    if not media_path:
        raise HugoConfigError(
            f"mediaBasePath not configured in Hugo config for environment '{environment}'. "
            f"Add 'mediaBasePath = \"path/to/assets\"' to config/_default/params.toml or "
            f"config/{environment}/params.toml"
        )

    return media_path


def get_base_url(
    environment: str = DEFAULT_ENVIRONMENT,
    config_dir: Optional[Path] = None
) -> str:
    """
    Get the Hugo site base URL for the specified environment.

    Args:
        environment: The Hugo environment name (default: 'production')
        config_dir: Optional path to the Hugo config directory

    Returns:
        The base URL string

    Raises:
        HugoConfigError: If baseURL is not configured
    """
    config = get_hugo_config(environment, config_dir)

    base_url = config.get('baseURL')
    if not base_url:
        raise HugoConfigError(
            f"baseURL not configured in Hugo config for environment '{environment}'. "
            f"Add 'baseURL = \"https://...\"' to config/_default/config.toml"
        )

    return base_url


def list_environments(config_dir: Optional[Path] = None) -> list:
    """
    List available Hugo environments.

    Returns the names of all environment directories found in the config
    directory, plus 'production' (which uses _default).

    Args:
        config_dir: Optional path to the Hugo config directory

    Returns:
        List of environment names (always includes 'production')
    """
    if config_dir is None:
        config_dir = DEFAULT_CONFIG_DIR

    config_dir = Path(config_dir)

    environments = ['production']  # Always available

    if config_dir.exists():
        for subdir in config_dir.iterdir():
            if subdir.is_dir() and subdir.name != '_default':
                environments.append(subdir.name)

    return sorted(environments)


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Read Hugo configuration values"
    )
    parser.add_argument(
        '-e', '--environment',
        default=DEFAULT_ENVIRONMENT,
        help=f"Hugo environment (default: {DEFAULT_ENVIRONMENT})"
    )
    parser.add_argument(
        '--s3cdn',
        action='store_true',
        help="Print only the S3CDN URL"
    )
    parser.add_argument(
        '--media-path',
        action='store_true',
        help="Print only the media base path"
    )
    parser.add_argument(
        '--base-url',
        action='store_true',
        help="Print only the base URL"
    )
    parser.add_argument(
        '--list-envs',
        action='store_true',
        help="List available environments"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help="Output full config as JSON"
    )

    args = parser.parse_args()

    try:
        if args.list_envs:
            for env in list_environments():
                print(env)
        elif args.s3cdn:
            print(get_s3cdn_url(args.environment))
        elif args.media_path:
            print(get_media_base_path(args.environment))
        elif args.base_url:
            print(get_base_url(args.environment))
        elif args.json:
            config = get_hugo_config(args.environment)
            print(json.dumps(config, indent=2, default=str))
        else:
            # Print summary
            config = get_hugo_config(args.environment)
            print(f"Environment: {args.environment}")
            print(f"S3CDN:       {config.get('S3CDN', 'NOT SET')}")
            print(f"Media Path:  {config.get('mediaBasePath', 'NOT SET')}")
            print(f"Base URL:    {config.get('baseURL', 'NOT SET')}")
    except HugoConfigError as e:
        print(f"Error: {e}", file=__import__('sys').stderr)
        exit(1)
