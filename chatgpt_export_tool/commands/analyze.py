"""
Analyze command for chatgpt_export_tool.

Analyzes the structure of ChatGPT conversations.json export files.
"""

import argparse
import os
import sys
from typing import Dict, Any, Optional

from chatgpt_export_tool.core.parser import JSONParser, get_file_size, format_size
from chatgpt_export_tool.core.field_config import FieldSelector

# Import ijson for error handling
try:
    import ijson
except ImportError:
    ijson = None


class AnalyzeCommand:
    """Command for analyzing JSON file structure."""
    
    def __init__(self, filepath: str, output_file: Optional[str] = None, 
                 verbose: bool = False, fields: str = "all"):
        """Initialize analyze command.
        
        Args:
            filepath: Path to the JSON file to analyze.
            output_file: Optional path to write output to.
            verbose: If True, print progress information.
            fields: Field selection mode (default: "all").
        """
        self.filepath = filepath
        self.output_file = output_file
        self.verbose = verbose
        self.fields = fields
    
    def run(self) -> int:
        """Execute the analyze command.
        
        Returns:
            Exit code (0 for success, 1 for error).
        """
        try:
            self._validate_file()
            self._print_analysis()
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except (ijson.JSONError if ijson else Exception) as e:
            print(f"Error: Invalid JSON file - {e}", file=sys.stderr)
            return 1
        except PermissionError as e:
            print(f"Error: Permission denied - {e}", file=sys.stderr)
            return 1
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: Unexpected error - {e}", file=sys.stderr)
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _validate_file(self):
        """Validate that the file exists and is accessible."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
    
    def _print_analysis(self):
        """Print the analysis results."""
        file_size = get_file_size(self.filepath)
        
        output_lines = []
        output_lines.append(f"File: {self.filepath}")
        output_lines.append(f"Size: {format_size(file_size)} ({file_size:,} bytes)")
        output_lines.append("")
        
        if self.verbose:
            output_lines.append("Analyzing structure (this may take a moment for large files)...")
            output_lines.append("Using streaming JSON parsing (ijson)...")
            output_lines.append("")
        
        # Run the analysis
        parser = JSONParser(self.filepath)
        results = parser.analyze(verbose=self.verbose)
        
        output_lines.append("=" * 60)
        output_lines.append("ANALYSIS RESULTS")
        output_lines.append("=" * 60)
        output_lines.append("")
        output_lines.append(f"Top-level structure: JSON Array of conversation objects")
        output_lines.append(f"Number of threads/conversations: {results['conversation_count']:,}")
        output_lines.append(f"Total message nodes in mappings: {results['message_count']:,}")
        output_lines.append("")
        output_lines.append("-" * 60)
        output_lines.append("ALL UNIQUE FIELD NAMES FOUND:")
        output_lines.append("-" * 60)
        
        sorted_fields = sorted(results['all_fields'])
        output_lines.append(f"Total unique fields: {len(sorted_fields)}")
        output_lines.append("")
        
        # Categorize and display fields
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
        fields=args.fields
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
    
    analyze_parser.add_argument(
        "--fields", "-f",
        default="all",
        help="Field selection mode: all, none, include <fields>, exclude <fields>, groups <groups>"
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
    
    return analyze_parser
