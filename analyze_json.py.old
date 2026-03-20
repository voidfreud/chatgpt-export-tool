#!/usr/bin/env python3
"""
Analyze the structure of a large JSON file containing ChatGPT conversations.

Part of chatgpt-export-tool - A Python tool for exporting and analyzing
ChatGPT conversations.json export files.

Uses streaming JSON parsing (ijson) to handle large files efficiently.
Supports both CLI and programmatic usage.

Usage:
    analyze-json [--file <path>] [--output <path>] [--verbose]

    python analyze_json.py [--file <path>] [--output <path>] [--verbose]
"""

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, Any, Set, Optional

try:
    import ijson
except ImportError:
    print("ijson not found. Installing...")
    import subprocess
    subprocess.check_call(["uv", "pip", "install", "ijson"])
    import ijson


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


def analyze_json_streaming(filepath: str, verbose: bool = False) -> Dict[str, Any]:
    """Analyze JSON file using streaming parser.
    
    Uses ijson for memory-efficient parsing of large files.
    
    Args:
        filepath: Path to the JSON file.
        verbose: If True, print progress information.
        
    Returns:
        Dictionary containing analysis results with keys:
        - conversation_count: Number of top-level items
        - message_count: Total message nodes
        - all_fields: Set of all unique field names
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    results: Dict[str, Any] = {
        'conversation_count': 0,
        'message_count': 0,
        'all_fields': set(),
    }
    
    with open(filepath, 'rb') as f:
        parser = ijson.parse(f)
        
        conversation_count = 0
        message_count = 0
        all_fields: Set[str] = set()
        in_conversation = False
        in_mapping = False
        in_message_node = False
        
        current_conversation_fields: Set[str] = set()
        current_node_fields: Set[str] = set()
        
        for prefix, event, parser_event, value in parser:
            parts = prefix.split('.')
            
            # Track top-level array items (conversations)
            if prefix == '' and event == 'start_array':
                pass
            elif len(parts) == 1 and event == 'start_map':
                in_conversation = True
                current_conversation_fields = set()
            elif len(parts) == 1 and event == 'end_map':
                in_conversation = False
                conversation_count += 1
                all_fields.update(current_conversation_fields)
            
            # Fields within conversation
            elif in_conversation and len(parts) == 1 and event not in ('start_map', 'end_map', 'start_array', 'end_array'):
                current_conversation_fields.add(parts[0])
                all_fields.add(parts[0])
            
            # Mapping object
            elif in_conversation and parts[0] == 'mapping' and len(parts) == 1:
                if event == 'start_map':
                    in_mapping = True
                elif event == 'end_map':
                    in_mapping = False
            
            # Node IDs within mapping (the UUID keys)
            elif in_conversation and in_mapping and len(parts) == 2 and parts[1] and event == 'start_map':
                in_message_node = True
                current_node_fields = set()
            
            # Fields within a node
            elif in_conversation and in_mapping and in_message_node:
                if event in ('start_map', 'end_map'):
                    if event == 'end_map':
                        message_count += 1
                        all_fields.update(current_node_fields)
                        in_message_node = False
                elif parts[-1]:
                    current_node_fields.add(parts[-1])
                    all_fields.add(parts[-1])
    
    results['conversation_count'] = conversation_count
    results['message_count'] = message_count
    results['all_fields'] = all_fields
    
    return results


def analyze_with_full_iteration(filepath: str, verbose: bool = False) -> Dict[str, Any]:
    """Analyze JSON file by iterating through conversations.
    
    Uses ijson.items() for more accurate counting and field collection.
    
    Args:
        filepath: Path to the JSON file.
        verbose: If True, print progress information.
        
    Returns:
        Dictionary containing analysis results with keys:
        - conversation_count: Number of conversations
        - message_count: Total message nodes
        - all_fields: Set of all unique field names
        - sample_conversation: Sample structure from first conversation
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    results: Dict[str, Any] = {
        'conversation_count': 0,
        'message_count': 0,
        'all_fields': set(),
        'sample_conversation': None,
    }
    
    with open(filepath, 'rb') as f:
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


def categorize_fields(fields: Set[str]) -> Dict[str, list]:
    """Categorize field names by their hierarchical level.
    
    Args:
        fields: Set of all field names.
        
    Returns:
        Dictionary mapping category names to lists of field names.
    """
    conversation_level = ['title', 'create_time', 'update_time', 'mapping', 
                          'moderation_results', 'current_node', 'plugin_ids', 
                          '_id', 'conversation_id', 'type']
    mapping_level = ['id', 'parent', 'children', 'message']
    message_level = ['author', 'content', 'status', 'end_turn', 'weight', 
                     'recipient', 'channel', 'create_time', 'update_time']
    author_level = ['role', 'name']
    content_level = ['content_type', 'parts', 'language', 'response_format_name', 
                     'text', 'user_profile', 'user_instructions']
    
    categorized: Dict[str, list] = {
        'conversation': [],
        'mapping': [],
        'message': [],
        'author': [],
        'content': [],
        'metadata': []
    }
    
    all_categorized = set(conversation_level + mapping_level + message_level + 
                          author_level + content_level)
    
    for field in sorted(fields):
        if field in conversation_level:
            categorized['conversation'].append(field)
        elif field in mapping_level:
            categorized['mapping'].append(field)
        elif field in message_level:
            categorized['message'].append(field)
        elif field in author_level:
            categorized['author'].append(field)
        elif field in content_level:
            categorized['content'].append(field)
        else:
            categorized['metadata'].append(field)
    
    return categorized


def print_analysis(filepath: str, output_file: Optional[str] = None, verbose: bool = False) -> None:
    """Print the analysis results.
    
    Args:
        filepath: Path to the analyzed JSON file.
        output_file: Optional path to write output to.
        verbose: If True, print additional progress information.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_size = get_file_size(filepath)
    
    output_lines = []
    output_lines.append(f"File: {filepath}")
    output_lines.append(f"Size: {format_size(file_size)} ({file_size:,} bytes)")
    output_lines.append("")
    
    if verbose:
        output_lines.append("Analyzing structure (this may take a moment for large files)...")
        output_lines.append("Using streaming JSON parsing (ijson)...")
        output_lines.append("")
    
    # Run the analysis
    results = analyze_with_full_iteration(filepath, verbose=verbose)
    
    output_lines.append("=" * 60)
    output_lines.append("ANALYSIS RESULTS")
    output_lines.append("=" * 60)
    output_lines.append("")
    output_lines.append(f"Top-level structure: JSON Array of conversation objects")
    output_lines.append(f"Number of threads/conversations: {results['conversation_count']:,}")
    output_lines.append(f"Total message nodes in mappings: {results['message_count']:,}")
    output_lines.append("")
    output_lines.append("-" * 60)
    output_lines.append("ALL UNIQUE FIELD NAMES FOUND:")
    output_lines.append("-" * 60)
    
    sorted_fields = sorted(results['all_fields'])
    output_lines.append(f"Total unique fields: {len(sorted_fields)}")
    output_lines.append("")
    
    # Categorize and display fields
    categorized = categorize_fields(results['all_fields'])
    
    for category, fields in categorized.items():
        if fields:
            output_lines.append(f"{category.capitalize()}-level fields:")
            output_lines.append(f"  {', '.join(sorted(fields))}")
            output_lines.append("")
    
    output_lines.append("-" * 60)
    output_lines.append("SAMPLE STRUCTURE (first conversation):")
    output_lines.append("-" * 60)
    if results['sample_conversation']:
        for key, value in results['sample_conversation'].items():
            output_lines.append(f"  {key}: {value}")
    
    output = "\n".join(output_lines)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Output written to: {output_file}")
    else:
        print(output)


def create_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Analyze the structure of ChatGPT conversations.json export files. Part of chatgpt-export-tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  analyze-json data.json
  analyze-json data.json --verbose
  analyze-json data.json --output results.txt
  analyze-json --output results.txt data.json
        """
    )
    
    parser.add_argument(
        'file',
        nargs='?',
        help="Path to the JSON file to analyze"
    )
    
    parser.add_argument(
        '-o', '--output',
        metavar='PATH',
        help="Write output to the specified file instead of stdout"
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output with progress information"
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1'
    )
    
    return parser


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = create_parser()
    args = parser.parse_args()
    
    if args.file is None:
        print("Please provide a JSON file path", file=sys.stderr)
        return 1
    
    try:
        print_analysis(args.file, args.output, args.verbose)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ijson.JSONError as e:
        print(f"Error: Invalid JSON file - {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: Unexpected error - {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
