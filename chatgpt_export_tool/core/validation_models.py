"""Shared validation result models."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark the result invalid.

        Args:
            message: Error message.
        """
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message.

        Args:
            message: Warning message.
        """
        self.warnings.append(message)

    def add_suggestion(self, message: str) -> None:
        """Add a suggestion message.

        Args:
            message: Suggestion message.
        """
        self.suggestions.append(message)

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one.

        Args:
            other: Validation result to merge.
        """
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.suggestions.extend(other.suggestions)

        if not other.is_valid:
            self.is_valid = False

    def __str__(self) -> str:
        """Render the validation result for human-readable display."""
        parts = []
        if self.errors:
            parts.append(f"Errors: {'; '.join(self.errors)}")
        if self.warnings:
            parts.append(f"Warnings: {'; '.join(self.warnings)}")
        if self.suggestions:
            parts.append(f"Suggestions: {'; '.join(self.suggestions)}")
        return " ".join(parts) if parts else "Valid"
