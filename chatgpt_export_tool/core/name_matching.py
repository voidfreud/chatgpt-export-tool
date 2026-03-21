"""Shared helpers for name and pattern matching."""

import fnmatch
from difflib import get_close_matches
from typing import Iterable, Set


def matches_name(name: str, pattern: str) -> bool:
    """Return whether a name matches a pattern.

    Args:
        name: Concrete field or metadata name.
        pattern: User-provided pattern.

    Returns:
        Whether the name matches the pattern.
    """
    if pattern == "*":
        return True
    if name == pattern:
        return True
    if pattern in name:
        return True
    return fnmatch.fnmatch(name, pattern)


def match_names(patterns: Iterable[str], available_names: Iterable[str]) -> Set[str]:
    """Resolve all names matched by one or more patterns.

    Args:
        patterns: Patterns to match.
        available_names: Names that may match.

    Returns:
        Matched names.
    """
    available = set(available_names)
    return {
        name
        for pattern in patterns
        for name in available
        if matches_name(name, pattern)
    }


def find_similar_names(
    name: str,
    available_names: Iterable[str],
    max_results: int = 3,
) -> list[str]:
    """Return close matches for a name.

    Args:
        name: Name to compare.
        available_names: Known names.
        max_results: Maximum number of suggestions.

    Returns:
        Similar names ordered by closeness.
    """
    return get_close_matches(
        name,
        list(available_names),
        n=max_results,
        cutoff=0.6,
    )
