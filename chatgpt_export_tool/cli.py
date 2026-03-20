"""
Main CLI entry point for chatgpt_export_tool.

Provides a modular command-line interface for analyzing and exporting
ChatGPT conversations from JSON export files.
"""

import argparse
import sys

from chatgpt_export_tool.commands.analyze import add_analyze_parser, analyze_command
from chatgpt_export_tool.commands.export import add_export_parser, export_command

# Field groups available for --fields option
FIELD_GROUPS = ["conversation", "message", "metadata", "minimal"]


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="chatgpt-export",
        description=(
            "Analyze structure and export ChatGPT conversations from JSON export files.\n\n"
            "Analyzes conversations to show statistics, structure, and field coverage.\n"
            "Exports conversations to txt or json with flexible field selection."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0   Success
  1   Error (file not found, invalid arguments, etc.)
  130 Interrupted by user (Ctrl+C)

Examples:
  chatgpt-export analyze data.json
  chatgpt-export analyze data.json --verbose
  chatgpt-export analyze data.json --output results.txt

  chatgpt-export export data.json --format txt --output conversations.txt
  chatgpt-export export data.json --format json --output conversations.json
  chatgpt-export export data.json --fields groups minimal
  chatgpt-export export data.json --fields include title,create_time --output report.txt

Field Groups: conversation, message, metadata, minimal
See 'chatgpt-export analyze -h' or 'chatgpt-export export -h' for full details.
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.1")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add subcommand parsers
    add_analyze_parser(subparsers)
    add_export_parser(subparsers)

    return parser


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Dispatch to appropriate command
    if args.command == "analyze":
        return analyze_command(args)
    elif args.command == "export":
        return export_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
