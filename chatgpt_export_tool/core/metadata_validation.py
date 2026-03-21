"""Metadata-pattern validation helpers."""

from typing import List

from .category_fields import METADATA_FIELDS
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

    if pattern not in METADATA_FIELDS:
        result.add_warning(
            f"Pattern '{pattern}' matches no known metadata fields. "
            f"Known fields: {', '.join(sorted(METADATA_FIELDS.keys()))}"
        )

    return result


def validate_metadata_patterns(
    patterns: List[str],
    pattern_type: str = "include",
) -> ValidationResult:
    """Validate multiple metadata field patterns.

    Args:
        patterns: Metadata patterns to validate.
        pattern_type: Unused compatibility parameter retained for callers.

    Returns:
        Aggregated validation result.
    """
    del pattern_type

    result = ValidationResult()
    for pattern in patterns:
        result.merge(validate_metadata_pattern(pattern))
    return result
