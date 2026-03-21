"""Docs and packaging contract tests for the cleaned CLI surface."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FIELDS = ROOT / "Fields.md"
PYPROJECT = ROOT / "pyproject.toml"


def test_readme_examples_match_current_documented_cli() -> None:
    """README should describe the intended cleaned CLI and development workflow."""
    text = README.read_text()

    verbose_example = "chatgpt-export analyze path/to/conversations.json --verbose"
    debug_example = "chatgpt-export analyze path/to/conversations.json --debug"
    fields_example = (
        "chatgpt-export export path/to/conversations.json --fields "
        '"include title,create_time"'
    )

    assert verbose_example in text
    assert debug_example in text
    assert fields_example in text
    assert "uv sync --group dev" in text
    assert "uv add --group dev pytest pytest-cov ruff" in text
    assert "Sample conversation structure" not in text
    assert "--verbosity full" not in text
    assert "└── data/" not in text


def test_fields_reference_uses_current_command_name() -> None:
    """Fields.md should use the current command name and composition story."""
    text = FIELDS.read_text()

    include_example = (
        "chatgpt-export export input.json --include title create_time model_slug"
    )
    exclude_example = (
        "chatgpt-export export input.json --exclude plugin_ids moderation_results"
    )

    assert include_example in text
    assert exclude_example in text
    assert "chatgpt-export analyze input.json --fields" in text
    assert "chatgpt export" not in text
    assert "mutually exclusive" not in text.lower()


def test_pyproject_uses_package_discovery_and_dev_group() -> None:
    """Packaging should discover subpackages automatically and keep dev tools grouped."""
    text = PYPROJECT.read_text()

    project_block = text.split("[project]")[1].split("[project.scripts]")[0]
    dependency_groups = text.split("[dependency-groups]")[1]

    assert "[tool.setuptools.packages.find]" in text
    assert 'include = ["chatgpt_export_tool*"]' in text
    assert 'packages = ["chatgpt_export_tool"' not in text
    assert "pytest>=7.0.0" not in project_block
    assert "pytest>=7.0.0" in dependency_groups
    assert "ruff>=0.15.7" in text
