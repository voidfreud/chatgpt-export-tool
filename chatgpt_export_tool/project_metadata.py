"""Project metadata helpers."""

from pathlib import Path

try:  # pragma: no cover - Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


def read_project_version() -> str:
    """Read the package version from ``pyproject.toml``."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as handle:
        payload = tomllib.load(handle)

    project = payload.get("project")
    if not isinstance(project, dict):
        raise RuntimeError("Unable to determine package version from pyproject.toml")

    version = project.get("version")
    if not isinstance(version, str):
        raise RuntimeError("Unable to determine package version from pyproject.toml")
    return version
