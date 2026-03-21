"""Unified runtime filtering pipeline."""

from typing import Any, Dict, List, Optional

from .filter_models import FilterConfig
from .field_selector import FieldSelector
from .metadata_selector import MetadataSelector
from .logging_utils import get_logger
from .metadata_validation import validate_metadata_patterns
from .validators import ValidationResult, get_validator

logger = get_logger()


class FilterPipeline:
    """Apply field and metadata filtering to conversations."""

    def __init__(
        self,
        field_selector: FieldSelector,
        metadata_selector: Optional[MetadataSelector] = None,
        validation: Optional[ValidationResult] = None,
        applied_filters: Optional[List[str]] = None,
    ) -> None:
        """Initialize the pipeline.

        Args:
            field_selector: Conversation field selector.
            metadata_selector: Optional metadata selector.
            validation: Optional validation result.
        """
        self.field_selector = field_selector
        self.metadata_selector = metadata_selector
        self.validation = validation
        self.applied_filters = applied_filters or []

    @classmethod
    def from_config(
        cls,
        config: FilterConfig,
        raise_on_invalid: bool = False,
    ) -> "FilterPipeline":
        """Create a ready-to-use filter pipeline.

        Args:
            config: Filter configuration.
            raise_on_invalid: Whether to raise on validation errors.

        Returns:
            Configured filter pipeline.
        """
        validation: Optional[ValidationResult] = None
        if config.validate:
            validation = get_validator().validate_field_spec(config.field_spec)
            if not validation.is_valid and raise_on_invalid:
                raise ValueError(
                    f"Invalid field spec: {config.field_spec}. Errors: {validation.errors}"
                )
            for warning in validation.warnings:
                logger.warning(warning)

        metadata_selector: Optional[MetadataSelector] = None
        applied_filters = [f"fields={config.field_spec}"]

        if config.include_metadata or config.exclude_metadata:
            metadata_validation = ValidationResult()
            if config.include_metadata:
                metadata_validation.merge(
                    validate_metadata_patterns(config.include_metadata)
                )
            if config.exclude_metadata:
                metadata_validation.merge(
                    validate_metadata_patterns(config.exclude_metadata)
                )
            if not metadata_validation.is_valid and raise_on_invalid:
                raise ValueError(
                    f"Invalid metadata filters. Errors: {metadata_validation.errors}"
                )
            for warning in metadata_validation.warnings:
                logger.warning(warning)
            if validation is None:
                validation = metadata_validation
            else:
                validation.merge(metadata_validation)
            metadata_selector = MetadataSelector.from_args(
                include=config.include_metadata,
                exclude=config.exclude_metadata,
            )
            applied_filters.append(
                "metadata: include="
                f"{config.include_metadata or []}, exclude={config.exclude_metadata or []}"
            )

        return cls(
            field_selector=FieldSelector.from_string(config.field_spec),
            metadata_selector=metadata_selector,
            validation=validation,
            applied_filters=applied_filters,
        )

    def filter(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Filter a single conversation.

        Args:
            conversation: Conversation dictionary.

        Returns:
            Filtered conversation dictionary.
        """
        filtered = self.field_selector.filter_conversation(conversation)
        if self.metadata_selector is not None:
            filtered = self.metadata_selector.filter_metadata(filtered)
        return filtered

    def filter_many(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter multiple conversations.

        Args:
            conversations: Conversations to filter.

        Returns:
            Filtered conversations.
        """
        return [self.filter(conversation) for conversation in conversations]


__all__ = ["FilterConfig", "FilterPipeline"]
