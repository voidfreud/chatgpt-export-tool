"""Compatibility façade for nested conversation field selection."""

from typing import Any, Dict, List, Optional, Set

from .conversation_filter import ConversationFilter
from .field_rules import categorize_fields
from .field_spec import build_field_spec, parse_field_spec


class FieldSelector:
    """Compatibility wrapper around the parsed field-spec filter."""

    MODES = ["all", "none", "include", "exclude", "groups"]

    def __init__(
        self,
        mode: str,
        fields: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
    ) -> None:
        """Initialize a field selector.

        Args:
            mode: Selection mode.
            fields: Explicit fields for include/exclude modes.
            groups: Named groups for groups mode.

        Raises:
            ValueError: If the selector configuration is invalid.
        """
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.MODES}")

        self.mode = mode
        self.fields = fields or []
        self.groups = groups or []

        if mode in {"include", "exclude"} and not fields:
            raise ValueError(f"Mode '{mode}' requires fields list")
        if mode == "groups" and not groups:
            raise ValueError("Mode 'groups' requires groups list")

        self.spec = build_field_spec(
            mode=mode,
            fields=list(self.fields),
            groups=list(self.groups),
        )
        self._filter = ConversationFilter(self.spec)

    @classmethod
    def from_string(cls, field_spec: str) -> "FieldSelector":
        """Create a selector from a field-spec string.

        Args:
            field_spec: Field specification string.

        Returns:
            Configured field selector.
        """
        parsed_spec = parse_field_spec(field_spec)
        return cls(
            mode=parsed_spec.mode,
            fields=parsed_spec.fields,
            groups=parsed_spec.groups,
        )

    @property
    def explicit_field_names(self) -> Set[str]:
        """Return the explicit field names targeted by the selector."""
        return self._filter.explicit_field_names

    def get_selected_fields(self, all_fields: Set[str]) -> Set[str]:
        """Resolve the selected fields for a given dictionary.

        Args:
            all_fields: Available field names in the current dictionary.

        Returns:
            Selected field names.
        """
        return self._filter.get_selected_fields(all_fields)

    def filter_conversation(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter a conversation, including nested mapping/message structures.

        Args:
            conv: Conversation dictionary.

        Returns:
            Filtered conversation dictionary.
        """
        return self._filter.filter_conversation(conv)

    @staticmethod
    def categorize_fields(fields: Set[str]) -> Dict[str, List[str]]:
        """Categorize field names by hierarchical level."""
        return categorize_fields(fields)
