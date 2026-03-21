"""Tests for shared name-matching helpers."""

from chatgpt_export_tool.core.name_matching import (
    find_similar_names,
    match_names,
    matches_name,
)


def test_matches_name_supports_exact_substring_and_glob() -> None:
    """Matching semantics should stay consistent across callers."""
    assert matches_name("title", "title")
    assert matches_name("model_slug", "model")
    assert matches_name("plugin_ids", "plugin*")
    assert not matches_name("title", "author")


def test_match_names_resolves_across_multiple_patterns() -> None:
    """Multiple patterns should resolve to one deduplicated name set."""
    matched = match_names(
        patterns=["title", "model*"],
        available_names={"title", "model_slug", "plugin_ids"},
    )

    assert matched == {"title", "model_slug"}


def test_find_similar_names_returns_close_matches() -> None:
    """Similarity search should remain available for validation suggestions."""
    similar = find_similar_names("titel", {"title", "author", "content"})

    assert "title" in similar
