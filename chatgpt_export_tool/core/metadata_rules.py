"""Shared helpers for metadata field resolution."""

from typing import Iterable, Set

from .name_matching import match_names


def get_matching_metadata_fields(
    patterns: Iterable[str],
    available_fields: Set[str],
) -> Set[str]:
    """Resolve metadata fields matched by the provided patterns.

    Args:
        patterns: Metadata patterns to match.
        available_fields: Known metadata field names.

    Returns:
        Matching metadata fields.
    """
    return match_names(patterns, available_fields)


def resolve_metadata_fields_to_keep(
    include_fields: Set[str],
    exclude_fields: Set[str],
    available_fields: Set[str],
) -> Set[str]:
    """Resolve the final metadata field set to keep.

    Args:
        include_fields: Metadata include patterns.
        exclude_fields: Metadata exclude patterns.
        available_fields: Known metadata field names.

    Returns:
        Metadata fields to retain.
    """
    if include_fields:
        fields_to_keep = get_matching_metadata_fields(include_fields, available_fields)
    else:
        fields_to_keep = set(available_fields)

    if exclude_fields:
        fields_to_keep -= get_matching_metadata_fields(exclude_fields, fields_to_keep)

    return fields_to_keep
