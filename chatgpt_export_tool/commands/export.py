"""
Export command for chatgpt_export_tool.

Exports ChatGPT conversations to various formats (txt, json) with
flexible field selection and metadata filtering.
"""

import argparse
from typing import List, Optional

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.core.field_config import FieldSelector, MetadataSelector
from chatgpt_export_tool.core.formatters import get_formatter
from chatgpt_export_tool.core.parser import JSONParser

# Field groups available for --fields groups option
FIELD_GROUPS = ["conversation", "message", "metadata", "minimal"]


class ExportCommand(BaseCommand):
    """Command for exporting conversations to various formats."""

    def __init__(
        self,
        filepath: str,
        format_type: str = "txt",
        output_file: Optional[str] = None,
        fields: str = "all",
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        verbose: bool = False,
        debug: bool = False,
    ):
        """Initialize export command.

        Args:
            filepath: Path to the JSON file to export.
            format_type: Output format ('txt' or 'json').
            output_file: Optional path to write output to.
            fields: Field selection mode.
            include: Metadata fields to include.
            exclude: Metadata fields to exclude.
            verbose: If True, enable verbose (INFO) logging.
            debug: If True, enable debug logging.
        """
        super().__init__(filepath=filepath, verbose=verbose, debug=debug)
        self.format_type = format_type
        self.output_file = output_file
        self.fields = fields
        self.include = include
        self.exclude = exclude

    def _execute(self):
        """Export conversations to the specified format."""
        self.logger.debug(f"Creating field selector with mode: {self.fields}")
        # Create field selector
        field_selector = FieldSelector.from_string(self.fields)

        # Create metadata selector if include/exclude provided
        metadata_selector = None
        if self.include or self.exclude:
            self.logger.debug(
                f"Creating metadata selector: include={self.include}, exclude={self.exclude}"
            )
            metadata_selector = MetadataSelector.from_args(
                include=self.include, exclude=self.exclude
            )
            included = metadata_selector.get_included_fields()
            excluded = metadata_selector.get_excluded_fields()
            self.logger.info(
                f"Metadata filtering: including={included if included else 'all'}, excluding={excluded if excluded else 'none'}"
            )

        self.logger.debug(f"Creating formatter for type: {self.format_type}")
        # Create formatter
        formatter = get_formatter(self.format_type)

        # Parse and export
        self.logger.debug(f"Parsing file: {self.filepath}")
        parser = JSONParser(self.filepath)

        if self.logger.level <= 20:  # INFO
            print(f"Exporting {self.filepath} to {self.format_type} format...")

        self.logger.info(f"Starting export to {self.format_type} format")

        conversations = []
        for conv in parser.iterate_conversations(verbose=self.logger.level <= 20):
            # Apply field filtering
            filtered_conv = field_selector.filter_conversation(conv)

            # Apply metadata filtering if metadata selector is configured
            if metadata_selector:
                filtered_conv = metadata_selector.filter_metadata(filtered_conv)
                self.logger.debug(f"Metadata filtering applied to conversation")

            formatted = formatter.format_conversation(filtered_conv, field_selector)
            conversations.append(formatted)

        self.logger.info(f"Exported {len(conversations)} conversations")

        output = "\n".join(conversations)

        if self.output_file:
            with open(self.output_file, "w") as f:
                f.write(output)
            self.logger.info(f"Output written to: {self.output_file}")
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
        include=getattr(args, "include", None),
        exclude=getattr(args, "exclude", None),
        verbose=args.verbose,
        debug=args.debug,
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
        help="Extract conversations with field selection and metadata filtering",
        description=(
            "Export ChatGPT conversations to txt or json format.\n\n"
            "Select which fields to include/exclude using --fields or\n"
            "filter by metadata using --include/--exclude options."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Field Groups (for --fields groups):
  conversation  - _id, conversation_id, create_time, update_time, title, type
  message      - author, content, status, end_turn
  metadata     - model_slug, message_type, is_archived
  minimal      - title, create_time, message (useful for quick overview)

Metadata Fields (for --include/--exclude):
  id, title, create_time, update_time, model_slug, message_type,
  plugin_ids, conversation_id, type, moderation_results, current_node, is_archived

Examples:
  chatgpt-export export data.json
  chatgpt-export export data.json --format txt --output conversations.txt
  chatgpt-export export data.json --format json --output conversations.json
  chatgpt-export export data.json --fields groups minimal
  chatgpt-export export data.json --fields include title,create_time
  chatgpt-export export data.json --fields exclude model_slug,plugin_ids
  chatgpt-export export data.json --include title model_slug --output filtered.txt
        """,
    )

    export_parser.add_argument(
        "file", help="Path to the conversations.json file to export"
    )

    export_parser.add_argument(
        "--format",
        "-F",
        choices=["txt", "json"],
        default="txt",
        help="Output format: 'txt' (default) or 'json'",
    )

    # Create a mutually exclusive group for --fields vs --include/--exclude
    field_group = export_parser.add_mutually_exclusive_group()

    field_group.add_argument(
        "--fields",
        "-f",
        default="all",
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
        help="Export only conversations with these metadata fields",
    )

    field_group.add_argument(
        "--exclude",
        nargs="+",
        metavar="FIELD",
        help="Exclude these metadata fields from export",
    )

    export_parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Write output to file instead of stdout",
    )

    export_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show progress information during export",
    )

    export_parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show detailed debug information",
    )

    return export_parser
