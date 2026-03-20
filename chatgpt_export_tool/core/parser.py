"""
JSON parsing module for ChatGPT conversations.

Handles memory-efficient streaming parsing of large JSON files using ijson.
"""

import os
from typing import Dict, Any, Set, Optional


def get_file_size(filepath: str) -> int:
    """Get file size in bytes.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        File size in bytes.
        
    Raises:
        OSError: If the file cannot be accessed.
    """
    return os.path.getsize(filepath)


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes.
        
    Returns:
        Human-readable size string (e.g., "1.23 MB").
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


class JSONParser:
    """Memory-efficient JSON parser for ChatGPT conversations.
    
    Uses ijson for streaming parsing to handle large files without
    loading them entirely into memory.
    """
    
    def __init__(self, filepath: str):
        """Initialize parser with file path.
        
        Args:
            filepath: Path to the JSON file to parse.
        """
        self.filepath = filepath
        self._ensure_ijson()
    
    @staticmethod
    def _ensure_ijson():
        """Ensure ijson is installed, install if needed."""
        try:
            import ijson
        except ImportError:
            import subprocess
            subprocess.check_call(["uv", "pip", "install", "ijson"])
    
    def analyze(self, verbose: bool = False) -> Dict[str, Any]:
        """Analyze JSON file structure.
        
        Args:
            verbose: If True, print progress information.
            
        Returns:
            Dictionary containing analysis results with keys:
            - conversation_count: Number of conversations
            - message_count: Total message nodes
            - all_fields: Set of all unique field names
            - sample_conversation: Sample structure from first conversation
        """
        import ijson
        
        results: Dict[str, Any] = {
            'conversation_count': 0,
            'message_count': 0,
            'all_fields': set(),
            'sample_conversation': None,
        }
        
        with open(self.filepath, 'rb') as f:
            conversations = ijson.items(f, 'item')
            
            for conv in conversations:
                results['conversation_count'] += 1
                results['all_fields'].update(conv.keys())
                
                # Count messages in mapping
                if 'mapping' in conv and conv['mapping']:
                    for node_id, node in conv['mapping'].items():
                        results['all_fields'].update(node.keys())
                        if 'message' in node and node['message']:
                            results['message_count'] += 1
                            msg = node['message']
                            results['all_fields'].update(msg.keys())
                            if 'author' in msg and msg['author']:
                                results['all_fields'].update(msg['author'].keys())
                            if 'content' in msg and msg['content']:
                                results['all_fields'].update(msg['content'].keys())
                            if 'metadata' in msg and msg['metadata']:
                                results['all_fields'].update(msg['metadata'].keys())
                
                # Store first conversation as sample
                if results['sample_conversation'] is None:
                    results['sample_conversation'] = {
                        'title': conv.get('title', 'N/A'),
                        'has_mapping': 'mapping' in conv,
                        'mapping_size': len(conv.get('mapping', {}))
                    }
                
                if verbose and results['conversation_count'] % 100 == 0:
                    print(f"  Processed {results['conversation_count']} conversations...")
        
        return results
    
    def iterate_conversations(self, verbose: bool = False):
        """Iterate over conversations in the JSON file.
        
        Args:
            verbose: If True, print progress information.
            
        Yields:
            Each conversation dictionary.
        """
        import ijson
        
        with open(self.filepath, 'rb') as f:
            conversations = ijson.items(f, 'item')
            for idx, conv in enumerate(conversations):
                if verbose and (idx + 1) % 100 == 0:
                    print(f"  Processed {idx + 1} conversations...")
                yield conv
    
    def get_conversations(self, limit: Optional[int] = None) -> list:
        """Get conversations from the JSON file.
        
        Args:
            limit: Maximum number of conversations to retrieve.
            
        Returns:
            List of conversation dictionaries.
        """
        conversations = []
        for conv in self.iterate_conversations():
            conversations.append(conv)
            if limit and len(conversations) >= limit:
                break
        return conversations
