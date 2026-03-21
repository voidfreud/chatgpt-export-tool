"""Field group definitions shared by parsing, validation, and CLI help."""

from typing import Dict, List

# Valid field group names for CLI --fields groups option
FIELD_GROUPS: List[str] = [
    "conversation",
    "message",
    "metadata",
    "minimal",
]

# Field group to actual field mappings
# Used by FieldSelector when mode="groups"
FIELD_GROUP_MAPPING: Dict[str, List[str]] = {
    "conversation": [
        "_id",
        "conversation_id",
        "create_time",
        "update_time",
        "title",
        "type",
    ],
    "message": ["author", "content", "status", "end_turn"],
    "metadata": ["model_slug", "message_type", "is_archived"],
    "minimal": ["title", "create_time", "message"],
}

__all__ = ["FIELD_GROUPS", "FIELD_GROUP_MAPPING"]
