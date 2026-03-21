"""Top-level package metadata for chatgpt_export_tool."""

from pathlib import Path
import re


def _read_version() -> str:
    """Read the package version from the project metadata."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', content, re.MULTILINE)
    if match is None:
        raise RuntimeError("Unable to determine package version from pyproject.toml")
    return match.group(1)


__version__ = _read_version()

__all__ = ["__version__"]
