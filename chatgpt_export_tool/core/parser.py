"""
JSON parsing module for ChatGPT conversations.

Handles memory-efficient streaming parsing of large JSON files using ijson.
"""

from typing import Any, Dict, Set

import ijson

from chatgpt_export_tool.core.utils import format_size, get_file_size, get_logger

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
            - sample_conversation: Sample structure from first conversation
        """
        logger.debug(f"Starting JSON analysis for file: {self.filepath}")

        results: Dict[str, Any] = {
            "conversation_count": 0,
            "message_count": 0,
            "all_fields": set(),
            "sample_conversation": None,
            "min_date": None,
            "max_date": None,
        }

        with open(self.filepath, "rb") as f:
            logger.debug("Opened file, starting ijson streaming parse")
            conversations = ijson.items(f, "item")

            for conv in conversations:
                results["conversation_count"] += 1
                results["all_fields"].update(conv.keys())

                # Track date range from conversation create_time
                create_time = conv.get("create_time")
                if create_time is not None:
                    if results["min_date"] is None or create_time < results["min_date"]:
                        results["min_date"] = create_time
                    if results["max_date"] is None or create_time > results["max_date"]:
                        results["max_date"] = create_time

                # Count messages in mapping
                if "mapping" in conv and conv["mapping"]:
                    logger.debug(
                        f"Conversation {results['conversation_count']}: processing mapping with {len(conv['mapping'])} nodes"
                    )
                    for node_id, node in conv["mapping"].items():
                        results["all_fields"].update(node.keys())
                        if "message" in node and node["message"]:
                            results["message_count"] += 1
                            msg = node["message"]
                            results["all_fields"].update(msg.keys())
                            if "author" in msg and msg["author"]:
                                results["all_fields"].update(msg["author"].keys())
                            if "content" in msg and msg["content"]:
                                results["all_fields"].update(msg["content"].keys())
                            if "metadata" in msg and msg["metadata"]:
                                results["all_fields"].update(msg["metadata"].keys())

                # Store first conversation as sample
                if results["sample_conversation"] is None:
                    logger.debug(
                        f"Storing sample conversation structure (conversation 1)"
                    )
                    results["sample_conversation"] = {
                        "title": conv.get("title", "N/A"),
                        "has_mapping": "mapping" in conv,
                        "mapping_size": len(conv.get("mapping", {})),
                    }

                if verbose and results["conversation_count"] % 100 == 0:
                    logger.debug(
                        f"  Processed {results['conversation_count']} conversations..."
                    )

        logger.debug(
            f"Analysis complete: {results['conversation_count']} conversations, {results['message_count']} messages, {len(results['all_fields'])} unique fields"
        )
        return results

    def iterate_conversations(self, verbose: bool = False):
        """Iterate over conversations in the JSON file.

        Args:
            verbose: If True, print progress information.

        Yields:
            Each conversation dictionary.
        """
        logger.debug(f"Starting conversation iteration for file: {self.filepath}")

        with open(self.filepath, "rb") as f:
            conversations = ijson.items(f, "item")
            idx = -1
            for idx, conv in enumerate(conversations):
                if verbose and (idx + 1) % 100 == 0:
                    logger.debug(f"  Processed {idx + 1} conversations...")
                yield conv

        logger.debug(f"Completed iteration: yielded {idx + 1} conversations total")
