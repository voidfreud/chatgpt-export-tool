"""Formatting helpers for analysis output."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from chatgpt_export_tool.core.field_selector import FieldSelector
from chatgpt_export_tool.core.utils import format_timestamp, get_logger

logger = get_logger()


@dataclass
class AnalyzeConfig:
    """Configuration for analysis output.

    Attributes:
        include_fields: Whether to include field coverage details.
    """

    include_fields: bool = False


def format_analysis_text(
    results: Dict[str, Any],
    config: Optional[AnalyzeConfig] = None,
) -> str:
    """Format analysis results as human-readable text.

    Args:
        results: Analysis results dictionary.
        config: Optional analysis formatting configuration.

    Returns:
        Formatted analysis output.
    """
    if config is None:
        config = AnalyzeConfig()
        logger.debug("No analysis config provided, using defaults")

    lines = [
        "=" * 60,
        "ANALYSIS RESULTS",
        "=" * 60,
        "",
    ]

    if "analysis_date" in results:
        lines.append(f"Analysis date: {results['analysis_date']}")
    if "filepath" in results:
        lines.append(f"File path: {results['filepath']}")
    if "file_size" in results:
        lines.append(f"File size: {results['file_size']}")

    lines.append(f"Number of threads/conversations: {results['conversation_count']:,}")
    lines.append(f"Total message nodes in mappings: {results['message_count']:,}")

    if results.get("min_date") is not None and results.get("max_date") is not None:
        lines.append(f"From: {format_timestamp(results['min_date'])}")
        lines.append(f"To: {format_timestamp(results['max_date'])}")

    lines.append("")

    if config.include_fields and "all_fields" in results:
        lines.extend(
            [
                "-" * 60,
                "ALL UNIQUE FIELD NAMES FOUND:",
                "-" * 60,
            ]
        )
        sorted_fields = sorted(results["all_fields"])
        lines.append(f"Total unique fields: {len(sorted_fields)}")
        lines.append("")

        categorized = FieldSelector.categorize_fields(results["all_fields"])
        logger.debug("Field categorization: %s", list(categorized))

        for category, fields in categorized.items():
            if not fields:
                continue
            lines.append(f"{category.capitalize()}-level fields:")
            lines.append(f"  {', '.join(sorted(fields))}")
            lines.append("")

    output = "\n".join(lines)
    logger.debug("Generated analysis output with %s characters", len(output))
    return output
