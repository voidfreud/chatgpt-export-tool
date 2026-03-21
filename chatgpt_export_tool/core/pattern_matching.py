"""Shared helpers for exact, substring, and wildcard field matching."""

import fnmatch
from collections.abc import Iterable
from typing import Set


def matches_pattern(field_name: str, pattern: str) -> bool:
    """Check whether a field name matches a user pattern.

    Args:
        field_name: Actual field name.
        pattern: Pattern to test.

    Returns:
        Whether the field matches the pattern.
    """
    if pattern == "*":
        return True
    if field_name == pattern:
        return True
    if pattern in field_name:
        return True
    return fnmatch.fnmatch(field_name, pattern)


def resolve_matching_fields(
    patterns: Iterable[str],
    available_fields: Set[str],
) -> Set[str]:
    """Resolve all fields matched by one or more patterns.

    Args:
        patterns: Patterns to match.
        available_fields: Candidate field names.

    Returns:
        Matched field names.
    """
    matching: Set[str] = set()
    for pattern in patterns:
        for field_name in available_fields:
            if matches_pattern(field_name, pattern):
                matching.add(field_name)
    return matching
