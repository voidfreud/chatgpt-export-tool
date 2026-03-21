"""Filename and target-path resolution for exports."""

from pathlib import Path
from typing import Any, Dict, Optional, Set

from .conversation_access import get_conversation_title
from .file_naming import FileNamer
from chatgpt_export_tool.core.splitter import SplitMode


class OutputPathResolver:
    """Resolve destination paths for split export writes."""

    def __init__(
        self,
        output_dir: str | Path = "output",
        format_type: str = "txt",
        split_mode: Optional[SplitMode] = None,
        file_namer: Optional[FileNamer] = None,
    ) -> None:
        """Initialize the path resolver.

        Args:
            output_dir: Base output directory.
            format_type: File extension without leading dot.
            split_mode: Active split mode.
            file_namer: Optional filename normalizer.
        """
        self.output_dir = Path(output_dir)
        self.format_type = format_type
        self.split_mode = split_mode
        self.file_namer = file_namer or FileNamer()

    def get_filepath(self, conversation: Dict[str, Any], group_key: str) -> Path:
        """Build the target filepath for one conversation.

        Args:
            conversation: Conversation dictionary.
            group_key: Resolved group key.

        Returns:
            Target path.
        """
        directory, stem = self.resolve_target_location(conversation, group_key)
        filename = self.file_namer.get_filename(stem, self.format_type)
        return directory / filename

    def resolve_target_location(
        self,
        conversation: Dict[str, Any],
        group_key: str,
    ) -> tuple[Path, str]:
        """Resolve the destination directory and filename stem.

        Args:
            conversation: Conversation dictionary.
            group_key: Resolved group key.

        Returns:
            Directory and filename stem tuple.
        """
        title = get_conversation_title(conversation)

        if self.split_mode == SplitMode.DATE:
            return self.output_dir / group_key, title
        if self.split_mode == SplitMode.ID:
            return self.output_dir, group_key
        return self.output_dir, title

    def get_unique_filepath(
        self,
        conversation: Dict[str, Any],
        group_key: str,
        used_paths: Set[Path],
    ) -> Path:
        """Resolve a collision-safe filepath.

        Args:
            conversation: Conversation dictionary.
            group_key: Group key for the conversation.
            used_paths: Already assigned paths for this write batch.

        Returns:
            Unique filepath for the conversation.
        """
        filepath = self.get_filepath(conversation, group_key)
        if filepath not in used_paths and not filepath.exists():
            return filepath

        suffix = 2
        while True:
            candidate = filepath.with_name(f"{filepath.stem}_{suffix}{filepath.suffix}")
            if candidate not in used_paths and not candidate.exists():
                return candidate
            suffix += 1
