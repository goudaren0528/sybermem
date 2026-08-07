from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, Mapping
from urllib.parse import quote


SECTION_BY_TYPE: Final[Mapping[str, str]] = {
    "change": "Feature Changes",
    "decision": "Technical Decisions",
    "requirement": "Requirements / Discussions",
    "bug": "Bug Fix Records",
}
TOPIC_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[\w][\w-]*$")


@dataclass(frozen=True, slots=True)
class Record:
    record_id: str
    record_type: str
    date: str
    title: str
    status: str
    source: str
    priority: str
    severity: str
    key_conclusion: str
    topics: tuple[str, ...]
    path: Path


@dataclass(frozen=True, slots=True)
class LegacyTableOverlay:
    date: str = ""
    title: str = ""
    source: str = ""
    priority: str = ""
    severity: str = ""


@dataclass(frozen=True, slots=True)
class InvalidRecordMetadataError(RuntimeError):
    field: str
    value: str
    reason: str

    def __str__(self) -> str:
        return f"invalid SyberMem record metadata {self.field}={self.value!r}: {self.reason}"


def validate_topic(topic: str) -> str:
    """Return a safe topic tag or raise a typed metadata error."""
    if TOPIC_PATTERN.fullmatch(topic) is None:
        raise InvalidRecordMetadataError(field="topics", value=topic, reason="topic must contain only word characters and hyphens")
    return topic


def generated_sections(root: Path, records: tuple[Record, ...]) -> Mapping[str, str]:
    """Render all derived project INDEX sections."""
    return {
        "Key Conclusions": _render_key_conclusions(records),
        "Feature Changes": _render_standard_table(root, records, "change"),
        "Technical Decisions": _render_standard_table(root, records, "decision"),
        "Requirements / Discussions": _render_requirements_table(root, records),
        "Bug Fix Records": _render_bugs_table(root, records),
        "Topic Index": _render_topic_index(records),
    }


def minimal_skeleton() -> str:
    """Return the static fallback used when a project has no INDEX yet."""
    return "\n".join(["# SyberMem Index", "", "This file summarizes all project records.", ""])


def _records_of_type(records: tuple[Record, ...], record_type: str) -> tuple[Record, ...]:
    return tuple(record for record in records if record.record_type == record_type)


def _render_key_conclusions(records: tuple[Record, ...]) -> str:
    lines = [
        "## Key Conclusions",
        "",
        "<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->",
        "<!-- add new conclusions here -->",
    ]
    for record in records:
        if record.key_conclusion:
            topics = " ".join(f"#{validate_topic(topic)}" for topic in record.topics)
            topic_prefix = f" {topics}" if topics else ""
            lines.append(f"- [{record.record_id}]{topic_prefix} — {_escape_markdown_text(record.key_conclusion)} ({_escape_markdown_text(record.date)})")
    return "\n".join(lines)


def _render_standard_table(root: Path, records: tuple[Record, ...], record_type: str) -> str:
    title = SECTION_BY_TYPE[record_type]
    lines = [f"## {title}", "", "| ID | Date | Title | Status | Link |", "|----|------|-------|--------|------|", "<!-- add new records here -->"]
    for record in _records_of_type(records, record_type):
        lines.append(f"| {record.record_id} | {_cell(record.date)} | {_cell(record.title)} | {_cell(record.status)} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_requirements_table(root: Path, records: tuple[Record, ...]) -> str:
    lines = ["## Requirements / Discussions", "", "| ID | Date | Title | Source | Priority | Link |", "|----|------|-------|--------|----------|------|", "<!-- add new records here -->"]
    for record in _records_of_type(records, "requirement"):
        lines.append(f"| {record.record_id} | {_cell(record.date)} | {_cell(record.title)} | {_cell(record.source)} | {_cell(record.priority)} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_bugs_table(root: Path, records: tuple[Record, ...]) -> str:
    lines = ["## Bug Fix Records", "", "| ID | Date | Title | Severity | Link |", "|----|------|-------|----------|------|", "<!-- add new records here -->"]
    for record in _records_of_type(records, "bug"):
        lines.append(f"| {record.record_id} | {_cell(record.date)} | {_cell(record.title)} | {_cell(record.severity)} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_topic_index(records: tuple[Record, ...]) -> str:
    by_topic: dict[str, list[str]] = {}
    for record in records:
        for topic in record.topics:
            safe_topic = validate_topic(topic)
            by_topic.setdefault(safe_topic, []).append(record.record_id)
    lines = ["## Topic Index", "", "<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->"]
    for topic in sorted(by_topic):
        record_ids = ", ".join(sorted(by_topic[topic]))
        lines.append(f"- {topic}: {record_ids}")
    return "\n".join(lines)


def _link(root: Path, record: Record) -> str:
    sybermem_root = (root / ".sybermem").resolve()
    try:
        relative_path = record.path.resolve().relative_to(sybermem_root)
    except ValueError as exc:
        raise InvalidRecordMetadataError(field="path", value=str(record.path), reason="record path must be under .sybermem") from exc
    relative = "/".join(quote(part, safe="-._~") for part in relative_path.parts)
    return f"[link]({relative})"


def _cell(value: str) -> str:
    return _escape_markdown_text(value)


def _escape_markdown_text(value: str) -> str:
    normalized = " ".join(value.splitlines())
    escaped = normalized.replace("\\", "\\\\")
    for char in ("|", "[", "]", "(", ")"):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped
