"""Tests for shared command boundary behavior."""

from unittest.mock import patch

from chatgpt_export_tool.commands import BaseCommand


class _CrashCommand(BaseCommand):
    """Minimal command used to exercise shared error handling."""

    def _execute(self) -> None:
        raise RuntimeError("boom")


def test_base_command_handles_unexpected_errors_without_raising(
    tmp_path, capsys
) -> None:
    """Unexpected command errors should turn into exit code 1 and stderr output."""
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")

    result = _CrashCommand(str(data_file)).run()

    captured = capsys.readouterr()
    assert result == 1
    assert "Unexpected error - boom" in captured.err


class _PermissionCommand(BaseCommand):
    """Minimal command that fails with a permission error."""

    def _execute(self) -> None:
        raise PermissionError("nope")


class _InterruptCommand(BaseCommand):
    """Minimal command that simulates cancellation."""

    def _execute(self) -> None:
        raise KeyboardInterrupt


def test_base_command_handles_permission_errors(tmp_path, capsys) -> None:
    """Permission failures should render a clear error and exit 1."""
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")

    result = _PermissionCommand(str(data_file)).run()

    captured = capsys.readouterr()
    assert result == 1
    assert "Permission denied - nope" in captured.err


def test_base_command_handles_keyboard_interrupts(tmp_path, capsys) -> None:
    """Keyboard interrupts should return the conventional 130 exit code."""
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")

    result = _InterruptCommand(str(data_file)).run()

    captured = capsys.readouterr()
    assert result == 130
    assert "Operation cancelled by user." in captured.err


def test_base_command_handles_missing_input_file(capsys) -> None:
    """Missing input files should be caught before command execution."""
    result = _CrashCommand("/definitely/missing.json").run()

    captured = capsys.readouterr()
    assert result == 1
    assert "Error:" in captured.err


def test_base_command_prints_traceback_in_debug_mode(tmp_path, capsys) -> None:
    """Debug logging should emit a traceback for unexpected top-level errors."""
    data_file = tmp_path / "data.json"
    data_file.write_text("[]", encoding="utf-8")

    with patch("traceback.print_exc") as print_exc:
        result = _CrashCommand(str(data_file), debug=True).run()

    captured = capsys.readouterr()
    assert result == 1
    assert "Unexpected error - boom" in captured.err
    print_exc.assert_called_once()
