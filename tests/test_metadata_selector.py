"""Tests for metadata selection behavior."""

from chatgpt_export_tool.core.metadata_selector import MetadataSelector


def test_metadata_selector_resolves_fields_to_keep_from_patterns() -> None:
    """Metadata selector should expose its resolved keep-set explicitly."""
    selector = MetadataSelector.from_args(include=["model*"], exclude=["plugin_ids"])

    fields = selector.resolve_fields_to_keep()

    assert "model_slug" in fields
    assert "plugin_ids" not in fields


def test_metadata_selector_filters_only_nested_message_metadata() -> None:
    """Metadata selection should mutate nested metadata dictionaries only."""
    conversation = {
        "title": "Example",
        "mapping": {
            "node": {
                "message": {
                    "metadata": {
                        "model_slug": "gpt",
                        "plugin_ids": ["x"],
                    }
                }
            }
        },
    }

    filtered = MetadataSelector.from_args(include=["model*"]).filter_metadata(
        conversation
    )

    assert filtered["title"] == "Example"
    assert filtered["mapping"]["node"]["message"]["metadata"] == {"model_slug": "gpt"}
