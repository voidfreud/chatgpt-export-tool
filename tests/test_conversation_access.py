"""Tests for atomic conversation-access helpers."""

from chatgpt_export_tool.core.conversation_access import (
    get_conversation_title,
    get_date_group_key,
    get_display_conversation_id,
    get_id_group_key,
    get_message_role,
    get_message_text,
    get_subject_group_key,
    iter_messages,
)


def test_conversation_identity_helpers_use_expected_fallbacks() -> None:
    """Conversation identity helpers should preserve the current fallback rules."""
    conversation = {"title": "", "_id": "mongo-1"}

    assert get_conversation_title(conversation) == "untitled"
    assert get_display_conversation_id(conversation) == "mongo-1"
    assert get_subject_group_key(conversation) == "untitled_mongo-1"
    assert get_id_group_key(conversation) == "mongo-1"


def test_get_date_group_key_returns_none_for_invalid_timestamp() -> None:
    """Date grouping helper should stay pure and return ``None`` on bad input."""
    assert get_date_group_key({"create_time": "bad"}) is None


def test_message_helpers_iterate_and_render_message_content() -> None:
    """Message access helpers should expose the same formatter-friendly data."""
    conversation = {
        "mapping": {
            "node-1": {
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"parts": ["Hello", "World"]},
                }
            }
        }
    }

    messages = list(iter_messages(conversation))

    assert len(messages) == 1
    assert get_message_role(messages[0]) == "assistant"
    assert get_message_text(messages[0]) == "Hello\nWorld"
