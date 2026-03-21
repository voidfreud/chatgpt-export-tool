"""Export orchestration for conversations."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from chatgpt_export_tool.core.conversation_formatters import (
    BaseFormatter,
    JSONFormatter,
    _json_default,
    get_formatter,
)
from chatgpt_export_tool.core.filter_pipeline import FilterConfig, FilterPipeline
from chatgpt_export_tool.core.output_writer import OutputWriter, WriteJob, WriteResult
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.split_keys import resolve_group_key
from chatgpt_export_tool.core.splitter import SplitMode
from chatgpt_export_tool.core.utils import get_logger

logger = get_logger()


@dataclass
class ExportConfig:
    """Configuration for export operations.

    Attributes:
        filepath: Path to the conversations export.
        format_type: Output formatter type.
        output_file: Optional single-file output path.
        output_dir: Output directory for split exports.
        split_mode: Export split mode.
        field_spec: Field selection specification.
        include_metadata: Metadata patterns to include.
        exclude_metadata: Metadata patterns to exclude.
        verbose: Whether verbose progress logging is enabled.
    """

    filepath: str
    format_type: str = "txt"
    output_file: Optional[str] = None
    output_dir: str = "output"
    split_mode: SplitMode = SplitMode.SINGLE
    field_spec: str = "all"
    include_metadata: Optional[List[str]] = None
    exclude_metadata: Optional[List[str]] = None
    verbose: bool = False


@dataclass
class ExportResult:
    """Structured result for an export operation.

    Attributes:
        stdout_output: Output that should be written to stdout.
        output_file: Written single-file path, if any.
        output_dir: Written output directory, if any.
        write_result: Detailed result for split writes.
    """

    stdout_output: Optional[str] = None
    output_file: Optional[str] = None
    output_dir: Optional[str] = None
    write_result: Optional[WriteResult] = None


class ExportService:
    """Service for exporting conversations."""

    def __init__(self, config: ExportConfig) -> None:
        """Initialize the export service.

        Args:
            config: Export configuration.
        """
        self.config = config
        self.parser = JSONParser(config.filepath)

    def export(self) -> ExportResult:
        """Run the configured export.

        Returns:
            Structured export result.
        """
        formatter = get_formatter(self.config.format_type)
        pipeline = self._build_pipeline()

        if self.config.split_mode == SplitMode.SINGLE:
            return self._export_single(formatter, pipeline)
        return self._export_split(formatter, pipeline)

    def _build_pipeline(self) -> FilterPipeline:
        """Build the runtime filtering pipeline.

        Returns:
            Configured filter pipeline.
        """
        return FilterPipeline.from_config(
            FilterConfig(
                field_spec=self.config.field_spec,
                include_metadata=self.config.include_metadata,
                exclude_metadata=self.config.exclude_metadata,
            ),
            raise_on_invalid=True,
        )

    def _export_single(
        self,
        formatter: BaseFormatter,
        pipeline: FilterPipeline,
    ) -> ExportResult:
        """Export all conversations as a single output.

        Args:
            formatter: Conversation formatter.
            pipeline: Conversation filtering pipeline.

        Returns:
            Single-output export result.
        """
        if self.config.output_file:
            output_path = Path(self.config.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_single_output(output_path, formatter, pipeline)
            logger.info("Wrote single export file to %s", output_path)
            return ExportResult(output_file=str(output_path))

        return ExportResult(
            stdout_output=self._build_single_stdout_output(formatter, pipeline)
        )

    def _export_split(
        self,
        formatter: BaseFormatter,
        pipeline: FilterPipeline,
    ) -> ExportResult:
        """Export conversations into multiple files.

        Args:
            formatter: Conversation formatter.
            pipeline: Conversation filtering pipeline.

        Returns:
            Split-output export result.
        """
        writer = OutputWriter(
            output_dir=self.config.output_dir,
            format_type=self.config.format_type,
            split_mode=self.config.split_mode,
        )
        jobs = (
            WriteJob(
                source_conversation=conversation,
                rendered_conversation=pipeline.filter(conversation),
                group_key=resolve_group_key(
                    self.config.split_mode, conversation, logger
                ),
            )
            for conversation in self.parser.iterate_conversations(
                verbose=self.config.verbose
            )
        )
        write_result = writer.write_jobs(jobs, formatter)
        logger.info(
            "Wrote %s split export files to %s",
            write_result.files_written,
            self.config.output_dir,
        )
        return ExportResult(
            output_dir=self.config.output_dir,
            write_result=write_result,
        )

    def _build_single_stdout_output(
        self,
        formatter: BaseFormatter,
        pipeline: FilterPipeline,
    ) -> str:
        """Build stdout output for single-export mode."""
        if isinstance(formatter, JSONFormatter):
            conversations = [
                pipeline.filter(conversation)
                for conversation in self.parser.iterate_conversations(
                    verbose=self.config.verbose
                )
            ]
            return json.dumps(
                conversations,
                indent=formatter.indent,
                sort_keys=formatter.sort_keys,
                default=_json_default,
            )

        return "\n".join(
            formatter.format_conversation(pipeline.filter(conversation))
            for conversation in self.parser.iterate_conversations(
                verbose=self.config.verbose
            )
        )

    def _write_single_output(
        self,
        output_path: Path,
        formatter: BaseFormatter,
        pipeline: FilterPipeline,
    ) -> None:
        """Write single-output export content incrementally."""
        with open(output_path, "w", encoding="utf-8") as handle:
            if isinstance(formatter, JSONFormatter):
                handle.write("[")
                first = True
                for conversation in self.parser.iterate_conversations(
                    verbose=self.config.verbose
                ):
                    if not first:
                        handle.write(",\n")
                    handle.write(
                        formatter.format_conversation(pipeline.filter(conversation))
                    )
                    first = False
                handle.write("]")
                return

            first = True
            for conversation in self.parser.iterate_conversations(
                verbose=self.config.verbose
            ):
                if not first:
                    handle.write("\n")
                handle.write(
                    formatter.format_conversation(pipeline.filter(conversation))
                )
                first = False
