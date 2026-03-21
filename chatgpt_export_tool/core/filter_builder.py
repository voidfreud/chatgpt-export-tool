"""Factory helpers for runtime filter construction."""

import logging

from .field_selector import FieldSelector
from .filter_models import FilterConfig, FilterResult
from .metadata_selector import MetadataSelector
from .validators import get_validator


def build_filter_result(
    config: FilterConfig,
    raise_on_invalid: bool,
    logger: logging.Logger,
) -> FilterResult:
    """Create selectors and validation state for a filter configuration.

    Args:
        config: Filter configuration.
        raise_on_invalid: Whether to raise on validation errors.
        logger: Logger for validation warnings.

    Returns:
        Build result with selectors and validation state.
    """
    result = FilterResult()
    validator = get_validator()

    if config.validate:
        validation = validator.validate_field_spec(config.field_spec)
        result.validation = validation

        if not validation.is_valid and raise_on_invalid:
            raise ValueError(
                f"Invalid field spec: {config.field_spec}. Errors: {validation.errors}"
            )

        for warning in validation.warnings:
            logger.warning(warning)

    result.field_selector = FieldSelector.from_string(config.field_spec)
    result.applied_filters.append(f"fields={config.field_spec}")

    if config.include_metadata or config.exclude_metadata:
        result.metadata_selector = MetadataSelector.from_args(
            include=config.include_metadata,
            exclude=config.exclude_metadata,
        )
        result.applied_filters.append(
            "metadata: include="
            f"{config.include_metadata or []}, exclude={config.exclude_metadata or []}"
        )

    return result
