"""Small shared formatting helpers."""

from datetime import datetime


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


def format_timestamp(timestamp: float, time_format: str = "%H:%M %d-%m-%Y") -> str:
    """Format a Unix timestamp to human-readable date string.

    Args:
        timestamp: Unix timestamp (seconds since epoch). May be float, int, or Decimal.

    Returns:
        Formatted date string.
    """
    # Handle Decimal values from JSON parser
    dt = datetime.fromtimestamp(float(timestamp))
    return dt.strftime(time_format)
