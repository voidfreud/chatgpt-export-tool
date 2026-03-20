"""
Commands package for chatgpt_export_tool.

Provides command implementations for analyze and export operations.
"""

import sys
from abc import ABC, abstractmethod

from chatgpt_export_tool.core.utils import validate_file, setup_logging, get_logger


class BaseCommand(ABC):
    """Abstract base class for command implementations.
    
    Provides common error handling and logging setup.
    """
    
    def __init__(self, filepath: str, verbose: bool = False, debug: bool = False):
        """Initialize base command.
        
        Args:
            filepath: Path to the JSON file to process.
            verbose: If True, enable verbose (INFO) logging.
            debug: If True, enable debug logging.
        """
        self.filepath = filepath
        
        # Setup logging
        setup_logging(verbose=verbose, debug=debug)
        self.logger = get_logger()
    
    def run(self) -> int:
        """Execute the command with common error handling.
        
        Returns:
            Exit code (0 for success, 1 for error).
        """
        try:
            self.logger.info(f"Processing file: {self.filepath}")
            validate_file(self.filepath)
            self._execute()
            return 0
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except PermissionError as e:
            self.logger.error(f"Permission denied: {e}")
            print(f"Error: Permission denied - {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            print("\nOperation cancelled by user.", file=sys.stderr)
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.logger.debug(f"Traceback:", exc_info=True)
            print(f"Error: Unexpected error - {e}", file=sys.stderr)
            if self.logger.level <= 10:  # DEBUG
                import traceback
                traceback.print_exc()
            return 1
    
    @abstractmethod
    def _execute(self):
        """Execute the specific command logic.
        
        Must be implemented by subclasses.
        """
        pass


from chatgpt_export_tool.commands.analyze import analyze_command, AnalyzeCommand
from chatgpt_export_tool.commands.export import export_command, ExportCommand

__all__ = [
    "BaseCommand",
    "analyze_command",
    "AnalyzeCommand",
    "export_command",
    "ExportCommand",
]
