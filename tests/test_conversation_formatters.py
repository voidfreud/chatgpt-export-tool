"""Tests for conversation text formatting."""

from chatgpt_export_tool.core.conversation_formatters import TextFormatter
from chatgpt_export_tool.core.runtime_config import TextOutputConfig, TranscriptConfig
from chatgpt_export_tool.core.utils import format_timestamp


def test_text_formatter_renders_human_readable_header_and_turn_timestamps() -> None:
    """Text formatting should render configured header fields and turn timestamps."""
    conversation = {
        "title": "Transcript",
        "id": "conv-1",
        "create_time": 1709337600.0,
        "current_node": "assistant",
        "mapping": {
            "user": {
                "parent": None,
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["question"]},
                    "create_time": 1709337600.0,
                },
            },
            "assistant": {
                "parent": "user",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["answer"]},
                    "create_time": 1709337660.0,
                },
            },
        },
    }

    formatter = TextFormatter(
        transcript_config=TranscriptConfig(),
        text_output_config=TextOutputConfig(
            include_header=True,
            header_fields=("title", "id", "create_time"),
            conversation_time_format="%Y-%m-%d %H:%M",
            turn_time_format="%H:%M",
        ),
    )

    output = formatter.format_conversation(conversation)

    assert "Title: Transcript" in output
    assert "ID: conv-1" in output
    assert f"Created: {format_timestamp(1709337600.0, '%Y-%m-%d %H:%M')}" in output
    assert f"User [{format_timestamp(1709337600.0, '%H:%M')}]\nquestion" in output
    assert (
        f"Assistant [{format_timestamp(1709337660.0, '%H:%M')}]\nanswer" in output
    )


def test_text_formatter_can_disable_header_and_turn_timestamps() -> None:
    """Formatting toggles should keep transcript output predictable."""
    conversation = {
        "current_node": "assistant",
        "mapping": {
            "user": {
                "parent": None,
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["question"]},
                    "create_time": 1709337600.0,
                },
            },
            "assistant": {
                "parent": "user",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["answer"]},
                    "create_time": 1709337660.0,
                },
            },
        },
    }

    formatter = TextFormatter(
        transcript_config=TranscriptConfig(include_turn_timestamps=False),
        text_output_config=TextOutputConfig(include_header=False),
    )

    output = formatter.format_conversation(conversation)

    assert "Title:" not in output
    assert "[00:" not in output
    assert "User\nquestion" in output
    assert "Assistant\nanswer" in output


def test_text_formatter_renders_context_as_preamble_not_chat_turn() -> None:
    """User-editable context should render before chat turns as transcript context."""
    conversation = {
        "title": "Transcript",
        "id": "conv-1",
        "current_node": "assistant",
        "mapping": {
            "context": {
                "parent": None,
                "message": {
                    "author": {"role": "user"},
                    "content": {
                        "content_type": "user_editable_context",
                        "user_profile": "profile",
                        "user_instructions": "instructions",
                    },
                    "metadata": {"is_visually_hidden_from_conversation": True},
                },
            },
            "user": {
                "parent": "context",
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

    output = TextFormatter().format_conversation(conversation)

    assert "Conversation Context" in output
    assert "User profile: profile" in output
    assert "User instructions: instructions" in output
    assert "User\nquestion" in output
    assert "Assistant\nanswer" in output
