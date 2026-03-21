"""Reusable field-selection rules and nested-field sets."""

from typing import Dict, List, Set

from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS
from .field_spec import FieldSpec

AUTHOR_FIELDS = set(CATEGORY_FIELDS["author"])
CONTENT_FIELDS = set(CATEGORY_FIELDS["content"])
METADATA_FIELD_NAMES = set(METADATA_FIELDS)
MESSAGE_NESTED_FIELDS = (
    set(CATEGORY_FIELDS["message"])
    | AUTHOR_FIELDS
    | CONTENT_FIELDS
    | METADATA_FIELD_NAMES
)
MAPPING_NESTED_FIELDS = set(CATEGORY_FIELDS["mapping"]) | MESSAGE_NESTED_FIELDS


def should_anchor_nested_fields(
    spec: FieldSpec,
    nested_fields: Set[str],
    include_exclude: bool = False,
) -> bool:
    """Decide whether a container must be kept to reach nested fields.

    Args:
        spec: Parsed field specification.
        nested_fields: Field names reachable within the nested container.
        include_exclude: Whether exclude mode should keep the container by default.

    Returns:
        Whether the container should be retained as an anchor.
    """
    if spec.mode == "exclude":
        return include_exclude
    if spec.mode not in {"include", "groups"}:
        return False
    return bool(spec.explicit_field_names & nested_fields)


def should_copy_nested_field(spec: FieldSpec, field_name: str) -> bool:
    """Whether a nested field should be copied wholesale instead of filtered.

    Args:
        spec: Parsed field specification.
        field_name: Nested field name.

    Returns:
        Whether to deep-copy the nested field directly.
    """
    return (
        spec.mode in {"include", "groups"} and field_name in spec.explicit_field_names
    )


def categorize_fields(fields: Set[str]) -> Dict[str, List[str]]:
    """Categorize field names by hierarchical level.

    Args:
        fields: Field names to categorize.

    Returns:
        Category-to-field mapping.
    """
    categorized: Dict[str, List[str]] = {
        "conversation": [],
        "mapping": [],
        "message": [],
        "author": [],
        "content": [],
        "metadata": [],
        "unknown": [],
    }

    for field in sorted(fields):
        for category, category_fields in CATEGORY_FIELDS.items():
            if field in category_fields:
                categorized[category].append(field)
                break
        else:
            if field in METADATA_FIELDS:
                categorized["metadata"].append(field)
            else:
                categorized["unknown"].append(field)

    return categorized
