"""Formatting helpers plus compatibility re-exports."""

from datetime import datetime

from .file_utils import get_file_size as get_file_size
from .file_utils import validate_file as validate_file
from .logging_utils import get_logger as get_logger
from .logging_utils import setup_logging as setup_logging


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


def format_timestamp(timestamp: float) -> str:
    """Format a Unix timestamp to human-readable date string.

    Args:
        timestamp: Unix timestamp (seconds since epoch). May be float, int, or Decimal.

    Returns:
        Formatted string in "hh:mm dd-mm-yyyy" format.
    """
    # Handle Decimal values from JSON parser
    dt = datetime.fromtimestamp(float(timestamp))
    return dt.strftime("%H:%M %d-%m-%Y")
