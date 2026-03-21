"""Tests for TOML runtime configuration loading and defaults."""

from pathlib import Path

import pytest

from chatgpt_export_tool.core.runtime_config import (
    DEFAULT_CONFIG_FILENAME,
    load_runtime_config,
)


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
