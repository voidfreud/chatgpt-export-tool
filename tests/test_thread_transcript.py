"""Tests for transcript extraction and visibility rules."""

from chatgpt_export_tool.core.runtime_config import TranscriptConfig
from chatgpt_export_tool.core.thread_transcript import (
    extract_message_text,
    iter_branch_messages,
    iter_transcript_entries,
)


def test_default_transcript_policy_keeps_user_text_thoughts_and_context() -> None:
    """Default transcript policy should keep the intended visible defaults."""
    conversation = {
        "current_node": "assistant-text",
        "mapping": {
            "root": {"parent": None, "message": None},
            "system": {
                "parent": "root",
                "message": {
                    "author": {"role": "system"},
                    "content": {"content_type": "text", "parts": ["system hidden"]},
                    "metadata": {"is_visually_hidden_from_conversation": True},
                },
            },
            "context": {
                "parent": "system",
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "user_editable_context",
                        "user_profile": "profile",
                        "user_instructions": "instructions",
                    },
                    "metadata": {
                        "is_visually_hidden_from_conversation": True,
                        "is_user_system_message": True,
                    },
                },
            },
            "user-text": {
                "parent": "context",
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["question"]},
                    "create_time": 10,
                },
            },
            "assistant-thoughts": {
                "parent": "user-text",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "thoughts", "parts": ["thinking"]},
                    "create_time": 11,
                },
            },
            "assistant-code": {
                "parent": "assistant-thoughts",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "code", "parts": ["search(...)"]},
                    "create_time": 12,
                },
            },
            "tool": {
                "parent": "assistant-code",
                "message": {
                    "author": {"role": "tool"},
                    "content": {"content_type": "text", "parts": ["tool output"]},
                    "create_time": 13,
                },
            },
            "assistant-text": {
                "parent": "tool",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["answer"]},
                    "create_time": 14,
                },
            },
        },
    }

    entries = list(iter_transcript_entries(conversation, TranscriptConfig()))

    assert [(entry.role, entry.content_type, entry.text) for entry in entries] == [
        (
            "user",
            "user_editable_context",
            "User profile: profile\nUser instructions: instructions",
        ),
        ("user", "text", "question"),
        ("assistant", "thoughts", "thinking"),
        ("assistant", "text", "answer"),
    ]


def test_transcript_policy_can_enable_assistant_code() -> None:
    """Transcript policy should be able to show hidden content types when enabled."""
    conversation = {
        "current_node": "assistant-code",
        "mapping": {
            "root": {"parent": None, "message": None},
            "user": {
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["question"]},
                },
            },
            "assistant-code": {
                "parent": "user",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "code", "parts": ["search(...)"]},
                },
            },
        },
    }

    entries = list(
        iter_transcript_entries(
            conversation,
            TranscriptConfig(show_assistant_code=True),
        )
    )

    assert [(entry.role, entry.content_type) for entry in entries] == [
        ("user", "text"),
        ("assistant", "code"),
    ]


def test_transcript_policy_compacts_user_editable_context_by_default() -> None:
    """User-editable context should stay visible without dominating the transcript."""
    conversation = {
        "current_node": "context",
        "mapping": {
            "root": {"parent": None, "message": None},
            "context": {
                "parent": "root",
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "user_editable_context",
                        "user_profile": "A" * 220,
                        "user_instructions": "B" * 220,
                    },
                    "metadata": {"is_visually_hidden_from_conversation": True},
                },
            },
        },
    }

    entry = list(iter_transcript_entries(conversation, TranscriptConfig()))[0]

    assert entry.content_type == "user_editable_context"
    assert "..." in entry.text
    assert len(entry.text) < 400


def test_transcript_policy_can_show_tool_text_but_hide_execution_output() -> None:
    """Content-type overrides should allow more granular transcript tuning."""
    conversation = {
        "current_node": "tool-exec",
        "mapping": {
            "root": {"parent": None, "message": None},
            "tool-text": {
                "parent": "root",
                "message": {
                    "author": {"role": "tool"},
                    "content": {"content_type": "text", "parts": ["status"]},
                },
            },
            "tool-exec": {
                "parent": "tool-text",
                "message": {
                    "author": {"role": "tool"},
                    "content": {
                        "content_type": "execution_output",
                        "parts": ["verbose output"],
                    },
                },
            },
        },
    }

    entries = list(
        iter_transcript_entries(
            conversation,
            TranscriptConfig(
                show_tool_messages=True,
                exclude_content_types=("execution_output",),
            ),
        )
    )

    assert [(entry.role, entry.content_type, entry.text) for entry in entries] == [
        ("tool", "text", "status")
    ]


def test_iter_branch_messages_falls_back_when_current_node_is_missing() -> None:
    """Broken current-node references should still yield mapping messages."""
    conversation = {
        "current_node": "missing-node",
        "mapping": {
            "user": {
                "parent": None,
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["question"]},
                },
            },
            "assistant": {
                "parent": "user",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["answer"]},
                },
            },
        },
    }

    messages = list(iter_branch_messages(conversation, follow_current=True))

    assert len(messages) == 2


def test_extract_message_text_uses_full_context_mode_when_requested() -> None:
    """User-editable context rendering should honor the configured mode."""
    message = {
        "content": {
            "content_type": "user_editable_context",
            "user_profile": "profile " * 50,
            "user_instructions": "instructions " * 50,
        }
    }

    text = extract_message_text(
        message,
        TranscriptConfig(
            user_editable_context_mode="full",
            user_editable_context_preview_chars=20,
        ),
    )

    assert "..." not in text
    assert "profile profile" in text
