"""Docs and packaging contract tests for the cleaned CLI surface."""

from pathlib import Path

from chatgpt_export_tool.cli import create_parser


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FIELDS = ROOT / "Fields.md"
PYPROJECT = ROOT / "pyproject.toml"


def test_readme_examples_match_current_documented_cli() -> None:
    """README should describe the intended cleaned CLI and development workflow."""
    text = README.read_text()

    assert "Python `3.10+`" in text
    assert "https://github.com/voidfreud/chatgpt-export-tool.git" in text
    assert "uv run chatgpt-export analyze data.json --debug" in text
    assert 'uv run chatgpt-export export data.json --fields "groups minimal"' in text
    assert "uv sync --group dev" in text
    assert "Single-file export buffers formatted output" not in text
    assert "Python 3.7 or higher" not in text
    assert "--verbosity full" not in text


def test_fields_reference_uses_current_command_name() -> None:
    """Fields.md should use the current command name and composition story."""
    text = FIELDS.read_text()

    assert 'chatgpt-export export data.json --fields "groups minimal"' in text
    assert "chatgpt-export export data.json --include model_slug" in text
    assert (
        'chatgpt-export export data.json --include "model*" --exclude plugin_ids'
        in text
    )
    assert "analyze --fields" in text
    assert "chatgpt export" not in text
    assert "approximately 160 unique fields" not in text.lower()


def test_pyproject_uses_package_discovery_and_dev_group() -> None:
    """Packaging should discover subpackages automatically and keep dev tools grouped."""
    text = PYPROJECT.read_text()

    project_block = text.split("[project]")[1].split("[project.scripts]")[0]
    dependency_groups = text.split("[dependency-groups]")[1]

    assert "[tool.setuptools.packages.find]" in text
    assert 'include = ["chatgpt_export_tool*"]' in text
    assert 'packages = ["chatgpt_export_tool"' not in text
    assert 'requires-python = ">=3.10"' in text
    assert "pytest>=7.0.0" not in project_block
    assert "pytest>=7.0.0" in dependency_groups
    assert "ruff>=0.15.7" in text


def test_documented_examples_parse_with_current_cli() -> None:
    """Representative README and Fields examples should parse as documented."""
    parser = create_parser()
    examples = [
        ["analyze", "data.json"],
        ["analyze", "data.json", "--fields"],
        ["analyze", "data.json", "--verbose", "--output", "analysis.txt"],
        ["export", "data.json"],
        ["export", "data.json", "--format", "json", "--output", "conversations.json"],
        ["export", "data.json", "--split", "subject", "--output-dir", "exports"],
        ["export", "data.json", "--fields", "groups minimal"],
        [
            "export",
            "data.json",
            "--fields",
            "include title,mapping",
            "--include",
            "model*",
            "--exclude",
            "plugin_ids",
        ],
    ]

    for example in examples:
        args = parser.parse_args(example)
        assert args.command in {"analyze", "export"}
