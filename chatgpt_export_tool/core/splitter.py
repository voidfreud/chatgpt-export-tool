"""
Conversation splitting logic.

Provides SplitMode enum and SplitProcessor for dividing
conversations into groups based on various criteria.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, List

from chatgpt_export_tool.core.parser import JSONParser
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
        logger.debug(f"SplitProcessor initialized with mode={mode.value}")

    def process(self) -> SplitResult:
        """Process all conversations and split according to mode.

        Returns:
            SplitResult with grouped conversations.
        """
        logger.info(f"Starting split processing with mode={self.mode.value}")
        groups: Dict[str, List[Dict[str, Any]]] = {}
        conversation_count = 0

        for conv in self.parser.iterate_conversations(verbose=self.logger.level <= 20):
            key = self._get_group_key(conv)
            logger.debug(
                f"Conversation '{conv.get('title', 'N/A')}' -> group key '{key}'"
            )

            if key not in groups:
                logger.debug(f"Creating new group: {key}")
                groups[key] = []
            groups[key].append(conv)
            conversation_count += 1

            if conversation_count % 100 == 0:
                logger.debug(f"Processed {conversation_count} conversations...")

        result = SplitResult(
            mode=self.mode,
            groups=groups,
            total_conversations=conversation_count,
            group_count=len(groups),
        )

        logger.info(
            f"Split complete: {result.total_conversations} conversations "
            f"into {result.group_count} groups"
        )
        return result

    def _get_group_key(self, conv: Dict[str, Any]) -> str:
        """Get the group key for a conversation based on split mode.

        Args:
            conv: Conversation dictionary.

        Returns:
            Group key string.
        """
        if self.mode == SplitMode.SINGLE:
            return "all"

        elif self.mode == SplitMode.SUBJECT:
            # Each conversation is its own group
            title = conv.get("title", "untitled")
            conv_id = conv.get("id", conv.get("_id", "unknown"))
            return f"{title}_{conv_id}"

        elif self.mode == SplitMode.DATE:
            # Group by creation date (daily)
            create_time = conv.get("create_time")
            if create_time is not None:
                try:
                    dt = datetime.fromtimestamp(float(create_time))
                    return dt.strftime("%Y-%m-%d")
                except (ValueError, OSError) as e:
                    logger.warning(f"Could not parse create_time {create_time}: {e}")
            return "unknown_date"

        elif self.mode == SplitMode.ID:
            # Group by conversation ID
            # conversation_id is the primary UUID used for API calls and sharing
            # id is a fallback, _id is the MongoDB ObjectId (least preferred)
            conv_id = conv.get("conversation_id", conv.get("id", conv.get("_id")))
            if conv_id is not None:
                return str(conv_id)
            logger.warning("Conversation has no ID field, using 'unknown_id'")
            return "unknown_id"

        return "all"

    @property
    def logger(self):
        """Property to access module logger (for verbose logging in iterate)."""
        return logger


__all__ = ["SplitMode", "SplitResult", "SplitProcessor"]
