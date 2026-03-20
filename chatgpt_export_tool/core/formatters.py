"""
Output formatters for ChatGPT export data.

Provides text, JSON, and future CSV formatting support.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseFormatter(ABC):
    """Abstract base class for output formatters."""
    
    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation.
        
        Args:
            data: Data to format.
            
        Returns:
            Formatted string output.
        """
        pass
    
    @abstractmethod
    def format_conversation(self, conv: Dict[str, Any], field_selector=None) -> str:
        """Format a single conversation.
        
        Args:
            conv: Conversation dictionary.
            field_selector: Optional FieldSelector to filter fields.
            
        Returns:
            Formatted conversation string.
        """
        pass


class TextFormatter(BaseFormatter):
    """Human-readable text formatter."""
    
    def __init__(self, include_header: bool = True, indent: str = "  "):
        """Initialize text formatter.
        
        Args:
            include_header: Whether to include headers in output.
            indent: String to use for indentation.
        """
        self.include_header = include_header
        self.indent = indent
    
    def format(self, data: Any) -> str:
        """Format data as human-readable text.
        
        Args:
            data: Data to format (can be analysis results or conversations).
            
        Returns:
            Formatted text string.
        """
        if isinstance(data, dict):
            if 'conversation_count' in data and 'message_count' in data:
                return self._format_analysis(data)
            return self._format_dict(data)
        elif isinstance(data, list):
            return self._format_list(data)
        else:
            return str(data)
    
    def _format_analysis(self, results: Dict[str, Any]) -> str:
        """Format analysis results as text.
        
        Args:
            results: Analysis results dictionary.
            
        Returns:
            Formatted analysis text.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ANALYSIS RESULTS")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Top-level structure: JSON Array of conversation objects")
        lines.append(f"Number of threads/conversations: {results['conversation_count']:,}")
        lines.append(f"Total message nodes in mappings: {results['message_count']:,}")
        lines.append("")
        
        if 'all_fields' in results:
            lines.append("-" * 60)
            lines.append("ALL UNIQUE FIELD NAMES FOUND:")
            lines.append("-" * 60)
            sorted_fields = sorted(results['all_fields'])
            lines.append(f"Total unique fields: {len(sorted_fields)}")
            lines.append("")
            
            # Categorize and display fields
            from chatgpt_export_tool.core.field_config import FieldSelector
            categorized = FieldSelector.categorize_fields(results['all_fields'])
            
            for category, fields in categorized.items():
                if fields:
                    lines.append(f"{category.capitalize()}-level fields:")
                    lines.append(f"  {', '.join(sorted(fields))}")
                    lines.append("")
        
        if results.get('sample_conversation'):
            lines.append("-" * 60)
            lines.append("SAMPLE STRUCTURE (first conversation):")
            lines.append("-" * 60)
            for key, value in results['sample_conversation'].items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def _format_dict(self, data: Dict[str, Any], level: int = 0) -> str:
        """Format dictionary as text.
        
        Args:
            data: Dictionary to format.
            level: Indentation level.
            
        Returns:
            Formatted dictionary text.
        """
        lines = []
        prefix = self.indent * level
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_dict(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: [{len(value)} items]")
            else:
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:100] + "..."
                lines.append(f"{prefix}{key}: {str_value}")
        
        return "\n".join(lines)
    
    def _format_list(self, data: List[Any]) -> str:
        """Format list as text.
        
        Args:
            data: List to format.
            
        Returns:
            Formatted list text.
        """
        lines = []
        for i, item in enumerate(data):
            lines.append(f"[{i}] {item}")
        return "\n".join(lines)
    
    def format_conversation(self, conv: Dict[str, Any], field_selector=None) -> str:
        """Format a single conversation as text.
        
        Args:
            conv: Conversation dictionary.
            field_selector: Optional FieldSelector to filter fields.
            
        Returns:
            Formatted conversation text.
        """
        if field_selector:
            conv = field_selector.filter_conversation(conv)
        
        lines = []
        lines.append("-" * 40)
        lines.append(f"Title: {conv.get('title', 'N/A')}")
        lines.append(f"ID: {conv.get('id', conv.get('_id', 'N/A'))}")
        lines.append(f"Created: {conv.get('create_time', 'N/A')}")
        lines.append("")
        
        if 'mapping' in conv and conv['mapping']:
            lines.append(f"Messages ({len(conv['mapping'])} nodes):")
            for node_id, node in conv['mapping'].items():
                if 'message' in node and node['message']:
                    msg = node['message']
                    author = msg.get('author', {})
                    role = author.get('role', 'unknown') if isinstance(author, dict) else 'unknown'
                    content = msg.get('content', {})
                    if isinstance(content, dict):
                        parts = content.get('parts', [])
                        text = parts[0] if parts else ''
                    else:
                        text = str(content)
                    
                    if len(text) > 200:
                        text = text[:200] + "..."
                    
                    lines.append(f"  [{role}] {text}")
        
        lines.append("-" * 40)
        return "\n".join(lines)


class JSONFormatter(BaseFormatter):
    """Structured JSON formatter."""
    
    def __init__(self, indent: int = 2, sort_keys: bool = True):
        """Initialize JSON formatter.
        
        Args:
            indent: Number of spaces for indentation.
            sort_keys: Whether to sort dictionary keys.
        """
        self.indent = indent
        self.sort_keys = sort_keys
    
    def format(self, data: Any) -> str:
        """Format data as JSON.
        
        Args:
            data: Data to format.
            
        Returns:
            JSON string.
        """
        return json.dumps(data, indent=self.indent, sort_keys=self.sort_keys)
    
    def format_conversation(self, conv: Dict[str, Any], field_selector=None) -> str:
        """Format a single conversation as JSON.
        
        Args:
            conv: Conversation dictionary.
            field_selector: Optional FieldSelector to filter fields.
            
        Returns:
            JSON string representation of conversation.
        """
        if field_selector:
            conv = field_selector.filter_conversation(conv)
        return self.format(conv)


# Registry of available formatters
FORMATTERS = {
    "txt": TextFormatter,
    "json": JSONFormatter,
}


def get_formatter(format_type: str, **kwargs) -> BaseFormatter:
    """Get formatter by type.
    
    Args:
        format_type: Formatter type ('txt', 'json').
        **kwargs: Additional arguments for formatter constructor.
        
    Returns:
        Formatter instance.
        
    Raises:
        ValueError: If formatter type is not supported.
    """
    if format_type not in FORMATTERS:
        raise ValueError(f"Unsupported format: {format_type}. Available: {list(FORMATTERS.keys())}")
    return FORMATTERS[format_type](**kwargs)
