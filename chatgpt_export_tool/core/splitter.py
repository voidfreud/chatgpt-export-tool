"""Conversation splitting orchestration."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.split_keys import resolve_group_key
from chatgpt_export_tool.core.utils import get_logger

# Module-level logger for consistent naming across the codebase
logger = get_logger()


class SplitMode(Enum):
    """Split mode for export operations.

    Attributes:
        SINGLE: All conversations to one file (backward compatible).
        SUBJECT: Each conversation to its own file.
        DATE: Group conversations by creation date (daily folders).
        ID: Group conversations by their ID field.
    """

    SINGLE = "single"
    SUBJECT = "subject"
    DATE = "date"
    ID = "id"


@dataclass
class SplitResult:
    """Result of splitting conversations.

    Attributes:
        mode: The split mode used.
        groups: Dictionary mapping group key to list of conversations.
        total_conversations: Total conversations processed.
        group_count: Number of groups created.
    """

    mode: SplitMode
    groups: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    total_conversations: int = 0
    group_count: int = 0

    def __post_init__(self):
        """Calculate totals from groups if not explicitly set."""
        if self.total_conversations == 0 and self.groups:
            self.total_conversations = sum(len(convs) for convs in self.groups.values())
        if self.group_count == 0 and self.groups:
            self.group_count = len(self.groups)


class SplitProcessor:
    """Processes conversations and splits them according to mode.

    Example:
        >>> parser = JSONParser("data.json")
        >>> processor = SplitProcessor(parser, mode=SplitMode.DATE)
        >>> result = processor.process()
        >>> for date_folder, convs in result.groups.items():
        ...     print(f"{date_folder}: {len(convs)} conversations")
    """

    def __init__(self, parser: JSONParser, mode: SplitMode = SplitMode.SINGLE):
        """Initialize split processor.

        Args:
            parser: JSONParser instance for iterating conversations.
            mode: Split mode to use.
        """
        self.parser = parser
        self.mode = mode
        logger.debug("SplitProcessor initialized with mode=%s", mode.value)

    def process(self) -> SplitResult:
        """Process all conversations and split according to mode.

        Returns:
            SplitResult with grouped conversations.
        """
        logger.info("Starting split processing with mode=%s", self.mode.value)
        groups: Dict[str, List[Dict[str, Any]]] = {}
        conversation_count = 0

        for conv in self.parser.iterate_conversations(verbose=self.logger.level <= 20):
            key = self._get_group_key(conv)
            logger.debug(
                "Conversation %r -> group key %r",
                conv.get("title", "N/A"),
                key,
            )

            if key not in groups:
                logger.debug("Creating new group: %s", key)
                groups[key] = []
            groups[key].append(conv)
            conversation_count += 1

            if conversation_count % 100 == 0:
                logger.debug("Processed %s conversations...", conversation_count)

        result = SplitResult(
            mode=self.mode,
            groups=groups,
            total_conversations=conversation_count,
            group_count=len(groups),
        )

        logger.info(
            "Split complete: %s conversations into %s groups",
            result.total_conversations,
            result.group_count,
        )
        return result

    def _get_group_key(self, conv: Dict[str, Any]) -> str:
        """Get the group key for a conversation based on split mode.

        Args:
            conv: Conversation dictionary.

        Returns:
            Group key string.
        """
        return resolve_group_key(self.mode, conv, logger)

    @property
    def logger(self):
        """Property to access module logger (for verbose logging in iterate)."""
        return logger


__all__ = ["SplitMode", "SplitResult", "SplitProcessor"]
