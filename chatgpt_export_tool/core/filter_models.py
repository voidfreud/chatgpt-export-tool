"""Shared models for runtime filter configuration."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FilterConfig:
    """Configuration for conversation filtering."""

    field_spec: str = "all"
    include_metadata: Optional[List[str]] = None
    exclude_metadata: Optional[List[str]] = None
    validate: bool = True
