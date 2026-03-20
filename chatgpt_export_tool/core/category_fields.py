"""
Field category definitions.

Single source of truth for field categories used by FieldSelector
to categorize fields by hierarchical level.
"""

from typing import Dict, List


# Single source of truth for field categories
# Used by FieldSelector.categorize_fields() to categorize fields by hierarchical level
CATEGORY_FIELDS: Dict[str, List[str]] = {
    'conversation': ["title", "create_time", "update_time", "mapping", 
                     "moderation_results", "current_node", "plugin_ids", 
                     "_id", "conversation_id", "type"],
    'mapping': ["id", "parent", "children", "message"],
    'message': ["author", "content", "status", "end_turn", "weight", 
                "recipient", "channel", "create_time", "update_time"],
    'author': ["role", "name"],
    'content': ["content_type", "parts", "language", "response_format_name", 
                "text", "user_profile", "user_instructions"],
}


# Metadata fields available in conversation message.metadata
# These are the user-facing names that can be used with --include/--exclude
METADATA_FIELDS: Dict[str, str] = {
    "id": "Conversation ID",
    "title": "Conversation title",
    "create_time": "Creation timestamp",
    "update_time": "Last update timestamp",
    "model_slug": "Model identifier",
    "message_type": "Message type indicator",
    "plugin_ids": "List of plugin IDs used",
    "conversation_id": "Conversation UUID",
    "type": "Conversation type",
    "moderation_results": "Moderation check results",
    "current_node": "Current node in conversation tree",
    "is_archived": "Archive status",
}
