"""Runtime contract tests for the cleaned CLI and filtering flow."""

import json
from pathlib import Path

import pytest

from chatgpt_export_tool.cli import create_parser
from chatgpt_export_tool.commands.analyze import AnalyzeCommand
from chatgpt_export_tool.commands.export import ExportCommand, export_command
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

        with pytest.raises(SystemExit):
            parser.parse_args(
                ["analyze", "--config", "chatgpt_export.toml", "data.json"]
            )

    def test_verbose_analyze_output_file_keeps_report_clean(
        self, tmp_path: Path
    ) -> None:
        """Verbose analyze should log progress without polluting the saved report."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        output_file = tmp_path / "analysis.txt"

        command = AnalyzeCommand(
            filepath=str(source_file),
            output_file=str(output_file),
            include_fields=True,
            verbose=True,
        )

        exit_code = command.run()

        assert exit_code == 0
        content = output_file.read_text(encoding="utf-8")
        assert content.startswith("=" * 60)
        assert "Analyzing structure" not in content
        assert "Using streaming JSON parsing" not in content

    def test_analyze_output_creates_parent_directories(self, tmp_path: Path) -> None:
        """Analyze should create missing parent directories for output files."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        output_file = tmp_path / "nested" / "analysis.txt"

        command = AnalyzeCommand(
            filepath=str(source_file),
            output_file=str(output_file),
        )

        exit_code = command.run()

        assert exit_code == 0
        assert output_file.exists()


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

    def test_export_rejects_output_dir_for_single_split(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Single split should reject split-directory output targets."""
        parser = create_parser()
        args = parser.parse_args(
            ["export", "data.json", "--split", "single", "--output-dir", "exports"]
        )

        exit_code = export_command(args)

        captured = capsys.readouterr()
        assert exit_code == 2
        assert "--output-dir can only be used" in captured.err

    def test_export_rejects_output_file_for_split_modes(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Split modes should reject single-file output targets."""
        parser = create_parser()
        args = parser.parse_args(
            ["export", "data.json", "--split", "subject", "--output", "out.txt"]
        )

        exit_code = export_command(args)

        captured = capsys.readouterr()
        assert exit_code == 2
        assert "--output can only be used" in captured.err

    def test_export_accepts_config_argument(self) -> None:
        """Export parser should expose TOML config loading."""
        parser = create_parser()

        args = parser.parse_args(
            ["export", "data.json", "--config", "chatgpt_export.toml"]
        )

        assert args.config == "chatgpt_export.toml"

    def test_export_direct_command_uses_explicit_config_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """Direct Python construction should honor explicit config defaults too."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        config_path = tmp_path / "chatgpt_export.toml"
        config_path.write_text(
            """
[defaults]
format = "json"
split = "subject"
fields = "groups minimal"
output_dir = "exports"
""".strip(),
            encoding="utf-8",
        )

        command = ExportCommand(
            filepath=str(source_file),
            output_dir=str(tmp_path / "exports"),
            config_path=str(config_path),
        )

        assert command.config.format_type == "json"
        assert command.config.split_mode.value == "subject"
        assert command.config.field_spec == "groups minimal"


class TestFilteringContract:
    """Tests for the unified filtering runtime."""

    def test_groups_message_keeps_nested_message_structure(self) -> None:
        """Message field groups keep nested message data."""
        pipeline = FilterPipeline.from_config(FilterConfig(field_spec="groups message"))

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
        pipeline = FilterPipeline.from_config(
            FilterConfig(
                field_spec="include title,mapping",
                include_metadata=["model*"],
                exclude_metadata=["plugin_ids"],
            )
        )

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

    def test_unknown_metadata_patterns_warn_without_stripping_structure(self) -> None:
        """Unknown metadata patterns should warn but keep structural fields intact."""
        pipeline = FilterPipeline.from_config(
            FilterConfig(field_spec="all", include_metadata=["typo_pattern"])
        )

        conversation = {
            "title": "Test",
            "create_time": 1709337600.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "metadata": {
                            "model_slug": "gpt-4",
                            "message_type": "next",
                        }
                    }
                }
            },
        }

        filtered = pipeline.filter(conversation)

        assert filtered["title"] == "Test"
        assert filtered["create_time"] == 1709337600.0
        assert filtered["mapping"]["node-1"]["message"]["metadata"] == {}
        assert pipeline.validation is not None
        assert pipeline.validation.warnings


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
        )

        exit_code = command.run()

        assert exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "Title: Alpha" in content

    def test_single_json_output_is_valid_json(self, tmp_path: Path) -> None:
        """Single JSON export writes one valid JSON document."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        output_file = tmp_path / "combined.json"

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="single",
            format_type="json",
            output_file=str(output_file),
        )

        exit_code = command.run()

        assert exit_code == 0
        payload = json.loads(output_file.read_text(encoding="utf-8"))
        assert isinstance(payload, list)
        assert [conversation["title"] for conversation in payload] == ["Alpha", "Beta"]

    def test_text_export_uses_configured_transcript_defaults(
        self, tmp_path: Path
    ) -> None:
        """Transcript defaults should be read from TOML when no CLI override is given."""
        source_file = tmp_path / "conversations.json"
        source_file.write_text(
            json.dumps(
                [
                    {
                        "title": "Alpha",
                        "id": "conv-1",
                        "create_time": 1709337600.0,
                        "current_node": "assistant-text",
                        "mapping": {
                            "root": {"parent": None, "message": None},
                            "user": {
                                "parent": "root",
                                "message": {
                                    "author": {"role": "user"},
                                    "content": {
                                        "content_type": "text",
                                        "parts": ["question"],
                                    },
                                    "create_time": 1709337600.0,
                                },
                            },
                            "assistant-code": {
                                "parent": "user",
                                "message": {
                                    "author": {"role": "assistant"},
                                    "content": {
                                        "content_type": "code",
                                        "parts": ["search(...)"],
                                    },
                                    "create_time": 1709337601.0,
                                },
                            },
                            "assistant-text": {
                                "parent": "assistant-code",
                                "message": {
                                    "author": {"role": "assistant"},
                                    "content": {
                                        "content_type": "text",
                                        "parts": ["answer"],
                                    },
                                    "create_time": 1709337602.0,
                                },
                            },
                        },
                    }
                ]
            ),
            encoding="utf-8",
        )
        config_path = tmp_path / "chatgpt_export.toml"
        config_path.write_text(
            """
[transcript]
show_assistant_code = true
""".strip(),
            encoding="utf-8",
        )
        output_file = tmp_path / "combined.txt"

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="single",
            output_file=str(output_file),
            config_path=str(config_path),
        )

        exit_code = command.run()

        assert exit_code == 0
        content = output_file.read_text(encoding="utf-8")
        assert "search(...)" in content
        assert "answer" in content

    def test_split_subject_naming_uses_stable_source_fields(
        self, tmp_path: Path
    ) -> None:
        """Subject split filenames should come from source title plus id."""
        source_file = tmp_path / "conversations.json"
        source_file.write_text(
            json.dumps(
                [
                    {"title": "Same", "id": "conv-1", "mapping": {}},
                    {"title": "Same", "id": "conv-2", "mapping": {}},
                ]
            ),
            encoding="utf-8",
        )
        output_dir = tmp_path / "exports"

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="subject",
            output_dir=str(output_dir),
            fields="none",
        )

        exit_code = command.run()

        assert exit_code == 0
        names = sorted(path.name for path in output_dir.iterdir())
        assert names == ["Same_conv-1.txt", "Same_conv-2.txt"]

    def test_split_write_failures_return_non_zero_exit_code(
        self, tmp_path: Path
    ) -> None:
        """Split export should fail when the output target cannot be written."""
        source_file = _write_conversations_file(tmp_path / "conversations.json")
        bad_target = tmp_path / "not-a-directory"
        bad_target.write_text("occupied", encoding="utf-8")

        command = ExportCommand(
            filepath=str(source_file),
            split_mode="subject",
            output_dir=str(bad_target),
        )

        exit_code = command.run()

        assert exit_code == 1
