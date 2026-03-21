"""Project metadata helpers."""

from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "chatgpt-export-tool"
UNKNOWN_VERSION = "0+unknown"


def read_project_version() -> str:
    """Read the installed package version when available."""
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return UNKNOWN_VERSION
