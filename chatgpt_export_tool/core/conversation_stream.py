"""Streaming iteration helpers for conversation exports."""

from collections.abc import Iterator
from typing import Any, Dict

import ijson

from .utils import get_logger

logger = get_logger()


def iterate_conversations(
    filepath: str,
    verbose: bool = False,
) -> Iterator[Dict[str, Any]]:
    """Stream conversations from a ChatGPT export file.

    Args:
        filepath: JSON export path.
        verbose: Whether to log progress every 100 conversations.

    Yields:
        Conversation dictionaries from the top-level export array.
    """
    with open(filepath, "rb") as handle:
        conversations = ijson.items(handle, "item")
        index = -1
        for index, conversation in enumerate(conversations):
            if verbose and (index + 1) % 100 == 0:
                logger.debug("  Processed %s conversations...", index + 1)
            yield conversation

    logger.debug("Completed iteration: yielded %s conversations total", index + 1)
