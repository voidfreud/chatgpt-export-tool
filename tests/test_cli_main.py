"""Tests for CLI main edge paths."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from chatgpt_export_tool import cli


def test_main_dispatches_export_command() -> None:
    """The CLI entry point should dispatch export commands."""
    with patch.object(cli, "export_command", return_value=7) as export_mock:
        with patch.object(
            cli,
            "create_parser",
            return_value=Mock(
                parse_args=Mock(return_value=SimpleNamespace(command="export")),
                print_help=Mock(),
            ),
        ):
            assert cli.main() == 7
            export_mock.assert_called_once()


def test_main_falls_back_to_help_for_unknown_command() -> None:
    """Unknown command values should print help and return 1."""
    parser = Mock(
        parse_args=Mock(return_value=SimpleNamespace(command="unexpected")),
        print_help=Mock(),
    )

    with patch.object(cli, "create_parser", return_value=parser):
        assert cli.main() == 1

    parser.print_help.assert_called_once()
