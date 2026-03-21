"""Conversation output formatters."""

import json
import re
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from chatgpt_export_tool.core.conversation_access import (
    get_conversation_title,
    get_display_conversation_id,
)
from chatgpt_export_tool.core.runtime_config import TextOutputConfig, TranscriptConfig
from chatgpt_export_tool.core.thread_transcript import iter_transcript_entries
from chatgpt_export_tool.core.utils import format_timestamp, get_logger

logger = get_logger()
CHATGPT_ARTIFACT_RE = re.compile(r"[^]*")


@dataclass(frozen=True)
class TurnBlock:
    """One rendered transcript turn after grouping."""

    heading: str
    text: str


def _json_default(value: Any) -> Any:
    """Normalize non-standard JSON values produced by streaming parsing."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class BaseFormatter(ABC):
    """Abstract base class for conversation formatters."""

    @abstractmethod
    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a single conversation."""


class TextFormatter(BaseFormatter):
    """Human-readable text formatter."""

    def __init__(
        self,
        include_header: bool = True,
        indent: str = "  ",
        transcript_config: Optional[TranscriptConfig] = None,
        text_output_config: Optional[TextOutputConfig] = None,
    ) -> None:
        """Initialize a text formatter.

        Args:
            include_header: Whether to include headers in output.
            indent: Indentation string for nested dictionaries.
            transcript_config: Transcript visibility policy.
            text_output_config: Text output formatting policy.
        """
        self.transcript_config = transcript_config or TranscriptConfig()
        self.text_output_config = text_output_config or TextOutputConfig(
            include_header=include_header
        )
        self.include_header = self.text_output_config.include_header
        self.indent = indent
        logger.debug(
            "Initialized TextFormatter with include_header=%s indent=%r",
            self.include_header,
            indent,
        )

    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a conversation as text.

        Args:
            conv: Conversation dictionary.

        Returns:
            Formatted conversation text.
        """
        lines = ["-" * 40]

        if self.include_header:
            lines.extend(self._render_header(conv))
            lines.append("")

        context_entries = []
        chat_entries = []
        for entry in iter_transcript_entries(conv, self.transcript_config):
            if entry.content_type == "user_editable_context":
                context_entries.append(entry)
            else:
                chat_entries.append(entry)

        if context_entries:
            lines.extend(self._render_context_entries(context_entries))
            if chat_entries:
                lines.append("")

        turn_blocks = self._group_chat_entries(chat_entries)
        if (
            turn_blocks
            and self.include_header
            and self.text_output_config.include_turn_count_in_header
        ):
            header_index = self._find_header_insert_index(lines)
            lines.insert(header_index, f"Turns: {len(turn_blocks)}")
            lines.insert(header_index + 1, "")

        lines.extend(self._render_chat_entries(turn_blocks))

        lines.append("-" * 40)
        return "\n".join(lines)

    def _find_header_insert_index(self, lines: list[str]) -> int:
        try:
            return lines.index("")
        except ValueError:
            return len(lines)

    def _render_context_entries(self, entries: list[Any]) -> list[str]:
        lines = [self._render_section_heading("Conversation Context")]
        for entry in entries:
            for line in self._prepare_text(entry.text).splitlines():
                if line.strip():
                    lines.append(f"{self.indent}{line}")
        return lines

    def _group_chat_entries(self, entries: list[Any]) -> list[TurnBlock]:
        blocks: list[TurnBlock] = []
        current_heading: Optional[str] = None
        current_parts: list[str] = []

        for index, entry in enumerate(entries, start=1):
            heading = self._render_turn_heading(entry, turn_number=index)
            prepared_text = self._prepare_text(entry.text)
            if current_heading == heading:
                current_parts.append(prepared_text)
                continue
            if current_heading is not None:
                blocks.append(TurnBlock(current_heading, "\n\n".join(current_parts)))
            current_heading = heading
            current_parts = [prepared_text]

        if current_heading is not None:
            blocks.append(TurnBlock(current_heading, "\n\n".join(current_parts)))
        return blocks

    def _render_chat_entries(self, entries: list[TurnBlock]) -> list[str]:
        lines: list[str] = []
        for index, entry in enumerate(entries):
            if index > 0:
                lines.append("")
                if (
                    self.text_output_config.layout_mode == "reading"
                    and self.text_output_config.turn_separator
                ):
                    lines.append(self.text_output_config.turn_separator)
                    lines.append("")
            lines.append(entry.heading)
            body_lines = self._wrap_body_lines(entry.text)
            if self.text_output_config.layout_mode == "compact":
                if body_lines:
                    first_line = body_lines[0].lstrip()
                    lines[-1] = f"{entry.heading} {first_line}".rstrip()
                    lines.extend(body_lines[1:])
                continue
            lines.extend(body_lines)
        return lines

    def _render_turn_heading(self, entry: Any, *, turn_number: int) -> str:
        role_label = self._get_role_label(entry.role, entry.content_type)
        if self.text_output_config.include_turn_numbers:
            role_label = f"Turn {turn_number} · {role_label}"
        if (
            self.transcript_config.include_turn_timestamps
            and entry.timestamp is not None
        ):
            timestamp = format_timestamp(
                entry.timestamp,
                self.text_output_config.turn_time_format,
            )
            heading = f"{role_label} [{timestamp}]"
        else:
            heading = role_label

        if self.text_output_config.heading_style == "markdown":
            return f"## {heading}"
        return f"{heading}:"

    def _get_role_label(self, role: str, content_type: str) -> str:
        if role == "assistant" and content_type == "thoughts":
            return "Assistant Thoughts"
        if role == "assistant" and content_type == "reasoning_recap":
            return "Assistant Reasoning"
        return role.replace("_", " ").title()

    def _prepare_text(self, text: str) -> str:
        prepared = text
        if self.text_output_config.strip_chatgpt_artifacts:
            prepared = CHATGPT_ARTIFACT_RE.sub("", prepared)
            prepared = re.sub(r"\n{3,}", "\n\n", prepared)
        return prepared.strip()

    def _render_section_heading(self, title: str) -> str:
        if self.text_output_config.heading_style == "markdown":
            return f"## {title}"
        return title

    def _wrap_body_lines(self, text: str) -> list[str]:
        indent = (
            "" if self.text_output_config.heading_style == "markdown" else self.indent
        )
        width = self.text_output_config.wrap_width
        rendered: list[str] = []

        for raw_line in text.splitlines() or [""]:
            if not raw_line.strip():
                rendered.append("")
                continue

            if width <= 0:
                rendered.append(f"{indent}{raw_line}" if indent else raw_line)
                continue

            if self._is_structured_line(raw_line):
                fill = textwrap.fill(
                    raw_line,
                    width=width,
                    initial_indent=indent,
                    subsequent_indent=f"{indent}  " if indent else "  ",
                    replace_whitespace=False,
                    drop_whitespace=False,
                )
            else:
                fill = textwrap.fill(
                    raw_line,
                    width=width,
                    initial_indent=indent,
                    subsequent_indent=indent,
                    replace_whitespace=False,
                    drop_whitespace=False,
                )
            rendered.extend(fill.splitlines())
        return rendered

    def _is_structured_line(self, line: str) -> bool:
        stripped = line.lstrip()
        if not stripped:
            return False
        if stripped.startswith(("```", "#", ">", "- ", "* ", "+ ")):
            return True
        prefix, _, suffix = stripped.partition(". ")
        return prefix.isdigit() and bool(suffix)

    def _render_header(self, conv: Dict[str, Any]) -> list[str]:
        lines: list[str] = []
        for field_name in self.text_output_config.header_fields:
            value = self._get_header_value(conv, field_name)
            if value is None:
                continue
            lines.append(f"{self._get_header_label(field_name)}: {value}")
        return lines

    def _get_header_label(self, field_name: str) -> str:
        if field_name == "id":
            return "ID"
        if field_name == "create_time":
            return "Created"
        if field_name == "update_time":
            return "Updated"
        if field_name == "conversation_id":
            return "Conversation ID"
        return field_name.replace("_", " ").title()

    def _get_header_value(self, conv: Dict[str, Any], field_name: str) -> Optional[str]:
        if field_name == "title":
            return get_conversation_title(conv)
        if field_name == "id":
            return get_display_conversation_id(conv)
        value = conv.get(field_name)
        if value is None:
            return None
        if field_name in {"create_time", "update_time"}:
            try:
                return format_timestamp(
                    float(value),
                    self.text_output_config.conversation_time_format,
                )
            except (TypeError, ValueError):
                return str(value)
        return str(value)


class JSONFormatter(BaseFormatter):
    """Structured JSON formatter."""

    def __init__(self, indent: int = 2, sort_keys: bool = True) -> None:
        """Initialize a JSON formatter.

        Args:
            indent: Number of spaces to indent JSON output.
            sort_keys: Whether to sort JSON object keys.
        """
        self.indent = indent
        self.sort_keys = sort_keys

    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a conversation as JSON.

        Args:
            conv: Conversation dictionary.

        Returns:
            JSON string output.
        """
        return json.dumps(
            conv,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=_json_default,
        )


FORMATTERS = {
    "txt": TextFormatter,
    "json": JSONFormatter,
}


def get_formatter(format_type: str, **kwargs: Any) -> BaseFormatter:
    """Get a formatter instance by type.

    Args:
        format_type: Formatter identifier.
        **kwargs: Formatter constructor keyword arguments.

    Returns:
        Configured formatter instance.

    Raises:
        ValueError: If the formatter type is unsupported.
    """
    if format_type not in FORMATTERS:
        raise ValueError(
            f"Unsupported format: {format_type}. Available: {list(FORMATTERS.keys())}"
        )
    formatter_kwargs = kwargs
    if format_type == "json":
        formatter_kwargs = {}
    formatter = FORMATTERS[format_type](**formatter_kwargs)
    logger.debug("Created formatter %s", type(formatter).__name__)
    return formatter
