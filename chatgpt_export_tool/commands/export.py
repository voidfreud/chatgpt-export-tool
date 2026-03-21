"""Export command for chatgpt_export_tool."""

import argparse
import sys
from typing import Optional

from chatgpt_export_tool.commands import BaseCommand
from chatgpt_export_tool.commands.options import add_logging_arguments
from chatgpt_export_tool.core.export_service import ExportConfig, ExportService
from chatgpt_export_tool.core.runtime_config import load_runtime_config
from chatgpt_export_tool.core.splitter import SplitMode


class ExportCommand(BaseCommand):
    """Export conversations to text or JSON outputs."""

    def __init__(
        self,
        filepath: str,
        format_type: Optional[str] = None,
        output_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        split_mode: Optional[str] = None,
        fields: Optional[str] = None,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        config_path: Optional[str] = None,
        verbose: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize the export command.

        Args:
            filepath: Input JSON export path.
            format_type: Output format identifier.
            output_file: Optional single-file output path.
            output_dir: Optional split-output directory.
            split_mode: Export split mode string.
            fields: Field selection specification.
            include: Metadata include patterns.
            exclude: Metadata exclude patterns.
            config_path: Optional TOML config path.
            verbose: Whether INFO logging is enabled.
            debug: Whether DEBUG logging is enabled.
        """
        super().__init__(filepath=filepath, verbose=verbose, debug=debug)
        runtime_config = load_runtime_config(config_path)
        resolved_format = format_type or runtime_config.defaults.format_type
        resolved_output_dir = output_dir or runtime_config.defaults.output_dir
        resolved_split_mode = split_mode or runtime_config.defaults.split_mode
        resolved_fields = fields or runtime_config.defaults.field_spec
        resolved_include = include or list(runtime_config.defaults.include_metadata)
        resolved_exclude = exclude or list(runtime_config.defaults.exclude_metadata)
        self._validate_output_targets(
            split_mode=resolved_split_mode,
            output_file=output_file,
            output_dir=output_dir,
        )
        self.config = ExportConfig(
            filepath=filepath,
            format_type=resolved_format,
            output_file=output_file,
            output_dir=resolved_output_dir,
            split_mode=SplitMode(resolved_split_mode),
            field_spec=resolved_fields,
            include_metadata=resolved_include,
            exclude_metadata=resolved_exclude,
            verbose=self.logger.level <= 20,
            transcript_config=runtime_config.transcript,
            text_output_config=runtime_config.text_output,
        )

    @staticmethod
    def _validate_output_targets(
        split_mode: str,
        output_file: Optional[str],
        output_dir: Optional[str],
    ) -> None:
        """Validate output-target arguments for the selected split mode."""
        if split_mode == "single" and output_dir:
            raise ValueError(
                "--output-dir can only be used with split modes subject, date, or id"
            )
        if split_mode != "single" and output_file:
            raise ValueError("--output can only be used with --split single")

    def _execute(self) -> None:
        """Run the export command."""
        service = ExportService(self.config)
        result = service.export()

        if result.stdout_output is not None:
            print(result.stdout_output)
            return

        if result.output_file is not None:
            print(f"Output written to: {result.output_file}")
            return

        if result.write_result is not None and result.output_dir is not None:
            for error in result.write_result.errors:
                self.logger.error(error)
            if result.write_result.errors:
                raise RuntimeError(
                    f"Encountered {len(result.write_result.errors)} export write errors"
                )
            print(
                f"Exported {result.write_result.files_written} files to {result.output_dir}/"
            )


def export_command(args: argparse.Namespace) -> int:
    """Run the export subcommand.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Process exit code.
    """
    try:
        command = ExportCommand(
            filepath=args.file,
            format_type=args.format,
            output_file=getattr(args, "output", None),
            output_dir=getattr(args, "output_dir", None),
            split_mode=getattr(args, "split", None),
            fields=args.fields,
            include=getattr(args, "include", None),
            exclude=getattr(args, "exclude", None),
            config_path=getattr(args, "config", None),
            verbose=args.verbose,
            debug=args.debug,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return command.run()


def add_export_parser(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Register the export subcommand parser.

    Args:
        subparsers: Root parser subparsers collection.

    Returns:
        Configured export parser.
    """
    export_parser = subparsers.add_parser(
        "export",
        help="Extract conversations with field selection and metadata filtering",
        description=(
            "Export ChatGPT conversations to txt or json format.\n\n"
            "Use --fields to control which structural fields are retained,\n"
            "and compose --include/--exclude to filter metadata fields.\n"
            "Use --split to organize output into directories."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Split Modes:
  single   - All conversations to one output stream or file (default)
  subject  - Each conversation to its own file (named from title + id)
  date     - Group conversations by creation date (daily folders)
  id       - Each conversation to its own file named from conversation ID

Output Options:
  -o, --output FILE     - Write single-file output to FILE (for --split single)
  --output-dir DIR      - Write split output to directory DIR (default: ./output)

Field Groups (for --fields groups):
  conversation  - _id, conversation_id, create_time, update_time, title, type
  message       - author, content, status, end_turn
  metadata      - model_slug, message_type, is_archived
  minimal       - title, create_time, message

Examples:
  chatgpt-export export data.json
  chatgpt-export export data.json --output conversations.txt
  chatgpt-export export data.json --format json --output conversations.json
  chatgpt-export export data.json --config chatgpt_export.toml
  chatgpt-export export data.json --split subject --output-dir ./exports
  chatgpt-export export data.json --fields "groups minimal" --split subject
  chatgpt-export export data.json --fields "include title,mapping" --include "model*" --exclude plugin_ids
        """,
    )

    export_parser.add_argument(
        "file",
        help="Path to the conversations.json file to export",
    )
    export_parser.add_argument(
        "--config",
        metavar="PATH",
        help="Load defaults from TOML config file",
    )
    export_parser.add_argument(
        "--format",
        "-F",
        choices=["txt", "json"],
        default=None,
        help="Output format: 'txt' or 'json' (default from config or built-in fallback)",
    )
    export_parser.add_argument(
        "--fields",
        "-f",
        default=None,
        help=(
            "Field selection: 'all', 'none', "
            "'include field1,field2', 'exclude field1,field2', "
            "'groups group1,group2' (default from config or built-in fallback)"
        ),
    )
    export_parser.add_argument(
        "--include",
        nargs="+",
        metavar="FIELD",
        help="Include only metadata fields matching these patterns",
    )
    export_parser.add_argument(
        "--exclude",
        nargs="+",
        metavar="FIELD",
        help="Exclude metadata fields matching these patterns",
    )
    export_parser.add_argument(
        "--split",
        "-s",
        choices=[mode.value for mode in SplitMode],
        default=None,
        help=(
            "Split mode: 'single', 'subject' (one file per conversation), "
            "'date' (daily folders), 'id' (by conversation ID); "
            "default from config or built-in fallback"
        ),
    )

    output_group = export_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write output to FILE (for --split single)",
    )
    output_group.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory for split mode (default: ./output)",
    )

    add_logging_arguments(export_parser)
    return export_parser
