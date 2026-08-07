from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, Mapping

from .records import iter_record_files, parse_project_yaml, parse_record_file
from .project_index_render import InvalidRecordMetadataError, LegacyTableOverlay, Record, generated_sections, minimal_skeleton, validate_topic


DERIVED_SECTIONS: Final[tuple[str, ...]] = (
    "Key Conclusions",
    "Feature Changes",
    "Technical Decisions",
    "Requirements / Discussions",
    "Bug Fix Records",
    "Topic Index",
)
CANONICAL_RECORD_DIRECTORIES: Final[Mapping[str, str]] = {
    "change": "changes",
    "decision": "decisions",
    "requirement": "requirements",
    "bug": "bugs",
}
RECORD_TYPES: Final[frozenset[str]] = frozenset(("change", "decision", "requirement", "bug"))
RECORD_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(change|decision|requirement|bug)-(?:\d{3}|[0-9a-f]{32})$")
HEADING_PATTERN: Final[re.Pattern[str]] = re.compile(r"^## (.+)$")
CONCLUSION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^- \[([^\]]+)]\s*((?:#[\w-]+\s*)*)—\s*(.*?)\s*\(([^)]*)\)\s*$")
TABLE_ROW_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\|\s*(.*?)\s*\|$")
TOPIC_PATTERN: Final[re.Pattern[str]] = re.compile(r"^-\s*([^:]+):\s*(.*)$")


@dataclass(frozen=True, slots=True)
class DuplicateRecordIdError(RuntimeError):
    record_id: str
    paths: tuple[Path, Path]

    def __str__(self) -> str:
        first, second = self.paths
        return f"duplicate SyberMem record_id {self.record_id!r}: {_safe_record_path(first)} and {_safe_record_path(second)}"


@dataclass(frozen=True, slots=True)
class ConclusionOverlay:
    topics: tuple[str, ...]
    text: str
    date: str


@dataclass(frozen=True, slots=True)
class LegacyOverlay:
    conclusions: Mapping[str, ConclusionOverlay]
    topics: Mapping[str, tuple[str, ...]]
    tables: Mapping[str, LegacyTableOverlay]


def build_project_index(root: Path) -> str:
    """Build the deterministic derived project INDEX content for a SyberMem root."""
    existing = _read_existing_index(root)
    overlay = _parse_legacy_overlay(existing)
    records = _load_records(root, overlay)
    generated = generated_sections(root, records)
    base = existing if existing else minimal_skeleton()
    return _replace_derived_sections(base, generated)


def write_project_index(root: Path) -> bool:
    """Write .sybermem/INDEX.md only when derived content changed."""
    index_path = root / ".sybermem" / "INDEX.md"
    next_content = build_project_index(root)
    if index_path.is_file() and index_path.read_text(encoding="utf-8") == next_content:
        return False
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(next_content, encoding="utf-8")
    return True


def check_project_index(root: Path) -> bool:
    """Return whether the existing project INDEX matches derived content without writing."""
    index_path = root / ".sybermem" / "INDEX.md"
    if not index_path.is_file():
        return False
    return index_path.read_text(encoding="utf-8") == build_project_index(root)


def _read_existing_index(root: Path) -> str:
    index_path = root / ".sybermem" / "INDEX.md"
    if not index_path.is_file():
        return ""
    return index_path.read_text(encoding="utf-8")


def _load_records(root: Path, overlay: LegacyOverlay) -> tuple[Record, ...]:
    project = parse_project_yaml(root)
    project_id = project.get("project_id", "")
    slug = project.get("slug", "")
    records: list[Record] = []
    seen: dict[str, Path] = {}
    for path in iter_record_files(root):
        row = parse_record_file(path, project_id, slug)
        record_type = row["type"]
        record_id = row["record_id"]
        if record_type not in RECORD_TYPES or not record_id or not _is_canonical_record_path(path, record_type):
            continue
        previous = seen.get(record_id)
        if previous is not None:
            raise DuplicateRecordIdError(record_id=record_id, paths=(previous, path))
        seen[record_id] = path
        records.append(_record_from_row(row, path, overlay))
    return tuple(sorted(records, key=lambda record: (record.record_id, record.path.as_posix())))


def _record_from_row(row: Mapping[str, str], path: Path, overlay: LegacyOverlay) -> Record:
    record_id = row["record_id"]
    record_type = row["type"]
    _validate_record_id(record_id, record_type)
    conclusion = overlay.conclusions.get(record_id)
    table = overlay.tables.get(record_id, LegacyTableOverlay())
    parsed_topics = tuple(topic for topic in row["topics"].split(",") if topic)
    topics = tuple(validate_topic(topic) for topic in (parsed_topics or overlay.topics.get(record_id, ()) or (conclusion.topics if conclusion else ())))
    key_conclusion = row["key_conclusion"] or (conclusion.text if conclusion else "")
    date = row["created_at"] or (conclusion.date if conclusion else "") or table.date
    title = row["title"] or table.title
    source = row["source"] or table.source
    priority = row["priority"] or table.priority
    severity = row["severity"] or table.severity
    return Record(
        record_id=record_id,
        record_type=record_type,
        date=date,
        title=title,
        status=row["status"],
        source=source,
        priority=priority,
        severity=severity,
        key_conclusion=key_conclusion,
        topics=topics,
        path=path,
    )


def _safe_record_path(path: Path) -> str:
    """Return a non-absolute record path suitable for user-facing diagnostics."""
    parts = path.as_posix().split("/")
    if ".sybermem" in parts:
        sybermem_index = parts.index(".sybermem")
        return "/".join(parts[sybermem_index:])
    return path.name


def _is_canonical_record_path(path: Path, record_type: str) -> bool:
    """Return whether a parsed record lives under the canonical directory for its type."""
    return path.parent.name == CANONICAL_RECORD_DIRECTORIES[record_type]


def _validate_record_id(record_id: str, record_type: str) -> None:
    match = RECORD_ID_PATTERN.fullmatch(record_id)
    if match is None or match.group(1) != record_type:
        raise InvalidRecordMetadataError(
            field="record_id",
            value=record_id,
            reason="record_id must be type-001 legacy form or type-32hex UUID-backed form matching the record type",
        )


def _parse_legacy_overlay(text: str) -> LegacyOverlay:
    sections = _section_bodies(text)
    conclusions = _parse_conclusion_overlay(sections.get("Key Conclusions", ""))
    topics = _parse_topic_overlay(sections.get("Topic Index", ""))
    tables = _parse_table_overlay(sections)
    return LegacyOverlay(conclusions=conclusions, topics=topics, tables=tables)


def _section_bodies(text: str) -> dict[str, str]:
    lines = text.splitlines()
    headings = [(index, match.group(1).strip()) for index, line in enumerate(lines) if (match := HEADING_PATTERN.match(line))]
    bodies: dict[str, str] = {}
    for position, (start, name) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        bodies[name] = "\n".join(lines[start + 1 : end])
    return bodies


def _parse_conclusion_overlay(body: str) -> dict[str, ConclusionOverlay]:
    conclusions: dict[str, ConclusionOverlay] = {}
    for line in body.splitlines():
        match = CONCLUSION_PATTERN.match(line)
        if match is None:
            continue
        record_id, raw_topics, text, date = match.groups()
        topics = tuple(topic.lstrip("#") for topic in raw_topics.split() if topic)
        conclusions[record_id] = ConclusionOverlay(topics=topics, text=_unescape_markdown_text(text), date=_unescape_markdown_text(date))
    return conclusions


def _parse_topic_overlay(body: str) -> dict[str, tuple[str, ...]]:
    topics_by_record: dict[str, list[str]] = {}
    for line in body.splitlines():
        match = TOPIC_PATTERN.match(line)
        if match is None:
            continue
        topic, raw_ids = match.groups()
        for record_id in [part.strip() for part in raw_ids.split(",") if part.strip()]:
            topics_by_record.setdefault(record_id, []).append(topic.strip())
    return {record_id: tuple(topics) for record_id, topics in topics_by_record.items()}


def _parse_table_overlay(sections: Mapping[str, str]) -> dict[str, LegacyTableOverlay]:
    overlays: dict[str, LegacyTableOverlay] = {}
    _merge_requirement_overlays(overlays, sections.get("Requirements / Discussions", ""))
    _merge_bug_overlays(overlays, sections.get("Bug Fix Records", ""))
    return overlays


def _merge_requirement_overlays(overlays: dict[str, LegacyTableOverlay], body: str) -> None:
    for cells in _table_rows(body):
        record_id = _overlay_record_id(cells[0], "requirement")
        if len(cells) >= 6 and record_id is not None:
            overlays[record_id] = LegacyTableOverlay(date=cells[1], title=cells[2], source=cells[3], priority=cells[4])


def _merge_bug_overlays(overlays: dict[str, LegacyTableOverlay], body: str) -> None:
    for cells in _table_rows(body):
        record_id = _overlay_record_id(cells[0], "bug")
        if len(cells) >= 5 and record_id is not None:
            overlays[record_id] = LegacyTableOverlay(date=cells[1], title=cells[2], severity=cells[3])


def _overlay_record_id(cell: str, record_type: str) -> str | None:
    generated_prefix = f"{record_type}-"
    if cell.isdigit():
        return f"{generated_prefix}{cell}"
    if cell.startswith(generated_prefix) and len(cell) > len(generated_prefix):
        return cell
    return None


def _table_rows(body: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in body.splitlines():
        match = TABLE_ROW_PATTERN.match(line)
        if match is None or "---" in line:
            continue
        cells = tuple(_unescape_markdown_text(cell.strip()) for cell in _split_table_cells(match.group(1)))
        if cells and cells[0] != "Number" and cells[0] != "ID":
            rows.append(cells)
    return tuple(rows)


def _split_table_cells(row: str) -> tuple[str, ...]:
    cells: list[str] = []
    cell: list[str] = []
    escaped = False
    for char in row:
        if escaped:
            cell.append(char)
            escaped = False
        elif char == "\\":
            cell.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(cell))
            cell = []
        else:
            cell.append(char)
    cells.append("".join(cell))
    return tuple(cells)


def _unescape_markdown_text(value: str) -> str:
    chars: list[str] = []
    index = 0
    escapable = frozenset(r"\|[]()")
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value) and value[index + 1] in escapable:
            chars.append(value[index + 1])
            index += 2
        else:
            chars.append(char)
            index += 1
    return "".join(chars)


def _replace_derived_sections(existing: str, generated: Mapping[str, str]) -> str:
    lines = existing.splitlines()
    spans = _heading_spans(lines)
    replaced: list[str] = []
    cursor = 0
    seen: set[str] = set()
    for name, start, end in spans:
        replaced.extend(lines[cursor:start])
        if name in generated:
            replaced.extend(generated[name].splitlines())
            replaced.append("")
            seen.add(name)
        else:
            replaced.extend(lines[start:end])
        cursor = end
    replaced.extend(lines[cursor:])
    for name in DERIVED_SECTIONS:
        if name not in seen:
            if replaced and replaced[-1] != "":
                replaced.append("")
            replaced.extend(generated[name].splitlines())
    return "\n".join(_trim_trailing_blank_lines(replaced)) + "\n"


def _heading_spans(lines: list[str]) -> tuple[tuple[str, int, int], ...]:
    headings = [(index, match.group(1).strip()) for index, line in enumerate(lines) if (match := HEADING_PATTERN.match(line))]
    spans: list[tuple[str, int, int]] = []
    for position, (start, name) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        spans.append((name, start, end))
    return tuple(spans)


def _trim_trailing_blank_lines(lines: list[str]) -> tuple[str, ...]:
    end = len(lines)
    while end > 0 and lines[end - 1] == "":
        end -= 1
    return tuple(lines[:end])
