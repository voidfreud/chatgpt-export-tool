"""Tests for semantic runtime config validation."""

import pytest

from chatgpt_export_tool.core.config_models import DefaultsConfig, TranscriptConfig
from chatgpt_export_tool.core.config_validation import (
    validate_defaults_config,
    validate_transcript_config,
)


def test_validate_defaults_config_accepts_builtin_defaults() -> None:
    """The built-in default config should be semantically valid."""
    validate_defaults_config(DefaultsConfig())


def test_validate_defaults_config_rejects_invalid_format() -> None:
    """Unknown output formats should fail semantic validation."""
    with pytest.raises(ValueError):
        validate_defaults_config(DefaultsConfig(format_type="yaml"))


def test_validate_transcript_config_rejects_overlapping_content_rules() -> None:
    """A content type cannot be both forced in and forced out."""
    with pytest.raises(ValueError):
        validate_transcript_config(
            TranscriptConfig(
                include_content_types=("text",),
                exclude_content_types=("text",),
            )
        )
