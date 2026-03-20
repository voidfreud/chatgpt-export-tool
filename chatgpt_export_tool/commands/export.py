"""
Export command for chatgpt_export_tool.

Exports ChatGPT conversations to various formats (txt, json) with
flexible field selection, metadata filtering, and split options.
"""

import argparse
from typing import List, Optional

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.core.field_config import (
    FieldSelector,
    MetadataSelector,
)
from chatgpt_export_tool.core.formatters import get_formatter
from chatgpt_export_tool.core.output_writer import OutputWriter
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.splitter import SplitMode, SplitProcessor


class ExportCommand(BaseCommand):
    """Command for exporting conversations to various formats."""

    def __init__(
        self,
        filepath: str,
        format_type: str = "txt",
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        split_mode: str = "single",
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
            output_file: Optional path to write single file output to.
            output_dir: Optional output directory for split mode.
            split_mode: Split mode ('single', 'subject', 'date').
            fields: Field selection mode.
            include: Metadata fields to include.
            exclude: Metadata fields to exclude.
            verbose: If True, enable verbose (INFO) logging.
            debug: If True, enable debug logging.
        """
        super().__init__(filepath=filepath, verbose=verbose, debug=debug)
        self.format_type = format_type
        self.output_file = output_file
        self.output_dir = output_dir or "output"
        self.split_mode = SplitMode(split_mode)
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

        self.logger.info(f"Starting export with split mode: {self.split_mode.value}")

        if self.split_mode == SplitMode.SINGLE and not self.output_dir:
            # Legacy single-file mode
            self._export_single(parser, field_selector, metadata_selector, formatter)
        else:
            # Split mode with directory output
            self._export_split(parser, field_selector, metadata_selector, formatter)

    def _export_single(
        self,
        parser: JSONParser,
        field_selector: FieldSelector,
        metadata_selector: Optional[MetadataSelector],
        formatter,
    ):
        """Export all conversations to a single file (legacy mode).

        Args:
            parser: JSONParser instance.
            field_selector: FieldSelector instance.
            metadata_selector: Optional MetadataSelector instance.
            formatter: Formatter instance.
        """
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

    def _export_split(
        self,
        parser: JSONParser,
        field_selector: FieldSelector,
        metadata_selector: Optional[MetadataSelector],
        formatter,
    ):
        """Export conversations with splitting into directory structure.

        Args:
            parser: JSONParser instance.
            field_selector: FieldSelector instance.
            metadata_selector: Optional MetadataSelector instance.
            formatter: Formatter instance.
        """
        # Create split processor
        self.logger.debug(f"Creating SplitProcessor with mode: {self.split_mode.value}")
        split_processor = SplitProcessor(parser, mode=self.split_mode)

        # Process and split conversations
        split_result = split_processor.process()
        self.logger.info(
            f"Split into {split_result.group_count} groups "
            f"({split_result.total_conversations} total conversations)"
        )

        # Apply field and metadata filtering to each group
        filtered_groups: dict = {}
        for group_key, conversations in split_result.groups.items():
            filtered_convs = []
            for conv in conversations:
                filtered_conv = field_selector.filter_conversation(conv)
                if metadata_selector:
                    filtered_conv = metadata_selector.filter_metadata(filtered_conv)
                filtered_convs.append(filtered_conv)
            filtered_groups[group_key] = filtered_convs

        # Create output writer and write files
        self.logger.debug(f"Creating OutputWriter for directory: {self.output_dir}")
        output_writer = OutputWriter(
            output_dir=self.output_dir,
            format_type=self.format_type,
            split_mode=self.split_mode,
        )

        write_result = output_writer.write_conversations(filtered_groups, formatter)

        self.logger.info(
            f"Wrote {write_result.files_written} files "
            f"({write_result.total_bytes} bytes)"
        )
        print(f"Exported {write_result.files_written} files to {self.output_dir}/")

        if write_result.errors:
            self.logger.warning(f"{len(write_result.errors)} errors occurred")
            for error in write_result.errors:
                self.logger.error(error)


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
        output_file=getattr(args, "output", None),
        output_dir=getattr(args, "output_dir", None),
        split_mode=getattr(args, "split", "single"),
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
            "filter by metadata using --include/--exclude options.\n"
            "Use --split to organize output into directories."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Split Modes:
  single   - All conversations to one file (default, backward compatible)
  subject  - Each conversation to its own file (named by title)
  date     - Group conversations by creation date (daily folders)

Output Options:
  -o, --output FILE     - Write single file output to FILE (for --split single)
  --output-dir DIR     - Write split output to directory DIR (default: ./output)

Field Groups (for --fields groups):
  conversation  - _id, conversation_id, create_time, update_time, title, type
  message      - author, content, status, end_turn
  metadata     - model_slug, message_type, is_archived
  minimal      - title, create_time, message (useful for quick overview)

Metadata Fields (for --include/--exclude):
  id, title, create_time, update_time, model_slug, message_type,
  plugin_ids, conversation_id, type, moderation_results, current_node, is_archived

Examples:
  # Single file output (backward compatible)
  chatgpt-export export data.json
  chatgpt-export export data.json --format txt --output conversations.txt
  chatgpt-export export data.json --format json --output conversations.json

  # Split by subject (each conversation = own file)
  chatgpt-export export data.json --split subject --output-dir ./exports

  # Split by date (daily folders)
  chatgpt-export export data.json --split date --output-dir ./exports
  # Creates: ./exports/2024-03-20/conversation_title.txt

  # With field selection
  chatgpt-export export data.json --split subject --fields groups minimal --output-dir ./exports
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

    # Split mode argument
    export_parser.add_argument(
        "--split",
        "-s",
        choices=["single", "subject", "date"],
        default="single",
        help="Split mode: 'single' (default), 'subject' (one file per conversation), 'date' (daily folders)",
    )

    # Output options
    output_group = export_parser.add_mutually_exclusive_group()

    output_group.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write output to file (for single file mode)",
    )

    output_group.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory for split mode (default: ./output)",
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
