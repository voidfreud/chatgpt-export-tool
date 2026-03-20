"""
Export command for chatgpt_export_tool.

Exports ChatGPT conversations to various formats (txt, json).
"""

import argparse
import os
import sys
from typing import Optional

from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.field_config import FieldSelector
from chatgpt_export_tool.core.formatters import get_formatter


class ExportCommand:
    """Command for exporting conversations to various formats."""
    
    def __init__(self, filepath: str, format_type: str = "txt",
                 output_file: Optional[str] = None, fields: str = "all",
                 verbose: bool = False):
        """Initialize export command.
        
        Args:
            filepath: Path to the JSON file to export.
            format_type: Output format ('txt' or 'json').
            output_file: Optional path to write output to.
            fields: Field selection mode.
            verbose: If True, print progress information.
        """
        self.filepath = filepath
        self.format_type = format_type
        self.output_file = output_file
        self.fields = fields
        self.verbose = verbose
    
    def run(self) -> int:
        """Execute the export command.
        
        Returns:
            Exit code (0 for success, 1 for error).
        """
        try:
            self._validate_file()
            self._export()
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
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
    
    def _export(self):
        """Export conversations to the specified format."""
        # Create field selector
        field_selector = FieldSelector.from_string(self.fields)
        
        # Create formatter
        formatter = get_formatter(self.format_type)
        
        # Parse and export
        parser = JSONParser(self.filepath)
        
        if self.verbose:
            print(f"Exporting {self.filepath} to {self.format_type} format...")
        
        conversations = []
        for conv in parser.iterate_conversations(verbose=self.verbose):
            # Apply field filtering
            filtered_conv = field_selector.filter_conversation(conv)
            formatted = formatter.format_conversation(filtered_conv, field_selector)
            conversations.append(formatted)
        
        output = "\n".join(conversations)
        
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(output)
            print(f"Output written to: {self.output_file}")
        else:
            print(output)


def export_command(args: argparse.Namespace) -> int:
    """Entry point for the export subcommand.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, 1 for error).
    """
    command = ExportCommand(
        filepath=args.file,
        format_type=args.format,
        output_file=args.output,
        fields=args.fields,
        verbose=args.verbose
    )
    return command.run()


def add_export_parser(subparsers) -> argparse.ArgumentParser:
    """Add export subcommand parser.
    
    Args:
        subparsers: Subparsers object from argparse.
        
    Returns:
        Configured argument parser for export command.
    """
    export_parser = subparsers.add_parser(
        "export",
        help="Export conversations to various formats"
    )
    
    export_parser.add_argument(
        "file",
        help="Path to the JSON file to export"
    )
    
    export_parser.add_argument(
        "--format", "-F",
        choices=["txt", "json"],
        default="txt",
        help="Output format (default: txt)"
    )
    
    export_parser.add_argument(
        "--fields", "-f",
        default="all",
        help="Field selection mode: all, none, include <fields>, exclude <fields>, groups <groups>"
    )
    
    export_parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Write output to the specified file instead of stdout"
    )
    
    export_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output with progress information"
    )
    
    return export_parser
