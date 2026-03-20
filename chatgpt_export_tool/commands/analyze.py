"""
Analyze command for chatgpt_export_tool.

Analyzes the structure of ChatGPT conversations.json export files.
Provides statistics, structure overview, and field coverage analysis.
"""

import argparse
from typing import List, Optional

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.core.field_config import FIELD_GROUPS
from chatgpt_export_tool.core.formatters import AnalyzeConfig, TextFormatter
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.utils import format_size, get_file_size


class AnalyzeCommand(BaseCommand):
    """Command for analyzing JSON file structure."""

    def __init__(
        self,
        filepath: str,
        output_file: Optional[str] = None,
        field_selection: str = "all",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        include_fields: bool = False,
    ):
        """Initialize analyze command.

        Args:
            filepath: Path to the JSON file to analyze.
            output_file: Optional path to write output to.
            field_selection: Field selection mode (default: "all").
            include: Metadata fields to include.
            exclude: Metadata fields to exclude.
            include_fields: Whether to include field coverage info (default: False).
        """
        super().__init__(filepath=filepath)
        self.output_file = output_file
        self.field_selection = field_selection
        self.include = include
        self.exclude = exclude
        self.include_fields = include_fields

    def _execute(self):
        """Execute the analyze command logic."""
        self.logger.debug(f"Getting file size for: {self.filepath}")
        file_size = get_file_size(self.filepath)

        output_lines = []
        output_lines.append(f"File: {self.filepath}")
        output_lines.append(f"Size: {format_size(file_size)} ({file_size:,} bytes)")
        output_lines.append("")

        if self.logger.level <= 20:  # INFO
            output_lines.append(
                "Analyzing structure (this may take a moment for large files)..."
            )
            output_lines.append("Using streaming JSON parsing (ijson)...")
            output_lines.append("")

        self.logger.info("Starting JSON analysis")
        # Run the analysis
        parser = JSONParser(self.filepath)
        results = parser.analyze(verbose=self.logger.level <= 20)

        # Add file size to results for analysis output
        results["file_size"] = format_size(file_size)

        self.logger.info(f"Found {results['conversation_count']:,} conversations")
        self.logger.info(f"Found {results['message_count']:,} total messages")

        # Create AnalyzeConfig based on include_fields flag
        analyze_config = AnalyzeConfig(include_fields=self.include_fields)
        self.logger.debug(
            f"Using AnalyzeConfig with include_fields={self.include_fields}"
        )

        # Use TextFormatter._format_analysis() to avoid code duplication
        formatter = TextFormatter()
        analysis_output = formatter._format_analysis(results, analyze_config)

        output_lines.append(analysis_output)

        output = "\n".join(output_lines)

        if self.output_file:
            with open(self.output_file, "w") as f:
                f.write(output)
            self.logger.info(f"Output written to: {self.output_file}")
            print(f"Output written to: {self.output_file}")
        else:
            print(output)


def analyze_command(args: argparse.Namespace) -> int:
    """Entry point for the analyze subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    command = AnalyzeCommand(
        filepath=args.file,
        output_file=args.output,
        field_selection=getattr(args, "field_selection", "all"),
        include=getattr(args, "include", None),
        exclude=getattr(args, "exclude", None),
        include_fields=args.include_fields,
    )
    return command.run()


def add_analyze_parser(subparsers) -> argparse.ArgumentParser:
    """Add analyze subcommand parser.

    Args:
        subparsers: Subparsers object from argparse.

    Returns:
        Configured argument parser for analyze command.
    """
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Show statistics and field coverage of conversations",
        description=(
            "Analyze a ChatGPT conversations.json export file.\n\n"
            "Shows statistics (conversation count, message count)\n"
            "and field coverage analysis for each conversation level."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  Without --fields  - Only threads/conversations count + message count
  With --fields     - Above + field coverage info (unique field names)

Field Selection (for output formatting):
  conversation  - _id, conversation_id, create_time, update_time, title, type
  message       - author, content, status, end_turn
  metadata      - model_slug, message_type, is_archived
  minimal       - title, create_time, message (useful for quick overview)

Examples:
  chatgpt-export analyze data.json
  chatgpt-export analyze data.json --fields
  chatgpt-export analyze data.json --output analysis.txt
  chatgpt-export analyze data.json --fields --output analysis.txt
        """,
    )

    analyze_parser.add_argument(
        "file", help="Path to the conversations.json file to analyze"
    )

    # Create a mutually exclusive group for --field-selection vs --include/--exclude
    field_group = analyze_parser.add_mutually_exclusive_group()

    field_group.add_argument(
        "--field-selection",
        "-F",
        default="all",
        dest="field_selection",
        help=(
            "Field selection: 'all' (default), 'none', "
            "'include field1,field2', 'exclude field1,field2', "
            "'groups group1,group2'"
        ),
    )

    field_group.add_argument(
        "--include",
        nargs="+",
        metavar="FIELD",
        help="Metadata fields to include (e.g., title create_time model_slug)",
    )

    field_group.add_argument(
        "--exclude",
        nargs="+",
        metavar="FIELD",
        help="Metadata fields to exclude (e.g., model_slug plugin_ids)",
    )

    analyze_parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Write output to file instead of stdout",
    )

    analyze_parser.add_argument(
        "--fields",
        action="store_true",
        default=False,
        dest="include_fields",
        help="Include field coverage info in output (unique field names)",
    )

    return analyze_parser
