# Field Selection Reference

This document describes the field-selection and metadata-selection features that the current CLI actually supports.

It is intentionally practical rather than exhaustive. The goal is to document the fields, groups, and selectors you can use with `chatgpt-export`, not to guess every field that might appear in every historical `conversations.json` file.

## Structural Levels

The tool understands conversation data at these nested levels:

```text
conversation
└── mapping node
    └── message
        ├── author
        ├── content
        └── metadata
```

The field selector can retain or remove fields across those levels while preserving the containers needed to reach nested selected fields.

## `--fields`

The `--fields` argument accepts one field-selection spec.

Supported forms:

```text
all
none
include field1,field2
exclude field1,field2
groups group1,group2
```

Examples:

```bash
chatgpt-export export data.json --fields all
chatgpt-export export data.json --fields none
chatgpt-export export data.json --fields "include title,create_time,mapping"
chatgpt-export export data.json --fields "exclude moderation_results,plugin_ids"
chatgpt-export export data.json --fields "groups minimal"
chatgpt-export export data.json --fields "groups conversation,message"
```

Multi-word specs must be quoted.

## Field Groups

The current built-in field groups are:

### `conversation`

Includes:

- `_id`
- `conversation_id`
- `create_time`
- `update_time`
- `title`
- `type`

### `message`

Includes:

- `author`
- `content`
- `status`
- `end_turn`

### `metadata`

Includes:

- `model_slug`
- `message_type`
- `is_archived`

### `minimal`

Includes:

- `title`
- `create_time`
- `message`

## Known Structural Fields

These are the structural fields the tool currently categorizes by level.

### Conversation

- `title`
- `create_time`
- `update_time`
- `mapping`
- `moderation_results`
- `current_node`
- `plugin_ids`
- `_id`
- `conversation_id`
- `type`

### Mapping Node

- `id`
- `parent`
- `children`
- `message`

### Message

- `author`
- `content`
- `status`
- `end_turn`
- `weight`
- `recipient`
- `channel`
- `create_time`
- `update_time`

### Author

- `role`
- `name`

### Content

- `content_type`
- `parts`
- `language`
- `response_format_name`
- `text`
- `user_profile`
- `user_instructions`

Unknown names are still allowed in `include` and `exclude` field specs, but the validator may warn about them.

## Metadata Filtering

Metadata filtering is separate from `--fields`.

Use:

- `--include PATTERN [PATTERN ...]`
- `--exclude PATTERN [PATTERN ...]`

These apply to known metadata names inside nested `message.metadata` dictionaries after structural field filtering.

Examples:

```bash
chatgpt-export export data.json --include model_slug
chatgpt-export export data.json --include "model*" --exclude plugin_ids
chatgpt-export export data.json --fields "groups message" --include is_archived
```

Pattern matching supports:

- exact matches
- substring matches
- shell-style wildcards such as `model*`

## Known Metadata Names

The current metadata filter recognizes these names:

- `model_slug`
- `message_type`
- `plugin_ids`
- `is_archived`

## How Filtering Combines

Filtering happens in this order:

1. structural field selection through `--fields`
2. metadata filtering through `--include` and `--exclude`
3. formatting to text or JSON

This means:

- `--fields` decides whether structural containers like `mapping`, `message`, `author`, `content`, and `metadata` survive
- `--include` and `--exclude` decide which metadata keys remain inside metadata dictionaries

## Practical Recipes

Keep only a small readable subset:

```bash
chatgpt-export export data.json --fields "groups minimal"
```

Keep titles and timestamps but drop plugin noise:

```bash
chatgpt-export export data.json --fields "exclude plugin_ids,moderation_results"
```

Keep only message-oriented structure and model metadata:

```bash
chatgpt-export export data.json --fields "groups message" --include "model*"
```

Write one file per conversation with a minimal payload:

```bash
chatgpt-export export data.json --split subject --output-dir exports --fields "groups minimal"
```

## Notes

- `analyze --fields` reports field coverage; it does not accept the export-style field-selection spec.
- `export --split single` writes to stdout unless `--output` is provided.
- Subject split files are named from the source conversation title plus identifier.
- Split modes such as `subject`, `date`, and `id` write to `--output-dir`.
