"""Tests for split-key resolution helpers."""

from chatgpt_export_tool.core.output.split_keys import resolve_group_key


def test_resolve_group_key_subject_uses_title_and_id_fallbacks() -> None:
    """Subject split keys should remain readable and deterministic."""
    assert resolve_group_key("subject", {"title": "Chat", "id": "123"}) == "Chat_123"
    assert resolve_group_key("subject", {"_id": "abc"}) == "untitled_abc"


def test_resolve_group_key_date_handles_valid_and_missing_timestamps() -> None:
    """Date split keys should remain stable for valid and missing timestamps."""
    assert resolve_group_key("date", {"create_time": 1709294400.0}) == "2024-03-01"
    assert resolve_group_key("date", {}) == "unknown_date"


def test_resolve_group_key_id_prefers_conversation_id() -> None:
    """ID split keys should use the most specific conversation identifier."""
    assert (
        resolve_group_key(
            "id",
            {"conversation_id": "conv-1", "id": "legacy-1", "_id": "mongo-1"},
        )
        == "conv-1"
    )
    assert resolve_group_key("id", {}) == "unknown_id"
