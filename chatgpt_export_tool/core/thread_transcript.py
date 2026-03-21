"""Transcript extraction and visibility policy for conversation threads."""

from dataclasses import dataclass
from typing import Any, Dict, Iterator, Optional

from .runtime_config import TranscriptConfig


@dataclass(frozen=True)
class TranscriptEntry:
    """One visible transcript entry."""

    role: str
    content_type: str
    text: str
    timestamp: Optional[float]


def iter_transcript_entries(
    conversation: Dict[str, Any],
    policy: TranscriptConfig,
) -> Iterator[TranscriptEntry]:
    """Yield transcript entries according to the configured policy."""
    for message in iter_branch_messages(
        conversation, follow_current=policy.follow_current_branch
    ):
        entry = _build_entry(message, policy)
        if entry is None:
            continue
        if _should_include_message(message, entry, policy):
            yield entry


def iter_branch_messages(
    conversation: Dict[str, Any],
    follow_current: bool,
) -> Iterator[Dict[str, Any]]:
    """Yield raw message dictionaries from the chosen conversation branch."""
    mapping = conversation.get("mapping")
    current_node = conversation.get("current_node")
    if not follow_current or not isinstance(mapping, dict) or not current_node:
        yield from _iter_mapping_messages(conversation)
        return

    branch: list[Dict[str, Any]] = []
    node_id = str(current_node)
    seen: set[str] = set()

    while node_id and node_id not in seen:
        seen.add(node_id)
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            break
        message = node.get("message")
        if isinstance(message, dict):
            branch.append(message)
        parent = node.get("parent")
        if parent is None:
            break
        node_id = str(parent)

    if not branch:
        yield from _iter_mapping_messages(conversation)
        return

    yield from reversed(branch)


def _iter_mapping_messages(conversation: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if isinstance(message, dict):
            yield message


def _build_entry(
    message: Dict[str, Any],
    policy: TranscriptConfig,
) -> Optional[TranscriptEntry]:
    text = extract_message_text(message, policy)
    role = get_message_role(message)
    content_type = get_message_content_type(message)
    timestamp = get_message_create_time(message)
    return TranscriptEntry(
        role=role,
        content_type=content_type,
        text=text,
        timestamp=timestamp,
    )


def _should_include_message(
    message: Dict[str, Any],
    entry: TranscriptEntry,
    policy: TranscriptConfig,
) -> bool:
    if policy.skip_blank_messages and not entry.text.strip():
        return False

    if policy.honor_visual_hidden_flag and _is_visually_hidden(message):
        if entry.content_type not in policy.show_visually_hidden_content_types:
            return False

    if entry.content_type in policy.exclude_content_types:
        return False
    if entry.content_type in policy.include_content_types:
        return True

    if entry.role == "system":
        return policy.show_system_messages
    if entry.role == "tool":
        return policy.show_tool_messages
    if entry.role == "user":
        if entry.content_type == "user_editable_context":
            return policy.show_user_editable_context
        if entry.content_type == "multimodal_text":
            return policy.show_multimodal_text
        return policy.show_user_text
    if entry.role == "assistant":
        if entry.content_type == "thoughts":
            return policy.show_assistant_thoughts
        if entry.content_type == "code":
            return policy.show_assistant_code
        if entry.content_type == "reasoning_recap":
            return policy.show_reasoning_recap
        if entry.content_type == "multimodal_text":
            return policy.show_multimodal_text
        return policy.show_assistant_text
    return False


def get_message_role(message: Dict[str, Any]) -> str:
    """Return a message author's role."""
    author = message.get("author")
    if isinstance(author, dict):
        return str(author.get("role", "unknown"))
    return "unknown"


def get_message_content_type(message: Dict[str, Any]) -> str:
    """Return message content type."""
    content = message.get("content")
    if isinstance(content, dict):
        return str(content.get("content_type", "text"))
    return type(content).__name__


def get_message_create_time(message: Dict[str, Any]) -> Optional[float]:
    """Return a message creation timestamp when available and parseable."""
    create_time = message.get("create_time")
    if create_time is None:
        return None
    try:
        return float(create_time)
    except (TypeError, ValueError):
        return None


def extract_message_text(
    message: Dict[str, Any],
    policy: Optional[TranscriptConfig] = None,
) -> str:
    """Extract readable text from a message."""
    content = message.get("content")
    if not isinstance(content, dict):
        return "" if content is None else str(content)

    content_type = str(content.get("content_type", "text"))
    if content_type == "user_editable_context":
        resolved_policy = policy or TranscriptConfig()
        return _render_user_editable_context(
            content,
            mode=resolved_policy.user_editable_context_mode,
            preview_chars=resolved_policy.user_editable_context_preview_chars,
        )

    parts = content.get("parts", [])
    if isinstance(parts, list) and parts:
        rendered_parts = [str(part) for part in parts if str(part).strip()]
        if rendered_parts:
            return "\n".join(rendered_parts)

    text = content.get("text")
    if text is not None:
        return str(text)

    if not isinstance(parts, list):
        return str(parts)
    return ""


def _render_user_editable_context(
    content: Dict[str, Any],
    *,
    mode: str,
    preview_chars: int,
) -> str:
    lines: list[str] = []
    user_profile = content.get("user_profile")
    user_instructions = content.get("user_instructions")
    if user_profile:
        lines.append(
            f"User profile: {_format_context_value(str(user_profile), mode, preview_chars)}"
        )
    if user_instructions:
        lines.append(
            "User instructions: "
            f"{_format_context_value(str(user_instructions), mode, preview_chars)}"
        )
    return "\n".join(lines)


def _format_context_value(value: str, mode: str, preview_chars: int) -> str:
    if mode == "full":
        return value

    compact_value = " ".join(value.split())
    if len(compact_value) <= preview_chars:
        return compact_value
    return compact_value[: preview_chars - 3].rstrip() + "..."


def _is_visually_hidden(message: Dict[str, Any]) -> bool:
    metadata = message.get("metadata")
    if not isinstance(metadata, dict):
        return False
    return bool(metadata.get("is_visually_hidden_from_conversation"))
