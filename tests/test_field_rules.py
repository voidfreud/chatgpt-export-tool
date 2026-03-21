"""Tests for atomic field-rule helpers."""

from chatgpt_export_tool.core.field_rules import (
    AUTHOR_FIELDS,
    MESSAGE_NESTED_FIELDS,
    categorize_fields,
    should_anchor_nested_fields,
    should_copy_nested_field,
)
from chatgpt_export_tool.core.field_spec import build_field_spec


def test_should_anchor_nested_fields_for_include_and_exclude() -> None:
    """Nested anchor rules should stay stable across modes."""
    include_spec = build_field_spec(mode="include", fields=["name"])
    exclude_spec = build_field_spec(mode="exclude", fields=["mapping"])

    assert should_anchor_nested_fields(
        include_spec, AUTHOR_FIELDS, include_exclude=True
    )
    assert should_anchor_nested_fields(
        exclude_spec,
        MESSAGE_NESTED_FIELDS,
        include_exclude=True,
    )
    assert not should_anchor_nested_fields(exclude_spec, AUTHOR_FIELDS)


def test_should_copy_nested_field_only_for_explicit_nested_targets() -> None:
    """Nested copy rules should only fire for explicitly targeted fields."""
    groups_spec = build_field_spec(mode="groups", groups=["message"])
    include_spec = build_field_spec(mode="include", fields=["title"])

    assert should_copy_nested_field(groups_spec, "author")
    assert should_copy_nested_field(groups_spec, "content")
    assert not should_copy_nested_field(include_spec, "author")


def test_categorize_fields_still_matches_existing_contract() -> None:
    """Unknown fields should be separated from known metadata names."""
    categorized = categorize_fields({"title", "author", "unknown_field"})

    assert categorized["conversation"] == ["title"]
    assert categorized["message"] == ["author"]
    assert categorized["metadata"] == []
    assert categorized["unknown"] == ["unknown_field"]
