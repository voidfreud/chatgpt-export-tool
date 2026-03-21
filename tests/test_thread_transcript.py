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


def test_transcript_helpers_cover_non_dict_and_fallback_content_shapes() -> None:
    """Transcript helpers should stay resilient to odd export payloads."""
    conversation = {
        "mapping": {
            "bad-node": "skip-me",
            "user": {
                "message": {
                    "author": "plain-user",
                    "content": "raw text payload",
                    "create_time": "bad-time",
                }
            },
            "assistant": {
                "message": {
                    "author": {},
                    "content": {"content_type": "text", "parts": "scalar-parts"},
                }
            },
        }
    }

    entries = list(
        iter_transcript_entries(
            conversation,
            TranscriptConfig(
                follow_current_branch=False,
                include_content_types=("str", "text"),
            ),
        )
    )

    assert [
        (entry.role, entry.content_type, entry.text, entry.timestamp)
        for entry in entries
    ] == [
        ("unknown", "str", "raw text payload", None),
        ("unknown", "text", "scalar-parts", None),
    ]


def test_transcript_policy_handles_unknown_roles_and_hidden_overrides() -> None:
    """Unknown roles should stay hidden unless explicitly forced by content type."""
    conversation = {
        "current_node": "weird",
        "mapping": {
            "weird": {
                "parent": None,
                "message": {
                    "author": {"role": "critic"},
                    "content": {
                        "content_type": "multimodal_text",
                        "parts": ["visible"],
                    },
                    "metadata": {"is_visually_hidden_from_conversation": True},
                },
            }
        },
    }

    hidden_entries = list(iter_transcript_entries(conversation, TranscriptConfig()))
    forced_entries = list(
        iter_transcript_entries(
            conversation,
            TranscriptConfig(
                include_content_types=("multimodal_text",),
                show_visually_hidden_content_types=("multimodal_text",),
            ),
        )
    )

    assert hidden_entries == []
    assert [
        (entry.role, entry.content_type, entry.text) for entry in forced_entries
    ] == [("critic", "multimodal_text", "visible")]


def test_transcript_policy_covers_remaining_role_and_content_type_branches() -> None:
    """System/tool/user/assistant content-type toggles should all behave explicitly."""
    conversation = {
        "current_node": "assistant-mm",
        "mapping": {
            "system": {
                "parent": None,
                "message": {
                    "author": {"role": "system"},
                    "content": {"content_type": "text", "parts": ["system"]},
                },
            },
            "tool": {
                "parent": "system",
                "message": {
                    "author": {"role": "tool"},
                    "content": {"content_type": "text", "parts": ["tool"]},
                },
            },
            "user-mm": {
                "parent": "tool",
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "multimodal_text",
                        "parts": ["user-mm"],
                    },
                },
            },
            "assistant-recap": {
                "parent": "user-mm",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "reasoning_recap",
                        "parts": ["recap"],
                    },
                },
            },
            "assistant-mm": {
                "parent": "assistant-recap",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "multimodal_text",
                        "parts": ["assistant-mm"],
                    },
                },
            },
        },
    }

    entries = list(
        iter_transcript_entries(
            conversation,
            TranscriptConfig(
                show_system_messages=True,
                show_tool_messages=True,
                show_reasoning_recap=True,
            ),
        )
    )

    assert [(entry.role, entry.content_type, entry.text) for entry in entries] == [
        ("system", "text", "system"),
        ("tool", "text", "tool"),
        ("user", "multimodal_text", "user-mm"),
        ("assistant", "reasoning_recap", "recap"),
        ("assistant", "multimodal_text", "assistant-mm"),
    ]


def test_transcript_branch_and_text_helpers_cover_fallback_edges() -> None:
    """Branch traversal and text extraction should cover remaining fallback edges."""
    cyclic_conversation = {
        "current_node": "a",
        "mapping": {
            "a": {"parent": "b", "message": None},
            "b": {
                "parent": "a",
                "message": {"author": {"role": "user"}, "content": {}},
            },
            "c": "skip",
        },
    }

    branch_messages = list(
        iter_branch_messages(cyclic_conversation, follow_current=True)
    )
    assert len(branch_messages) == 1

    assert (
        extract_message_text(
            {
                "content": {
                    "content_type": "text",
                    "parts": ["   ", ""],
                    "text": "fallback text",
                }
            }
        )
        == "fallback text"
    )
    assert (
        extract_message_text({"content": {"content_type": "text", "parts": []}}) == ""
    )
    assert (
        extract_message_text(
            {
                "content": {
                    "content_type": "user_editable_context",
                    "user_instructions": "instructions only",
                }
            }
        )
        == "User instructions: instructions only"
    )
    assert (
        extract_message_text(
            {
                "content": {
                    "content_type": "user_editable_context",
                    "user_profile": "profile only",
                }
            }
        )
        == "User profile: profile only"
    )
