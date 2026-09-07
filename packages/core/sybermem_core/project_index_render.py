from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, Mapping
from urllib.parse import quote

from .records import parse_record_file


SECTION_BY_TYPE: Final[Mapping[str, str]] = {
    "change": "Feature Changes",
    "decision": "Technical Decisions",
    "requirement": "Requirements / Discussions",
    "bug": "Bug Fix Records",
    "norm": "Project Norms",
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
    lifecycle: str = ""
    superseded_by: str = ""


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
    phase_digest_covered = _phase_digest_covered_ids(root, records)
    return {
        "Key Conclusions": _render_key_conclusions(records, phase_digest_covered),
        "Archived Conclusions": _render_archived_conclusions(root, records, phase_digest_covered),
        "Phase Digests": _render_digest_table(root, "digests", "Title", "Coverage", "add new digest records here"),
        "Theme Digests": _render_digest_table(root, "theme-digests", "Theme", "Coverage", "add new theme digest records here"),
        "Feature Changes": _render_standard_table(root, records, "change"),
        "Technical Decisions": _render_standard_table(root, records, "decision"),
        "Requirements / Discussions": _render_requirements_table(root, records),
        "Bug Fix Records": _render_bugs_table(root, records),
        "Project Norms": _render_standard_table(root, records, "norm"),
        "Topic Index": _render_topic_index(records),
        "Usage": _render_usage(),
    }


def minimal_skeleton() -> str:
    """Return the complete deterministic INDEX template used for every build."""
    return "\n".join([
        "# SyberMem Index", "", "This file summarizes all project records.", "", "---", "",
        "## Key Conclusions", "", "<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->", "<!-- add new conclusions here -->", "", "---", "",
        "## Archived Conclusions", "", "<!-- Not injected at session start; findable via /sybermem-search -->", "<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->", "<!-- add new archived conclusions here -->", "", "---", "",
        "## Phase Digests", "", "| Number | Date | Title | Status | Coverage | Link |", "|--------|------|-------|--------|----------|------|", "<!-- add new digest records here -->", "", "---", "",
        "## Theme Digests", "", "| Number | Date | Theme | Status | Coverage | Link |", "|--------|------|-------|--------|----------|------|", "<!-- add new theme digest records here -->", "", "---", "",
        "## Feature Changes", "", "| ID | Date | Title | Status | Link |", "|----|------|-------|--------|------|", "<!-- add new records here -->", "", "---", "",
        "## Technical Decisions", "", "| ID | Date | Title | Status | Link |", "|----|------|-------|--------|------|", "<!-- add new records here -->", "", "---", "",
        "## Requirements / Discussions", "", "| ID | Date | Title | Source | Priority | Link |", "|----|------|-------|--------|----------|------|", "<!-- add new records here -->", "", "---", "",
        "## Bug Fix Records", "", "| ID | Date | Title | Severity | Link |", "|----|------|-------|----------|------|", "<!-- add new records here -->", "", "---", "",
        "## Project Norms", "", "| ID | Date | Title | Status | Link |", "|----|------|-------|--------|------|", "<!-- add new records here -->", "", "---", "",
        "## Usage", "", "- **changes/**: Record all feature changes", "- **decisions/**: Record important technical decisions and their rationale", "- **requirements/**: Record discussion processes, requirement sources, and design reasoning", "- **bugs/**: Record bug analysis and fix approaches", "- **norms/**: Record durable project norms", "", ".sybermem/INDEX.md is derived from canonical record files. Use `sybermem project index build` to regenerate it and `sybermem project index check` to verify it is current.", "", "---", "",
        "## Topic Index", "", "<!-- Auto-maintained: maps topic tags to record IDs for fast lookup -->", "",
    ])


def _records_of_type(records: tuple[Record, ...], record_type: str) -> tuple[Record, ...]:
    return tuple(record for record in records if record.record_type == record_type)


def _render_key_conclusions(records: tuple[Record, ...], phase_digest_covered: frozenset[str]) -> str:
    lines = [
        "## Key Conclusions",
        "",
        "<!-- One-line core conclusion per record. Format: [id] #topic1 #topic2 — description (date) -->",
        "<!-- add new conclusions here -->",
    ]
    for record in records:
        if record.key_conclusion and not _is_archived(record, phase_digest_covered):
            topics = " ".join(f"#{validate_topic(topic)}" for topic in record.topics)
            topic_prefix = f" {topics}" if topics else ""
            lines.append(f"- [{record.record_id}]{topic_prefix} — {_escape_markdown_text(record.key_conclusion)} ({_escape_markdown_text(record.date)})")
    return "\n".join(lines)


def _render_archived_conclusions(root: Path, records: tuple[Record, ...], phase_digest_covered: frozenset[str]) -> str:
    lines = [
        "## Archived Conclusions", "",
        "<!-- Not injected at session start; findable via /sybermem-search -->",
        "<!-- Suffix each line with: [superseded by <id>] or [compressed in <id>] or [archived] -->",
        "<!-- add new archived conclusions here -->",
    ]
    for record in records:
        if not record.key_conclusion or not _is_archived(record, phase_digest_covered):
            continue
        reason = f"[superseded by {record.superseded_by}]" if record.superseded_by else (
            f"[compressed in {_covered_digest_label(root, record)}]"
            if record.record_id in phase_digest_covered else "[archived]"
        )
        topics = " ".join(f"#{validate_topic(topic)}" for topic in record.topics)
        topic_prefix = f" {topics}" if topics else ""
        lines.append(f"- [{record.record_id}]{topic_prefix} — {_escape_markdown_text(record.key_conclusion)} ({_escape_markdown_text(record.date)}) {reason}")
    return "\n".join(lines)


def _is_archived(record: Record, phase_digest_covered: frozenset[str] = frozenset()) -> bool:
    return (
        record.lifecycle.strip().lower() in {"archived", "superseded"}
        or record.status.strip().lower() in {"archived", "superseded"}
        or bool(record.superseded_by)
        or record.record_id in phase_digest_covered
    )


def _phase_digest_covered_ids(root: Path, records: tuple[Record, ...]) -> frozenset[str]:
    digest_dir = root / ".sybermem" / "digests"
    if not digest_dir.is_dir():
        return frozenset()
    by_path: dict[str, str] = {}
    for record in records:
        relative = record.path.relative_to(root / ".sybermem").as_posix()
        by_path[relative] = record.record_id
        by_path[record.path.name] = record.record_id
        by_path[record.path.stem] = record.record_id
    covered: set[str] = set()
    for path in sorted(digest_dir.glob("*.md")):
        fields = _frontmatter_fields(path)
        if fields.get("type", "") not in {"", "digest"}:
            continue
        for source in fields.get("source_records", "").split(","):
            source = source.strip()
            if not source:
                continue
            covered.add(by_path.get(source, by_path.get(Path(source).name, by_path.get(Path(source).stem, source))))
    return frozenset(covered)


def _covered_digest_label(root: Path, record: Record) -> str:
    digest_dir = root / ".sybermem" / "digests"
    relative = record.path.relative_to(root / ".sybermem").as_posix()
    # A digest may reference a source either by path (relative / filename / stem) or by
    # canonical record_id (common in inline flow lists like `source_records: [change-001]`).
    identifiers = {relative, record.path.name, record.path.stem, record.record_id}
    for path in sorted(digest_dir.glob("*.md")) if digest_dir.is_dir() else ():
        fields = _frontmatter_fields(path)
        sources = {source.strip() for source in fields.get("source_records", "").split(",") if source.strip()}
        if identifiers & sources:
            return fields.get("number", "") or _id_suffix(parse_record_file(path, "", "").get("record_id", "")) or path.stem
    return "digest"


def _render_digest_table(root: Path, directory: str, label: str, coverage_label: str, anchor: str) -> str:
    theme = directory == "theme-digests"
    lines = [f"## {'Theme' if theme else 'Phase'} Digests", "", f"| Number | Date | {label} | Status | {coverage_label} | Link |", "|--------|------|-------|--------|----------|------|", f"<!-- {anchor} -->"]
    digest_dir = root / ".sybermem" / directory
    rows: list[tuple[str, str, str, str, str, Path]] = []
    if digest_dir.is_dir():
        for path in sorted(digest_dir.glob("*.md")):
            row = parse_record_file(path, "", "")
            if row.get("type", "") not in {"", "digest", "theme-digest"}:
                continue
            fields = _frontmatter_fields(path)
            number = fields.get("number", "") or _id_suffix(row.get("record_id", "")) or _id_suffix(path.stem)
            title = fields.get("theme", "") if theme else row.get("title", "")
            title = title or row.get("title", "")
            sources = fields.get("source_records", "")
            coverage = fields.get("coverage", "") or (f"{len([x for x in sources.split(',') if x])} records" if sources else "")
            rows.append((row.get("created_at", ""), number, title, row.get("status", ""), coverage, path))
    for date, number, title, status, coverage, path in sorted(rows, key=lambda item: (item[0], item[1], item[5].name)):
        relative = "/".join(quote(part, safe="-._~") for part in path.relative_to(root / ".sybermem").parts)
        lines.append(f"| {_cell(number)} | {_cell(date)} | {_cell(title)} | {_cell(status)} | {_cell(coverage)} | [link]({relative}) |")
    return "\n".join(lines)


def _frontmatter_fields(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").lstrip("\ufeff").splitlines()
    if not lines or lines[0] != "---":
        return {}
    fields: dict[str, str] = {}
    current = ""
    values: list[str] = []
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith(" ") or line.startswith("-"):
            if current == "source_records":
                values.append(line.strip().lstrip("-").strip())
            continue
        if ":" in line:
            if current == "source_records" and values:
                fields[current] = ",".join(values)
            current, value = line.split(":", 1)
            current = current.strip()
            value = value.strip()
            # Normalize an inline YAML flow list (e.g. `source_records: [change-001, change-002]`)
            # into the same comma-separated form the multi-line branch produces, so list-valued
            # fields like source_records parse identically regardless of inline vs block style.
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1]
                value = ",".join(item.strip().strip("'\"") for item in inner.split(",") if item.strip())
            fields[current] = value
            values = []
    # Only let the trailing block-list collection overwrite when it actually gathered
    # items; an inline flow list already stored the value above and must not be clobbered.
    if current == "source_records" and values:
        fields[current] = ",".join(values)
    return fields


def _id_suffix(value: str) -> str:
    return value.rsplit("-", 1)[-1] if "-" in value else ""


def _render_usage() -> str:
    return "\n".join([
        "## Usage", "", "- **changes/**: Record all feature changes", "- **decisions/**: Record important technical decisions and their rationale",
        "- **requirements/**: Record discussion processes, requirement sources, and design reasoning", "- **bugs/**: Record bug analysis and fix approaches", "- **norms/**: Record durable project norms",
        "", ".sybermem/INDEX.md is derived from canonical record files. Use `sybermem project index build` to regenerate it and `sybermem project index check` to verify it is current.",
    ])


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
