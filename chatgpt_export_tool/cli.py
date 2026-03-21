"""Main CLI entry point for chatgpt_export_tool."""

import argparse
import sys

from chatgpt_export_tool import __version__
from chatgpt_export_tool.commands.analyze import add_analyze_parser, analyze_command
from chatgpt_export_tool.commands.export import add_export_parser, export_command


def create_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="chatgpt-export",
        description=(
            "Analyze structure and export ChatGPT conversations from JSON export files.\n\n"
            "Analyzes conversations to show statistics and field coverage.\n"
            "Exports conversations to txt or json with composable filtering."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0   Success
  1   Error (file not found, invalid arguments, etc.)
  130 Interrupted by user (Ctrl+C)

Examples:
  chatgpt-export analyze data.json
  chatgpt-export analyze data.json --verbose --fields
  chatgpt-export analyze data.json --debug --output results.txt

  chatgpt-export export data.json
  chatgpt-export export data.json --output conversations.txt
  chatgpt-export export data.json --format json --output conversations.json
  chatgpt-export export data.json --fields "groups minimal"
  cp chatgpt_export.toml.example chatgpt_export.toml
  chatgpt-export export data.json --config chatgpt_export.toml
  chatgpt-export export data.json --fields "include title,mapping" --include "model*" --exclude plugin_ids

See 'chatgpt-export analyze -h' or 'chatgpt-export export -h' for full details.
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    add_analyze_parser(subparsers)
    add_export_parser(subparsers)
    return parser


def main() -> int:
    """Run the CLI entry point.

    Returns:
        Process exit code.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "analyze":
        return analyze_command(args)
    if args.command == "export":
        return export_command(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
