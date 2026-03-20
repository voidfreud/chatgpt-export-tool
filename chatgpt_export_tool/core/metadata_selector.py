"""
Metadata field selection logic.

Provides MetadataSelector class for filtering conversation metadata
fields with glob pattern and partial matching support.
"""

import fnmatch
from typing import Any, Dict, List, Optional, Set

from .category_fields import METADATA_FIELDS


class MetadataSelector:
    """Handles metadata field inclusion/exclusion with glob pattern and partial matching.

    Supports:
    - Exact field names (e.g., "title", "model_slug")
    - Partial matching (e.g., "time" matches "create_time", "update_time")
    - Glob patterns (e.g., "model*" matches "model_slug", "model_name")
    - Wildcard "*" to match all metadata fields

    Attributes:
        include_fields: Set of field patterns to include.
        exclude_fields: Set of field patterns to exclude.
    """

    def __init__(
        self,
        include_fields: Optional[Set[str]] = None,
        exclude_fields: Optional[Set[str]] = None,
    ):
        """Initialize metadata selector.

        Args:
            include_fields: Set of field patterns to include.
            exclude_fields: Set of field patterns to exclude.
        """
        self.include_fields = include_fields or set()
        self.exclude_fields = exclude_fields or set()

    @classmethod
    def from_args(
        cls, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None
    ) -> "MetadataSelector":
        """Create MetadataSelector from CLI arguments.

        Args:
            include: List of field patterns to include.
            exclude: List of field patterns to exclude.

        Returns:
            Configured MetadataSelector instance.
        """
        include_fields = set(include) if include else set()
        exclude_fields = set(exclude) if exclude else set()
        return cls(include_fields=include_fields, exclude_fields=exclude_fields)

    def _matches_pattern(self, field_name: str, pattern: str) -> bool:
        """Check if a field name matches a pattern.

        Args:
            field_name: The actual field name to check.
            pattern: The pattern to match against (can be glob pattern).

        Returns:
            True if the field matches the pattern.
        """
        # Handle wildcard to match all
        if pattern == "*":
            return True

        # Handle exact match
        if field_name == pattern:
            return True

        # Handle partial match (field_name contains pattern)
        if pattern in field_name:
            return True

        # Handle glob patterns (e.g., "model*" matches "model_slug")
        if fnmatch.fnmatch(field_name, pattern):
            return True

        return False

    def _get_matching_fields(
        self, patterns: Set[str], available_fields: Set[str]
    ) -> Set[str]:
        """Get all fields that match any of the given patterns.

        Args:
            patterns: Set of field patterns to match.
            available_fields: Set of available field names.

        Returns:
            Set of field names that match at least one pattern.
        """
        matching = set()
        for pattern in patterns:
            for field in available_fields:
                if self._matches_pattern(field, pattern):
                    matching.add(field)
        return matching

    def filter_metadata(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter conversation metadata based on include/exclude patterns.

        This filters the message.metadata fields within the conversation.
        If no include patterns are specified, all fields are considered available.
        If no exclude patterns are specified, no fields are excluded.

        Args:
            conv: Conversation dictionary potentially containing message metadata.

        Returns:
            Filtered conversation dictionary with metadata filtered.
        """
        result = dict(conv)

        # Get all metadata fields from available METADATA_FIELDS
        available_metadata = set(METADATA_FIELDS.keys())

        # Determine which fields to include
        if self.include_fields:
            # If include is set, only include fields matching the include patterns
            include_matches = self._get_matching_fields(
                self.include_fields, available_metadata
            )
            fields_to_keep = include_matches
        else:
            # If no include specified, all available metadata fields are candidates
            fields_to_keep = available_metadata

        # Apply exclusions
        if self.exclude_fields:
            exclude_matches = self._get_matching_fields(
                self.exclude_fields, fields_to_keep
            )
            fields_to_keep -= exclude_matches

        # Filter top-level conversation fields (metadata lives at conversation level)
        for key in list(result.keys()):
            if key in available_metadata and key not in fields_to_keep:
                del result[key]

        # Also filter message metadata if present (nested metadata)
        if "mapping" in result:
            result["mapping"] = self._filter_mapping_metadata(
                result["mapping"], fields_to_keep
            )

        return result

    def _filter_mapping_metadata(
        self, mapping: Dict[str, Any], fields_to_keep: Set[str]
    ) -> Dict[str, Any]:
        """Filter metadata within message nodes of the mapping.

        Args:
            mapping: The conversation mapping dictionary.
            fields_to_keep: Set of metadata field names to keep.

        Returns:
            Filtered mapping dictionary.
        """
        if not isinstance(mapping, dict):
            return mapping

        filtered = {}
        for node_id, node in mapping.items():
            if isinstance(node, dict) and "message" in node:
                msg = dict(node["message"]) if node["message"] else {}
                if isinstance(msg, dict) and "metadata" in msg:
                    metadata = msg["metadata"]
                    if isinstance(metadata, dict):
                        filtered_metadata = {
                            k: v for k, v in metadata.items() if k in fields_to_keep
                        }
                        msg["metadata"] = filtered_metadata
                filtered[node_id] = node
            else:
                filtered[node_id] = node
        return filtered

    def get_included_fields(self) -> Set[str]:
        """Get the set of fields that will be included based on current patterns.

        Returns:
            Set of field names that match the include patterns.
        """
        if not self.include_fields:
            return set()
        available_metadata = set(METADATA_FIELDS.keys())
        return self._get_matching_fields(self.include_fields, available_metadata)

    def get_excluded_fields(self) -> Set[str]:
        """Get the set of fields that will be excluded based on current patterns.

        Returns:
            Set of field names that match the exclude patterns.
        """
        if not self.exclude_fields:
            return set()
        available_metadata = set(METADATA_FIELDS.keys())
        return self._get_matching_fields(self.exclude_fields, available_metadata)
