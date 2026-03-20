"""
Field selection logic.

Provides FieldSelector class for handling field inclusion/exclusion
with multiple modes (all, none, include, exclude, groups).
"""

from typing import Set, List, Dict, Any, Optional

from .category_fields import CATEGORY_FIELDS


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
