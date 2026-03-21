"""Tests for TOML runtime configuration loading and defaults."""

from pathlib import Path

import pytest

from chatgpt_export_tool.core.config.runtime import (
    DEFAULT_CONFIG_FILENAME,
    load_runtime_config,
)
from chatgpt_export_tool.core.logging_utils import setup_logging


def test_load_runtime_config_defaults_when_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing config file should fall back to built-in defaults."""
    monkeypatch.chdir(tmp_path)

    config = load_runtime_config()

    assert config.defaults.format_type == "txt"
    assert config.transcript.show_assistant_thoughts is True
    assert config.text_output.header_fields == ("title", "id", "create_time")
    assert config.source_path is None


def test_load_runtime_config_only_uses_explicit_path(tmp_path: Path) -> None:
    """Config loading should be explicit instead of ambient."""
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    config_path.write_text(
        """
[defaults]
format = "json"
split = "subject"

[transcript]
show_tool_messages = true

[text_output]
header_fields = ["title", "conversation_id"]
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(str(config_path))

    assert config.defaults.format_type == "json"
    assert config.defaults.split_mode == "subject"
    assert config.transcript.show_tool_messages is True
    assert config.text_output.header_fields == ("title", "conversation_id")
    assert config.source_path == str(config_path)


def test_load_runtime_config_does_not_implicitly_read_cwd_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A repo-local config file should not silently change behavior."""
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    config_path.write_text(
        """
[defaults]
format = "json"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = load_runtime_config()

    assert config.defaults.format_type == "txt"
    assert config.source_path is None


def test_load_runtime_config_rejects_invalid_types(tmp_path: Path) -> None:
    """Invalid TOML value types should fail fast."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[transcript]
show_tool_messages = "yes"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_semantic_values(tmp_path: Path) -> None:
    """Semantically invalid values should fail before command execution."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[defaults]
format = "yaml"
split = "weekly"

[transcript]
user_editable_context_mode = "summary"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_section_shape(tmp_path: Path) -> None:
    """Config sections must be TOML tables when present."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
defaults = "not-a-table"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_missing_explicit_path() -> None:
    """An explicit config path should fail fast when the file is missing."""
    with pytest.raises(ValueError):
        load_runtime_config("/definitely/missing/chatgpt_export.toml")


def test_load_runtime_config_rejects_invalid_numeric_and_list_values(
    tmp_path: Path,
) -> None:
    """Integer and string-list config fields should validate strictly."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[transcript]
user_editable_context_preview_chars = -1
show_visually_hidden_content_types = "user_editable_context"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_string_value_type(tmp_path: Path) -> None:
    """String-valued config keys should reject non-string TOML values."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[defaults]
format = 123
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_integer_value_type(tmp_path: Path) -> None:
    """Integer-valued config keys should reject non-integer TOML values."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[transcript]
user_editable_context_preview_chars = "wide"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_string_list_items(tmp_path: Path) -> None:
    """String-list config keys should reject mixed-type arrays."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[text_output]
header_fields = ["title", 1]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_rejects_invalid_metadata_defaults(tmp_path: Path) -> None:
    """Metadata defaults should validate during config loading."""
    config_path = tmp_path / "broken.toml"
    config_path.write_text(
        """
[defaults]
include_metadata = [""]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))


def test_load_runtime_config_warns_for_unknown_metadata_defaults(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown metadata defaults should warn at config-load time."""
    setup_logging(verbose=True)
    config_path = tmp_path / "warn.toml"
    config_path.write_text(
        """
[defaults]
include_metadata = ["unknown_metadata"]
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(str(config_path))

    captured = capsys.readouterr()
    assert config.defaults.include_metadata == ("unknown_metadata",)
    assert "matches no known metadata fields" in captured.err


def test_load_runtime_config_parses_text_layout_options(tmp_path: Path) -> None:
    """Text output layout options should load from TOML."""
    config_path = tmp_path / "layout.toml"
    config_path.write_text(
        """
[text_output]
layout_mode = "compact"
heading_style = "markdown"
include_turn_count_in_header = false
include_turn_numbers = true
turn_separator = "***"
strip_chatgpt_artifacts = false
wrap_width = 120
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(str(config_path))

    assert config.text_output.layout_mode == "compact"
    assert config.text_output.heading_style == "markdown"
    assert config.text_output.include_turn_count_in_header is False
    assert config.text_output.include_turn_numbers is True
    assert config.text_output.turn_separator == "***"
    assert config.text_output.strip_chatgpt_artifacts is False
    assert config.text_output.wrap_width == 120


def test_load_runtime_config_rejects_invalid_text_output_values(tmp_path: Path) -> None:
    """Invalid text output semantics should fail during config loading."""
    config_path = tmp_path / "broken-layout.toml"
    config_path.write_text(
        """
[text_output]
layout_mode = "wide"
heading_style = "html"
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_runtime_config(str(config_path))
