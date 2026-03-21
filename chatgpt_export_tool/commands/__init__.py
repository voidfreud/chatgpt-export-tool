"""Shared command infrastructure for chatgpt_export_tool."""

import sys
import traceback
from abc import ABC, abstractmethod

from chatgpt_export_tool.core.file_utils import validate_file
from chatgpt_export_tool.core.logging_utils import get_logger, setup_logging


class BaseCommand(ABC):
    """Abstract base class for command implementations."""

    def __init__(
        self, filepath: str, verbose: bool = False, debug: bool = False
    ) -> None:
        """Initialize common command state.

        Args:
            filepath: Input file path to process.
            verbose: Whether INFO logging is enabled.
            debug: Whether DEBUG logging is enabled.
        """
        self.filepath = filepath
        setup_logging(verbose=verbose, debug=debug)
        self.logger = get_logger()

    def run(self) -> int:
        """Execute the command with common validation and error handling.

        Returns:
            Process exit code.
        """
        try:
            self.logger.info("Processing file: %s", self.filepath)
            validate_file(self.filepath)
            self._execute()
            return 0
        except FileNotFoundError as exc:
            self.logger.error("File not found: %s", exc)
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except PermissionError as exc:
            self.logger.error("Permission denied: %s", exc)
            print(f"Error: Permission denied - {exc}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            print("\nOperation cancelled by user.", file=sys.stderr)
            return 130
        except Exception as exc:  # pragma: no cover - defensive top-level guard
            self.logger.error("Unexpected error: %s", exc)
            self.logger.debug("Traceback:", exc_info=True)
            print(f"Error: Unexpected error - {exc}", file=sys.stderr)
            if self.logger.level <= 10:
                traceback.print_exc()
            return 1

    @abstractmethod
    def _execute(self) -> None:
        """Execute the specific command logic."""


__all__ = ["BaseCommand"]
