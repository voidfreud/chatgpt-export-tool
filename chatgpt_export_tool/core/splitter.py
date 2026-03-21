"""Split mode definitions."""

from enum import Enum


class SplitMode(Enum):
    """Split mode for export operations.

    Attributes:
        SINGLE: All conversations to one file.
        SUBJECT: Each conversation to its own file.
        DATE: Group conversations by creation date (daily folders).
        ID: Group conversations by their ID field.
    """

    SINGLE = "single"
    SUBJECT = "subject"
    DATE = "date"
    ID = "id"


__all__ = ["SplitMode"]
