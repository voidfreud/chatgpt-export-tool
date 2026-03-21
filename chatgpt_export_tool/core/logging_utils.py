"""Logging configuration helpers for the application."""

import logging
import sys
from typing import Optional

_logger: Optional[logging.Logger] = None


def setup_logging(verbose: bool = False, debug: bool = False) -> logging.Logger:
    """Configure the application logger.

    Args:
        verbose: Enable INFO logging.
        debug: Enable DEBUG logging.

    Returns:
        Configured logger instance.
    """
    global _logger

    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logger = logging.getLogger("chatgpt_export_tool")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Return the application logger, creating a default one if needed."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("chatgpt_export_tool")
        _logger.setLevel(logging.WARNING)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        _logger.addHandler(handler)
    return _logger
