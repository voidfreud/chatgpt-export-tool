"""Filesystem-safe filename generation."""

import re
from typing import Any, Optional

from .conversation_access import get_conversation_title


class FileNamer:
    """Generate safe, readable filenames."""

    INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    MAX_LENGTH = 200

    def __init__(self, max_length: int = MAX_LENGTH) -> None:
        """Initialize a file namer.

        Args:
            max_length: Maximum filename length.
        """
        self.max_length = max_length

    def sanitize(self, title: Optional[str]) -> str:
        """Sanitize text for filesystem-safe use.

        Args:
            title: Raw text.

        Returns:
            Sanitized filename stem.
        """
        if not title:
            return "untitled"

        sanitized = self.INVALID_CHARS.sub("_", title)
        sanitized = re.sub(r"_+", "_", sanitized)
        sanitized = sanitized.strip("_").strip()
        sanitized = sanitized.replace(" ", "_")

        if len(sanitized) > self.max_length:
            sanitized = sanitized[: self.max_length - 3] + "..."

        return sanitized or "untitled"

    def get_filename(self, stem: Any, extension: str = "txt") -> str:
        """Build a filename from a stem and extension.

        Args:
            stem: Filename stem or conversation dictionary.
            extension: File extension without the leading dot.

        Returns:
            Filename with extension.
        """
        if isinstance(stem, dict):
            stem = get_conversation_title(stem)
        return f"{self.sanitize(stem)}.{extension}"
