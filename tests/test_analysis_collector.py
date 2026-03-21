"""Tests for the streaming analysis collector."""

from chatgpt_export_tool.core.analysis_collector import AnalysisCollector


def test_analysis_collector_tracks_nested_message_fields() -> None:
    """Collector should gather counts and nested field names from one conversation."""
    collector = AnalysisCollector()
    collector.add_conversation(
        {
            "title": "Test",
            "create_time": 100.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["hello"]},
                        "metadata": {"model_slug": "gpt"},
                    }
                }
            },
        }
    )

    results = collector.to_dict()

    assert results["conversation_count"] == 1
    assert results["message_count"] == 1
    assert {"title", "mapping", "message", "role", "parts", "model_slug"} <= results[
        "all_fields"
    ]
