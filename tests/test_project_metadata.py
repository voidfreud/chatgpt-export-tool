"""Tests for project metadata helpers."""

from importlib.metadata import PackageNotFoundError

from chatgpt_export_tool.project_metadata import (
    UNKNOWN_VERSION,
    read_project_version,
)


def test_read_project_version_matches_package_version() -> None:
    """Project metadata should expose a usable version string."""
    version = read_project_version()

    assert isinstance(version, str)
    assert version


def test_read_project_version_returns_non_empty_string() -> None:
    """The reported version should always be a non-empty string."""
    version = read_project_version()

    assert isinstance(version, str)
    assert version
    assert "." in version


def test_read_project_version_falls_back_when_distribution_missing(
    monkeypatch,
) -> None:
    """Missing installed metadata should return the safe fallback version."""

    def _raise_missing(_: str) -> str:
        raise PackageNotFoundError

    monkeypatch.setattr("chatgpt_export_tool.project_metadata.version", _raise_missing)

    assert read_project_version() == UNKNOWN_VERSION
