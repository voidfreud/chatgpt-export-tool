# ChatGPT Conversations.json Field Reference

This document describes all fields found in the ChatGPT `conversations.json` export file. The JSON structure contains conversation data organized across multiple nested levels with approximately 160 unique fields.

## Table of Contents

- [File Structure Overview](#file-structure-overview)
- [Conversation-Level Fields](#conversation-level-fields)
- [Mapping/Node-Level Fields](#mappingnode-level-fields)
- [Message-Level Fields](#message-level-fields)
- [Author-Level Fields](#author-level-fields)
- [Content-Level Fields](#content-level-fields)
- [Metadata-Level Fields](#metadata-level-fields)

---

## File Structure Overview

The `conversations.json` file contains an array of conversation objects. Each conversation has the following hierarchical structure:

```
conversations[]
├── conversation metadata (top-level fields)
├── mapping{} (dictionary of message nodes)
│   └── node
│       ├── children[] (array of child node UUIDs)
│       ├── id (UUID of this node)
│       ├── message (message object)
│       │   ├── author{}
│       │   ├── content{}
│       │   └── metadata{}
│       └── parent (UUID of parent node, null for root)
```

---

## Conversation-Level Fields

Top-level fields describing the conversation as a whole.

| Field | Description |
|-------|-------------|
| `_id` | MongoDB ObjectId for the conversation document in OpenAI's database |
| `conversation_id` | Unique identifier (UUID) for the conversation, used for API calls and sharing |
| `create_time` | Unix timestamp indicating when the conversation was first created |
| `current_node` | UUID of the currently active/last message node in the conversation |
| `mapping` | Dictionary mapping node UUIDs to their message node objects, containing the full conversation tree |
| `moderation_results` | Array of content moderation check results for messages in the conversation |
| `plugin_ids` | Array of plugin IDs that were used or invoked during this conversation |
| `title` | Display title of the conversation, shown in the conversation list |
| `type` | Conversation type indicator (e.g., "chat" for standard conversations) |
| `update_time` | Unix timestamp indicating when the conversation was last modified |

---

## Mapping/Node-Level Fields

Fields within each node of the `mapping` dictionary.

| Field | Description |
|-------|-------------|
| `children` | Array of UUIDs pointing to child message nodes in the conversation tree |
| `id` | UUID identifier for this specific message node |
| `message` | The message object containing author, content, and metadata |
| `parent` | UUID of the parent message node; `null` for the root message of a conversation |

---

## Message-Level Fields

Fields within the `message` object of each mapping node.

| Field | Description |
|-------|-------------|
| `author` | Object containing the author `name` and `role` (user, assistant, system) |
| `channel` | Channel identifier where the message was sent |
| `content` | Message content object with `content_type`, `parts`, and optional text |
| `end_turn` | Boolean indicating if this message ends the current conversation turn |
| `recipient` | Recipient identifier for the message (e.g., "all" for broadcast) |
| `status` | Message status such as "finished_successfully", "in_progress", or "failed" |
| `weight` | Weight value affecting model sampling probability for responses |

---

## Author-Level Fields

Fields within the `author` object of a message.

| Field | Description |
|-------|-------------|
| `name` | Author identifier name (e.g., "assistant" or user's identifier) |
| `role` | Role of the message author: "user", "assistant", "system", or "tool" |

---

## Content-Level Fields

Fields within the `content` object of a message.

| Field | Description |
|-------|-------------|
| `content_type` | Type of content (e.g., "text", "code", "execution_output") |
| `language` | Language code for code blocks or multilingual content (e.g., "python") |
| `parts` | Array of content parts, typically text strings or code blocks |
| `response_format_name` | Name of the response format used (e.g., "json", "markdown") |
| `text` | Text content string for simple text-based messages |
| `user_instructions` | Instructions provided by the user for this specific message |
| `user_profile` | User profile information when context is provided |

---

## Metadata-Level Fields

Fields within the `metadata` object of a message. These provide extensive context about message processing, sources, and system behavior.

### General Message Metadata

| Field | Description |
|-------|-------------|
| `message_type` | Type classification of the message (e.g., "user", "assistant") |
| `model_slug` | Model identifier slug used to generate this response |
| `request_id` | Unique request identifier for tracking API calls |
| `source` | Source of the message (e.g., "api", "browser") |
| `state` | Current state of the message processing |
| `timestamp_` | Timestamp associated with the message |

### Conversation State & Status

| Field | Description |
|-------|-------------|
| `is_archived` | Whether the conversation has been archived |
| `is_complete` | Whether an operation or message generation is complete |
| `is_loading_message` | Whether this is a loading/placeholder message |
| `is_starred` | Whether the conversation is marked as starred/favorited |
| `is_error` | Whether this message represents an error condition |
| `is_ephemeral` | Whether the message is temporary and not persisted |
| `finish_details` | Object containing details about how the message generation finished |

### Turn & Conversation Flow

| Field | Description |
|-------|-------------|
| `end_turn` | Boolean indicating if this message ends a conversation turn |
| `parent_id` | ID of the parent message in the conversation tree |
| `conversation_origin` | Origin type of the conversation (e.g., "share", "normal") |
| `conversation_template_id` | ID of a conversation template used, if any |

### Search & Retrieval

| Field | Description |
|-------|-------------|
| `citations` | Source citations for factual claims in the response |
| `search_queries` | Array of search queries executed for this message |
| `search_source` | Source of search results (e.g., "web", "file") |
| `search_result_groups` | Grouped search results by category or source |
| `search_display_string` | Formatted display string for search results |
| `searched_display_string` | Display string showing what was searched |
| `search_turns_count` | Number of turns that involved search |
| `client_reported_search_source` | Client-reported source of search information |
| `contextual_answers_available_sources` | Available sources for contextual answer generation |
| `is_contextual_answers_available_sources` | Whether contextual answer sources are available |
| `is_contextual_answers_supported` | Whether contextual answers feature is supported |
| `is_contextual_answers_system_message` | Whether this is a contextual answers system message |
| `is_contextual_retry_user_message` | Whether this is a contextual retry request message |
| `retrieval_file_index` | File index for document retrieval |
| `retrieval_turn_number` | Turn number for retrieval operations |
| `selected_sources` | User-selected sources for grounding |
| `content_references` | References found within the content |
| `content_references_by_file` | Content references grouped by file |

### Async & Background Tasks

| Field | Description |
|-------|-------------|
| `async_status` | Status of an asynchronous operation |
| `async_task_id` | ID for tracking an async task |
| `async_task_created_at` | Creation timestamp for an async task |
| `async_task_prompt` | Prompt associated with an async task |
| `async_task_status_messages` | Status messages for async task progress |
| `async_task_title` | Title of the async task |
| `async_task_type` | Type classification of the async task |
| `async_task_conversation_id` | Conversation ID linked to an async task |
| `is_async_task_result_message` | Whether this message contains async task results |
| `trigger_async_ux` | Whether to trigger async user experience patterns |

### Reasoning & Thinking

| Field | Description |
|-------|-------------|
| `reasoning_status` | Status of model reasoning (e.g., "in_progress", "complete") |
| `reasoning_title` | Title for reasoning steps displayed to user |
| `reasoning_group_id` | Group identifier for related reasoning messages |
| `is_visually_hidden_reasoning_group` | Whether reasoning is hidden from conversation view |
| `skip_reasoning_title` | Whether to skip displaying reasoning title |
| `thoughts` | Model's internal thoughts or reasoning process |
| `deep_research_version` | Version number for deep research feature |

### Attachments & Files

| Field | Description |
|-------|-------------|
| `attachments` | File attachments included with the message |
| `assets` | Attached assets such as images, files, or media |
| `screenshot` | Screenshot data captured during the session |
| `canvas` | Canvas/whiteboard data for visual collaboration |

### Web & URL Information

| Field | Description |
|-------|-------------|
| `url` | URL reference associated with the message |
| `urls` | Multiple URL references |
| `display_url` | URL formatted for display |
| `blocked_urls` | URLs blocked for this message |
| `safe_urls` | URLs verified as safe |
| `domain` | Domain name associated with the content |
| `cloud_doc_urls` | URLs for cloud-stored documents |

### Model & Generation Settings

| Field | Description |
|-------|-------------|
| `default_model_slug` | Default model identifier for the conversation |
| `requested_model_slug` | Model specifically requested by the user |
| `b1de6e2_rm` | Internal reference to a model variant |
| `b1de6e2_s` | Internal setting for model behavior |

### User Interface & Display

| Field | Description |
|-------|-------------|
| `display_title` | Title formatted for display purposes |
| `message_locale` | Locale/language code of the message |
| `followup_prompts` | Suggested follow-up prompts for the user |
| `targeted_reply` | Targeted reply content suggestions |
| `targeted_reply_label` | Label for the targeted reply feature |

### Developer & System Messages

| Field | Description |
|-------|-------------|
| `is_user_system_message` | Whether this is a user-defined system message |
| `rebase_developer_message` | Developer message for conversation rebasing |
| `rebase_system_message` | System message for conversation rebasing |
| `is_do_not_remember` | Whether the model should not remember this content |
| `system_hints` | Hints provided to the system for processing |

### Plugins & Extensions

| Field | Description |
|-------|-------------|
| `gizmo_id` | ID for a gizmo/extension used in the conversation |
| `gizmo_type` | Type classification of the gizmo |
| `invoked_plugin` | Plugin that was invoked during message processing |
| `disabled_tool_ids` | IDs of tools that were disabled for this message |
| `tether_id` | Tether identifier for connected services |

### Image Generation

| Field | Description |
|-------|-------------|
| `image_results` | Results from image generation operations |
| `image_gen_title` | Title assigned to a generated image |

### Voice & Audio

| Field | Description |
|-------|-------------|
| `voice` | Voice settings and configuration |
| `voice_mode_message` | Message associated with voice mode |
| `real_time_audio_has_video` | Whether real-time audio includes video |

### Dictation

| Field | Description |
|-------|-------------|
| `dictation` | Data from voice dictation input |

### Computer & Terminal

| Field | Description |
|-------|-------------|
| `computer_id` | Identifier for the computer/client device |
| `command` | Command that was executed |

### GitHub Integration

| Field | Description |
|-------|-------------|
| `selected_github_repos` | GitHub repositories selected for context |

### External Integrations

| Field | Description |
|-------|-------------|
| `sugar_item_id` | Sugar CRM item identifier |
| `sugar_item_visible` | Whether the Sugar CRM item is visible |
| `connector_source` | Source for external connector data |

### Update & Edit Operations (n7jupd prefix)

| Field | Description |
|-------|-------------|
| `n7jupd_crefs` | Citation references for updates |
| `n7jupd_crefs_by_file` | Citation references grouped by file |
| `n7jupd_message` | Message content for an update |
| `n7jupd_schedulable` | Whether the update can be scheduled |
| `n7jupd_subtool` | Subtool name for the update |
| `n7jupd_summary` | Summary content for the update |
| `n7jupd_title` | Title for the update |
| `n7jupd_titles` | Multiple title values |
| `n7jupd_url` | URL reference for the update |
| `n7jupd_urls` | Multiple URL references |
| `n7jupd_v` | Version number for the update |

### Classification & Analysis

| Field | Description |
|-------|-------------|
| `classifier_response` | Response from a classification model |
| `sonic_classification_result` | Classification result from Sonic model |
| `source_analysis_msg_id` | Message ID for source analysis |

### Summary & Results

| Field | Description |
|-------|-------------|
| `summary` | Summary content of the conversation or message |
| `aggregate_result` | Aggregated result from computations |
| `result` | General result content |
| `finished_text` | Final text content when generation finished |
| `finished_duration_sec` | Duration in seconds when generation finished |
| `initial_text` | Initial text before processing |

### Memory & Context

| Field | Description |
|-------|-------------|
| `memory_scope` | Scope for the memory feature |
| `pending_memory_info` | Pending information for memory processing |
| `user_context_message_data` | User context data attached to message |

### Permissions & Access

| Field | Description |
|-------|-------------|
| `permissions` | Permission settings for the conversation |
| `exclusive_key` | Exclusive key for resource locking |

### Miscellaneous Flags

| Field | Description |
|-------|-------------|
| `is_visually_hidden_from_conversation` | Whether message is hidden from conversation view |
| `is_study_mode` | Whether study mode is enabled |
| `needs_startup` | Whether startup initialization is needed |
| `stop_reason` | Reason why message generation stopped |

### Logging & Debugging

| Field | Description |
|-------|-------------|
| `debug_sonic_thread_id` | Thread ID for debug logging |
| `serialization_metadata` | Metadata for serialization processes |

### Paragen (Prompt Augmentation)

| Field | Description |
|-------|-------------|
| `paragen_variant_choice` | Selected variant choice for prompt augmentation |
| `paragen_variants_info` | Information about prompt variants |
| `augmented_paragen_prompt_label` | Label for augmented prompt |

### ChatGPT SDK

| Field | Description |
|-------|-------------|
| `chatgdk_sdk` | Information about the ChatGPT SDK used |

---

## Field Naming Conventions

The following patterns indicate internal or experimental fields:

| Pattern | Description |
|---------|-------------|
| `n7jupd_*` | Update operation related fields (likely internal feature flag) |
| `b1de6e2_*` | Internal model variant references |
| `sonic_*` | Fields related to Sonic classification model |
| `gizmo_*` | Gizmo/extension related fields |
| `sugar_*` | Sugar CRM integration fields |

---

## Data Types Reference

| Type | Description |
|------|-------------|
| `string` | Text strings (UUIDs, timestamps, content) |
| `number` | Numeric values (timestamps, weights) |
| `boolean` | True/false flags for features and states |
| `object` | Nested objects (author, content, metadata) |
| `array` | Lists of values (children, attachments) |
| `null` | Empty/missing values |

---

## Notes

- Timestamps are stored as Unix timestamps (seconds since epoch) unless otherwise specified
- UUIDs follow the format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- MongoDB ObjectIds follow the format: `xxxxxxxxxxxxxxxxxxxxxxxx`

## Metadata Field Filtering (--include / --exclude / --fields)

The `export` command supports filtering metadata fields using `--include` and `--exclude`. These options can be combined with `--fields` so top-level field selection and metadata filtering stay separate. `analyze` uses `--fields` only to toggle field coverage output.

### Available Metadata Fields

The following fields can be used with `--include` or `--exclude`:

| Field | Description |
|-------|-------------|
| `id` | Conversation ID |
| `title` | Conversation title |
| `create_time` | Creation timestamp |
| `update_time` | Last update timestamp |
| `model_slug` | Model identifier |
| `message_type` | Message type indicator |
| `plugin_ids` | List of plugin IDs used |
| `conversation_id` | Conversation UUID |
| `type` | Conversation type |
| `moderation_results` | Moderation check results |
| `current_node` | Current node in conversation tree |
| `is_archived` | Archive status |

### Matching Patterns

The metadata filtering supports multiple matching strategies:

| Pattern Type | Example | Matches |
|--------------|---------|---------|
| Exact match | `title` | `title` |
| Partial match | `time` | `create_time`, `update_time` |
| Glob pattern | `model*` | `model_slug` |
| Wildcard (`*`) | `*` | All metadata fields |

### Usage Examples

```bash
# Include only specific metadata fields
chatgpt-export export input.json --include title create_time model_slug

# Exclude specific metadata fields
chatgpt-export export input.json --exclude plugin_ids moderation_results

# Include all metadata fields (equivalent to default behavior)
chatgpt-export export input.json --include "*"

# Use with other options
chatgpt-export export input.json --fields "groups minimal" --include title create_time --format json -o output.json

# Analyze with filtered metadata
chatgpt-export analyze input.json --fields
```

### Composition

- `--include` and `--exclude` can be used together
- `--fields` controls top-level field selection or field groups
- Quote any `--fields` value that contains spaces
- Use `analyze --fields` when you only want field coverage output

## See Also

- [README.md](README.md) - Tool usage and command documentation
