"""
Field configuration and selection logic.

Provides flexible field filtering/selection for export operations.

This module re-exports from specialized modules for backward compatibility.
For direct imports, prefer:
    from chatgpt_export_tool.core.field_groups import FIELD_GROUPS, FIELD_GROUP_MAPPING
    from chatgpt_export_tool.core.validators import FieldValidator, validate_field_spec
    from chatgpt_export_tool.core.filter_pipeline import FilterPipeline, FilterConfig
    from chatgpt_export_tool.core.field_selector import FieldSelector
    from chatgpt_export_tool.core.metadata_selector import MetadataSelector
"""

# Re-export field groups
# Re-export category fields for backward compatibility
from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS
from .field_groups import FIELD_GROUP_MAPPING, FIELD_GROUPS

# Re-export selectors
from .field_selector import FieldSelector
from .filter_pipeline import FilterConfig, FilterPipeline
from .metadata_selector import MetadataSelector

# Re-export validators and pipeline
from .validators import FieldValidator, ValidationResult, validate_field_spec

__all__ = [
    # Field groups
    "FIELD_GROUPS",
    "FIELD_GROUP_MAPPING",
    # Category fields
    "CATEGORY_FIELDS",
    "METADATA_FIELDS",
    # Selectors
    "FieldSelector",
    "MetadataSelector",
    # Validators
    "FieldValidator",
    "ValidationResult",
    "validate_field_spec",
    # Pipeline
    "FilterPipeline",
    "FilterConfig",
]
