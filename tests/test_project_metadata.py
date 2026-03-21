"""Tests for project metadata helpers."""

from chatgpt_export_tool.project_metadata import read_project_version


def test_read_project_version_matches_package_version() -> None:
    """Project metadata should expose the current package version."""
    assert read_project_version() == "0.1"


def test_read_project_version_returns_non_empty_string() -> None:
    """The reported version should always be a non-empty string."""
    version = read_project_version()

    assert isinstance(version, str)
    assert version
    assert "." in version
