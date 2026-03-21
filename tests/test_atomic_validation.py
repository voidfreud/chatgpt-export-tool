"""Tests for the new atomic validation modules."""

from chatgpt_export_tool.core.field_validation import FieldValidator
from chatgpt_export_tool.core.metadata_validation import validate_metadata_patterns
from chatgpt_export_tool.core.validation_models import ValidationResult


def test_validation_result_module_is_stable() -> None:
    """ValidationResult should remain usable from the atomic module directly."""
    result = ValidationResult()
    result.add_error("boom")
    result.add_warning("heads up")

    assert result.is_valid is False
    assert "boom" in str(result)
    assert "heads up" in str(result)


def test_field_validator_uses_split_field_spec_parser() -> None:
    """Field-spec validation should work directly through the atomic validator."""
    validator = FieldValidator()

    shorthand = validator.validate_field_spec("title,create_time")
    groups = validator.validate_field_spec("groups message,minimal")

    assert shorthand.is_valid is True
    assert groups.is_valid is True


def test_metadata_pattern_aggregation_stays_valid() -> None:
    """Metadata pattern aggregation should keep warning-only semantics."""
    result = validate_metadata_patterns(["unknown_xyz", "*"])

    assert result.is_valid is True
    assert result.warnings
