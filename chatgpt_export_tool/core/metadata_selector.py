"""Metadata filtering for conversations."""

from typing import Any, Dict, List, Optional, Set

from .category_fields import METADATA_FIELDS
from .metadata_rules import resolve_metadata_fields_to_keep


class MetadataSelector:
    """Filter conversation metadata using include and exclude patterns."""

    def __init__(
        self,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None,
    ) -> None:
        """Initialize a metadata selector.

        Args:
            include_fields: Patterns to include.
            exclude_fields: Patterns to exclude.
        """
        self.include_fields = include_fields or set()
        self.exclude_fields = exclude_fields or set()

    @classmethod
    def from_args(
        cls,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> "MetadataSelector":
        """Create a metadata selector from CLI-style arguments.

        Args:
            include: Include patterns.
            exclude: Exclude patterns.

        Returns:
            Configured metadata selector.
        """
        return cls(
            include_fields=set(include or []),
            exclude_fields=set(exclude or []),
        )

    def filter_metadata(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter top-level and nested message metadata in place.

        Args:
            conv: Conversation dictionary.

        Returns:
            Filtered conversation dictionary.
        """
        fields_to_keep = resolve_metadata_fields_to_keep(
            self.include_fields,
            self.exclude_fields,
            set(METADATA_FIELDS.keys()),
        )

        for key in list(conv.keys()):
            if key in METADATA_FIELDS and key not in fields_to_keep:
                del conv[key]

        mapping = conv.get("mapping")
        if isinstance(mapping, dict):
            self._filter_mapping_metadata(mapping, fields_to_keep)

        return conv

    def _filter_mapping_metadata(
        self,
        mapping: Dict[str, Any],
        fields_to_keep: Set[str],
    ) -> None:
        """Filter metadata in message nodes in place.

        Args:
            mapping: Conversation mapping dictionary.
            fields_to_keep: Resolved metadata fields to keep.

        """
        for node in mapping.values():
            if not isinstance(node, dict):
                continue

            message = node.get("message")
            if not isinstance(message, dict):
                continue

            metadata = message.get("metadata")
            if isinstance(metadata, dict):
                message["metadata"] = {
                    key: value
                    for key, value in metadata.items()
                    if key in fields_to_keep
                }
