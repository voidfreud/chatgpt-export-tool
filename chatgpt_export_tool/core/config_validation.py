"""Semantic validation for runtime configuration."""

from .config_models import DefaultsConfig, TranscriptConfig
from .field_validation import FieldValidator
from .metadata_validation import validate_metadata_patterns
from .splitter import SplitMode
from .validation_models import ValidationResult


def validate_defaults_config(defaults: DefaultsConfig) -> None:
    """Validate default config values that have constrained semantics."""
    valid_formats = {"txt", "json"}
    if defaults.format_type not in valid_formats:
        raise ValueError(
            "Config value 'format' must be one of: " + ", ".join(sorted(valid_formats))
        )

    valid_split_modes = {mode.value for mode in SplitMode}
    if defaults.split_mode not in valid_split_modes:
        raise ValueError(
            "Config value 'split' must be one of: "
            + ", ".join(sorted(valid_split_modes))
        )

    validation = FieldValidator().validate_field_spec(defaults.field_spec)
    if not validation.is_valid:
        raise ValueError(
            "Config value 'fields' is invalid: " + "; ".join(validation.errors)
        )


def validate_metadata_defaults(defaults: DefaultsConfig) -> ValidationResult:
    """Validate metadata include/exclude defaults from TOML config."""
    result = ValidationResult()

    if defaults.include_metadata:
        result.merge(validate_metadata_patterns(list(defaults.include_metadata)))
    if defaults.exclude_metadata:
        result.merge(validate_metadata_patterns(list(defaults.exclude_metadata)))

    return result


def validate_transcript_config(transcript: TranscriptConfig) -> None:
    """Validate transcript policy settings."""
    valid_context_modes = {"compact", "full"}
    if transcript.user_editable_context_mode not in valid_context_modes:
        raise ValueError(
            "Config value 'user_editable_context_mode' must be one of: "
            + ", ".join(sorted(valid_context_modes))
        )

    overlap = set(transcript.include_content_types) & set(
        transcript.exclude_content_types
    )
    if overlap:
        raise ValueError(
            "Transcript content types cannot be both included and excluded: "
            + ", ".join(sorted(overlap))
        )
