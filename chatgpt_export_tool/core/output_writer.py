"""Output writing and file naming logic."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from chatgpt_export_tool.core.conversation_formatters import BaseFormatter
from chatgpt_export_tool.core.file_naming import FileNamer
from chatgpt_export_tool.core.output_paths import OutputPathResolver
from chatgpt_export_tool.core.splitter import SplitMode
from chatgpt_export_tool.core.utils import get_logger

logger = get_logger()


@dataclass
class WriteResult:
    """Result of writing one or more export files."""

    files_written: int = 0
    directories_created: int = 0
    total_bytes: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Record a write error.

        Args:
            error: Error message.
        """
        self.errors.append(error)
        logger.error("Write error: %s", error)

    def merge(self, other: "WriteResult") -> None:
        """Merge another write result into this one.

        Args:
            other: Result to merge.
        """
        self.files_written += other.files_written
        self.directories_created += other.directories_created
        self.total_bytes += other.total_bytes
        self.errors.extend(other.errors)


class OutputWriter:
    """Write formatted conversations to disk."""

    def __init__(
        self,
        output_dir: str = "output",
        format_type: str = "txt",
        split_mode: Optional[SplitMode] = None,
    ) -> None:
        """Initialize an output writer.

        Args:
            output_dir: Base output directory.
            format_type: File format extension.
            split_mode: Active split mode.
        """
        self.output_dir = Path(output_dir)
        self.format_type = format_type
        self.split_mode = split_mode
        self.file_namer = FileNamer()
        self.path_resolver = OutputPathResolver(
            output_dir=self.output_dir,
            format_type=self.format_type,
            split_mode=self.split_mode,
            file_namer=self.file_namer,
        )

    def write_conversations(
        self,
        groups: Dict[str, List[Dict[str, Any]]],
        formatter: BaseFormatter,
    ) -> WriteResult:
        """Write grouped conversations to disk.

        Args:
            groups: Grouped conversations.
            formatter: Formatter to render each conversation.

        Returns:
            Aggregate write result.
        """
        result = WriteResult()
        used_paths: Set[Path] = set()

        if self._ensure_directory(self.output_dir):
            result.directories_created += 1

        for group_key, conversations in groups.items():
            for conversation in conversations:
                try:
                    filepath = self._get_unique_filepath(
                        conversation, group_key, used_paths
                    )
                    bytes_written = self._write_single(
                        conversation, filepath, formatter
                    )
                    used_paths.add(filepath)
                    result.files_written += 1
                    result.total_bytes += bytes_written
                except Exception as exc:
                    result.add_error(
                        f"Error writing conversation '{conversation.get('title', 'N/A')}': {exc}"
                    )

        return result

    def _get_filepath(self, conv: Dict[str, Any], group_key: str) -> Path:
        """Build the target filepath for one conversation.

        Args:
            conv: Conversation dictionary.
            group_key: Resolved group key.

        Returns:
            Target path.
        """
        return self.path_resolver.get_filepath(conv, group_key)

    def _resolve_target_location(
        self,
        conv: Dict[str, Any],
        group_key: str,
    ) -> tuple[Path, str]:
        """Resolve the destination directory and filename stem.

        Args:
            conv: Conversation dictionary.
            group_key: Resolved group key.

        Returns:
            Directory and filename stem tuple.
        """
        return self.path_resolver.resolve_target_location(conv, group_key)

    def _get_unique_filepath(
        self,
        conv: Dict[str, Any],
        group_key: str,
        used_paths: Set[Path],
    ) -> Path:
        """Resolve a collision-safe filepath.

        Args:
            conv: Conversation dictionary.
            group_key: Group key for the conversation.
            used_paths: Already assigned paths for this write batch.

        Returns:
            Unique filepath for the conversation.
        """
        return self.path_resolver.get_unique_filepath(conv, group_key, used_paths)

    def _ensure_directory(self, dir_path: Path) -> bool:
        """Ensure a directory exists.

        Args:
            dir_path: Directory to create if needed.

        Returns:
            Whether the directory was newly created.
        """
        if dir_path.exists():
            return False
        dir_path.mkdir(parents=True, exist_ok=True)
        return True

    def _write_single(
        self,
        conv: Dict[str, Any],
        filepath: Path,
        formatter: BaseFormatter,
    ) -> int:
        """Write one conversation file.

        Args:
            conv: Conversation data.
            filepath: Target file path.
            formatter: Formatter to render the conversation.

        Returns:
            Number of characters written.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        content = formatter.format_conversation(conv)
        with open(filepath, "w", encoding="utf-8") as handle:
            return handle.write(content)


__all__ = ["FileNamer", "OutputWriter", "WriteResult"]
