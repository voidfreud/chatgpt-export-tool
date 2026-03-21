"""Conversation filtering over nested ChatGPT export structures."""

from copy import deepcopy
from typing import Any, Dict, Set

from .field_rules import (
    AUTHOR_FIELDS,
    CONTENT_FIELDS,
    MAPPING_NESTED_FIELDS,
    MESSAGE_NESTED_FIELDS,
    METADATA_FIELD_NAMES,
    should_anchor_nested_fields,
    should_copy_nested_field,
)
from .field_spec import FieldSpec


class ConversationFilter:
    """Apply a parsed field specification to nested conversation data."""

    def __init__(self, spec: FieldSpec) -> None:
        """Initialize the conversation filter.

        Args:
            spec: Parsed field specification.
        """
        self.spec = spec

    @property
    def explicit_field_names(self) -> Set[str]:
        """Return the explicit field names targeted by the filter."""
        return self.spec.explicit_field_names

    def get_selected_fields(self, all_fields: Set[str]) -> Set[str]:
        """Resolve selected fields for a given dictionary.

        Args:
            all_fields: Available field names in the current dictionary.

        Returns:
            Selected field names.
        """
        if self.spec.mode == "all":
            return set(all_fields)
        if self.spec.mode == "none":
            return set()
        if self.spec.mode == "include":
            return set(self.spec.fields) & all_fields
        if self.spec.mode == "exclude":
            return all_fields - set(self.spec.fields)
        if self.spec.mode == "groups":
            return self.explicit_field_names & all_fields
        return set(all_fields)

    def filter_conversation(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter a conversation, including nested mapping/message structures.

        Args:
            conv: Conversation dictionary.

        Returns:
            Filtered conversation dictionary.
        """
        if self.spec.mode == "all":
            return deepcopy(conv)
        if self.spec.mode == "none":
            return {}
        return self._filter_conversation_dict(conv)

    def _filter_conversation_dict(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        selected_keys = self.get_selected_fields(set(conv.keys()))
        if self._should_anchor_mapping() and "mapping" in conv:
            selected_keys.add("mapping")

        for key, value in conv.items():
            if key not in selected_keys:
                continue
            if key == "mapping" and isinstance(value, dict):
                if self._should_copy_nested_field("mapping"):
                    result[key] = deepcopy(value)
                    continue
                filtered_mapping = self._filter_mapping(value)
                if filtered_mapping:
                    result[key] = filtered_mapping
                continue
            result[key] = deepcopy(value)

        return result

    def _filter_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        filtered_mapping: Dict[str, Any] = {}

        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                continue

            selected_keys = self.get_selected_fields(set(node.keys()))
            if self._should_anchor_message() and "message" in node:
                selected_keys.add("message")

            filtered_node: Dict[str, Any] = {}
            for key, value in node.items():
                if key not in selected_keys:
                    continue
                if key == "message" and isinstance(value, dict):
                    if self._should_copy_nested_field("message"):
                        filtered_node[key] = deepcopy(value)
                        continue
                    filtered_message = self._filter_message(value)
                    if filtered_message:
                        filtered_node[key] = filtered_message
                    continue
                filtered_node[key] = deepcopy(value)

            if filtered_node:
                filtered_mapping[node_id] = filtered_node

        return filtered_mapping

    def _filter_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        filtered_message: Dict[str, Any] = {}
        selected_keys = self.get_selected_fields(set(message.keys()))

        if self._should_anchor_author() and "author" in message:
            selected_keys.add("author")
        if self._should_anchor_content() and "content" in message:
            selected_keys.add("content")
        if self._should_anchor_metadata() and "metadata" in message:
            selected_keys.add("metadata")

        for key, value in message.items():
            if key not in selected_keys:
                continue

            if key in {"author", "content", "metadata"} and isinstance(value, dict):
                self._assign_filtered_nested_value(filtered_message, key, value)
                continue

            filtered_message[key] = deepcopy(value)

        return filtered_message

    def _filter_nested_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        selected_keys = self.get_selected_fields(set(data.keys()))
        return {
            key: deepcopy(value) for key, value in data.items() if key in selected_keys
        }

    def _assign_filtered_nested_value(
        self,
        target: Dict[str, Any],
        key: str,
        value: Dict[str, Any],
    ) -> None:
        """Assign a nested dictionary field after applying copy/filter rules.

        Args:
            target: Target dictionary being built.
            key: Nested field name.
            value: Nested field dictionary.
        """
        if self._should_copy_nested_field(key):
            target[key] = deepcopy(value)
            return

        filtered_value = self._filter_nested_dict(value)
        if filtered_value:
            target[key] = filtered_value

    def _should_anchor_mapping(self) -> bool:
        return should_anchor_nested_fields(self.spec, MAPPING_NESTED_FIELDS)

    def _should_anchor_message(self) -> bool:
        return should_anchor_nested_fields(
            self.spec,
            MESSAGE_NESTED_FIELDS,
            include_exclude=True,
        )

    def _should_anchor_author(self) -> bool:
        return should_anchor_nested_fields(
            self.spec,
            AUTHOR_FIELDS,
            include_exclude=True,
        )

    def _should_anchor_content(self) -> bool:
        return should_anchor_nested_fields(
            self.spec,
            CONTENT_FIELDS,
            include_exclude=True,
        )

    def _should_anchor_metadata(self) -> bool:
        return should_anchor_nested_fields(
            self.spec,
            METADATA_FIELD_NAMES,
            include_exclude=True,
        )

    def _should_copy_nested_field(self, field_name: str) -> bool:
        return should_copy_nested_field(self.spec, field_name)
