"""
Output writing and file naming logic.

Handles writing formatted conversations to disk with
appropriate directory structure and file naming.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from chatgpt_export_tool.core.formatters import BaseFormatter, get_formatter
from chatgpt_export_tool.core.splitter import SplitMode
from chatgpt_export_tool.core.utils import get_logger

# Module-level logger for consistent naming across the codebase
logger = get_logger()


class FileNamer:
    """Handles sanitization and generation of filenames from conversations."""

    # Characters that are invalid in filenames across platforms
    INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
    MAX_LENGTH = 200

    def __init__(self, max_length: int = MAX_LENGTH):
        """Initialize file namer.

        Args:
            max_length: Maximum filename length.
        """
        self.max_length = max_length
        logger.debug(f"FileNamer initialized with max_length={max_length}")

    def sanitize(self, title: Optional[str]) -> str:
        """Sanitize conversation title for use as filename.

        Args:
            title: Original conversation title.

        Returns:
            Sanitized filename-safe string.
        """
        if not title:
            return "untitled"

        # Replace invalid characters with underscore
        sanitized = self.INVALID_CHARS.sub("_", title)
        # Collapse multiple underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        # Strip leading/trailing underscores and whitespace
        sanitized = sanitized.strip("_").strip()
        # Replace spaces with underscores for cleaner filenames
        sanitized = sanitized.replace(" ", "_")
        # Truncate if too long
        if len(sanitized) > self.max_length:
            sanitized = sanitized[: self.max_length - 3] + "..."

        result = sanitized or "untitled"
        logger.debug(f"sanitize('{title}') -> '{result}'")
        return result

    def get_filename(self, conv: Dict[str, Any], extension: str = "txt") -> str:
        """Get filename for a conversation.

        Args:
            conv: Conversation dictionary.
            extension: File extension (without dot).

        Returns:
            Sanitized filename with extension.
        """
        title = conv.get("title", "untitled")
        sanitized = self.sanitize(title)
        return f"{sanitized}.{extension}"


@dataclass
class WriteResult:
    """Result of a write operation.

    Attributes:
        files_written: Number of files written.
        directories_created: Number of directories created.
        total_bytes: Total bytes written.
        errors: List of error messages if any.
    """

    files_written: int = 0
    directories_created: int = 0
    total_bytes: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Write error: {error}")

    def merge(self, other: "WriteResult") -> None:
        """Merge another WriteResult into this one."""
        self.files_written += other.files_written
        self.directories_created += other.directories_created
        self.total_bytes += other.total_bytes
        self.errors.extend(other.errors)


class OutputWriter:
    """Writes formatted conversations to disk.

    Manages directory structure and file naming based on
    split mode and output configuration.

    Example:
        >>> writer = OutputWriter(
        ...     output_dir="output",
        ...     format_type="txt",
        ...     split_mode=SplitMode.DATE,
        ... )
        >>> result = writer.write_conversations(groups, formatter)
    """

    def __init__(
        self,
        output_dir: str = "output",
        format_type: str = "txt",
        split_mode: Optional[SplitMode] = None,
    ):
        """Initialize output writer.

        Args:
            output_dir: Base output directory.
            format_type: Output format (txt, json).
            split_mode: Split mode determining directory structure.
        """
        self.output_dir = Path(output_dir)
        self.format_type = format_type
        self.split_mode = split_mode
        self.file_namer = FileNamer()

        logger.debug(
            f"OutputWriter initialized: output_dir={output_dir}, "
            f"format_type={format_type}, split_mode={split_mode}"
        )

    def write_conversations(
        self,
        groups: Dict[str, List[Dict[str, Any]]],
        formatter: BaseFormatter,
    ) -> WriteResult:
        """Write grouped conversations to disk.

        Args:
            groups: Dictionary mapping group keys to conversation lists.
            formatter: Formatter instance for formatting conversations.

        Returns:
            WriteResult with statistics.
        """
        result = WriteResult()

        logger.info(f"Writing {len(groups)} groups to {self.output_dir}")

        for group_key, conversations in groups.items():
            logger.debug(
                f"Processing group '{group_key}' with {len(conversations)} conversations"
            )

            for conv in conversations:
                try:
                    filepath = self._get_filepath(conv, group_key)
                    bytes_written = self._write_single(conv, filepath, formatter)
                    result.files_written += 1
                    result.total_bytes += bytes_written
                    logger.debug(f"Wrote {bytes_written} bytes to {filepath}")
                except Exception as e:
                    error_msg = (
                        f"Error writing conversation '{conv.get('title', 'N/A')}': {e}"
                    )
                    result.add_error(error_msg)

        logger.info(
            f"Write complete: {result.files_written} files, "
            f"{result.directories_created} dirs, {result.total_bytes} bytes, "
            f"{len(result.errors)} errors"
        )
        return result

    def _get_filepath(self, conv: Dict[str, Any], group_key: str) -> Path:
        """Get the file path for a conversation.

        Args:
            conv: Conversation dictionary.
            group_key: Group key (for directory structure).

        Returns:
            Full file path.
        """
        # Determine directory based on split mode
        if self.split_mode == SplitMode.DATE:
            # Use date-based subdirectory
            dir_path = self.output_dir / group_key
        elif self.split_mode == SplitMode.SUBJECT:
            # Flat structure - files directly in output dir
            dir_path = self.output_dir
        else:
            # Single file mode - should not be used with this writer
            dir_path = self.output_dir

        # Get filename from conversation title
        filename = self.file_namer.get_filename(conv, self.format_type)

        return dir_path / filename

    def _ensure_directory(self, dir_path: Path) -> bool:
        """Ensure directory exists, create if needed.

        Args:
            dir_path: Directory path to ensure exists.

        Returns:
            True if directory was created, False if it already existed.
        """
        if dir_path.exists():
            return False
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {dir_path}")
        return True

    def _write_single(
        self, conv: Dict[str, Any], filepath: Path, formatter: BaseFormatter
    ) -> int:
        """Write a single conversation to disk.

        Args:
            conv: Conversation dictionary.
            filepath: Target file path.
            formatter: Formatter instance.

        Returns:
            Number of bytes written.
        """
        # Ensure parent directory exists
        parent = filepath.parent
        if self._ensure_directory(parent):
            logger.debug(f"Created directory structure for: {filepath}")

        # Format the conversation
        formatted = formatter.format_conversation(conv)

        # Ensure we write string content
        if isinstance(formatted, bytes):
            content = formatted.decode("utf-8")
        else:
            content = str(formatted)

        # Write to file
        with open(filepath, "w", encoding="utf-8") as f:
            bytes_written = f.write(content)

        logger.debug(f"Wrote {bytes_written} bytes to {filepath}")
        return bytes_written


__all__ = ["FileNamer", "WriteResult", "OutputWriter"]
