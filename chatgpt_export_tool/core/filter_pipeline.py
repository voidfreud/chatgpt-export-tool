"""
Unified filtering pipeline for chatgpt_export_tool.

Provides FilterPipeline that orchestrates field selection and
metadata filtering with a single, consistent interface.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .field_groups import FIELD_GROUP_MAPPING, FIELD_GROUPS
from .field_selector import FieldSelector
from .metadata_selector import MetadataSelector
from .validators import ValidationResult, get_validator

logger = logging.getLogger(__name__)


@dataclass
class FilterConfig:
    """Configuration for filtering operations.

    Attributes:
        field_spec: Field specification string (e.g., "include title,create_time").
        include_metadata: Metadata fields to include.
        exclude_metadata: Metadata fields to exclude.
        validate: Whether to validate input (default True).
    """

    field_spec: str = "all"
    include_metadata: Optional[List[str]] = None
    exclude_metadata: Optional[List[str]] = None
    validate: bool = True


@dataclass
class FilterResult:
    """Result of a filtering operation.

    Attributes:
        validation: Validation result if validated.
        field_selector: The FieldSelector instance used.
        metadata_selector: The MetadataSelector instance used.
        applied_filters: Description of filters that were applied.
    """

    validation: Optional[ValidationResult] = None
    field_selector: Optional[FieldSelector] = None
    metadata_selector: Optional[MetadataSelector] = None
    applied_filters: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (if validation was performed)."""
        if self.validation is None:
            return True
        return self.validation.is_valid

    def get_warnings(self) -> List[str]:
        """Get any warnings from validation."""
        if self.validation is None:
            return []
        return self.validation.warnings


class FilterPipeline:
    """Unified filtering pipeline for conversations.

    Orchestrates FieldSelector and MetadataSelector to provide
    a single interface for filtering conversations.

    Example:
        pipeline = FilterPipeline.from_config(FilterConfig(
            field_spec="include title,create_time",
            exclude_metadata=["model_slug"]
        ))

        filtered = pipeline.filter(conversation)
    """

    def __init__(
        self,
        field_selector: FieldSelector,
        metadata_selector: Optional[MetadataSelector] = None,
        validation: Optional[ValidationResult] = None,
    ) -> None:
        """Initialize pipeline with selectors.

        Args:
            field_selector: Configured FieldSelector.
            metadata_selector: Optional MetadataSelector.
            validation: Optional validation result.
        """
        self.field_selector = field_selector
        self.metadata_selector = metadata_selector
        self.validation = validation

    @classmethod
    def from_config(
        cls, config: FilterConfig, raise_on_invalid: bool = False
    ) -> FilterResult:
        """Create pipeline from FilterConfig.

        Args:
            config: Filter configuration.
            raise_on_invalid: If True, raise ValueError on invalid config.

        Returns:
            FilterResult containing pipeline and validation result.
        """
        result = FilterResult()
        validator = get_validator()

        # Validate if requested
        if config.validate:
            logger.debug(f"Validating field spec: {config.field_spec}")
            validation = validator.validate_field_spec(config.field_spec)
            result.validation = validation

            if not validation.is_valid and raise_on_invalid:
                raise ValueError(
                    f"Invalid field spec: {config.field_spec}. "
                    f"Errors: {validation.errors}"
                )

            # Log warnings
            for warning in validation.warnings:
                logger.warning(warning)

        # Create field selector (validation handled separately above)
        logger.debug(f"Creating FieldSelector with spec: {config.field_spec}")
        field_selector = FieldSelector.from_string(config.field_spec)
        result.field_selector = field_selector
        result.applied_filters.append(f"fields={config.field_spec}")

        # Create metadata selector if needed
        metadata_selector = None
        if config.include_metadata or config.exclude_metadata:
            logger.debug(
                f"Creating MetadataSelector: "
                f"include={config.include_metadata}, "
                f"exclude={config.exclude_metadata}"
            )
            metadata_selector = MetadataSelector.from_args(
                include=config.include_metadata,
                exclude=config.exclude_metadata,
            )
            result.metadata_selector = metadata_selector

            inc = config.include_metadata or []
            exc = config.exclude_metadata or []
            result.applied_filters.append(f"metadata: include={inc}, exclude={exc}")

        return result

    def filter(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Filter a conversation through the pipeline.

        Args:
            conversation: Conversation dictionary to filter.

        Returns:
            Filtered conversation dictionary.
        """
        logger.debug("Applying field selection")
        filtered = self.field_selector.filter_conversation(conversation)

        if self.metadata_selector:
            logger.debug("Applying metadata filtering")
            filtered = self.metadata_selector.filter_metadata(filtered)

        return filtered

    def filter_many(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter multiple conversations through the pipeline.

        Args:
            conversations: List of conversation dictionaries.

        Returns:
            List of filtered conversation dictionaries.
        """
        logger.debug(f"Filtering {len(conversations)} conversations")
        return [self.filter(conv) for conv in conversations]


__all__ = [
    "FilterConfig",
    "FilterResult",
    "FilterPipeline",
]
