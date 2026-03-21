"""Tests for direct conversation-filter branches."""

from chatgpt_export_tool.core.conversation_filter import ConversationFilter
from chatgpt_export_tool.core.field_spec import FieldSpec, build_field_spec


def test_get_selected_fields_covers_all_modes() -> None:
    """Selected-field resolution should handle every mode explicitly."""
    all_fields = {"title", "mapping", "create_time"}

    assert (
        ConversationFilter(build_field_spec("all")).get_selected_fields(all_fields)
        == all_fields
    )
    assert (
        ConversationFilter(build_field_spec("none")).get_selected_fields(all_fields)
        == set()
    )
    assert ConversationFilter(
        build_field_spec("include", fields=["title", "missing"])
    ).get_selected_fields(all_fields) == {"title"}
    assert ConversationFilter(
        build_field_spec("exclude", fields=["mapping"])
    ).get_selected_fields(all_fields) == {"title", "create_time"}
    assert ConversationFilter(
        build_field_spec("groups", groups=["minimal"])
    ).get_selected_fields(all_fields) == {"title", "create_time"}


def test_filter_conversation_handles_all_and_none_shortcuts() -> None:
    """Conversation filtering should keep the short-circuit behavior."""
    conversation = {"title": "Alpha", "mapping": {"node": {"message": {"author": {}}}}}

    assert (
        ConversationFilter(build_field_spec("all")).filter_conversation(conversation)
        == conversation
    )
    assert (
        ConversationFilter(build_field_spec("none")).filter_conversation(conversation)
        == {}
    )


def test_filter_conversation_keeps_anchor_containers_for_nested_include() -> None:
    """Nested field selection should preserve the container path to the data."""
    conversation = {
        "title": "Alpha",
        "mapping": {
            "node-1": {
                "id": "node-1",
                "message": {
                    "author": {"role": "user", "name": "Alex"},
                    "content": {"parts": ["hello"], "content_type": "text"},
                    "metadata": {"model_slug": "gpt-4"},
                },
            }
        },
    }

    filtered = ConversationFilter(
        build_field_spec("include", fields=["role"])
    ).filter_conversation(conversation)

    assert filtered == {
        "mapping": {
            "node-1": {
                "message": {
                    "author": {"role": "user"},
                }
            }
        }
    }


def test_filter_conversation_copies_explicit_nested_fields_wholesale() -> None:
    """Explicitly selected nested containers should be deep-copied intact."""
    conversation = {
        "mapping": {
            "node-1": {
                "message": {
                    "author": {"role": "user", "name": "Alex"},
                    "content": {"parts": ["hello"], "content_type": "text"},
                }
            }
        }
    }

    filtered = ConversationFilter(
        build_field_spec("include", fields=["content"])
    ).filter_conversation(conversation)

    assert filtered["mapping"]["node-1"]["message"]["content"] == {
        "parts": ["hello"],
        "content_type": "text",
    }


def test_filter_conversation_copies_explicit_message_container_and_node_fields() -> (
    None
):
    """Explicit message selection should copy the whole message and other node fields."""
    conversation = {
        "mapping": {
            "node-1": {
                "id": "node-1",
                "message": {
                    "author": {"role": "user"},
                    "content": {"parts": ["hello"]},
                    "metadata": {"model_slug": "gpt-4"},
                },
            }
        }
    }

    filtered = ConversationFilter(
        build_field_spec("include", fields=["message", "id"])
    ).filter_conversation(conversation)

    assert filtered == conversation


def test_filter_mapping_skips_non_dict_nodes_and_empty_filtered_nodes() -> None:
    """Filtering should ignore invalid mapping nodes and empty results."""
    conversation = {
        "mapping": {
            "bad-node": "not-a-dict",
            "empty-node": {"id": "node-1"},
            "good-node": {
                "message": {
                    "author": {"role": "user"},
                }
            },
        }
    }

    filtered = ConversationFilter(
        build_field_spec("include", fields=["role"])
    ).filter_conversation(conversation)

    assert filtered == {
        "mapping": {
            "good-node": {
                "message": {
                    "author": {"role": "user"},
                }
            }
        }
    }


def test_filter_nested_dict_skips_empty_nested_results() -> None:
    """Empty nested dictionaries should not be assigned into the result."""
    conversation = {
        "mapping": {
            "node-1": {
                "message": {
                    "metadata": {"model_slug": "gpt-4"},
                    "author": {"role": "user"},
                }
            }
        }
    }

    filtered = ConversationFilter(
        build_field_spec("include", fields=["nonexistent"])
    ).filter_conversation(conversation)

    assert filtered == {}


def test_filter_message_anchors_content_and_metadata_in_exclude_mode() -> None:
    """Exclude mode should keep nested containers when they survive by exclusion."""
    conversation = {
        "mapping": {
            "node-1": {
                "message": {
                    "author": {"role": "user", "name": "Alex"},
                    "content": {"parts": ["hello"], "content_type": "text"},
                    "metadata": {"model_slug": "gpt-4", "message_type": "next"},
                }
            }
        }
    }

    filtered = ConversationFilter(
        build_field_spec("exclude", fields=["role", "message_type"])
    ).filter_conversation(conversation)

    assert filtered["mapping"]["node-1"]["message"]["author"] == {"name": "Alex"}
    assert filtered["mapping"]["node-1"]["message"]["content"] == {
        "parts": ["hello"],
        "content_type": "text",
    }
    assert filtered["mapping"]["node-1"]["message"]["metadata"] == {
        "model_slug": "gpt-4"
    }


def test_assign_filtered_nested_value_skips_empty_filtered_nested_value() -> None:
    """Nested values should be omitted entirely when filtering empties them out."""
    conversation = {
        "mapping": {
            "node-1": {
                "message": {
                    "metadata": {"model_slug": "gpt-4"},
                }
            }
        }
    }

    filtered_empty = ConversationFilter(
        build_field_spec("include", fields=["author"])
    ).filter_conversation(conversation)

    assert filtered_empty == {}


def test_get_selected_fields_falls_back_for_unknown_mode() -> None:
    """Unexpected modes should conservatively keep available fields."""
    filterer = ConversationFilter(FieldSpec(mode="unexpected"))

    assert filterer.get_selected_fields({"title", "mapping"}) == {"title", "mapping"}
