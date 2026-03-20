"""Tests for validators module."""

import pytest

from chatgpt_export_tool.core.field_groups import FIELD_GROUP_MAPPING, FIELD_GROUPS
from chatgpt_export_tool.core.validators import (
    FieldValidator,
    ValidationResult,
    validate_field_spec,
    validate_metadata_pattern,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_default_is_valid(self):
        """Test that default ValidationResult is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_marks_invalid(self):
        """Test that add_error marks result as invalid."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning_keeps_valid(self):
        """Test that add_warning doesn't mark as invalid."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.is_valid is True
        assert "Test warning" in result.warnings

    def test_add_suggestion(self):
        """Test adding suggestions."""
        result = ValidationResult()
        result.add_suggestion("Try this")
        assert "Try this" in result.suggestions

    def test_str_representation(self):
        """Test string representation."""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")
        result_str = str(result)
        assert "Error" in result_str
        assert "Warning" in result_str


class TestFieldValidator:
    """Test FieldValidator class."""

    def test_init_builds_available_fields(self):
        """Test that validator builds available fields."""
        validator = FieldValidator()
        assert len(validator.available_fields) > 0
        assert "title" in validator.available_fields
        assert "author" in validator.available_fields

    def test_validate_field_name_valid(self):
        """Test validating a known field name."""
        validator = FieldValidator()
        result = validator.validate_field_name("title")
        assert result.is_valid is True

    def test_validate_field_name_unknown(self):
        """Test validating an unknown field name."""
        validator = FieldValidator()
        result = validator.validate_field_name("unknown_field_xyz")
        assert result.is_valid is True  # Unknown is warning, not error
        assert len(result.warnings) > 0

    def test_validate_field_name_invalid_format(self):
        """Test validating field with invalid format."""
        validator = FieldValidator()
        result = validator.validate_field_name("123 invalid")
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_field_names_multiple(self):
        """Test validating multiple field names."""
        validator = FieldValidator()
        result = validator.validate_field_names(["title", "author", "invalid_field"])
        # invalid_field produces warning, not error
        assert result.is_valid is True

    def test_validate_pattern_exact(self):
        """Test validating exact pattern."""
        validator = FieldValidator()
        result = validator.validate_pattern("title")
        assert result.is_valid is True

    def test_validate_pattern_wildcard(self):
        """Test validating wildcard pattern."""
        validator = FieldValidator()
        result = validator.validate_pattern("*")
        assert result.is_valid is True

    def test_validate_pattern_unknown(self):
        """Test validating unknown pattern."""
        validator = FieldValidator()
        result = validator.validate_pattern("xyz_unknown")
        assert result.is_valid is True  # Unknown pattern is warning
        assert len(result.warnings) > 0

    def test_validate_pattern_empty(self):
        """Test validating empty pattern."""
        validator = FieldValidator()
        result = validator.validate_pattern("")
        assert result.is_valid is False
        assert "Empty pattern" in result.errors[0]

    def test_validate_group_valid(self):
        """Test validating valid group name."""
        validator = FieldValidator()
        result = validator.validate_group("conversation")
        assert result.is_valid is True

    def test_validate_group_invalid(self):
        """Test validating invalid group name."""
        validator = FieldValidator()
        result = validator.validate_group("invalid_group")
        assert result.is_valid is False
        assert "invalid_group" in result.errors[0]

    def test_validate_groups_multiple(self):
        """Test validating multiple group names."""
        validator = FieldValidator()
        result = validator.validate_groups(["conversation", "message"])
        assert result.is_valid is True

    def test_validate_groups_with_invalid(self):
        """Test validating mix of valid and invalid groups."""
        validator = FieldValidator()
        result = validator.validate_groups(["conversation", "invalid"])
        assert result.is_valid is False

    def test_validate_mode_valid(self):
        """Test validating valid modes."""
        validator = FieldValidator()
        for mode in ["all", "none", "include", "exclude", "groups"]:
            result = validator.validate_mode(mode)
            assert result.is_valid is True

    def test_validate_mode_invalid(self):
        """Test validating invalid mode."""
        validator = FieldValidator()
        result = validator.validate_mode("invalid_mode")
        assert result.is_valid is False

    def test_validate_field_spec_all(self):
        """Test validating 'all' spec."""
        validator = FieldValidator()
        result = validator.validate_field_spec("all")
        assert result.is_valid is True

    def test_validate_field_spec_include(self):
        """Test validating include spec."""
        validator = FieldValidator()
        result = validator.validate_field_spec("include title,author")
        assert result.is_valid is True

    def test_validate_field_spec_exclude(self):
        """Test validating exclude spec."""
        validator = FieldValidator()
        result = validator.validate_field_spec("exclude model_slug")
        assert result.is_valid is True

    def test_validate_field_spec_groups(self):
        """Test validating groups spec."""
        validator = FieldValidator()
        result = validator.validate_field_spec("groups conversation,message")
        assert result.is_valid is True

    def test_validate_field_spec_invalid_group(self):
        """Test validating spec with invalid group."""
        validator = FieldValidator()
        result = validator.validate_field_spec("groups invalid_group")
        assert result.is_valid is False

    def test_validate_field_spec_empty(self):
        """Test validating empty spec."""
        validator = FieldValidator()
        result = validator.validate_field_spec("")
        assert result.is_valid is False

    def test_find_similar_fields(self):
        """Test finding similar fields."""
        validator = FieldValidator()
        similar = validator._find_similar_fields("titel", max_results=3)
        # Should find "title"
        assert "title" in similar


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_get_validator_returns_singleton(self):
        """Test that get_validator returns singleton."""
        from chatgpt_export_tool.core.validators import get_validator

        v1 = get_validator()
        v2 = get_validator()
        assert v1 is v2

    def test_validate_field_spec_convenience(self):
        """Test validate_field_spec convenience function."""
        result = validate_field_spec("all")
        assert result.is_valid is True

    def test_validate_metadata_pattern_known(self):
        """Test validating known metadata pattern."""
        result = validate_metadata_pattern("title")
        assert result.is_valid is True

    def test_validate_metadata_pattern_unknown(self):
        """Test validating unknown metadata pattern."""
        result = validate_metadata_pattern("unknown_xyz")
        assert result.is_valid is True  # Warning, not error
        assert len(result.warnings) > 0

    def test_validate_metadata_pattern_empty(self):
        """Test validating empty metadata pattern."""
        result = validate_metadata_pattern("")
        assert result.is_valid is False


class TestFieldGroupsIntegration:
    """Test that validators work correctly with field_groups."""

    def test_validator_knows_field_groups(self):
        """Test that FieldValidator knows about FIELD_GROUPS."""
        validator = FieldValidator()
        for group in FIELD_GROUPS:
            result = validator.validate_group(group)
            assert result.is_valid is True

    def test_field_group_mapping_usable(self):
        """Test that FIELD_GROUP_MAPPING is usable."""
        assert "conversation" in FIELD_GROUP_MAPPING
        assert len(FIELD_GROUP_MAPPING["conversation"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
