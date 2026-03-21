"""Runtime contract tests for the cleaned CLI and filtering flow."""

import json
from pathlib import Path

import pytest

from chatgpt_export_tool.cli import create_parser
from chatgpt_export_tool.commands.export import ExportCommand
from chatgpt_export_tool.core.filter_pipeline import FilterConfig, FilterPipeline


def _write_conversations_file(path: Path) -> Path:
    """Write a small conversations export fixture to disk.

    Args:
        path: Target JSON file path.

    Returns:
        The written file path.
    """
    conversations = [
        {
            "title": "Alpha",
            "id": "conv-1",
            "create_time": 1709337600.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "author": {"role": "user", "name": "Alex"},
                        "content": {"parts": ["hello"]},
                        "metadata": {"model_slug": "gpt-4", "plugin_ids": ["tool-a"]},
                    }
                }
            },
        },
        {
            "title": "Beta",
            "id": "conv-2",
            "create_time": 1709424000.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["world"]},
                        "metadata": {"model_slug": "gpt-4o", "plugin_ids": ["tool-b"]},
                    }
                }
            },
        },
    ]
    path.write_text(json.dumps(conversations), encoding="utf-8")
    return path


class TestAnalyzeCliContract:
    """Tests for the simplified analyze command surface."""

    def test_analyze_accepts_shared_logging_flags(self) -> None:
        """Analyze supports the shared verbose/debug flags."""
        parser = create_parser()

        args = parser.parse_args(["analyze", "--verbose", "--fields", "data.json"])
        assert args.verbose is True
        assert args.debug is False
        assert args.include_fields is True

        args = parser.parse_args(["analyze", "--debug", "data.json"])
        assert args.debug is True
        assert args.verbose is False

    def test_analyze_rejects_removed_filtering_options(self) -> None:
        """Analyze no longer exposes export-style filtering options."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["analyze", "--include", "title", "data.json"])

        with pytest.raises(SystemExit):
            parser.parse_args(["analyze", "--field-selection", "all", "data.json"])


class TestExportCliContract:
    """Tests for the cleaned-up export CLI contract."""

    def test_export_allows_composable_filtering_options(self) -> None:
        """Export supports combining field selection with metadata filters."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "export",
                "data.json",
                "--fields",
                "include title,mapping",
                "--include",
                "model*",
                "--exclude",
                "plugin_ids",
            ]
        )

        assert args.fields == "include title,mapping"
        assert args.include == ["model*"]
        assert args.exclude == ["plugin_ids"]

    def test_export_accepts_quoted_field_specs(self) -> None:
        """Examples with quoted multi-word field specs parse as intended."""
        parser = create_parser()

        args = parser.parse_args(
            ["export", "data.json", "--fields", "groups minimal", "--output", "out.txt"]
        )
        assert args.fields == "groups minimal"

        args = parser.parse_args(
            [
                "export",
                "data.json",
                "--fields",
                "include title,create_time",
                "--output",
                "out.txt",
            ]
        )
        assert args.fields == "include title,create_time"


class TestFilteringContract:
    """Tests for the unified filtering runtime."""

    def test_groups_message_keeps_nested_message_structure(self) -> None:
        """Message field groups keep nested message data."""
        result = FilterPipeline.from_config(FilterConfig(field_spec="groups message"))
        pipeline = result.build_pipeline()

        conversation = {
            "title": "Test",
            "create_time": 1709337600.0,
            "mapping": {
                "node-1": {
                    "id": "node-1",
                    "message": {
                        "author": {"role": "user", "name": "Alex"},
                        "content": {"parts": ["hello"], "content_type": "text"},
                        "status": "finished",
                        "end_turn": True,
                        "metadata": {"model_slug": "gpt-4", "plugin_ids": ["tool-a"]},
                    },
                }
            },
            "model_slug": "gpt-4",
        }

        filtered = pipeline.filter(conversation)

        assert "mapping" in filtered
        assert "title" not in filtered
        message = filtered["mapping"]["node-1"]["message"]
        assert message["author"] == {"role": "user", "name": "Alex"}
        assert message["content"]["parts"] == ["hello"]
        assert message["status"] == "finished"
        assert message["end_turn"] is True

    def test_metadata_filter_removes_nested_fields(self) -> None:
        """Metadata include/exclude applies to nested message metadata."""
        result = FilterPipeline.from_config(
            FilterConfig(
                field_spec="include title,mapping",
                include_metadata=["model*"],
                exclude_metadata=["plugin_ids"],
            )
        )
        pipeline = result.build_pipeline()

        conversation = {
            "title": "Test",
            "mapping": {
                "node-1": {
                    "message": {
                        "metadata": {
                            "model_slug": "gpt-4",
                            "plugin_ids": ["tool-a"],
                            "message_type": "next",
                        }
                    }
                }
            },
        }

        filtered = pipeline.filter(conversation)
        metadata = filtered["mapping"]["node-1"]["message"]["metadata"]

        assert metadata == {"model_slug": "gpt-4"}


class TestExportRuntimeContract:
    """Tests for single-file export behavior."""

    def test_single_split_without_output_writes_to_stdout(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Single split mode uses stdout when no output path is provided."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        output_dir = tmp_path / "exports"

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="single",
            output_dir=str(output_dir),
        )

        exit_code = command.run()

        captured = capsys.readouterr()
        assert exit_code == 0
        assert "Title: Alpha" in captured.out
        assert "Title: Beta" in captured.out
        assert "Exported 2 files" not in captured.out
        assert not output_dir.exists()

    def test_single_split_with_output_writes_one_file(self, tmp_path: Path) -> None:
        """Single split mode with --output writes a single combined file."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        output_file = tmp_path / "combined.txt"

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="single",
            output_file=str(output_file),
            output_dir=str(tmp_path / "unused-output-dir"),
        )

        exit_code = command.run()

        assert exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Title: Alpha" in content
        assert "Title: Beta" in content
