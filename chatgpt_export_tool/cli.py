"""
Main CLI entry point for chatgpt_export_tool.

Provides a modular command-line interface for analyzing and exporting
ChatGPT conversations from JSON export files.
"""

import argparse
import sys

from chatgpt_export_tool.commands.analyze import add_analyze_parser, analyze_command
from chatgpt_export_tool.commands.export import add_export_parser, export_command


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="chatgpt-export",
        description="A modular CLI tool for analyzing and exporting ChatGPT conversations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chatgpt-export analyze data.json
  chatgpt-export analyze data.json --verbose
  chatgpt-export analyze data.json --debug
  chatgpt-export analyze data.json --output results.txt
  chatgpt-export analyze data.json --fields include title,create_time
  chatgpt-export analyze data.json --fields exclude model_slug,plugin_ids
  chatgpt-export analyze data.json --fields groups message,minimal
  
  chatgpt-export export data.json --format txt --output report.txt
  chatgpt-export export data.json --format json --output data.json
  chatgpt-export export data.json --fields include title,message
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands'
    )
    
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
    if args.command == 'analyze':
        return analyze_command(args)
    elif args.command == 'export':
        return export_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
