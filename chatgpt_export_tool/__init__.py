"""Top-level package metadata for chatgpt_export_tool."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chatgpt-export-tool")
except PackageNotFoundError:  # pragma: no cover - source tree fallback
    __version__ = "unknown"

__all__ = ["__version__"]
