"""Tests for analyze_json.py"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

import pytest


# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImportModule:
    """Test that the module can be imported."""

    def test_import_analyze_json(self):
        """Test that analyze_json module can be imported."""
        import analyze_json
        assert hasattr(analyze_json, 'analyze_json_streaming')
        assert hasattr(analyze_json, 'analyze_with_full_iteration')
        assert hasattr(analyze_json, 'format_size')
        assert hasattr(analyze_json, 'categorize_fields')
        assert hasattr(analyze_json, 'create_parser')
        assert hasattr(analyze_json, 'main')

    def test_import_ijson(self):
        """Test that ijson can be imported (or is installed)."""
        import ijson
        assert hasattr(ijson, 'items')
        assert hasattr(ijson, 'parse')


class TestFormatSize:
    """Test the format_size helper function."""

    def test_format_bytes(self):
        """Test formatting bytes."""
        from analyze_json import format_size
        assert format_size(500) == "500.00 B"
        assert format_size(0) == "0.00 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes."""
        from analyze_json import format_size
        assert "KB" in format_size(2048)
        assert "KB" in format_size(1024)

    def test_format_megabytes(self):
        """Test formatting megabytes."""
        from analyze_json import format_size
        result = format_size(5 * 1024 * 1024)
        assert "MB" in result
        assert "5.00" in result or "4.00" in result  # Allow for some rounding

    def test_format_gigabytes(self):
        """Test formatting gigabytes."""
        from analyze_json import format_size
        result = format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result


class TestCategorizeFields:
    """Test the categorize_fields function."""

    def test_categorize_conversation_fields(self):
        """Test that conversation-level fields are categorized correctly."""
        from analyze_json import categorize_fields
        fields = {'title', 'create_time', 'mapping'}
        result = categorize_fields(fields)
        assert 'title' in result['conversation']
        assert 'create_time' in result['conversation']
        assert 'mapping' in result['conversation']

    def test_categorize_message_fields(self):
        """Test that message-level fields are categorized correctly."""
        from analyze_json import categorize_fields
        fields = {'author', 'content', 'status'}
        result = categorize_fields(fields)
        assert 'author' in result['message']
        assert 'content' in result['message']
        assert 'status' in result['message']

    def test_categorize_metadata_fields(self):
        """Test that unknown fields go to metadata."""
        from analyze_json import categorize_fields
        fields = {'unknown_field', 'custom_field'}
        result = categorize_fields(fields)
        assert 'unknown_field' in result['metadata']
        assert 'custom_field' in result['metadata']

    def test_categorize_empty_fields(self):
        """Test categorizing empty field set."""
        from analyze_json import categorize_fields
        result = categorize_fields(set())
        assert result['conversation'] == []
        assert result['message'] == []
        assert result['metadata'] == []


class TestGetFileSize:
    """Test the get_file_size function."""

    def test_get_file_size_existing(self):
        """Test getting size of existing file."""
        from analyze_json import get_file_size
        # Test this very file
        size = get_file_size(__file__)
        assert size > 0
        assert isinstance(size, int)

    def test_get_file_size_nonexistent(self):
        """Test that non-existent file raises OSError."""
        from analyze_json import get_file_size
        with pytest.raises(OSError):
            get_file_size('/nonexistent/path/to/file.json')


class TestAnalyzeJsonStreaming:
    """Test the analyze_json_streaming function."""

    def test_streaming_invalid_file(self):
        """Test that invalid file raises FileNotFoundError."""
        from analyze_json import analyze_json_streaming
        with pytest.raises(FileNotFoundError):
            analyze_json_streaming('/nonexistent/file.json')


class TestAnalyzeWithFullIteration:
    """Test the analyze_with_full_iteration function."""

    def test_full_iteration_invalid_file(self):
        """Test that invalid file raises FileNotFoundError."""
        from analyze_json import analyze_with_full_iteration
        with pytest.raises(FileNotFoundError):
            analyze_with_full_iteration('/nonexistent/file.json')


class TestCLIArguments:
    """Test CLI argument parsing."""

    def test_default_file_argument(self):
        """Test that default file argument is set correctly."""
        from analyze_json import create_parser
        parser = create_parser()
        args = parser.parse_args([])
        assert args.file == '3ae/conversations.json'

    def test_custom_file_argument(self):
        """Test that custom file argument is accepted."""
        from analyze_json import create_parser
        parser = create_parser()
        args = parser.parse_args(['custom/path.json'])
        assert args.file == 'custom/path.json'

    def test_verbose_flag(self):
        """Test that verbose flag is parsed correctly."""
        from analyze_json import create_parser
        parser = create_parser()
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True
        args = parser.parse_args(['-v'])
        assert args.verbose is True

    def test_output_flag(self):
        """Test that output flag is parsed correctly."""
        from analyze_json import create_parser
        parser = create_parser()
        args = parser.parse_args(['--output', 'results.txt'])
        assert args.output == 'results.txt'
        args = parser.parse_args(['-o', 'output.json'])
        assert args.output == 'output.json'

    def test_combined_arguments(self):
        """Test that multiple arguments work together."""
        from analyze_json import create_parser
        parser = create_parser()
        args = parser.parse_args(['--verbose', '--output', 'out.txt', 'input.json'])
        assert args.verbose is True
        assert args.output == 'out.txt'
        assert args.file == 'input.json'


class TestMainFunction:
    """Test the main function behavior."""

    def test_main_file_not_found(self):
        """Test that main returns 1 for non-existent file."""
        from analyze_json import main
        with patch('sys.argv', ['analyze-json', '/nonexistent/file.json']):
            result = main()
            assert result == 1

    def test_main_with_help(self):
        """Test that main handles --help correctly."""
        from analyze_json import main
        with patch('sys.argv', ['analyze-json', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
