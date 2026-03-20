"""
Field configuration and selection logic.

Provides flexible field filtering/selection for export operations.
"""

import fnmatch
from typing import Set, List, Dict, Any, Optional


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


class MetadataSelector:
    """Handles metadata field inclusion/exclusion with glob pattern and partial matching.
    
    Supports:
    - Exact field names (e.g., "title", "model_slug")
    - Partial matching (e.g., "time" matches "create_time", "update_time")
    - Glob patterns (e.g., "model*" matches "model_slug", "model_name")
    - Wildcard "*" to match all metadata fields
    
    Attributes:
        include_fields: Set of field patterns to include.
        exclude_fields: Set of field patterns to exclude.
    """
    
    def __init__(self, include_fields: Optional[Set[str]] = None, 
                 exclude_fields: Optional[Set[str]] = None):
        """Initialize metadata selector.
        
        Args:
            include_fields: Set of field patterns to include.
            exclude_fields: Set of field patterns to exclude.
        """
        self.include_fields = include_fields or set()
        self.exclude_fields = exclude_fields or set()
    
    @classmethod
    def from_args(cls, include: Optional[List[str]] = None, 
                  exclude: Optional[List[str]] = None) -> "MetadataSelector":
        """Create MetadataSelector from CLI arguments.
        
        Args:
            include: List of field patterns to include.
            exclude: List of field patterns to exclude.
            
        Returns:
            Configured MetadataSelector instance.
        """
        include_fields = set(include) if include else set()
        exclude_fields = set(exclude) if exclude else set()
        return cls(include_fields=include_fields, exclude_fields=exclude_fields)
    
    def _matches_pattern(self, field_name: str, pattern: str) -> bool:
        """Check if a field name matches a pattern.
        
        Args:
            field_name: The actual field name to check.
            pattern: The pattern to match against (can be glob pattern).
            
        Returns:
            True if the field matches the pattern.
        """
        # Handle wildcard to match all
        if pattern == "*":
            return True
        
        # Handle exact match
        if field_name == pattern:
            return True
        
        # Handle partial match (field_name contains pattern)
        if pattern in field_name:
            return True
        
        # Handle glob patterns (e.g., "model*" matches "model_slug")
        if fnmatch.fnmatch(field_name, pattern):
            return True
        
        return False
    
    def _get_matching_fields(self, patterns: Set[str], 
                            available_fields: Set[str]) -> Set[str]:
        """Get all fields that match any of the given patterns.
        
        Args:
            patterns: Set of field patterns to match.
            available_fields: Set of available field names.
            
        Returns:
            Set of field names that match at least one pattern.
        """
        matching = set()
        for pattern in patterns:
            for field in available_fields:
                if self._matches_pattern(field, pattern):
                    matching.add(field)
        return matching
    
    def filter_metadata(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter conversation metadata based on include/exclude patterns.
        
        This filters the message.metadata fields within the conversation.
        If no include patterns are specified, all fields are considered available.
        If no exclude patterns are specified, no fields are excluded.
        
        Args:
            conv: Conversation dictionary potentially containing message metadata.
            
        Returns:
            Filtered conversation dictionary with metadata filtered.
        """
        result = dict(conv)
        
        # Get all metadata fields from available METADATA_FIELDS
        available_metadata = set(METADATA_FIELDS.keys())
        
        # Determine which fields to include
        if self.include_fields:
            # If include is set, only include fields matching the include patterns
            include_matches = self._get_matching_fields(self.include_fields, available_metadata)
            fields_to_keep = include_matches
        else:
            # If no include specified, all available metadata fields are candidates
            fields_to_keep = available_metadata
        
        # Apply exclusions
        if self.exclude_fields:
            exclude_matches = self._get_matching_fields(self.exclude_fields, fields_to_keep)
            fields_to_keep -= exclude_matches
        
        # Filter top-level conversation fields (metadata lives at conversation level)
        for key in list(result.keys()):
            if key in available_metadata and key not in fields_to_keep:
                del result[key]
        
        # Also filter message metadata if present (nested metadata)
        if 'mapping' in result:
            result['mapping'] = self._filter_mapping_metadata(
                result['mapping'], fields_to_keep
            )
        
        return result
    
    def _filter_mapping_metadata(self, mapping: Dict[str, Any], 
                                  fields_to_keep: Set[str]) -> Dict[str, Any]:
        """Filter metadata within message nodes of the mapping.
        
        Args:
            mapping: The conversation mapping dictionary.
            fields_to_keep: Set of metadata field names to keep.
            
        Returns:
            Filtered mapping dictionary.
        """
        if not isinstance(mapping, dict):
            return mapping
            
        filtered = {}
        for node_id, node in mapping.items():
            if isinstance(node, dict) and 'message' in node:
                msg = dict(node['message']) if node['message'] else {}
                if isinstance(msg, dict) and 'metadata' in msg:
                    metadata = msg['metadata']
                    if isinstance(metadata, dict):
                        filtered_metadata = {
                            k: v for k, v in metadata.items() 
                            if k in fields_to_keep
                        }
                        msg['metadata'] = filtered_metadata
                filtered[node_id] = node
            else:
                filtered[node_id] = node
        return filtered
    
    def get_included_fields(self) -> Set[str]:
        """Get the set of fields that will be included based on current patterns.
        
        Returns:
            Set of field names that match the include patterns.
        """
        if not self.include_fields:
            return set()
        available_metadata = set(METADATA_FIELDS.keys())
        return self._get_matching_fields(self.include_fields, available_metadata)
    
    def get_excluded_fields(self) -> Set[str]:
        """Get the set of fields that will be excluded based on current patterns.
        
        Returns:
            Set of field names that match the exclude patterns.
        """
        if not self.exclude_fields:
            return set()
        available_metadata = set(METADATA_FIELDS.keys())
        return self._get_matching_fields(self.exclude_fields, available_metadata)


class FieldSelector:
    """Handles field inclusion/exclusion with multiple modes.
    
    Attributes:
        MODES: Valid selection modes.
        GROUPS: Preset field groups for common selections.
    """
    
    MODES = ["all", "none", "include", "exclude", "groups"]
    
    # Preset groups (can be defined in fields.json or hardcoded)
    GROUPS: Dict[str, List[str]] = {
        "conversation": ["_id", "conversation_id", "create_time", "update_time", "title", "type"],
        "message": ["author", "content", "status", "end_turn"],
        "metadata": ["model_slug", "message_type", "is_archived"],
        "minimal": ["title", "create_time", "message"],
    }
    
    def __init__(self, mode: str, fields: Optional[List[str]] = None, groups: Optional[List[str]] = None):
        """Initialize field selector.
        
        Args:
            mode: Selection mode - "all", "none", "include", "exclude", or "groups".
            fields: List of field names (for include/exclude modes).
            groups: List of group names to include (for groups mode).
            
        Raises:
            ValueError: If mode is invalid or required parameters are missing.
        """
        if mode not in self.MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self.MODES}")
        
        self.mode = mode
        self.fields = fields or []
        self.groups = groups or []
        
        if mode in ("include", "exclude") and not fields:
            raise ValueError(f"Mode '{mode}' requires fields list")
        if mode == "groups" and not groups:
            raise ValueError("Mode 'groups' requires groups list")
    
    @classmethod
    def from_string(cls, field_spec: str) -> "FieldSelector":
        """Create FieldSelector from command-line string.
        
        Args:
            field_spec: String specification like "all", "include title,create_time",
                       "exclude model_slug", "groups message,minimal".
                       
        Returns:
            Configured FieldSelector instance.
        """
        parts = field_spec.split()
        
        if not parts:
            return cls(mode="all")
        
        mode = parts[0]
        
        if mode == "all":
            return cls(mode="all")
        elif mode == "none":
            return cls(mode="none")
        elif mode == "include":
            fields = parts[1].split(",") if len(parts) > 1 else []
            return cls(mode="include", fields=fields)
        elif mode == "exclude":
            fields = parts[1].split(",") if len(parts) > 1 else []
            return cls(mode="exclude", fields=fields)
        elif mode == "groups":
            group_list = parts[1].split(",") if len(parts) > 1 else []
            return cls(mode="groups", groups=group_list)
        else:
            # Assume comma-separated field names for backward compatibility
            return cls(mode="include", fields=field_spec.split(","))
    
    def get_selected_fields(self, all_fields: Set[str]) -> Set[str]:
        """Get the set of fields based on selection mode.
        
        Args:
            all_fields: Set of all available field names.
            
        Returns:
            Set of selected field names.
        """
        if self.mode == "all":
            return all_fields
        elif self.mode == "none":
            return set()
        elif self.mode == "include":
            return set(self.fields) & all_fields
        elif self.mode == "exclude":
            return all_fields - set(self.fields)
        elif self.mode == "groups":
            selected = set()
            for group_name in self.groups:
                if group_name in self.GROUPS:
                    selected.update(self.GROUPS[group_name])
                else:
                    # Try to find group in categories
                    if group_name in CATEGORY_FIELDS:
                        selected.update(CATEGORY_FIELDS[group_name])
            return selected & all_fields
        return all_fields
    
    def filter_conversation(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        """Filter conversation fields.
        
        Args:
            conv: Conversation dictionary.
            
        Returns:
            Filtered conversation dictionary.
        """
        all_fields = set(conv.keys())
        selected = self.get_selected_fields(all_fields)
        return {k: v for k, v in conv.items() if k in selected}
    
    @staticmethod
    def categorize_fields(fields: Set[str]) -> Dict[str, List[str]]:
        """Categorize field names by their hierarchical level.
        
        Args:
            fields: Set of all field names.
            
        Returns:
            Dictionary mapping category names to lists of field names.
        """
        categorized: Dict[str, List[str]] = {
            'conversation': [],
            'mapping': [],
            'message': [],
            'author': [],
            'content': [],
            'metadata': []
        }
        
        # Build set of all categorized fields for fast lookup
        all_categorized = set()
        for cat_fields in CATEGORY_FIELDS.values():
            all_categorized.update(cat_fields)
        
        # Categorize each field
        for field in sorted(fields):
            found = False
            for category, cat_fields in CATEGORY_FIELDS.items():
                if field in cat_fields:
                    categorized[category].append(field)
                    found = True
                    break
            if not found:
                categorized['metadata'].append(field)
        
        return categorized
