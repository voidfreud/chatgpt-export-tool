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
            return self._run_with_handling()
        except FileNotFoundError as exc:
            return self._handle_file_not_found(exc)
        except PermissionError as exc:
            return self._handle_permission_error(exc)
        except KeyboardInterrupt:
            return self._handle_keyboard_interrupt()
        except Exception as exc:  # pragma: no cover - defensive top-level guard
            return self._handle_unexpected_error(exc)

    def _run_with_handling(self) -> int:
        """Validate common inputs and execute the concrete command."""
        self.logger.info("Processing file: %s", self.filepath)
        validate_file(self.filepath)
        self._execute()
        return 0

    def _handle_file_not_found(self, exc: FileNotFoundError) -> int:
        """Render a consistent file-not-found error."""
        self.logger.error("File not found: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    def _handle_permission_error(self, exc: PermissionError) -> int:
        """Render a consistent permission error."""
        self.logger.error("Permission denied: %s", exc)
        print(f"Error: Permission denied - {exc}", file=sys.stderr)
        return 1

    def _handle_keyboard_interrupt(self) -> int:
        """Render cancellation consistently."""
        self.logger.info("Operation cancelled by user")
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130

    def _handle_unexpected_error(self, exc: Exception) -> int:
        """Render an unexpected top-level failure."""
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
