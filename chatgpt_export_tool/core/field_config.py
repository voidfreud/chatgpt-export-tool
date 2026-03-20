"""
Field configuration and selection logic.

Provides flexible field filtering/selection for export operations.

This module re-exports from specialized modules for backward compatibility.
For direct imports, prefer:
    from chatgpt_export_tool.core.category_fields import CATEGORY_FIELDS, METADATA_FIELDS
    from chatgpt_export_tool.core.metadata_selector import MetadataSelector
    from chatgpt_export_tool.core.field_selector import FieldSelector
"""

# Re-export constants from category_fields for backward compatibility
from .category_fields import CATEGORY_FIELDS, METADATA_FIELDS

# Re-export classes from specialized modules for backward compatibility
from .metadata_selector import MetadataSelector
from .field_selector import FieldSelector

__all__ = [
    "CATEGORY_FIELDS",
    "METADATA_FIELDS", 
    "MetadataSelector",
    "FieldSelector",
]
