"""Tests for conversation text formatting."""

from chatgpt_export_tool.core.config.runtime import TextOutputConfig, TranscriptConfig
from chatgpt_export_tool.core.output.formatters import TextFormatter
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
    assert "Turns: 2" in output
    assert f"User [{format_timestamp(1709337600.0, '%H:%M')}]:\n  question" in output
    assert f"Assistant [{format_timestamp(1709337660.0, '%H:%M')}]:\n  answer" in output


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
    assert "User:\n  question" in output
    assert "Assistant:\n  answer" in output


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
    assert "User:\n  question" in output
    assert "Assistant:\n  answer" in output


def test_text_formatter_compact_mode_renders_tighter_turns() -> None:
    """Compact layout should keep the first content line on the heading line."""
    conversation = {
        "current_node": "assistant",
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

    formatter = TextFormatter(
        text_output_config=TextOutputConfig(
            include_header=False,
            layout_mode="compact",
            include_turn_count_in_header=False,
        )
    )

    output = formatter.format_conversation(conversation)

    assert "User: question" in output
    assert "Assistant: answer" in output
    assert "\n---\n" not in output


def test_text_formatter_markdown_mode_and_artifact_cleanup() -> None:
    """Markdown headings and ChatGPT artifact cleanup should be configurable."""
    conversation = {
        "current_node": "assistant",
        "mapping": {
            "assistant": {
                "parent": None,
                "message": {
                    "author": {"role": "assistant"},
                    "content": {
                        "content_type": "text",
                        "parts": ["Answer citeturn0search1\n\nnavlistfoobar"],
                    },
                },
            },
        },
    }

    formatter = TextFormatter(
        text_output_config=TextOutputConfig(
            include_header=False,
            heading_style="markdown",
            include_turn_count_in_header=False,
        )
    )

    output = formatter.format_conversation(conversation)

    assert "## Assistant" in output
    assert "cite" not in output
    assert "navlist" not in output


def test_text_formatter_groups_consecutive_same_speaker_turns() -> None:
    """Consecutive entries from the same rendered speaker should merge into one block."""
    conversation = {
        "current_node": "assistant-2",
        "mapping": {
            "assistant-1": {
                "parent": None,
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["first"]},
                    "create_time": 1,
                },
            },
            "assistant-2": {
                "parent": "assistant-1",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["second"]},
                    "create_time": 1,
                },
            },
        },
    }

    output = TextFormatter(
        text_output_config=TextOutputConfig(include_header=False),
    ).format_conversation(conversation)

    assert output.count("Assistant [") == 1
    assert "  first" in output
    assert "  second" in output


def test_text_formatter_keeps_context_entries_out_of_turn_count() -> None:
    """Context preamble should not inflate the visible chat-turn count."""
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

    assert "Turns: 2" in output
