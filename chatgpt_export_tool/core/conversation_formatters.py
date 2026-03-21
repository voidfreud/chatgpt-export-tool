"""Conversation output formatters."""

import json
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict

from chatgpt_export_tool.core.conversation_access import (
    get_display_conversation_id,
    get_message_role,
    get_message_text,
    iter_messages,
)
from chatgpt_export_tool.core.utils import get_logger

logger = get_logger()


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

    def __init__(self, include_header: bool = True, indent: str = "  ") -> None:
        """Initialize a text formatter.

        Args:
            include_header: Whether to include headers in output.
            indent: Indentation string for nested dictionaries.
        """
        self.include_header = include_header
        self.indent = indent
        logger.debug(
            "Initialized TextFormatter with include_header=%s indent=%r",
            include_header,
            indent,
        )

    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a conversation as text.

        Args:
            conv: Conversation dictionary.

        Returns:
            Formatted conversation text.
        """
        lines = [
            "-" * 40,
            f"Title: {conv.get('title', 'N/A')}",
            f"ID: {get_display_conversation_id(conv)}",
            f"Created: {conv.get('create_time', 'N/A')}",
            "",
        ]

        mapping = conv.get("mapping")
        if isinstance(mapping, dict) and mapping:
            lines.append(f"Messages ({len(mapping)} nodes):")
            for message in iter_messages(conv):
                lines.append(
                    f"  [{get_message_role(message)}] {get_message_text(message)}"
                )

        lines.append("-" * 40)
        return "\n".join(lines)


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
    formatter = FORMATTERS[format_type](**kwargs)
    logger.debug("Created formatter %s", type(formatter).__name__)
    return formatter
