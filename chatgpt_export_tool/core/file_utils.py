"""Filesystem helpers shared by commands and parsing."""

import os

from .logging_utils import get_logger


def validate_file(filepath: str) -> None:
    """Validate that a file exists and is accessible.

    Args:
        filepath: Path to the file to validate.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger = get_logger()
    logger.debug("Validating file: %s", filepath)

    if not os.path.exists(filepath):
        logger.debug("File not found: %s", filepath)
        raise FileNotFoundError(f"File not found: {filepath}")

    logger.debug("File validation passed: %s", filepath)


def get_file_size(filepath: str) -> int:
    """Get file size in bytes.

    Args:
        filepath: Path to the file.

    Returns:
        File size in bytes.
    """
    return os.path.getsize(filepath)
