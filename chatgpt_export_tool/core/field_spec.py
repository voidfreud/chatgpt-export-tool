"""Field-spec parsing and normalization."""

from dataclasses import dataclass, field
from typing import List, Set

from .field_groups import FIELD_GROUP_MAPPING

FIELD_SELECTION_MODES = ("all", "none", "include", "exclude", "groups")


def split_csv(value: str) -> List[str]:
    """Split a comma-separated string into normalized items.

    Args:
        value: Raw comma-separated string.

    Returns:
        List of non-empty stripped items.
    """
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class FieldSpec:
    """Normalized field-selection specification."""

    mode: str
    fields: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    explicit_field_names: Set[str] = field(default_factory=set)


def build_field_spec(
    mode: str,
    fields: List[str] | None = None,
    groups: List[str] | None = None,
) -> FieldSpec:
    """Build a normalized field specification from explicit parts.

    Args:
        mode: Field-selection mode.
        fields: Explicit field names.
        groups: Explicit field groups.

    Returns:
        Parsed field specification.
    """
    normalized_fields = list(fields or [])
    normalized_groups = list(groups or [])

    if mode in {"all", "none"}:
        return FieldSpec(mode=mode)
    if mode in {"include", "exclude"}:
        return FieldSpec(
            mode=mode,
            fields=normalized_fields,
            explicit_field_names=set(normalized_fields),
        )
    if mode == "groups":
        explicit_field_names = {
            field_name
            for group_name in normalized_groups
            for field_name in FIELD_GROUP_MAPPING.get(group_name, [])
        }
        return FieldSpec(
            mode=mode,
            groups=normalized_groups,
            explicit_field_names=explicit_field_names,
        )

    return FieldSpec(
        mode="include",
        fields=normalized_fields,
        explicit_field_names=set(normalized_fields),
    )


def parse_field_spec(field_spec: str) -> FieldSpec:
    """Parse a field-spec string into a normalized structure.

    Args:
        field_spec: Field specification string.

    Returns:
        Parsed field specification.
    """
    parts = field_spec.split(maxsplit=1)
    if not parts:
        return build_field_spec(mode="all")

    mode = parts[0]
    argument = parts[1] if len(parts) > 1 else ""

    if mode == "all":
        return build_field_spec(mode="all")
    if mode == "none":
        return build_field_spec(mode="none")
    if mode == "include":
        return build_field_spec(mode="include", fields=split_csv(argument))
    if mode == "exclude":
        return build_field_spec(mode="exclude", fields=split_csv(argument))
    if mode == "groups":
        return build_field_spec(mode="groups", groups=split_csv(argument))

    return build_field_spec(mode="include", fields=split_csv(field_spec))
