"""Streaming JSON parsing for ChatGPT conversations."""

from typing import Any, Dict

import ijson

from chatgpt_export_tool.core.analysis_collector import AnalysisCollector
from chatgpt_export_tool.core.file_utils import get_file_size
from chatgpt_export_tool.core.logging_utils import get_logger
from chatgpt_export_tool.core.utils import format_size

# Module-level logger for consistent naming across the codebase
logger = get_logger()


class JSONParser:
    """Memory-efficient JSON parser for ChatGPT conversations.

    Uses ijson for streaming parsing to handle large files without
    loading them entirely into memory.
    """

    def __init__(self, filepath: str):
        """Initialize parser with file path.

        Args:
            filepath: Path to the JSON file to parse.
        """
        self.filepath = filepath

    def analyze(self, verbose: bool = False) -> Dict[str, Any]:
        """Analyze JSON file structure.

        Args:
            verbose: If True, print progress information.

        Returns:
            Dictionary containing analysis results with keys:
            - conversation_count: Number of conversations
            - message_count: Total message nodes
            - all_fields: Set of all unique field names
        """
        logger.debug("Starting JSON analysis for file: %s", self.filepath)
        collector = AnalysisCollector()

        with open(self.filepath, "rb") as f:
            logger.debug("Opened file, starting ijson streaming parse")
            conversations = ijson.items(f, "item")

            for conv in conversations:
                collector.add_conversation(conv)

                mapping = conv.get("mapping")
                if isinstance(mapping, dict) and mapping:
                    logger.debug(
                        "Conversation %s: processing mapping with %s nodes",
                        collector.conversation_count,
                        len(mapping),
                    )

                if verbose and collector.conversation_count % 100 == 0:
                    logger.debug(
                        "  Processed %s conversations...",
                        collector.conversation_count,
                    )

        results = collector.to_dict()
        logger.debug(
            "Analysis complete: %s conversations, %s messages, %s unique fields",
            results["conversation_count"],
            results["message_count"],
            len(results["all_fields"]),
        )
        return results

    def iterate_conversations(self, verbose: bool = False):
        """Iterate over conversations in the JSON file.

        Args:
            verbose: If True, print progress information.

        Yields:
            Each conversation dictionary.
        """
        logger.debug("Starting conversation iteration for file: %s", self.filepath)

        with open(self.filepath, "rb") as f:
            conversations = ijson.items(f, "item")
            idx = -1
            for idx, conv in enumerate(conversations):
                if verbose and (idx + 1) % 100 == 0:
                    logger.debug("  Processed %s conversations...", idx + 1)
                yield conv

        logger.debug("Completed iteration: yielded %s conversations total", idx + 1)


__all__ = [
    "JSONParser",
    "format_size",
    "get_file_size",
]
