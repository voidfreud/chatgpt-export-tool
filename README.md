# ChatGPT Export Tool

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-cyan)](https://github.com/astral-sh/ruff)

A Python tool for exporting and analyzing ChatGPT `conversations.json` export files. Uses streaming JSON parsing to efficiently handle large files without loading them entirely into memory.

## Overview

The [`analyze_json.py`](analyze_json.py) script parses ChatGPT conversation exports and reports:

- Total number of conversations/threads
- Total message count across all conversations
- All unique field names organized by category
- Sample conversation structure

## Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/chatgpt-export-tool.git
cd chatgpt-export-tool

# Install dependencies using uv
uv sync

# Install the package in development mode
uv pip install -e .
```

### Using pip with uv

```bash
uv pip install -e .
```

## Usage

### Command Line

```bash
# Analyze the default file (3ae/conversations.json)
uv run analyze-json

# Analyze a specific file
uv run analyze-json path/to/conversations.json

# With verbose output
uv run analyze-json --verbose path/to/conversations.json

# Write output to a file
uv run analyze-json --output results.txt path/to/conversations.json

# Using the installed CLI command
analyze-json path/to/conversations.json --verbose --output results.txt
```

### Python API

```python
from analyze_json import analyze_with_full_iteration

# Analyze a file
results = analyze_with_full_iteration('path/to/conversations.json')

print(f"Conversations: {results['conversation_count']}")
print(f"Messages: {results['message_count']}")
print(f"Fields: {len(results['all_fields'])}")
```

## Output

The script displays:

| Metric | Description |
|--------|-------------|
| File size | Human-readable file size |
| Conversation count | Number of top-level conversation objects |
| Message count | Total nodes in all conversation mappings |
| Field categories | Fields grouped by level (conversation, mapping, message, author, content, metadata) |

## Field Categories

The script organizes fields into these hierarchical levels:

| Level | Description |
|-------|-------------|
| **Conversation** | Top-level fields (title, create_time, mapping, etc.) |
| **Mapping/Node** | Fields within message nodes (id, parent, children, message) |
| **Message** | Fields in the message object (author, content, status, etc.) |
| **Author** | Author object fields (name, role) |
| **Content** | Content object fields (content_type, parts, text, etc.) |
| **Metadata** | Message metadata fields (~130 fields) |

## How It Works

1. Uses `ijson` for streaming JSON parsing (doesn't load entire file into memory)
2. Iterates through conversations using `ijson.items()`
3. Counts messages by traversing the `mapping` dictionary in each conversation
4. Collects all unique field names at each level
5. Outputs categorized results

## Project Structure

```
.
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── analyze_json.py      # Main analysis script
├── tests/
│   └── test_analyze_json.py  # Test suite
└── Fields.md            # Field reference documentation
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=analyze_json --cov-report=html

# Run specific test file
uv run pytest tests/test_analyze_json.py -v
```

### Adding Dependencies

```bash
# Add runtime dependency
uv add ijson

# Add dev dependency
uv add --dev pytest pytest-cov
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Dependencies

| Package | Purpose |
|---------|---------|
| ijson | Streaming JSON parser for large files |

## Notes

- Designed to handle very large JSON files (>100MB) without memory issues
- Field documentation is maintained in [`Fields.md`](Fields.md)
- Requires Python 3.7 or higher
