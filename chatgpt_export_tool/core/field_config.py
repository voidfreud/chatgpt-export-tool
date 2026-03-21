"""Compatibility barrel for legacy field/filter imports."""

from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS
from .field_groups import FIELD_GROUP_MAPPING, FIELD_GROUPS
from .field_selector import FieldSelector
from .filter_pipeline import FilterConfig, FilterPipeline
from .metadata_selector import MetadataSelector
from .validators import FieldValidator, ValidationResult, validate_field_spec

__all__ = [
    "FIELD_GROUPS",
    "FIELD_GROUP_MAPPING",
    "CATEGORY_FIELDS",
    "METADATA_FIELDS",
    "FieldSelector",
    "MetadataSelector",
    "FieldValidator",
    "ValidationResult",
    "validate_field_spec",
    "FilterPipeline",
    "FilterConfig",
]
