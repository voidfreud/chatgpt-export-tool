# ChatGPT Export Tool

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-cyan)](https://github.com/astral-sh/ruff)

A CLI for analyzing and exporting ChatGPT `conversations.json` files.

The project focuses on two things:

- analyzing the structure of a ChatGPT export without loading the whole file into memory
- exporting conversations to text or JSON with structural field filtering and metadata filtering

It uses streaming JSON parsing with `ijson` and is organized around small core modules so filtering, formatting, split behavior, and path generation can be changed independently.

Persistent defaults can be stored in a single TOML config file. The repo ships a template at `chatgpt_export.toml.example`.

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

To apply config defaults, copy the template and pass `--config PATH`.

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
- transcript-oriented text export that follows the active branch
- split modes for one output, one file per conversation, date folders, or ID-based files

Examples:

```bash
uv run chatgpt-export export data.json
uv run chatgpt-export export data.json --output conversations.txt
uv run chatgpt-export export data.json --format json --output conversations.json
uv run chatgpt-export export data.json --split subject --output-dir exports
uv run chatgpt-export export data.json --fields "groups minimal" --split subject --output-dir exports
uv run chatgpt-export export data.json --fields "include title,mapping" --include "model*" --exclude plugin_ids
cp chatgpt_export.toml.example chatgpt_export.toml
uv run chatgpt-export export data.json --config chatgpt_export.toml
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

The metadata filter runs after structural field filtering and applies only to keys inside nested `message.metadata` dictionaries.

Examples:

```bash
uv run chatgpt-export export data.json --include model_slug
uv run chatgpt-export export data.json --include "model*" --exclude plugin_ids
uv run chatgpt-export export data.json --fields "groups message" --include is_archived
```

Currently supported metadata names include:

- `model_slug`
- `message_type`
- `plugin_ids`
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

`txt` is a transcript-oriented export that follows the active branch of the conversation tree.
`json` writes the filtered conversation objects directly.

By default, text export includes user text, assistant text, assistant thoughts, and user editable context when present. User editable context is rendered in a compact preview by default so transcripts stay readable. Text export hides tool plumbing, assistant code, reasoning recap, and blank/internal nodes unless the transcript policy is changed in config.

Text output defaults now favor reading clarity:

- conversation context is rendered as a separate preamble block
- visible turns are grouped into clearer chat-style `User` / `Assistant` sections
- turn counts can be shown in the header
- ChatGPT citation/navigation artifacts can be stripped from text output
- long paragraphs can be wrapped for easier reading

Important transcript policy options include:

- `user_editable_context_mode`
- `show_visually_hidden_content_types`
- `include_content_types`
- `exclude_content_types`

## Configuration

`export` accepts `--config PATH` and resolves defaults from one TOML file.

The repo ships `chatgpt_export.toml.example` as a template. Copy it to a local file such as `chatgpt_export.toml` and pass that path explicitly.

The config file is TOML and is intentionally kept to one file with sections such as:

- `[defaults]` for format, split mode, field selection, and output directory
- `[transcript]` for active-branch reconstruction and visibility rules
- `[text_output]` for header fields, transcript layout, and date/time formats

Notable `[text_output]` options include:

- `layout_mode = "reading" | "compact"`
- `heading_style = "plain" | "markdown"`
- `include_turn_count_in_header = true | false`
- `include_turn_numbers = true | false`
- `turn_separator = "---"`
- `strip_chatgpt_artifacts = true | false`
- `wrap_width = 88`

Practical transcript presets:

Reading-first transcript:
```toml
[text_output]
layout_mode = "reading"
heading_style = "plain"
include_turn_count_in_header = true
turn_separator = "---"
strip_chatgpt_artifacts = true
wrap_width = 88
```

Compact scanning transcript:
```toml
[text_output]
layout_mode = "compact"
include_turn_count_in_header = false
turn_separator = ""
wrap_width = 0
```

Markdown/notes transcript:
```toml
[text_output]
layout_mode = "reading"
heading_style = "markdown"
turn_separator = "---"
```

CLI arguments override TOML values. `analyze` does not currently use export config defaults.

## Architecture

The structure is intentionally modular at the subsystem level:

- command wiring and user-facing behavior live in `chatgpt_export_tool/commands/`
- streaming parse and analysis are separate from export formatting and writing
- structural field filtering and metadata filtering are separate concerns
- split-key resolution, filename policy, and writing are isolated from export orchestration

The core package is also grouped into shallow subpackages by concern:

- `core/config/` for runtime config models, loading, and validation
- `core/transcript/` for branch reconstruction and transcript extraction
- `core/validation/` for field and metadata validation
- `core/output/` for formatting, naming, path resolution, and writing

That separation is deliberate: most behavior changes can be made in one small subsystem instead of in one large control file.

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
- Text export follows the active thread path using `current_node` and `parent` links.
- The field-selection and metadata-selection surface is documented in [Fields.md](Fields.md).
