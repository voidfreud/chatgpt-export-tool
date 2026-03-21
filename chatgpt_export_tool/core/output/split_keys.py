"""Group-key policies for conversation splitting."""

from logging import Logger
from typing import Any, Dict

from chatgpt_export_tool.core.logging_utils import get_logger
from chatgpt_export_tool.core.transcript.access import (
    get_date_group_key,
    get_id_group_key,
    get_subject_group_key,
)


def resolve_group_key(
    mode: object,
    conversation: Dict[str, Any],
    logger: Logger | None = None,
) -> str:
    """Resolve the grouping key for a conversation and split mode.

    Args:
        mode: Split mode enum or string-like value.
        conversation: Conversation dictionary.
        logger: Logger used for warning paths.

    Returns:
        Group key string.
    """
    active_logger = logger or get_logger()
    mode_value = getattr(mode, "value", str(mode))

    if mode_value == "single":
        return "all"
    if mode_value == "subject":
        return _subject_group_key(conversation)
    if mode_value == "date":
        return _date_group_key(conversation, active_logger)
    if mode_value == "id":
        return _id_group_key(conversation, active_logger)
    return "all"


def _subject_group_key(conversation: Dict[str, Any]) -> str:
    """Build the grouping key for subject mode.

    Args:
        conversation: Conversation dictionary.

    Returns:
        Subject grouping key.
    """
    return get_subject_group_key(conversation)


def _date_group_key(conversation: Dict[str, Any], logger: Logger) -> str:
    """Build the grouping key for date mode.

    Args:
        conversation: Conversation dictionary.
        logger: Logger used for warning paths.

    Returns:
        Date grouping key.
    """
    date_key = get_date_group_key(conversation)
    if date_key is not None:
        return date_key

    create_time = conversation.get("create_time")
    if create_time is not None:
        logger.warning("Could not parse create_time %s", create_time)
    return "unknown_date"


def _id_group_key(conversation: Dict[str, Any], logger: Logger) -> str:
    """Build the grouping key for ID mode.

    Args:
        conversation: Conversation dictionary.
        logger: Logger used for warning paths.

    Returns:
        ID grouping key.
    """
    conversation_id = get_id_group_key(conversation)
    if conversation_id == "unknown_id":
        logger.warning("Conversation has no ID field, using 'unknown_id'")
    return conversation_id
