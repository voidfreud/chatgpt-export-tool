"""
Analyze command for chatgpt_export_tool.

Analyzes the structure of ChatGPT conversations.json export files.
"""

import argparse
import sys
from typing import Optional, List

from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.field_config import FieldSelector, MetadataSelector
from chatgpt_export_tool.core.utils import (
    validate_file, get_file_size, format_size, 
    setup_logging, get_logger
)


class AnalyzeCommand:
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
        self.filepath = filepath
        self.output_file = output_file
        self.fields = fields
        self.include = include
        self.exclude = exclude
        
        # Setup logging
        setup_logging(verbose=verbose, debug=debug)
        self.logger = get_logger()
    
    def run(self) -> int:
        """Execute the analyze command.
        
        Returns:
            Exit code (0 for success, 1 for error).
        """
        try:
            self.logger.info(f"Analyzing file: {self.filepath}")
            validate_file(self.filepath)
            self._print_analysis()
            return 0
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ijson.JSONError as e:
            self.logger.error(f"Invalid JSON file: {e}")
            print(f"Error: Invalid JSON file - {e}", file=sys.stderr)
            return 1
        except PermissionError as e:
            self.logger.error(f"Permission denied: {e}")
            print(f"Error: Permission denied - {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            print("\nOperation cancelled by user.", file=sys.stderr)
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.logger.debug(f"Traceback:", exc_info=True)
            print(f"Error: Unexpected error - {e}", file=sys.stderr)
            if self.logger.level <= 10:  # DEBUG
                import traceback
                traceback.print_exc()
            return 1
    
    def _print_analysis(self):
        """Print the analysis results."""
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
        
        output_lines.append("=" * 60)
        output_lines.append("ANALYSIS RESULTS")
        output_lines.append("=" * 60)
        output_lines.append("")
        output_lines.append(f"Top-level structure: JSON Array of conversation objects")
        output_lines.append(f"Number of threads/conversations: {results['conversation_count']:,}")
        output_lines.append(f"Total message nodes in mappings: {results['message_count']:,}")
        output_lines.append("")
        
        self.logger.info(f"Found {results['conversation_count']:,} conversations")
        self.logger.info(f"Found {results['message_count']:,} total messages")
        
        output_lines.append("-" * 60)
        output_lines.append("ALL UNIQUE FIELD NAMES FOUND:")
        output_lines.append("-" * 60)
        
        sorted_fields = sorted(results['all_fields'])
        output_lines.append(f"Total unique fields: {len(sorted_fields)}")
        output_lines.append("")
        
        # Categorize and display fields
        self.logger.debug("Categorizing fields by hierarchy level")
        categorized = FieldSelector.categorize_fields(results['all_fields'])
        
        for category, fields in categorized.items():
            if fields:
                output_lines.append(f"{category.capitalize()}-level fields:")
                output_lines.append(f"  {', '.join(sorted(fields))}")
                output_lines.append("")
        
        output_lines.append("-" * 60)
        output_lines.append("SAMPLE STRUCTURE (first conversation):")
        output_lines.append("-" * 60)
        if results['sample_conversation']:
            for key, value in results['sample_conversation'].items():
                output_lines.append(f"  {key}: {value}")
        
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


# Import ijson at module level for error handling
try:
    import ijson
except ImportError:
    ijson = None
