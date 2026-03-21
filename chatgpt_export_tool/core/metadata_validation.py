"""Metadata-pattern validation helpers."""

from typing import List

from .category_fields import METADATA_FIELDS
from .metadata_rules import get_matching_metadata_fields
from .validation_models import ValidationResult


def validate_metadata_pattern(pattern: str) -> ValidationResult:
    """Validate a metadata field pattern.

    Args:
        pattern: Metadata pattern to validate.

    Returns:
        Validation result.
    """
    result = ValidationResult()

    if not pattern or not pattern.strip():
        result.add_error("Empty metadata pattern")
        return result

    if pattern == "*":
        return result

    matches = get_matching_metadata_fields([pattern], set(METADATA_FIELDS))
    if not matches:
        result.add_warning(
            f"Pattern '{pattern}' matches no known metadata fields. "
            f"Known fields: {', '.join(sorted(METADATA_FIELDS.keys()))}"
        )

    return result


def validate_metadata_patterns(patterns: List[str]) -> ValidationResult:
    """Validate multiple metadata field patterns.

    Args:
        patterns: Metadata patterns to validate.

    Returns:
        Aggregated validation result.
    """
    result = ValidationResult()
    for pattern in patterns:
        result.merge(validate_metadata_pattern(pattern))
    return result
