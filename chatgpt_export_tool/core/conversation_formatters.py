"""Conversation output formatters."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from chatgpt_export_tool.core.analysis_formatter import (
    AnalyzeConfig,
    format_analysis_text,
)
from chatgpt_export_tool.core.conversation_access import (
    get_display_conversation_id,
    get_message_role,
    get_message_text,
    iter_messages,
)
from chatgpt_export_tool.core.utils import get_logger

logger = get_logger()


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation.

        Args:
            data: Data to format.

        Returns:
            Formatted output string.
        """

    @abstractmethod
    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a single conversation.

        Args:
            conv: Conversation dictionary.

        Returns:
            Formatted conversation string.
        """


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

    def format(self, data: Any, analyze_config: AnalyzeConfig | None = None) -> str:
        """Format generic data as text.

        Args:
            data: Data to format.
            analyze_config: Optional configuration for analysis output.

        Returns:
            Formatted output string.
        """
        if isinstance(data, dict):
            if "conversation_count" in data and "message_count" in data:
                return self._format_analysis(data, analyze_config)
            return self._format_dict(data)
        if isinstance(data, list):
            return self._format_list(data)
        return str(data)

    def _format_analysis(
        self,
        results: Dict[str, Any],
        config: AnalyzeConfig | None = None,
    ) -> str:
        """Format analysis results.

        Args:
            results: Analysis results dictionary.
            config: Optional analysis formatting configuration.

        Returns:
            Formatted analysis output.
        """
        return format_analysis_text(results, config)

    def _format_dict(self, data: Dict[str, Any], level: int = 0) -> str:
        """Format a nested dictionary as text.

        Args:
            data: Dictionary to format.
            level: Current indentation level.

        Returns:
            Formatted dictionary output.
        """
        prefix = self.indent * level
        lines: List[str] = []

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: [{len(value)} items]")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return "\n".join(lines)

    def _format_list(self, data: List[Any]) -> str:
        """Format a list as text.

        Args:
            data: List to format.

        Returns:
            Formatted list output.
        """
        return "\n".join(f"[{index}] {item}" for index, item in enumerate(data))

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

    def format(self, data: Any) -> str:
        """Format arbitrary data as JSON.

        Args:
            data: Data to serialize.

        Returns:
            JSON string output.
        """
        return json.dumps(data, indent=self.indent, sort_keys=self.sort_keys)

    def format_conversation(self, conv: Dict[str, Any]) -> str:
        """Format a conversation as JSON.

        Args:
            conv: Conversation dictionary.

        Returns:
            JSON string output.
        """
        return self.format(conv)


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
