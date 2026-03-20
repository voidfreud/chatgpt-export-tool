"""
Analyze command for chatgpt_export_tool.

Analyzes the structure of ChatGPT conversations.json export files.
"""

import argparse
from typing import Optional, List

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.formatters import TextFormatter
from chatgpt_export_tool.core.utils import get_file_size, format_size


class AnalyzeCommand(BaseCommand):
    """Command for analyzing JSON file structure."""
    
    def __init__(self, filepath: str, output_file: Optional[str] = None, 
                 verbose: bool = False, debug: bool = False, fields: str = "all",
                 include: Optional[List[str]] = None,
                 exclude: Optional[List[str]] = None):
        """Initialize analyze command.
        
        Args:
            filepath: Path to the JSON file to analyze.
            output_file: Optional path to write output to.
            verbose: If True, enable verbose (INFO) logging.
            debug: If True, enable debug logging.
            fields: Field selection mode (default: "all").
            include: Metadata fields to include.
            exclude: Metadata fields to exclude.
        """
        super().__init__(filepath=filepath, verbose=verbose, debug=debug)
        self.output_file = output_file
        self.fields = fields
        self.include = include
        self.exclude = exclude
    
    def _execute(self):
        """Execute the analyze command logic."""
        self.logger.debug(f"Getting file size for: {self.filepath}")
        file_size = get_file_size(self.filepath)
        
        output_lines = []
        output_lines.append(f"File: {self.filepath}")
        output_lines.append(f"Size: {format_size(file_size)} ({file_size:,} bytes)")
        output_lines.append("")
        
        if self.logger.level <= 20:  # INFO
            output_lines.append("Analyzing structure (this may take a moment for large files)...")
            output_lines.append("Using streaming JSON parsing (ijson)...")
            output_lines.append("")
        
        self.logger.info("Starting JSON analysis")
        # Run the analysis
        parser = JSONParser(self.filepath)
        results = parser.analyze(verbose=self.logger.level <= 20)
        
        self.logger.info(f"Found {results['conversation_count']:,} conversations")
        self.logger.info(f"Found {results['message_count']:,} total messages")
        
        # Use TextFormatter._format_analysis() to avoid code duplication
        formatter = TextFormatter()
        analysis_output = formatter._format_analysis(results)
        
        output_lines.append(analysis_output)
        
        output = "\n".join(output_lines)
        
        if self.output_file:
            with open(self.output_file, 'w') as f:
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
        verbose=args.verbose,
        debug=args.debug,
        fields=args.fields,
        include=getattr(args, 'include', None),
        exclude=getattr(args, 'exclude', None)
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
        help="Analyze JSON structure and field information"
    )
    
    analyze_parser.add_argument(
        "file",
        help="Path to the JSON file to analyze"
    )
    
    # Create a mutually exclusive group for --fields vs --include/--exclude
    field_group = analyze_parser.add_mutually_exclusive_group()
    
    field_group.add_argument(
        "--fields", "-f",
        default="all",
        help="Field selection mode: all, none, include <fields>, exclude <fields>, groups <groups>"
    )
    
    field_group.add_argument(
        "--include",
        nargs='+',
        metavar="FIELD",
        help="Metadata fields to include (use '*' for all, or specific field names)"
    )
    
    field_group.add_argument(
        "--exclude",
        nargs='+',
        metavar="FIELD",
        help="Metadata fields to exclude (use '*' for all, or specific field names)"
    )
    
    analyze_parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Write output to the specified file instead of stdout"
    )
    
    analyze_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with progress information"
    )
    
    analyze_parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug output with detailed logging"
    )
    
    return analyze_parser
