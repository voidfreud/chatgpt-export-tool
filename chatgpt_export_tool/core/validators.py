"""
Centralized validation for chatgpt_export_tool.

Provides validation functions and classes for field names,
patterns, modes, and user input sanitization.

All validation in one place with consistent error handling
and helpful suggestions for users.
"""

import fnmatch
import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from typing import List, Optional, Set

from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS
from .field_groups import FIELD_GROUP_MAPPING, FIELD_GROUPS


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether validation passed.
        errors: List of error messages.
        warnings: List of warning messages.
        suggestions: List of helpful suggestions.
    """

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add a helpful suggestion."""
        self.suggestions.append(message)

    def __str__(self) -> str:
        """String representation of validation result."""
        parts = []
        if self.errors:
            parts.append(f"Errors: {'; '.join(self.errors)}")
        if self.warnings:
            parts.append(f"Warnings: {'; '.join(self.warnings)}")
        if self.suggestions:
            parts.append(f"Suggestions: {'; '.join(self.suggestions)}")
        return " ".join(parts) if parts else "Valid"


class FieldValidator:
    """Validates field-related user input.

    Provides methods to validate:
    - Field names against known categories
    - Field patterns (glob, partial, exact)
    - Field group names
    - Selection modes

    Attributes:
        available_fields: Set of known field names.
        known_categories: Set of known category names.
    """

    # Pattern for valid field names: alphanumeric, underscore, dash
    FIELD_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_-]*$")

    def __init__(self) -> None:
        """Initialize validator with known fields."""
        self.available_fields = self._build_available_fields()
        self.known_categories = set(CATEGORY_FIELDS.keys())

    def _build_available_fields(self) -> Set[str]:
        """Build set of all available field names."""
        fields: Set[str] = set()
        for cat_fields in CATEGORY_FIELDS.values():
            fields.update(cat_fields)
        fields.update(METADATA_FIELDS.keys())
        return fields

    def validate_field_name(self, field_name: str) -> ValidationResult:
        """Validate a single field name.

        Args:
            field_name: Field name to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()

        # Check format
        if not self.FIELD_NAME_PATTERN.match(field_name):
            result.add_error(
                f"Invalid field name format: '{field_name}'. "
                f"Field names must start with letter/underscore and contain only "
                f"alphanumeric characters, underscores, or dashes."
            )

        # Check if known (only warn, don't error - may be custom fields)
        if field_name not in self.available_fields:
            result.add_warning(
                f"Unknown field: '{field_name}'. This field may be ignored."
            )
            # Suggest similar fields
            similar = self._find_similar_fields(field_name)
            if similar:
                result.add_suggestion(f"Did you mean: {', '.join(similar)}?")

        return result

    def validate_field_names(self, field_names: List[str]) -> ValidationResult:
        """Validate multiple field names.

        Args:
            field_names: List of field names to validate.

        Returns:
            Aggregated ValidationResult.
        """
        result = ValidationResult()

        for name in field_names:
            field_result = self.validate_field_name(name)
            result.errors.extend(field_result.errors)
            result.warnings.extend(field_result.warnings)
            result.suggestions.extend(field_result.suggestions)

        if result.errors:
            result.is_valid = False

        return result

    def validate_pattern(self, pattern: str) -> ValidationResult:
        """Validate a field pattern (glob, partial, exact).

        Args:
            pattern: Pattern to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()

        # Empty pattern
        if not pattern or not pattern.strip():
            result.add_error("Empty pattern provided")
            return result

        # Wildcard is always valid
        if pattern == "*":
            return result

        # Try to find matches
        matches = self._find_matching_fields(pattern)

        if not matches:
            result.add_warning(f"Pattern '{pattern}' matches no known fields")
            # Show some available fields as suggestion
            available_list = sorted(self.available_fields)
            sample = available_list[:10] if len(available_list) > 10 else available_list
            result.add_suggestion(
                f"Available fields include: {', '.join(sample)}{'...' if len(available_list) > 10 else ''}"
            )

        return result

    def validate_group(self, group_name: str) -> ValidationResult:
        """Validate a field group name.

        Args:
            group_name: Group name to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()

        if group_name not in FIELD_GROUPS:
            result.add_error(
                f"Unknown field group: '{group_name}'. "
                f"Valid groups are: {', '.join(FIELD_GROUPS)}"
            )

        return result

    def validate_groups(self, group_names: List[str]) -> ValidationResult:
        """Validate multiple field group names.

        Args:
            group_names: List of group names to validate.

        Returns:
            Aggregated ValidationResult.
        """
        result = ValidationResult()

        for name in group_names:
            group_result = self.validate_group(name)
            result.errors.extend(group_result.errors)
            result.warnings.extend(group_result.warnings)

        if result.errors:
            result.is_valid = False

        return result

    def validate_mode(self, mode: str) -> ValidationResult:
        """Validate a selection mode.

        Args:
            mode: Mode to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()
        valid_modes = ["all", "none", "include", "exclude", "groups"]

        if mode not in valid_modes:
            result.add_error(
                f"Invalid mode: '{mode}'. Must be one of: {', '.join(valid_modes)}"
            )

        return result

    def validate_field_spec(self, spec: str) -> ValidationResult:
        """Validate a complete field specification string.

        Parses and validates specs like:
        - "all"
        - "include title,create_time"
        - "exclude model_slug"
        - "groups message,minimal"

        Args:
            spec: Field specification string.

        Returns:
            ValidationResult with any errors or warnings.
        """
        result = ValidationResult()

        if not spec or not spec.strip():
            result.add_error("Empty field specification")
            return result

        parts = spec.split()
        mode = parts[0]

        # Validate mode
        mode_result = self.validate_mode(mode)
        result.errors.extend(mode_result.errors)

        # Validate mode-specific arguments
        if mode in ("include", "exclude"):
            if len(parts) < 2:
                result.add_error(f"Mode '{mode}' requires field names after mode")
            else:
                fields = parts[1].split(",")
                field_result = self.validate_field_names(fields)
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)
                result.suggestions.extend(field_result.suggestions)

        elif mode == "groups":
            if len(parts) < 2:
                result.add_error("Mode 'groups' requires group names after mode")
            else:
                groups = parts[1].split(",")
                group_result = self.validate_groups(groups)
                result.errors.extend(group_result.errors)
                result.warnings.extend(group_result.warnings)

        elif mode_result.is_valid:
            # Mode is valid but not include/exclude/groups
            # This handles "all" and "none" which need no further args
            pass
        else:
            # Unknown mode - for backward compat, treat as comma-separated fields
            fields = spec.split(",")
            if fields:
                field_result = self.validate_field_names(fields)
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)

        if result.errors:
            result.is_valid = False

        return result

    def _find_similar_fields(self, field_name: str, max_results: int = 3) -> List[str]:
        """Find fields similar to the given field name.

        Args:
            field_name: Field name to find matches for.
            max_results: Maximum number of results to return.

        Returns:
            List of similar field names.
        """
        return get_close_matches(
            field_name,
            list(self.available_fields),
            n=max_results,
            cutoff=0.6,
        )

    def _find_matching_fields(self, pattern: str) -> Set[str]:
        """Find all fields matching the given pattern.

        Args:
            pattern: Pattern to match against.

        Returns:
            Set of matching field names.
        """
        matches: Set[str] = set()

        for field_name in self.available_fields:
            # Exact match
            if field_name == pattern:
                matches.add(field_name)
            # Partial match
            elif pattern in field_name:
                matches.add(field_name)
            # Glob match
            elif fnmatch.fnmatch(field_name, pattern):
                matches.add(field_name)

        return matches


# Module-level validator instance (singleton)
_validator: Optional[FieldValidator] = None


def get_validator() -> FieldValidator:
    """Get the module-level FieldValidator instance.

    Returns:
        Singleton FieldValidator instance.
    """
    global _validator
    if _validator is None:
        _validator = FieldValidator()
    return _validator


def validate_field_spec(spec: str) -> ValidationResult:
    """Validate a field specification string.

    Convenience function that uses the module-level validator.

    Args:
        spec: Field specification string to validate.

    Returns:
        ValidationResult with any errors or warnings.
    """
    return get_validator().validate_field_spec(spec)


def validate_metadata_pattern(pattern: str) -> ValidationResult:
    """Validate a metadata field pattern.

    Args:
        pattern: Metadata pattern to validate.

    Returns:
        ValidationResult with any errors or warnings.
    """
    result = ValidationResult()

    if not pattern or not pattern.strip():
        result.add_error("Empty metadata pattern")
        return result

    if pattern == "*":
        return result

    # Check if matches any known metadata field
    if pattern not in METADATA_FIELDS:
        result.add_warning(
            f"Pattern '{pattern}' matches no known metadata fields. "
            f"Known fields: {', '.join(sorted(METADATA_FIELDS.keys()))}"
        )

    return result


def validate_metadata_patterns(
    patterns: List[str], pattern_type: str = "include"
) -> ValidationResult:
    """Validate a list of metadata patterns.

    Args:
        patterns: List of patterns to validate.
        pattern_type: Type of pattern ("include" or "exclude") for messaging.

    Returns:
        Aggregated ValidationResult.
    """
    result = ValidationResult()

    for pattern in patterns:
        pattern_result = validate_metadata_pattern(pattern)
        result.errors.extend(pattern_result.errors)
        result.warnings.extend(pattern_result.warnings)

    if result.errors:
        result.is_valid = False

    return result


__all__ = [
    "ValidationResult",
    "FieldValidator",
    "get_validator",
    "validate_field_spec",
    "validate_metadata_pattern",
    "validate_metadata_patterns",
]
