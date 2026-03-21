"""Tests for chatgpt_export_tool core functionality."""

from unittest.mock import patch

import pytest

# Import from the new package structure
from chatgpt_export_tool.cli import create_parser, main
from chatgpt_export_tool.core.analysis_formatter import (
    AnalyzeConfig,
    format_analysis_text,
)
from chatgpt_export_tool.core.file_utils import get_file_size
from chatgpt_export_tool.core.field_selector import FieldSelector
from chatgpt_export_tool.core.parser import JSONParser
from chatgpt_export_tool.core.utils import format_size


class TestImportModule:
    """Test that the module can be imported."""

    def test_import_core_modules(self):
        """Test that core modules can be imported."""
        from chatgpt_export_tool.core import (
            FieldSelector,
            JSONFormatter,
            JSONParser,
            TextFormatter,
        )

        assert JSONParser is not None
        assert FieldSelector is not None
        assert TextFormatter is not None
        assert JSONFormatter is not None

    def test_import_ijson(self):
        """Test that ijson can be imported (or is installed)."""
        import ijson

        assert hasattr(ijson, "items")
        assert hasattr(ijson, "parse")


class TestFormatSize:
    """Test the format_size helper function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        assert format_size(500) == "500.00 B"
        assert format_size(0) == "0.00 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_size(2048)
        assert "KB" in result
        assert "2.00" in result

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        result = format_size(5 * 1024 * 1024)
        assert "MB" in result
        assert "5.00" in result

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        result = format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result


class TestCategorizeFields:
    """Test the categorize_fields function."""

    def test_categorize_conversation_fields(self):
        """Test that conversation-level fields are categorized correctly."""
        fields = {"title", "create_time", "mapping"}
        result = FieldSelector.categorize_fields(fields)
        assert "title" in result["conversation"]
        assert "create_time" in result["conversation"]
        assert "mapping" in result["conversation"]

    def test_categorize_message_fields(self):
        """Test that message-level fields are categorized correctly."""
        fields = {"author", "content", "status"}
        result = FieldSelector.categorize_fields(fields)
        assert "author" in result["message"]
        assert "content" in result["message"]
        assert "status" in result["message"]

    def test_categorize_unknown_fields(self):
        """Test that unknown fields are tracked separately."""
        fields = {"unknown_field", "custom_field"}
        result = FieldSelector.categorize_fields(fields)
        assert "unknown_field" in result["unknown"]
        assert "custom_field" in result["unknown"]

    def test_categorize_empty_fields(self):
        """Test categorizing empty field set."""
        result = FieldSelector.categorize_fields(set())
        assert result["conversation"] == []
        assert result["message"] == []
        assert result["metadata"] == []
        assert result["unknown"] == []


class TestGetFileSize:
    """Test the get_file_size function."""

    def test_get_file_size_existing(self):
        """Test getting size of existing file."""
        # Test this very file
        size = get_file_size(__file__)
        assert size > 0
        assert isinstance(size, int)

    def test_get_file_size_nonexistent(self):
        """Test that non-existent file raises OSError."""
        with pytest.raises(OSError):
            get_file_size("/nonexistent/path/to/file.json")


class TestJSONParser:
    """Test the JSONParser class."""

    def test_parser_init_invalid_file(self):
        """Test that parser init with invalid file doesn't raise until analyze."""
        # Creating parser with non-existent file should not raise immediately
        parser = JSONParser("/nonexistent/file.json")
        assert parser.filepath == "/nonexistent/file.json"

    def test_parser_analyze_invalid_file(self):
        """Test that analyze raises FileNotFoundError for invalid file."""
        parser = JSONParser("/nonexistent/file.json")
        with pytest.raises(FileNotFoundError):
            parser.analyze()


class TestCLIArguments:
    """Test CLI argument parsing."""

    def test_default_command(self):
        """Test that no command shows help."""
        parser = create_parser()
        # With no args, command should be None
        args = parser.parse_args([])
        assert args.command is None

    def test_analyze_command(self):
        """Test analyze subcommand parsing."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "data.json"])
        assert args.command == "analyze"
        assert args.file == "data.json"

    def test_export_command(self):
        """Test export subcommand parsing."""
        parser = create_parser()
        args = parser.parse_args(["export", "data.json"])
        assert args.command == "export"
        assert args.file == "data.json"

    def test_output_flag(self):
        """Test that output flag is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "--output", "results.txt", "data.json"])
        assert args.output == "results.txt"

    def test_combined_arguments(self):
        """Test that multiple arguments work together."""
        parser = create_parser()
        args = parser.parse_args(
            ["analyze", "--fields", "--output", "out.txt", "input.json"]
        )
        assert args.include_fields is True
        assert args.output == "out.txt"
        assert args.file == "input.json"


class TestMainFunction:
    """Test the main function behavior."""

    def test_main_no_command(self):
        """Test that main returns 1 when no command is given."""
        with patch("sys.argv", ["chatgpt-export"]):
            result = main()
            assert result == 1

    def test_main_analyze_file_not_found(self):
        """Test that analyze returns 1 for non-existent file."""
        with patch("sys.argv", ["chatgpt-export", "analyze", "/nonexistent/file.json"]):
            result = main()
            assert result == 1

    def test_main_with_help(self):
        """Test that main handles --help correctly."""
        with patch("sys.argv", ["chatgpt-export", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestAnalyzeConfig:
    """Test the AnalyzeConfig dataclass."""

    def test_default_include_fields_is_false(self):
        """Test that default include_fields is False."""
        config = AnalyzeConfig()
        assert config.include_fields is False

    def test_include_fields_false_excludes_fields(self):
        """Test that include_fields=False excludes field info."""
        config = AnalyzeConfig(include_fields=False)
        assert config.include_fields is False

    def test_include_fields_true_includes_fields_only(self):
        """Test that include_fields=True includes only fields (no structure)."""
        config = AnalyzeConfig(include_fields=True)
        assert config.include_fields is True


class TestAnalysisFormatting:
    """Test analysis output formatting with include_fields."""

    def test_format_analysis_without_fields(self):
        """Test output without --fields contains only basic info."""
        results = {
            "conversation_count": 10,
            "message_count": 100,
            "all_fields": {"title", "create_time"},
            "filepath": "data/conversations.json",
            "analysis_date": "14:30 20-03-2026",
            "file_size": "128.11 MB",
        }
        config = AnalyzeConfig(include_fields=False)
        output = format_analysis_text(results, config)

        # Should contain basic info
        assert "10" in output or "10" in output  # conversation count
        assert "100" in output  # message count
        # Should contain analysis date and filepath
        assert "Analysis date:" in output
        assert "File path:" in output
        assert "14:30 20-03-2026" in output
        assert "data/conversations.json" in output
        # Should NOT contain field info
        assert "ALL UNIQUE FIELD NAMES" not in output
        # Should NOT contain sample structure
        assert "SAMPLE STRUCTURE" not in output

    def test_format_analysis_with_fields(self):
        """Test output with --fields includes field info."""
        results = {
            "conversation_count": 10,
            "message_count": 100,
            "all_fields": {"title", "create_time", "mapping"},
            "filepath": "data/conversations.json",
            "analysis_date": "14:30 20-03-2026",
            "file_size": "128.11 MB",
        }
        config = AnalyzeConfig(include_fields=True)
        output = format_analysis_text(results, config)

        # Should contain basic info
        assert "10" in output
        assert "100" in output
        # Should contain analysis date and filepath
        assert "Analysis date:" in output
        assert "File path:" in output
        assert "14:30 20-03-2026" in output
        assert "data/conversations.json" in output
        # Should contain field info
        assert "ALL UNIQUE FIELD NAMES" in output
        # Should NOT contain sample structure
        assert "SAMPLE STRUCTURE" not in output

    def test_format_analysis_without_config_defaults_to_no_fields(self):
        """Test that _format_analysis without config defaults to no fields."""
        results = {
            "conversation_count": 10,
            "message_count": 100,
            "all_fields": {"title"},
            "filepath": "data/conversations.json",
            "analysis_date": "14:30 20-03-2026",
            "file_size": "128.11 MB",
        }
        output = format_analysis_text(results, None)

        # Should contain analysis date and filepath
        assert "Analysis date:" in output
        assert "File path:" in output
        # Should NOT contain field info (default)
        assert "ALL UNIQUE FIELD NAMES" not in output
        # Should NOT contain sample structure
        assert "SAMPLE STRUCTURE" not in output


class TestCLIFieldsArgument:
    """Test CLI argument parsing for --fields flag."""

    def test_default_include_fields_false(self):
        """Test that default include_fields is False when not specified."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "data.json"])
        assert args.include_fields is False

    def test_fields_flag_enables_include_fields(self):
        """Test --fields flag enables include_fields."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "--fields", "data.json"])
        assert args.include_fields is True

    def test_fields_with_other_flags(self):
        """Test --fields combined with other flags."""
        parser = create_parser()
        args = parser.parse_args(
            ["analyze", "--fields", "--output", "out.txt", "data.json"]
        )
        assert args.include_fields is True
        assert args.output == "out.txt"
