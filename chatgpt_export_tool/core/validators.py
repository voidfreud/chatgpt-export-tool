"""Compatibility barrel for validation APIs."""

from typing import Optional

from .field_validation import FieldValidator
from .metadata_validation import validate_metadata_pattern, validate_metadata_patterns
from .validation_models import ValidationResult

_validator: Optional[FieldValidator] = None


def get_validator() -> FieldValidator:
    """Get the module-level `FieldValidator` singleton."""
    global _validator
    if _validator is None:
        _validator = FieldValidator()
    return _validator


def validate_field_spec(spec: str) -> ValidationResult:
    """Validate a field specification string.

    Args:
        spec: Field specification string to validate.

    Returns:
        Validation result.
    """
    return get_validator().validate_field_spec(spec)


__all__ = [
    "ValidationResult",
    "FieldValidator",
    "get_validator",
    "validate_field_spec",
    "validate_metadata_pattern",
    "validate_metadata_patterns",
]
