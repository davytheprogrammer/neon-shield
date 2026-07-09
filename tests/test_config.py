"""Tests for config loading and validation."""
import pytest
from src.core.config import Config, load_config, merge_with_cli, validate_config


def test_config_defaults():
    """Test default config values."""
    config = Config()
    assert config.log_level == "INFO"
    assert config.enable_image_swap is True
    assert config.http_port == 8081


def test_merge_cli_args():
    """Test CLI arg override."""
    config = Config()
    cli_args = {"verbose": True, "dry_run": True}
    config = merge_with_cli(config, cli_args)
    assert config.verbose is True
    assert config.dry_run is True


def test_validate_config_valid():
    """Test validation passes for valid config."""
    config = Config()
    validate_config(config)  # Should not raise


def test_validate_config_invalid_log_level():
    """Test validation fails for invalid log level."""
    config = Config(log_level="INVALID")
    with pytest.raises(SystemExit):
        validate_config(config)
