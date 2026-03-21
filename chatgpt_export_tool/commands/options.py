"""Shared CLI option helpers for command modules."""

import argparse


def add_logging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared logging arguments to a command parser.

    Args:
        parser: Command parser to update.
    """
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show progress information during processing",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show detailed debug information",
    )
