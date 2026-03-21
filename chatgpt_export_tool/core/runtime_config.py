"""Runtime configuration loading and resolution."""

from pathlib import Path
from typing import Any, Optional, Sequence

try:  # pragma: no cover - Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib

from .config_models import (
    DEFAULT_CONFIG_FILENAME,
    DefaultsConfig,
    RuntimeConfig,
    TextOutputConfig,
    TranscriptConfig,
)
from .config_validation import validate_defaults_config, validate_transcript_config


def load_runtime_config(config_path: Optional[str] = None) -> RuntimeConfig:
    """Load runtime configuration from TOML or defaults."""
    path = _resolve_config_path(config_path)
    if path is None:
        return RuntimeConfig()

    with open(path, "rb") as handle:
        payload = tomllib.load(handle)

    return RuntimeConfig(
        defaults=_load_defaults(payload.get("defaults")),
        transcript=_load_transcript(payload.get("transcript")),
        text_output=_load_text_output(payload.get("text_output")),
        source_path=str(path),
    )


def _resolve_config_path(config_path: Optional[str]) -> Optional[Path]:
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ValueError(f"Config file not found: {config_path}")
        return path
    return None


def _load_defaults(section: Any) -> DefaultsConfig:
    section = _expect_table(section, "defaults")
    defaults = DefaultsConfig(
        format_type=_get_str(section, "format", DefaultsConfig.format_type),
        split_mode=_get_str(section, "split", DefaultsConfig.split_mode),
        field_spec=_get_str(section, "fields", DefaultsConfig.field_spec),
        output_dir=_get_str(section, "output_dir", DefaultsConfig.output_dir),
        include_metadata=_get_str_list(
            section,
            "include_metadata",
            DefaultsConfig.include_metadata,
        ),
        exclude_metadata=_get_str_list(
            section,
            "exclude_metadata",
            DefaultsConfig.exclude_metadata,
        ),
    )
    validate_defaults_config(defaults)
    return defaults


def _load_transcript(section: Any) -> TranscriptConfig:
    section = _expect_table(section, "transcript")
    defaults = TranscriptConfig()
    transcript = TranscriptConfig(
        follow_current_branch=_get_bool(
            section, "follow_current_branch", defaults.follow_current_branch
        ),
        show_system_messages=_get_bool(
            section, "show_system_messages", defaults.show_system_messages
        ),
        show_tool_messages=_get_bool(
            section, "show_tool_messages", defaults.show_tool_messages
        ),
        show_user_text=_get_bool(section, "show_user_text", defaults.show_user_text),
        show_assistant_text=_get_bool(
            section, "show_assistant_text", defaults.show_assistant_text
        ),
        show_assistant_thoughts=_get_bool(
            section,
            "show_assistant_thoughts",
            defaults.show_assistant_thoughts,
        ),
        show_user_editable_context=_get_bool(
            section,
            "show_user_editable_context",
            defaults.show_user_editable_context,
        ),
        show_multimodal_text=_get_bool(
            section, "show_multimodal_text", defaults.show_multimodal_text
        ),
        show_assistant_code=_get_bool(
            section, "show_assistant_code", defaults.show_assistant_code
        ),
        show_reasoning_recap=_get_bool(
            section, "show_reasoning_recap", defaults.show_reasoning_recap
        ),
        skip_blank_messages=_get_bool(
            section, "skip_blank_messages", defaults.skip_blank_messages
        ),
        honor_visual_hidden_flag=_get_bool(
            section,
            "honor_visual_hidden_flag",
            defaults.honor_visual_hidden_flag,
        ),
        include_turn_timestamps=_get_bool(
            section,
            "include_turn_timestamps",
            defaults.include_turn_timestamps,
        ),
        user_editable_context_mode=_get_str(
            section,
            "user_editable_context_mode",
            defaults.user_editable_context_mode,
        ),
        user_editable_context_preview_chars=_get_int(
            section,
            "user_editable_context_preview_chars",
            defaults.user_editable_context_preview_chars,
            minimum=0,
        ),
        show_visually_hidden_content_types=_get_str_list(
            section,
            "show_visually_hidden_content_types",
            defaults.show_visually_hidden_content_types,
        ),
        include_content_types=_get_str_list(
            section,
            "include_content_types",
            defaults.include_content_types,
        ),
        exclude_content_types=_get_str_list(
            section,
            "exclude_content_types",
            defaults.exclude_content_types,
        ),
    )
    validate_transcript_config(transcript)
    return transcript


def _load_text_output(section: Any) -> TextOutputConfig:
    section = _expect_table(section, "text_output")
    defaults = TextOutputConfig()
    return TextOutputConfig(
        include_header=_get_bool(section, "include_header", defaults.include_header),
        header_fields=_get_str_list(section, "header_fields", defaults.header_fields),
        conversation_time_format=_get_str(
            section,
            "conversation_time_format",
            defaults.conversation_time_format,
        ),
        turn_time_format=_get_str(
            section,
            "turn_time_format",
            defaults.turn_time_format,
        ),
    )


def _expect_table(section: Any, section_name: str) -> dict[str, Any]:
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ValueError(f"Config section '{section_name}' must be a table")
    return section


def _get_str(section: dict[str, Any], key: str, default: str) -> str:
    value = section.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"Config value '{key}' must be a string")
    return value


def _get_bool(section: dict[str, Any], key: str, default: bool) -> bool:
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"Config value '{key}' must be a boolean")
    return value


def _get_int(
    section: dict[str, Any],
    key: str,
    default: int,
    *,
    minimum: Optional[int] = None,
) -> int:
    value = section.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"Config value '{key}' must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"Config value '{key}' must be >= {minimum}")
    return value


def _get_str_list(
    section: dict[str, Any],
    key: str,
    default: Sequence[str],
) -> tuple[str, ...]:
    value = section.get(key, list(default))
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Config value '{key}' must be an array of strings")
    return tuple(value)


__all__ = [
    "DEFAULT_CONFIG_FILENAME",
    "DefaultsConfig",
    "RuntimeConfig",
    "TextOutputConfig",
    "TranscriptConfig",
    "load_runtime_config",
]
