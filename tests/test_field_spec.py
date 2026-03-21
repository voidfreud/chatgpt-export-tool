"""Tests for atomic field-spec parsing helpers."""

from chatgpt_export_tool.core.field_selector import FieldSelector
from chatgpt_export_tool.core.field_spec import (
    build_field_spec,
    parse_field_spec,
    split_csv,
)


def test_split_csv_strips_and_ignores_empty_items() -> None:
    """CSV parsing should normalize whitespace and empty segments."""
    assert split_csv(" title, create_time ,, mapping ") == [
        "title",
        "create_time",
        "mapping",
    ]


def test_parse_field_spec_all_and_none() -> None:
    """Simple modes should parse without explicit fields."""
    assert parse_field_spec("all").mode == "all"
    assert parse_field_spec("none").mode == "none"


def test_parse_field_spec_include_and_groups() -> None:
    """Structured field specs should preserve their arguments."""
    include_spec = parse_field_spec("include title,create_time")
    assert include_spec.mode == "include"
    assert include_spec.fields == ["title", "create_time"]
    assert include_spec.explicit_field_names == {"title", "create_time"}

    groups_spec = parse_field_spec("groups conversation,message")
    assert groups_spec.mode == "groups"
    assert groups_spec.groups == ["conversation", "message"]
    assert "title" in groups_spec.explicit_field_names
    assert "author" in groups_spec.explicit_field_names


def test_parse_field_spec_supports_shorthand_csv() -> None:
    """Shorthand CSV should normalize into include mode."""
    spec = parse_field_spec("title,create_time")
    assert spec.mode == "include"
    assert spec.fields == ["title", "create_time"]


def test_build_field_spec_keeps_explicit_fields_for_groups() -> None:
    """Explicit field names should resolve from named groups."""
    spec = build_field_spec(mode="groups", groups=["minimal"])
    assert spec.groups == ["minimal"]
    assert spec.explicit_field_names == {"title", "create_time", "message"}


def test_field_selector_from_spec_exposes_normalized_properties() -> None:
    """FieldSelector should preserve a normalized spec as its public surface."""
    spec = build_field_spec(mode="include", fields=["title", "create_time"])

    selector = FieldSelector.from_spec(spec)

    assert selector.mode == "include"
    assert selector.fields == ["title", "create_time"]
    assert selector.groups == []
    assert selector.explicit_field_names == {"title", "create_time"}
