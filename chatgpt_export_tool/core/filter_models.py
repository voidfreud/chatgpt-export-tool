"""Shared models for runtime filter configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from .field_selector import FieldSelector
from .metadata_selector import MetadataSelector
from .validators import ValidationResult

if TYPE_CHECKING:
    from .filter_pipeline import FilterPipeline


@dataclass
class FilterConfig:
    """Configuration for conversation filtering."""

    field_spec: str = "all"
    include_metadata: Optional[List[str]] = None
    exclude_metadata: Optional[List[str]] = None
    validate: bool = True


@dataclass
class FilterResult:
    """Result of building a runtime filter pipeline."""

    validation: Optional[ValidationResult] = None
    field_selector: Optional[FieldSelector] = None
    metadata_selector: Optional[MetadataSelector] = None
    applied_filters: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Whether validation passed or was not requested."""
        if self.validation is None:
            return True
        return self.validation.is_valid

    def get_warnings(self) -> List[str]:
        """Return validation warnings, if any."""
        if self.validation is None:
            return []
        return self.validation.warnings

    def build_pipeline(self) -> "FilterPipeline":
        """Build a filter pipeline from the prepared selectors.

        Returns:
            Configured filter pipeline.

        Raises:
            ValueError: If the field selector has not been created.
        """
        if self.field_selector is None:
            raise ValueError("Field selector is required to build a filter pipeline")

        from .filter_pipeline import FilterPipeline

        return FilterPipeline(
            field_selector=self.field_selector,
            metadata_selector=self.metadata_selector,
            validation=self.validation,
        )
