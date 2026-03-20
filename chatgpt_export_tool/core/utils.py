"""
Shared utility functions for chatgpt_export_tool.

Provides file validation, logging configuration, and other common utilities.
"""

import logging
import os
import sys
from typing import Optional

# Global logger instance - configured in setup_logging()
_logger: Optional[logging.Logger] = None


def setup_logging(verbose: bool = False, debug: bool = False) -> logging.Logger:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose (INFO) logging.
        debug: Enable debug logging.

    Returns:
        Configured logger instance.
    """
    global _logger

    # Determine log level
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Create logger
    logger = logging.getLogger("chatgpt_export_tool")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    _logger = logger

    return logger


def get_logger() -> logging.Logger:
    """Get the application logger.

    Returns:
        Logger instance. If not configured, returns a default logger.
    """
    global _logger
    if _logger is None:
        # Create a basic logger if setup_logging hasn't been called
        _logger = logging.getLogger("chatgpt_export_tool")
        _logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        _logger.addHandler(handler)
    return _logger


def validate_file(filepath: str) -> None:
    """Validate that a file exists and is accessible.

    Args:
        filepath: Path to the file to validate.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger = get_logger()
    logger.debug(f"Validating file: {filepath}")

    if not os.path.exists(filepath):
        logger.debug(f"File not found: {filepath}")
        raise FileNotFoundError(f"File not found: {filepath}")

    logger.debug(f"File validation passed: {filepath}")


def get_file_size(filepath: str) -> int:
    """Get file size in bytes.

    Args:
        filepath: Path to the file.

    Returns:
        File size in bytes.

    Raises:
        OSError: If the file cannot be accessed.
    """
    return os.path.getsize(filepath)


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable size string (e.g., "1.23 MB").
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"
