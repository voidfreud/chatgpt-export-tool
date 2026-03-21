"""Runtime configuration models and defaults."""

from dataclasses import dataclass, field
from typing import Optional


DEFAULT_CONFIG_FILENAME = "chatgpt_export.toml"
DEFAULT_TIME_FORMAT = "%H:%M %d-%m-%Y"
DEFAULT_CONTEXT_PREVIEW_CHARS = 160


@dataclass(frozen=True)
class DefaultsConfig:
    """Default CLI/runtime values."""

    format_type: str = "txt"
    split_mode: str = "single"
    field_spec: str = "all"
    output_dir: str = "output"
    include_metadata: tuple[str, ...] = ()
    exclude_metadata: tuple[str, ...] = ()


@dataclass(frozen=True)
class TranscriptConfig:
    """Transcript extraction and visibility policy."""

    follow_current_branch: bool = True
    show_system_messages: bool = False
    show_tool_messages: bool = False
    show_user_text: bool = True
    show_assistant_text: bool = True
    show_assistant_thoughts: bool = True
    show_user_editable_context: bool = True
    show_multimodal_text: bool = True
    show_assistant_code: bool = False
    show_reasoning_recap: bool = False
    skip_blank_messages: bool = True
    honor_visual_hidden_flag: bool = True
    include_turn_timestamps: bool = True
    user_editable_context_mode: str = "compact"
    user_editable_context_preview_chars: int = DEFAULT_CONTEXT_PREVIEW_CHARS
    show_visually_hidden_content_types: tuple[str, ...] = ("user_editable_context",)
    include_content_types: tuple[str, ...] = ()
    exclude_content_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextOutputConfig:
    """Text transcript/header rendering settings."""

    include_header: bool = True
    header_fields: tuple[str, ...] = ("title", "id", "create_time")
    conversation_time_format: str = DEFAULT_TIME_FORMAT
    turn_time_format: str = DEFAULT_TIME_FORMAT
    layout_mode: str = "reading"
    heading_style: str = "plain"
    include_turn_count_in_header: bool = True
    include_turn_numbers: bool = False
    turn_separator: str = "---"
    strip_chatgpt_artifacts: bool = True
    wrap_width: int = 88


@dataclass(frozen=True)
class RuntimeConfig:
    """Resolved runtime configuration."""

    defaults: DefaultsConfig = field(default_factory=DefaultsConfig)
    transcript: TranscriptConfig = field(default_factory=TranscriptConfig)
    text_output: TextOutputConfig = field(default_factory=TextOutputConfig)
    source_path: Optional[str] = None
