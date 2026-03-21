"""Shared read-only helpers for conversation structures."""

from datetime import datetime
from typing import Any, Dict, Iterator, Optional


def get_conversation_title(conversation: Dict[str, Any]) -> str:
    """Return a safe conversation title.

    Args:
        conversation: Conversation dictionary.

    Returns:
        Conversation title or ``untitled``.
    """
    title = conversation.get("title")
    if title in {None, ""}:
        return "untitled"
    return str(title)


def get_display_conversation_id(conversation: Dict[str, Any]) -> str:
    """Return the preferred identifier for display output.

    Args:
        conversation: Conversation dictionary.

    Returns:
        Conversation identifier or ``N/A``.
    """
    identifier = conversation.get("id", conversation.get("_id"))
    if identifier is None:
        return "N/A"
    return str(identifier)


def get_subject_group_key(conversation: Dict[str, Any]) -> str:
    """Return the split key for subject-based exports.

    Args:
        conversation: Conversation dictionary.

    Returns:
        Subject-mode group key.
    """
    identifier = conversation.get("id", conversation.get("_id", "unknown"))
    return f"{get_conversation_title(conversation)}_{identifier}"


def get_id_group_key(conversation: Dict[str, Any]) -> str:
    """Return the split key for ID-based exports.

    Args:
        conversation: Conversation dictionary.

    Returns:
        ID-mode group key.
    """
    identifier = conversation.get("conversation_id", conversation.get("id"))
    if identifier is None:
        identifier = conversation.get("_id")
    if identifier is None:
        return "unknown_id"
    return str(identifier)


def get_date_group_key(conversation: Dict[str, Any]) -> Optional[str]:
    """Return the split key for date-based exports, if parseable.

    Args:
        conversation: Conversation dictionary.

    Returns:
        Date key in ``YYYY-MM-DD`` format, or ``None`` when unavailable.
    """
    create_time = conversation.get("create_time")
    if create_time is None:
        return None

    try:
        return datetime.fromtimestamp(float(create_time)).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def iter_mapping_nodes(conversation: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Yield mapping nodes from a conversation.

    Args:
        conversation: Conversation dictionary.

    Yields:
        Mapping nodes as dictionaries.
    """
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return

    for node in mapping.values():
        if isinstance(node, dict):
            yield node


def iter_messages(conversation: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    """Yield message dictionaries from a conversation.

    Args:
        conversation: Conversation dictionary.

    Yields:
        Message dictionaries.
    """
    for node in iter_mapping_nodes(conversation):
        message = node.get("message")
        if isinstance(message, dict):
            yield message


def get_message_role(message: Dict[str, Any]) -> str:
    """Return a message author's role.

    Args:
        message: Message dictionary.

    Returns:
        Message role or ``unknown``.
    """
    author = message.get("author")
    if isinstance(author, dict):
        return str(author.get("role", "unknown"))
    return "unknown"


def get_message_text(message: Dict[str, Any]) -> str:
    """Return the readable text for a message.

    Args:
        message: Message dictionary.

    Returns:
        Joined content text.
    """
    content = message.get("content")
    if not isinstance(content, dict):
        return "" if content is None else str(content)

    parts = content.get("parts", [])
    if not isinstance(parts, list):
        return str(parts)
    return "\n".join(str(part) for part in parts)
