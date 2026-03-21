"""Streaming analysis aggregation for conversations."""

from typing import Any, Dict

from .transcript.access import iter_mapping_nodes, iter_messages


class AnalysisCollector:
    """Collect counts and field coverage while streaming conversations."""

    def __init__(self) -> None:
        """Initialize the collector state."""
        self._results: Dict[str, Any] = {
            "conversation_count": 0,
            "message_count": 0,
            "all_fields": set(),
            "min_date": None,
            "max_date": None,
        }

    def add_conversation(self, conversation: Dict[str, Any]) -> None:
        """Add one conversation to the analysis state.

        Args:
            conversation: Conversation dictionary.
        """
        self._results["conversation_count"] += 1
        self._results["all_fields"].update(conversation.keys())

        self._update_date_range(conversation.get("create_time"))
        self._collect_mapping_fields(conversation.get("mapping"))

    def to_dict(self) -> Dict[str, Any]:
        """Return the collected results as a plain dictionary.

        Returns:
            Analysis results.
        """
        results = dict(self._results)
        results["all_fields"] = set(self._results["all_fields"])
        return results

    @property
    def conversation_count(self) -> int:
        """Return the number of collected conversations."""
        return int(self._results["conversation_count"])

    def _update_date_range(self, create_time: Any) -> None:
        """Update the min/max conversation timestamps.

        Args:
            create_time: Conversation create timestamp.
        """
        if create_time is None:
            return

        if self._results["min_date"] is None or create_time < self._results["min_date"]:
            self._results["min_date"] = create_time
        if self._results["max_date"] is None or create_time > self._results["max_date"]:
            self._results["max_date"] = create_time

    def _collect_mapping_fields(self, mapping: Any) -> None:
        """Collect fields from mapping nodes and messages.

        Args:
            mapping: Conversation mapping object.
        """
        if not isinstance(mapping, dict) or not mapping:
            return

        for node in iter_mapping_nodes({"mapping": mapping}):
            self._results["all_fields"].update(node.keys())

        for message in iter_messages({"mapping": mapping}):
            self._results["message_count"] += 1
            self._results["all_fields"].update(message.keys())
            self._update_nested_fields(message, "author")
            self._update_nested_fields(message, "content")
            self._update_nested_fields(message, "metadata")

    def _update_nested_fields(self, message: Dict[str, Any], key: str) -> None:
        """Collect keys from a nested message dictionary field.

        Args:
            message: Message dictionary.
            key: Nested field name.
        """
        value = message.get(key)
        if isinstance(value, dict) and value:
            self._results["all_fields"].update(value.keys())
