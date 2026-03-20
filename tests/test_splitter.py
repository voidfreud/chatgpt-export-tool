"""
Tests for splitter module.

Tests SplitMode enum, SplitProcessor class, and splitting logic.
"""

from unittest.mock import MagicMock, patch

import pytest

from chatgpt_export_tool.core.splitter import SplitMode, SplitProcessor, SplitResult


class TestSplitMode:
    """Tests for SplitMode enum."""

    def test_split_mode_values(self):
        """Test SplitMode enum has expected values."""
        assert SplitMode.SINGLE.value == "single"
        assert SplitMode.SUBJECT.value == "subject"
        assert SplitMode.DATE.value == "date"

    def test_split_mode_from_string(self):
        """Test creating SplitMode from string."""
        assert SplitMode("single") == SplitMode.SINGLE
        assert SplitMode("subject") == SplitMode.SUBJECT
        assert SplitMode("date") == SplitMode.DATE


class TestSplitResult:
    """Tests for SplitResult dataclass."""

    def test_default_values(self):
        """Test SplitResult default values."""
        result = SplitResult(mode=SplitMode.SINGLE)

        assert result.mode == SplitMode.SINGLE
        assert result.groups == {}
        assert result.total_conversations == 0
        assert result.group_count == 0

    def test_with_groups(self):
        """Test SplitResult with groups provided."""
        groups = {
            "2024-01-01": [{"title": "Conv 1"}, {"title": "Conv 2"}],
            "2024-01-02": [{"title": "Conv 3"}],
        }
        result = SplitResult(mode=SplitMode.DATE, groups=groups)

        assert result.total_conversations == 3
        assert result.group_count == 2

    def test_total_conversations_calculation(self):
        """Test total_conversations is calculated from groups."""
        groups: dict = {
            "group1": [{"id": 1}, {"id": 2}, {"id": 3}],
            "group2": [{"id": 4}, {"id": 5}],
        }
        result = SplitResult(mode=SplitMode.SUBJECT, groups=groups)

        assert result.total_conversations == 5
        assert result.group_count == 2


class TestSplitProcessor:
    """Tests for SplitProcessor class."""

    def test_init_default_mode(self):
        """Test SplitProcessor initializes with SINGLE mode by default."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser)

        assert processor.mode == SplitMode.SINGLE
        assert processor.parser == mock_parser

    def test_init_with_mode(self):
        """Test SplitProcessor initializes with specified mode."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        assert processor.mode == SplitMode.DATE

    def test_get_group_key_single(self):
        """Test _get_group_key returns 'all' for SINGLE mode."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.SINGLE)

        conv = {"title": "Test", "id": "123"}
        assert processor._get_group_key(conv) == "all"

    def test_get_group_key_subject(self):
        """Test _get_group_key returns title_id for SUBJECT mode."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.SUBJECT)

        conv = {"title": "My Conversation", "id": "abc123"}
        key = processor._get_group_key(conv)

        assert key == "My Conversation_abc123"

    def test_get_group_key_subject_no_id(self):
        """Test _get_group_key falls back to _id for SUBJECT mode."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.SUBJECT)

        conv = {"title": "My Conversation", "_id": "xyz789"}
        key = processor._get_group_key(conv)

        assert key == "My Conversation_xyz789"

    def test_get_group_key_subject_no_id_fallback(self):
        """Test _get_group_key falls back to 'unknown' when no id."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.SUBJECT)

        conv = {"title": "My Conversation"}
        key = processor._get_group_key(conv)

        assert key == "My Conversation_unknown"

    def test_get_group_key_subject_uses_title(self):
        """Test _get_group_key uses 'untitled' when no title."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.SUBJECT)

        conv = {"id": "123"}
        key = processor._get_group_key(conv)

        assert key == "untitled_123"

    def test_get_group_key_date(self):
        """Test _get_group_key returns date string for DATE mode."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        # Use noon UTC to avoid timezone issues
        conv = {"title": "Test", "create_time": 1709294400.0}  # 2024-03-01 12:00:00 UTC
        key = processor._get_group_key(conv)

        assert key == "2024-03-01"

    def test_get_group_key_date_no_timestamp(self):
        """Test _get_group_key returns 'unknown_date' when no create_time."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        conv = {"title": "Test"}
        key = processor._get_group_key(conv)

        assert key == "unknown_date"

    def test_process_single_mode(self):
        """Test process with SINGLE mode returns single group."""
        mock_parser = MagicMock()
        mock_parser.iterate_conversations.return_value = iter(
            [
                {"title": "Conv 1"},
                {"title": "Conv 2"},
            ]
        )
        processor = SplitProcessor(mock_parser, mode=SplitMode.SINGLE)

        result = processor.process()

        assert result.mode == SplitMode.SINGLE
        assert "all" in result.groups
        assert len(result.groups["all"]) == 2
        assert result.total_conversations == 2
        assert result.group_count == 1

    def test_process_subject_mode(self):
        """Test process with SUBJECT mode creates group per conversation."""
        mock_parser = MagicMock()
        mock_parser.iterate_conversations.return_value = iter(
            [
                {"title": "Conv 1", "id": "1"},
                {"title": "Conv 2", "id": "2"},
            ]
        )
        processor = SplitProcessor(mock_parser, mode=SplitMode.SUBJECT)

        result = processor.process()

        assert result.mode == SplitMode.SUBJECT
        assert result.group_count == 2
        assert result.total_conversations == 2

    def test_process_date_mode_groups_by_date(self):
        """Test process with DATE mode groups conversations by date."""
        mock_parser = MagicMock()
        # Use noon UTC timestamps to avoid timezone issues
        # 2024-03-01 12:00 UTC = 1709294400
        # 2024-03-02 12:00 UTC = 1709380800
        mock_parser.iterate_conversations.return_value = iter(
            [
                {"title": "Conv 1", "create_time": 1709294400.0},  # 2024-03-01
                {"title": "Conv 2", "create_time": 1709294400.0},  # 2024-03-01
                {"title": "Conv 3", "create_time": 1709380800.0},  # 2024-03-02
            ]
        )
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        result = processor.process()

        assert result.mode == SplitMode.DATE
        assert result.group_count == 2
        assert result.total_conversations == 3
        assert len(result.groups["2024-03-01"]) == 2
        assert len(result.groups["2024-03-02"]) == 1


class TestSplitProcessorEdgeCases:
    """Edge case tests for SplitProcessor."""

    def test_process_empty_file(self):
        """Test process with empty file."""
        mock_parser = MagicMock()
        mock_parser.iterate_conversations.return_value = iter([])
        processor = SplitProcessor(mock_parser, mode=SplitMode.SINGLE)

        result = processor.process()

        assert result.total_conversations == 0
        assert result.group_count == 0
        assert result.groups == {}

    def test_get_group_key_invalid_timestamp(self):
        """Test _get_group_key handles invalid timestamp."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        conv = {"title": "Test", "create_time": "invalid"}
        key = processor._get_group_key(conv)

        assert key == "unknown_date"

    def test_get_group_key_negative_timestamp(self):
        """Test _get_group_key handles negative timestamp."""
        mock_parser = MagicMock()
        processor = SplitProcessor(mock_parser, mode=SplitMode.DATE)

        conv = {"title": "Test", "create_time": -1.0}
        key = processor._get_group_key(conv)

        # Should return a valid date string or unknown_date
        assert key is not None
