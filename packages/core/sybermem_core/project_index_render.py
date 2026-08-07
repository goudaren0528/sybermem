from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Mapping


SECTION_BY_TYPE: Final[Mapping[str, str]] = {
    "change": "Feature Changes",
    "decision": "Technical Decisions",
    "requirement": "Requirements / Discussions",
    "bug": "Bug Fix Records",
}


@dataclass(frozen=True, slots=True)
class Record:
    record_id: str
    record_type: str
    date: str
    title: str
    status: str
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


def generated_sections(root: Path, records: tuple[Record, ...], tables: Mapping[str, LegacyTableOverlay]) -> Mapping[str, str]:
    """Render all derived project INDEX sections."""
    return {
        "Key Conclusions": _render_key_conclusions(records),
        "Feature Changes": _render_standard_table(root, records, "change"),
        "Technical Decisions": _render_standard_table(root, records, "decision"),
        "Requirements / Discussions": _render_requirements_table(root, records, tables),
        "Bug Fix Records": _render_bugs_table(root, records, tables),
        "Topic Index": _render_topic_index(records),
    }


def minimal_skeleton() -> str:
    """Return the static fallback used when a project has no INDEX yet."""
    return "\n".join(["# SyberMem Index", "", "This file summarizes all project records.", ""])


def _records_of_type(records: tuple[Record, ...], record_type: str) -> tuple[Record, ...]:
    return tuple(record for record in records if record.record_type == record_type)


def _render_key_conclusions(records: tuple[Record, ...]) -> str:
    lines = ["## Key Conclusions", "", "<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->"]
    for record in records:
        if record.key_conclusion:
            topics = " ".join(f"#{topic}" for topic in record.topics)
            topic_prefix = f" {topics}" if topics else ""
            lines.append(f"- [{record.record_id}]{topic_prefix} — {record.key_conclusion} ({record.date})")
    return "\n".join(lines)


def _render_standard_table(root: Path, records: tuple[Record, ...], record_type: str) -> str:
    title = SECTION_BY_TYPE[record_type]
    lines = [f"## {title}", "", "| ID | Date | Title | Status | Link |", "|----|------|-------|--------|------|"]
    for record in _records_of_type(records, record_type):
        lines.append(f"| {record.record_id} | {record.date} | {record.title} | {record.status} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_requirements_table(root: Path, records: tuple[Record, ...], tables: Mapping[str, LegacyTableOverlay]) -> str:
    lines = ["## Requirements / Discussions", "", "| ID | Date | Title | Source | Priority | Link |", "|----|------|-------|--------|----------|------|"]
    for record in _records_of_type(records, "requirement"):
        legacy = tables.get(record.record_id, LegacyTableOverlay())
        lines.append(f"| {record.record_id} | {record.date} | {record.title} | {legacy.source} | {legacy.priority} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_bugs_table(root: Path, records: tuple[Record, ...], tables: Mapping[str, LegacyTableOverlay]) -> str:
    lines = ["## Bug Fix Records", "", "| ID | Date | Title | Severity | Link |", "|----|------|-------|----------|------|"]
    for record in _records_of_type(records, "bug"):
        legacy = tables.get(record.record_id, LegacyTableOverlay())
        lines.append(f"| {record.record_id} | {record.date} | {record.title} | {legacy.severity} | {_link(root, record)} |")
    return "\n".join(lines)


def _render_topic_index(records: tuple[Record, ...]) -> str:
    by_topic: dict[str, list[str]] = {}
    for record in records:
        for topic in record.topics:
            by_topic.setdefault(topic, []).append(record.record_id)
    lines = ["## Topic Index", "", "<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->"]
    for topic in sorted(by_topic):
        record_ids = ", ".join(sorted(by_topic[topic]))
        lines.append(f"- {topic}: {record_ids}")
    return "\n".join(lines)


def _link(root: Path, record: Record) -> str:
    relative = record.path.relative_to(root / ".sybermem").as_posix()
    return f"[link]({relative})"
