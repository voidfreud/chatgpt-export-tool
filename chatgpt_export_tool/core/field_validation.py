"""Field-selection validation logic."""

import re
from typing import List, Set

from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS
from .field_groups import FIELD_GROUPS
from .field_spec import FIELD_SELECTION_MODES, parse_field_spec
from .name_matching import find_similar_names, match_names
from .validation_models import ValidationResult


class FieldValidator:
    """Validate field-related user input."""

    FIELD_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")

    def __init__(self) -> None:
        """Initialize the validator with the known field universe."""
        self.available_fields = self._build_available_fields()

    def _build_available_fields(self) -> Set[str]:
        fields: Set[str] = set()
        for category_fields in CATEGORY_FIELDS.values():
            fields.update(category_fields)
        fields.update(METADATA_FIELDS.keys())
        return fields

    def validate_field_name(self, field_name: str) -> ValidationResult:
        """Validate a single field name.

        Args:
            field_name: Field name to validate.

        Returns:
            Validation result.
        """
        result = ValidationResult()

        if not self.FIELD_NAME_PATTERN.match(field_name):
            result.add_error(
                f"Invalid field name format: '{field_name}'. "
                "Field names must start with letter/underscore and contain only "
                "alphanumeric characters, underscores, or dashes."
            )

        if field_name not in self.available_fields:
            result.add_warning(
                f"Unknown field: '{field_name}'. This field may be ignored."
            )
            similar = self.find_similar_fields(field_name)
            if similar:
                result.add_suggestion(f"Did you mean: {', '.join(similar)}?")

        return result

    def validate_field_names(self, field_names: List[str]) -> ValidationResult:
        """Validate multiple field names.

        Args:
            field_names: Field names to validate.

        Returns:
            Aggregated validation result.
        """
        result = ValidationResult()

        for name in field_names:
            result.merge(self.validate_field_name(name))
        return result

    def validate_pattern(self, pattern: str) -> ValidationResult:
        """Validate a field pattern.

        Args:
            pattern: Pattern to validate.

        Returns:
            Validation result.
        """
        result = ValidationResult()

        if not pattern or not pattern.strip():
            result.add_error("Empty pattern provided")
            return result

        if pattern == "*":
            return result

        matches = self._find_matching_fields(pattern)
        if not matches:
            result.add_warning(f"Pattern '{pattern}' matches no known fields")
            available_list = sorted(self.available_fields)
            sample = available_list[:10] if len(available_list) > 10 else available_list
            result.add_suggestion(
                f"Available fields include: {', '.join(sample)}"
                f"{'...' if len(available_list) > 10 else ''}"
            )

        return result

    def validate_group(self, group_name: str) -> ValidationResult:
        """Validate a field-group name.

        Args:
            group_name: Group name to validate.

        Returns:
            Validation result.
        """
        result = ValidationResult()
        if group_name not in FIELD_GROUPS:
            result.add_error(
                f"Unknown field group: '{group_name}'. "
                f"Valid groups are: {', '.join(FIELD_GROUPS)}"
            )
        return result

    def validate_groups(self, group_names: List[str]) -> ValidationResult:
        """Validate multiple field-group names.

        Args:
            group_names: Group names to validate.

        Returns:
            Aggregated validation result.
        """
        result = ValidationResult()

        for name in group_names:
            result.merge(self.validate_group(name))
        return result

    def validate_mode(self, mode: str) -> ValidationResult:
        """Validate a field-selection mode.

        Args:
            mode: Mode name.

        Returns:
            Validation result.
        """
        result = ValidationResult()
        if mode not in FIELD_SELECTION_MODES:
            result.add_error(
                f"Invalid mode: '{mode}'. Must be one of: {', '.join(FIELD_SELECTION_MODES)}"
            )
        return result

    def validate_field_spec(self, spec: str) -> ValidationResult:
        """Validate a complete field specification string.

        Args:
            spec: Field specification string.

        Returns:
            Validation result.
        """
        result = ValidationResult()

        if not spec or not spec.strip():
            result.add_error("Empty field specification")
            return result

        parsed_spec = parse_field_spec(spec)
        mode_result = self.validate_mode(parsed_spec.mode)
        result.merge(mode_result)

        if parsed_spec.mode in {"include", "exclude"}:
            if not parsed_spec.fields:
                result.add_error(
                    f"Mode '{parsed_spec.mode}' requires field names after mode"
                )
            else:
                result.merge(self.validate_field_names(parsed_spec.fields))
        elif parsed_spec.mode == "groups":
            if not parsed_spec.groups:
                result.add_error("Mode 'groups' requires group names after mode")
            else:
                result.merge(self.validate_groups(parsed_spec.groups))
        return result

    def find_similar_fields(self, field_name: str, max_results: int = 3) -> List[str]:
        """Find field names similar to the provided field name.

        Args:
            field_name: Field name to compare.
            max_results: Maximum number of suggestions.

        Returns:
            Similar field names.
        """
        return find_similar_names(
            field_name,
            self.available_fields,
            max_results=max_results,
        )

    def _find_matching_fields(self, pattern: str) -> Set[str]:
        """Find all fields matching a pattern.

        Args:
            pattern: Pattern to match.

        Returns:
            Matching field names.
        """
        return match_names([pattern], self.available_fields)
