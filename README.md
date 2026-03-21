# ChatGPT Export Tool

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-cyan)](https://github.com/astral-sh/ruff)

A CLI for analyzing and exporting ChatGPT `conversations.json` files.

The project focuses on two things:

- analyzing the structure of a ChatGPT export without loading the whole file into memory
- exporting conversations to text or JSON with structural field filtering and metadata filtering

It uses streaming JSON parsing with `ijson` and is organized around small core modules so filtering, formatting, split behavior, and path generation can be changed independently.

## Installation

This project currently targets Python `3.10+`.

```bash
git clone https://github.com/voidfreud/chatgpt-export-tool.git
cd chatgpt-export-tool
uv sync
```

For development tooling too:

```bash
uv sync --group dev
```

You can then run the CLI with:

```bash
uv run chatgpt-export --help
```

## Quick Start

Analyze an export:

```bash
uv run chatgpt-export analyze path/to/conversations.json
```

Include field coverage:

```bash
uv run chatgpt-export analyze path/to/conversations.json --fields
```

Export everything as text to stdout:

```bash
uv run chatgpt-export export path/to/conversations.json
```

Export everything as JSON to one file:

```bash
uv run chatgpt-export export path/to/conversations.json --format json --output conversations.json
```

Export one file per conversation:

```bash
uv run chatgpt-export export path/to/conversations.json --split subject --output-dir exports
```

## Commands

### `analyze`

`analyze` reports high-level structure and statistics for a `conversations.json` file.

It includes:

- conversation count
- message count
- file size
- date range
- optional field coverage with `--fields`

Examples:

```bash
uv run chatgpt-export analyze data.json
uv run chatgpt-export analyze data.json --fields
uv run chatgpt-export analyze data.json --verbose --output analysis.txt
uv run chatgpt-export analyze data.json --debug
```

### `export`

`export` writes conversations in either text or JSON format.

It supports:

- structural field filtering through `--fields`
- metadata filtering through `--include` and `--exclude`
- split modes for one output, one file per conversation, date folders, or ID-based files

Examples:

```bash
uv run chatgpt-export export data.json
uv run chatgpt-export export data.json --output conversations.txt
uv run chatgpt-export export data.json --format json --output conversations.json
uv run chatgpt-export export data.json --split subject --output-dir exports
uv run chatgpt-export export data.json --fields "groups minimal" --split subject --output-dir exports
uv run chatgpt-export export data.json --fields "include title,mapping" --include model* --exclude plugin_ids
```

## Field Filtering

The `--fields` option controls which structural fields are retained before formatting.

Supported forms:

- `all`
- `none`
- `include field1,field2`
- `exclude field1,field2`
- `groups group1,group2`

Examples:

```bash
uv run chatgpt-export export data.json --fields all
uv run chatgpt-export export data.json --fields none
uv run chatgpt-export export data.json --fields "include title,create_time,mapping"
uv run chatgpt-export export data.json --fields "exclude moderation_results,plugin_ids"
uv run chatgpt-export export data.json --fields "groups minimal"
```

Available field groups:

- `conversation`
- `message`
- `metadata`
- `minimal`

See [Fields.md](Fields.md) for the current field-selection reference.

## Metadata Filtering

The metadata filter runs after structural field filtering and applies to metadata names known by the tool.

Examples:

```bash
uv run chatgpt-export export data.json --include model_slug
uv run chatgpt-export export data.json --include model* --exclude plugin_ids
uv run chatgpt-export export data.json --fields "groups message" --include is_archived
```

Currently supported metadata names include:

- `id`
- `title`
- `create_time`
- `update_time`
- `model_slug`
- `message_type`
- `plugin_ids`
- `conversation_id`
- `type`
- `moderation_results`
- `current_node`
- `is_archived`

## Split Modes

`export` supports four split modes:

- `single`: one combined output stream or one output file
- `subject`: one file per conversation, named from title plus identifier
- `date`: date folders with one file per conversation
- `id`: one file per conversation, named from conversation ID

Important output behavior:

- `--split single` with no `--output` writes to stdout
- `--split single --output FILE` writes one file
- split modes like `subject`, `date`, and `id` write into `--output-dir`

## Output Formats

Supported formats:

- `txt`
- `json`

`txt` is a readable conversation-oriented export.  
`json` writes the filtered conversation objects directly.

## Architecture

The current structure is intentionally modular:

- CLI wiring lives in `chatgpt_export_tool/commands/`
- streaming and analysis live in `parser.py` and `analysis_collector.py`
- field parsing and structural filtering live in `field_spec.py`, `field_rules.py`, `conversation_filter.py`, and `filter_pipeline.py`
- metadata filtering lives in `metadata_selector.py`, `metadata_rules.py`, and `metadata_validation.py`
- export orchestration lives in `export_service.py`
- formatting lives in `analysis_formatter.py` and `conversation_formatters.py`
- split-key and output-path policies live in `split_keys.py`, `file_naming.py`, `output_paths.py`, and `output_writer.py`

That separation is deliberate: most behavior changes can now be made in a small, specific module instead of inside one large control file.

## Development

Run the checks used during refactoring:

```bash
uv run pytest
uv run pytest --cov=chatgpt_export_tool --cov-report=term-missing
uv run ruff check chatgpt_export_tool tests pyproject.toml
uv run ruff format --check chatgpt_export_tool tests
```

If you need to format files:

```bash
uv run ruff format chatgpt_export_tool tests
```

## Notes

- Input handling is streaming, so large exports do not need to be loaded into memory just to analyze or iterate conversations.
- Single-file JSON export writes one valid JSON document.
- Split exports write one conversation per output file.
- The field-selection and metadata-selection surface is documented in [Fields.md](Fields.md).
