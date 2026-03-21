"""Metadata filtering for conversations."""

from copy import deepcopy
from typing import Any, Dict, List, Optional, Set

from .category_fields import METADATA_FIELDS
from .metadata_rules import (
    get_matching_metadata_fields,
    resolve_metadata_fields_to_keep,
)
from .validators import ValidationResult, validate_metadata_pattern


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
        """Filter top-level and nested message metadata.

        Args:
            conv: Conversation dictionary.

        Returns:
            Filtered conversation copy.
        """
        result = deepcopy(conv)
        fields_to_keep = resolve_metadata_fields_to_keep(
            self.include_fields,
            self.exclude_fields,
            set(METADATA_FIELDS.keys()),
        )

        for key in list(result.keys()):
            if key in METADATA_FIELDS and key not in fields_to_keep:
                del result[key]

        mapping = result.get("mapping")
        if isinstance(mapping, dict):
            result["mapping"] = self._filter_mapping_metadata(mapping, fields_to_keep)

        return result

    def get_included_fields(self) -> Set[str]:
        """Resolve included metadata fields.

        Returns:
            Included metadata field names.
        """
        if not self.include_fields:
            return set()
        return get_matching_metadata_fields(
            self.include_fields,
            set(METADATA_FIELDS.keys()),
        )

    def get_excluded_fields(self) -> Set[str]:
        """Resolve excluded metadata fields.

        Returns:
            Excluded metadata field names.
        """
        if not self.exclude_fields:
            return set()
        return get_matching_metadata_fields(
            self.exclude_fields,
            set(METADATA_FIELDS.keys()),
        )

    def validate(self) -> ValidationResult:
        """Validate configured include/exclude patterns.

        Returns:
            Validation result.
        """
        result = ValidationResult()

        for pattern in self.include_fields:
            result.merge(validate_metadata_pattern(pattern))

        for pattern in self.exclude_fields:
            result.merge(validate_metadata_pattern(pattern))
        return result

    def _filter_mapping_metadata(
        self,
        mapping: Dict[str, Any],
        fields_to_keep: Set[str],
    ) -> Dict[str, Any]:
        """Filter metadata in message nodes.

        Args:
            mapping: Conversation mapping dictionary.
            fields_to_keep: Resolved metadata fields to keep.

        Returns:
            Filtered mapping copy.
        """
        filtered_mapping: Dict[str, Any] = {}

        for node_id, node in mapping.items():
            if not isinstance(node, dict):
                filtered_mapping[node_id] = node
                continue

            node_copy = deepcopy(node)
            message = node_copy.get("message")
            if not isinstance(message, dict):
                filtered_mapping[node_id] = node_copy
                continue

            metadata = message.get("metadata")
            if isinstance(metadata, dict):
                message["metadata"] = {
                    key: value
                    for key, value in metadata.items()
                    if key in fields_to_keep
                }
            filtered_mapping[node_id] = node_copy

        return filtered_mapping
