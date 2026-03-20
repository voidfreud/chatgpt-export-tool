"""Tests for chatgpt_export_tool core functionality."""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the new package structure
from chatgpt_export_tool.core.parser import get_file_size, format_size, JSONParser
from chatgpt_export_tool.core.field_config import FieldSelector
from chatgpt_export_tool.cli import create_parser, main


class TestImportModule:
    """Test that the module can be imported."""

    def test_import_core_modules(self):
        """Test that core modules can be imported."""
        from chatgpt_export_tool.core import JSONParser, FieldSelector, TextFormatter, JSONFormatter
        assert JSONParser is not None
        assert FieldSelector is not None
        assert TextFormatter is not None
        assert JSONFormatter is not None

    def test_import_ijson(self):
        """Test that ijson can be imported (or is installed)."""
        import ijson
        assert hasattr(ijson, 'items')
        assert hasattr(ijson, 'parse')


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
        fields = {'title', 'create_time', 'mapping'}
        result = FieldSelector.categorize_fields(fields)
        assert 'title' in result['conversation']
        assert 'create_time' in result['conversation']
        assert 'mapping' in result['conversation']

    def test_categorize_message_fields(self):
        """Test that message-level fields are categorized correctly."""
        fields = {'author', 'content', 'status'}
        result = FieldSelector.categorize_fields(fields)
        assert 'author' in result['message']
        assert 'content' in result['message']
        assert 'status' in result['message']

    def test_categorize_metadata_fields(self):
        """Test that unknown fields go to metadata."""
        fields = {'unknown_field', 'custom_field'}
        result = FieldSelector.categorize_fields(fields)
        assert 'unknown_field' in result['metadata']
        assert 'custom_field' in result['metadata']

    def test_categorize_empty_fields(self):
        """Test categorizing empty field set."""
        result = FieldSelector.categorize_fields(set())
        assert result['conversation'] == []
        assert result['message'] == []
        assert result['metadata'] == []


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
            get_file_size('/nonexistent/path/to/file.json')


class TestJSONParser:
    """Test the JSONParser class."""

    def test_parser_init_invalid_file(self):
        """Test that parser init with invalid file doesn't raise until analyze."""
        # Creating parser with non-existent file should not raise immediately
        parser = JSONParser('/nonexistent/file.json')
        assert parser.filepath == '/nonexistent/file.json'

    def test_parser_analyze_invalid_file(self):
        """Test that analyze raises FileNotFoundError for invalid file."""
        parser = JSONParser('/nonexistent/file.json')
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
        args = parser.parse_args(['analyze', 'data.json'])
        assert args.command == 'analyze'
        assert args.file == 'data.json'

    def test_export_command(self):
        """Test export subcommand parsing."""
        parser = create_parser()
        args = parser.parse_args(['export', 'data.json'])
        assert args.command == 'export'
        assert args.file == 'data.json'

    def test_verbose_flag(self):
        """Test that verbose flag is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(['analyze', '--verbose', 'data.json'])
        assert args.verbose is True

    def test_output_flag(self):
        """Test that output flag is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(['analyze', '--output', 'results.txt', 'data.json'])
        assert args.output == 'results.txt'

    def test_combined_arguments(self):
        """Test that multiple arguments work together."""
        parser = create_parser()
        args = parser.parse_args(['analyze', '--verbose', '--output', 'out.txt', 'input.json'])
        assert args.verbose is True
        assert args.output == 'out.txt'
        assert args.file == 'input.json'


class TestMainFunction:
    """Test the main function behavior."""

    def test_main_no_command(self):
        """Test that main returns 1 when no command is given."""
        with patch('sys.argv', ['chatgpt-export']):
            result = main()
            assert result == 1

    def test_main_analyze_file_not_found(self):
        """Test that analyze returns 1 for non-existent file."""
        with patch('sys.argv', ['chatgpt-export', 'analyze', '/nonexistent/file.json']):
            result = main()
            assert result == 1

    def test_main_with_help(self):
        """Test that main handles --help correctly."""
        with patch('sys.argv', ['chatgpt-export', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
