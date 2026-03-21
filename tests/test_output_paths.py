"""Tests for output path planning helpers."""

from pathlib import Path

from chatgpt_export_tool.core.output.naming import FileNamer
from chatgpt_export_tool.core.output.paths import OutputPathResolver
from chatgpt_export_tool.core.splitter import SplitMode


def test_output_path_resolver_builds_date_paths() -> None:
    """Date split mode should place files in date directories."""
    resolver = OutputPathResolver(
        output_dir=Path("/exports"),
        format_type="txt",
        split_mode=SplitMode.DATE,
        file_namer=FileNamer(),
    )

    path = resolver.get_filepath({"title": "Test Conversation"}, "2024-03-01")

    assert path == Path("/exports/2024-03-01/Test_Conversation.txt")


def test_output_path_resolver_adds_suffix_for_collisions() -> None:
    """Collision resolution should remain deterministic."""
    resolver = OutputPathResolver(
        output_dir=Path("/exports"),
        format_type="txt",
        split_mode=SplitMode.SUBJECT,
        file_namer=FileNamer(),
    )

    original = resolver.get_filepath({"title": "Chat", "id": "123"}, "Chat_123")
    unique = resolver.get_unique_filepath(
        {"title": "Chat", "id": "123"},
        "Chat_123",
        used_paths={original},
    )

    assert unique == Path("/exports/Chat_123_2.txt")
