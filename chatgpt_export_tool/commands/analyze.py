"""Analyze command for chatgpt_export_tool."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.commands.options import add_logging_arguments
from chatgpt_export_tool.core.analysis_formatter import (
    AnalyzeConfig,
    format_analysis_text,
)
from chatgpt_export_tool.core.file_utils import get_file_size
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.utils import format_size


class AnalyzeCommand(BaseCommand):
    """Analyze the structure of a conversations export."""

    def __init__(
        self,
        filepath: str,
        output_file: Optional[str] = None,
        include_fields: bool = False,
        verbose: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize the analyze command.

        Args:
            filepath: Input JSON file path.
            output_file: Optional path to write analysis output.
            include_fields: Whether to include field coverage.
            verbose: Whether INFO logging is enabled.
            debug: Whether DEBUG logging is enabled.
        """
        super().__init__(filepath=filepath, verbose=verbose, debug=debug)
        self.output_file = output_file
        self.include_fields = include_fields

    def _execute(self) -> None:
        """Run the analysis command."""
        file_size = get_file_size(self.filepath)

        if self.logger.level <= 20:
            self.logger.info(
                "Analyzing structure (this may take a moment for large files)..."
            )
            self.logger.info("Using streaming JSON parsing (ijson)...")

        parser = JSONParser(self.filepath)
        results = parser.analyze(verbose=self.logger.level <= 20)
        results["file_size"] = format_size(file_size)
        results["filepath"] = self.filepath
        results["analysis_date"] = datetime.now().strftime("%H:%M %d-%m-%Y")

        output = format_analysis_text(
            results,
            AnalyzeConfig(include_fields=self.include_fields),
        )

        if self.output_file:
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as handle:
                handle.write(output)
            print(f"Output written to: {output_path}")
            return

        print(output)


def analyze_command(args: argparse.Namespace) -> int:
    """Run the analyze subcommand.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code.
    """
    command = AnalyzeCommand(
        filepath=args.file,
        output_file=args.output,
        include_fields=args.include_fields,
        verbose=args.verbose,
        debug=args.debug,
    )
    return command.run()


def add_analyze_parser(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Register the analyze subcommand parser.

    Args:
        subparsers: Root parser subparsers collection.

    Returns:
        Configured analyze parser.
    """
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Show statistics and field coverage of conversations",
        description=(
            "Analyze a ChatGPT conversations.json export file.\n\n"
            "Shows statistics (conversation count, message count)\n"
            "and optional field coverage for each conversation level."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  Without --fields  - Only threads/conversations count + message count
  With --fields     - Above + field coverage info (unique field names)

Examples:
  chatgpt-export analyze data.json
  chatgpt-export analyze data.json --fields
  chatgpt-export analyze data.json --verbose --output analysis.txt
  chatgpt-export analyze data.json --debug
        """,
    )

    analyze_parser.add_argument(
        "file",
        help="Path to the conversations.json file to analyze",
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
    add_logging_arguments(analyze_parser)
    return analyze_parser
