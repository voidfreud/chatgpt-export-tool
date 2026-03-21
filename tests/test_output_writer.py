"""
Tests for output_writer module.

Tests FileNamer, WriteResult, and OutputWriter classes.
"""

from pathlib import Path
from typing import Dict, List, Optional

from chatgpt_export_tool.core.conversation_formatters import TextFormatter
from chatgpt_export_tool.core.output_writer import (
    FileNamer,
    OutputWriter,
    WriteJob,
    WriteResult,
)
from chatgpt_export_tool.core.output_paths import OutputPathResolver
from chatgpt_export_tool.core.splitter import SplitMode


class TestFileNamer:
    """Tests for FileNamer class."""

    def test_init_default_max_length(self):
        """Test FileNamer initializes with default max_length."""
        namer = FileNamer()
        assert namer.max_length == 200

    def test_init_custom_max_length(self):
        """Test FileNamer initializes with custom max_length."""
        namer = FileNamer(max_length=100)
        assert namer.max_length == 100

    def test_sanitize_replaces_invalid_chars(self):
        """Test sanitize replaces invalid filename characters."""
        namer = FileNamer()

        # < and > are replaced with underscore, then collapsed
        assert namer.sanitize("file<name>") == "file_name"
        # : is in INVALID_CHARS
        assert namer.sanitize("file:name") == "file_name"
        # \ is replaced
        assert namer.sanitize("file\\name") == "file_name"
        # " is replaced
        assert namer.sanitize('file"name') == "file_name"

    def test_sanitize_collapses_underscores(self):
        """Test sanitize collapses multiple underscores."""
        namer = FileNamer()

        assert namer.sanitize("file___name") == "file_name"
        # ## is not invalid, so stays; underscores collapse
        assert namer.sanitize("file__##__name") == "file_##_name"

    def test_sanitize_strips_leading_trailing_underscores(self):
        """Test sanitize strips leading and trailing underscores."""
        namer = FileNamer()

        assert namer.sanitize("_file_name_") == "file_name"
        # Spaces are preserved (not invalid chars), only underscores stripped
        # Input has spaces, then underscores, then spaces
        assert namer.sanitize("  _file_  ") == "_file_"

    def test_sanitize_replaces_spaces(self):
        """Test sanitize replaces spaces with underscores."""
        namer = FileNamer()

        assert namer.sanitize("file name") == "file_name"
        assert namer.sanitize("my conversation") == "my_conversation"

    def test_sanitize_truncates_long_titles(self):
        """Test sanitize truncates very long titles."""
        namer = FileNamer(max_length=20)

        long_title = "a" * 100
        result = namer.sanitize(long_title)
        assert len(result) == 20
        assert result.endswith("...")

    def test_sanitize_empty_string(self):
        """Test sanitize handles empty string."""
        namer = FileNamer()
        assert namer.sanitize("") == "untitled"

    def test_sanitize_none(self):
        """Test sanitize handles None."""
        namer = FileNamer()
        assert namer.sanitize(None) == "untitled"

    def test_get_filename(self):
        """Test get_filename returns sanitized title with extension."""
        namer = FileNamer()

        conv = {"title": "My Conversation"}
        filename = namer.get_filename(conv, "txt")

        assert filename == "My_Conversation.txt"

    def test_get_filename_default_extension(self):
        """Test get_filename uses 'txt' as default extension."""
        namer = FileNamer()

        conv = {"title": "Test"}
        filename = namer.get_filename(conv)

        assert filename == "Test.txt"

    def test_get_filename_falls_back_to_untitled(self):
        """Test get_filename uses 'untitled' when no title."""
        namer = FileNamer()

        conv = {}
        filename = namer.get_filename(conv)

        assert filename == "untitled.txt"


class TestWriteResult:
    """Tests for WriteResult dataclass."""

    def test_default_values(self):
        """Test WriteResult default values."""
        result = WriteResult()

        assert result.files_written == 0
        assert result.directories_created == 0
        assert result.total_bytes == 0
        assert result.errors == []

    def test_add_error(self):
        """Test add_error appends to errors list."""
        result = WriteResult()
        result.add_error("Test error")

        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_merge(self):
        """Test merge combines two WriteResults."""
        result1 = WriteResult(files_written=2, total_bytes=100)
        result2 = WriteResult(files_written=3, total_bytes=200, directories_created=1)

        result1.merge(result2)

        assert result1.files_written == 5
        assert result1.total_bytes == 300
        assert result1.directories_created == 1
        assert result1.errors == []

    def test_merge_preserves_errors(self):
        """Test merge combines errors from both results."""
        result1 = WriteResult()
        result1.add_error("Error 1")

        result2 = WriteResult()
        result2.add_error("Error 2")

        result1.merge(result2)

        assert len(result1.errors) == 2
        assert "Error 1" in result1.errors
        assert "Error 2" in result1.errors


class TestOutputWriter:
    """Tests for OutputWriter class."""

    def test_init_default_values(self):
        """Test OutputWriter initializes with correct defaults."""
        writer = OutputWriter()

        assert writer.output_dir == Path("output")
        assert writer.format_type == "txt"
        assert writer.split_mode is None

    def test_init_with_values(self):
        """Test OutputWriter initializes with custom values."""
        writer = OutputWriter(
            output_dir="/custom/path",
            format_type="json",
            split_mode=SplitMode.DATE,
        )

        assert writer.output_dir == Path("/custom/path")
        assert writer.format_type == "json"
        assert writer.split_mode == SplitMode.DATE

    def test_path_resolution_subject_mode_uses_title_plus_id(self):
        """Subject-mode filenames should include the source identifier."""
        resolver = OutputPathResolver(
            output_dir="/output", split_mode=SplitMode.SUBJECT
        )

        path = resolver.get_filepath({"title": "Test", "id": "123"}, "Test_123")

        assert path == Path("/output/Test_123.txt")

    def test_write_conversations_single_group(self, tmp_path):
        """Test write_jobs with two conversations."""
        writer = OutputWriter(output_dir=str(tmp_path), format_type="txt")

        jobs = [
            WriteJob(
                source_conversation={"title": "Conv 1", "id": "1"},
                rendered_conversation={"title": "Conv 1", "id": "1"},
                group_key="all",
            ),
            WriteJob(
                source_conversation={"title": "Conv 2", "id": "2"},
                rendered_conversation={"title": "Conv 2", "id": "2"},
                group_key="all",
            ),
        ]

        formatter = TextFormatter()
        result = writer.write_jobs(jobs, formatter)

        assert result.files_written == 2
        assert result.total_bytes > 0
        assert len(result.errors) == 0

    def test_write_jobs_reports_real_utf8_bytes(self, tmp_path):
        """total_bytes should track encoded byte count, not character count."""
        writer = OutputWriter(output_dir=str(tmp_path), format_type="txt")
        jobs = [
            WriteJob(
                source_conversation={"title": "Emoji", "id": "1"},
                rendered_conversation={
                    "title": "Emoji",
                    "id": "1",
                    "mapping": {
                        "node": {
                            "message": {
                                "author": {"role": "assistant"},
                                "content": {"parts": ["hello €"]},
                            }
                        }
                    },
                },
                group_key="all",
            )
        ]

        result = writer.write_jobs(jobs, TextFormatter())

        written_file = next(tmp_path.iterdir())
        expected_bytes = written_file.read_bytes()
        assert result.total_bytes == len(expected_bytes)

    def test_write_conversations_date_mode(self, tmp_path):
        """Test write_jobs with DATE mode creates subdirs."""
        writer = OutputWriter(
            output_dir=str(tmp_path),
            format_type="txt",
            split_mode=SplitMode.DATE,
        )

        jobs = [
            WriteJob(
                source_conversation={"title": "Conv 1", "id": "1"},
                rendered_conversation={"title": "Conv 1", "id": "1"},
                group_key="2024-03-01",
            ),
            WriteJob(
                source_conversation={"title": "Conv 2", "id": "2"},
                rendered_conversation={"title": "Conv 2", "id": "2"},
                group_key="2024-03-02",
            ),
        ]

        formatter = TextFormatter()
        result = writer.write_jobs(jobs, formatter)

        assert result.files_written == 2
        assert result.directories_created == 2
        assert (tmp_path / "2024-03-01").exists()
        assert (tmp_path / "2024-03-02").exists()

    def test_write_conversations_creates_output_dir(self, tmp_path):
        """Test write_jobs creates output directory if missing."""
        writer = OutputWriter(
            output_dir=str(tmp_path / "nonexistent"), format_type="txt"
        )

        jobs = [
            WriteJob(
                source_conversation={"title": "Conv 1", "id": "1"},
                rendered_conversation={"title": "Conv 1", "id": "1"},
                group_key="all",
            )
        ]

        formatter = TextFormatter()
        result = writer.write_jobs(jobs, formatter)

        # Directory should be created and write should succeed
        assert (tmp_path / "nonexistent").exists()
        assert result.files_written == 1
        assert len(result.errors) == 0


class TestOutputWriterEdgeCases:
    """Edge case tests for OutputWriter."""

    def test_write_empty_groups(self, tmp_path):
        """Test write_jobs with an empty job list."""
        writer = OutputWriter(output_dir=str(tmp_path), format_type="txt")

        formatter = TextFormatter()
        result = writer.write_jobs([], formatter)

        assert result.files_written == 0

    def test_write_conversations_multiple_groups(self, tmp_path):
        """Test write_jobs handles multiple groups correctly."""
        writer = OutputWriter(output_dir=str(tmp_path / "output"), format_type="txt")

        jobs = [
            WriteJob(
                source_conversation={"title": "Conv 1", "id": "1"},
                rendered_conversation={"title": "Conv 1", "id": "1"},
                group_key="group1",
            ),
            WriteJob(
                source_conversation={"title": "Conv 2", "id": "2"},
                rendered_conversation={"title": "Conv 2", "id": "2"},
                group_key="group2",
            ),
        ]

        formatter = TextFormatter()
        result = writer.write_jobs(jobs, formatter)

        # Both groups should succeed
        assert result.files_written == 2
        assert len(result.errors) == 0


class TestTextFormatterTruncationFix:
    """Tests verifying that the truncation bugs in TextFormatter are fixed.

    Regression tests for three bugs:
    1. format_conversation() hard-truncated message text at 200 chars
    2. _format_dict() hard-truncated dict values at 100 chars
    3. format_conversation() only extracted parts[0] from multi-part messages
    """

    # -- Helper to build a minimal conversation dict with mapping --

    @staticmethod
    def _make_conversation(
        title: str = "Test",
        parts: Optional[List[str]] = None,
        role: str = "user",
    ) -> Dict[str, object]:
        """Build a minimal conversation dict with a single mapping node.

        Args:
            title: Conversation title.
            parts: List of content parts for the message. Defaults to ["hello"].
            role: Author role for the message.

        Returns:
            Conversation dictionary suitable for TextFormatter.format_conversation().
        """
        if parts is None:
            parts = ["hello"]
        return {
            "title": title,
            "id": "conv-1",
            "create_time": 1709337600.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "author": {"role": role},
                        "content": {"parts": parts},
                    }
                }
            },
        }

    # -- 1. Long messages must NOT be truncated --

    def test_format_conversation_long_message_not_truncated(self):
        """A message longer than 200 chars must appear in full (no '...' suffix)."""
        long_text = "A" * 500
        conv = self._make_conversation(parts=[long_text])

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)
        normalized_output = output.replace("\n", "").replace(" ", "")

        # The full text must be present — not just the first 200 chars + "..."
        assert long_text in normalized_output, (
            "Message content was truncated; expected full 500-char string in output"
        )

    def test_format_conversation_very_long_message_preserved(self):
        """A message of 2000+ chars must be fully preserved."""
        long_text = "X" * 2000
        conv = self._make_conversation(parts=[long_text])

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)
        normalized_output = output.replace("\n", "").replace(" ", "")

        assert long_text in normalized_output, (
            "Very long message (2000 chars) was truncated"
        )

    # -- 2. Multi-part messages must be fully captured --

    def test_format_conversation_multi_part_message(self):
        """All parts from a multi-part message must appear in the output."""
        part1 = "First part of the message"
        part2 = "Second part of the message"
        conv = self._make_conversation(parts=[part1, part2])

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        assert part1 in output, "First content part is missing from output"
        assert part2 in output, "Second content part is missing from output"

    def test_format_conversation_three_parts(self):
        """Messages with three parts should have all three in output."""
        parts = ["Alpha", "Beta", "Gamma"]
        conv = self._make_conversation(parts=parts)

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        for part in parts:
            assert part in output, f"Content part '{part}' is missing from output"

    def test_format_conversation_empty_parts(self):
        """A message with empty parts should be skipped rather than rendered blank."""
        conv = self._make_conversation(parts=[])

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        assert "\nUser:\n" not in output

    def test_format_conversation_single_part_unchanged(self):
        """Regression: a single-part message should still work correctly."""
        conv = self._make_conversation(parts=["only part"])

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        assert "only part" in output

    def test_format_conversation_skips_empty_message_nodes(self):
        """Blank mapping nodes should not be rendered as empty chat turns."""
        conv = {
            "title": "Test",
            "id": "conv-1",
            "create_time": 1709337600.0,
            "mapping": {
                "node-1": {
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": []},
                    }
                },
                "node-2": {
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["real text"]},
                    }
                },
            },
        }

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        assert "User:\n  real text" in output
        assert "\nAssistant:\n" not in output
        assert "Messages (" not in output

    def test_format_conversation_uses_current_branch_and_timestamps(self):
        """Text formatting should follow the active branch and include timestamps."""
        conv = {
            "title": "Test",
            "id": "conv-1",
            "create_time": 1709337600.0,
            "current_node": "assistant-final",
            "mapping": {
                "root": {"parent": None, "message": None},
                "user-1": {
                    "parent": "root",
                    "message": {
                        "author": {"role": "user"},
                        "content": {"parts": ["question"]},
                        "create_time": 1709337600.0,
                    },
                },
                "assistant-draft": {
                    "parent": "user-1",
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["draft"]},
                        "create_time": 1709337601.0,
                    },
                },
                "assistant-final": {
                    "parent": "user-1",
                    "message": {
                        "author": {"role": "assistant"},
                        "content": {"parts": ["final answer"]},
                        "create_time": 1709337602.0,
                    },
                },
            },
        }

        formatter = TextFormatter()
        output = formatter.format_conversation(conv)

        assert "question" in output
        assert "final answer" in output
        assert "draft" not in output
        assert "User" in output
        assert "Assistant" in output
