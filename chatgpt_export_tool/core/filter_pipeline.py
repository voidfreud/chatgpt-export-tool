"""Unified runtime filtering pipeline."""

from typing import Any, Dict, List, Optional

from .filter_builder import build_filter_result
from .filter_models import FilterConfig, FilterResult
from .field_selector import FieldSelector
from .metadata_selector import MetadataSelector
from .utils import get_logger
from .validators import ValidationResult

logger = get_logger()


class FilterPipeline:
    """Apply field and metadata filtering to conversations."""

    def __init__(
        self,
        field_selector: FieldSelector,
        metadata_selector: Optional[MetadataSelector] = None,
        validation: Optional[ValidationResult] = None,
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

    @classmethod
    def from_config(
        cls,
        config: FilterConfig,
        raise_on_invalid: bool = False,
    ) -> FilterResult:
        """Create selectors for a filter configuration.

        Args:
            config: Filter configuration.
            raise_on_invalid: Whether to raise on validation errors.

        Returns:
            Build result with selectors and validation state.
        """
        return build_filter_result(
            config=config,
            raise_on_invalid=raise_on_invalid,
            logger=logger,
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


__all__ = ["FilterConfig", "FilterPipeline", "FilterResult"]
