from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Final, Mapping

from .records import iter_record_files, parse_project_yaml, parse_record_file
from .project_index_render import LegacyTableOverlay, Record, generated_sections, minimal_skeleton


DERIVED_SECTIONS: Final[tuple[str, ...]] = (
    "Key Conclusions",
    "Feature Changes",
    "Technical Decisions",
    "Requirements / Discussions",
    "Bug Fix Records",
    "Topic Index",
)
RECORD_TYPES: Final[frozenset[str]] = frozenset(("change", "decision", "requirement", "bug"))
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
        return f"duplicate SyberMem record_id {self.record_id!r}: {first} and {second}"


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
    generated = generated_sections(root, records, overlay.tables)
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
        if record_type not in RECORD_TYPES or not record_id:
            continue
        previous = seen.get(record_id)
        if previous is not None:
            raise DuplicateRecordIdError(record_id=record_id, paths=(previous, path))
        seen[record_id] = path
        records.append(_record_from_row(row, path, overlay))
    return tuple(sorted(records, key=lambda record: (record.record_id, record.path.as_posix())))


def _record_from_row(row: Mapping[str, str], path: Path, overlay: LegacyOverlay) -> Record:
    record_id = row["record_id"]
    conclusion = overlay.conclusions.get(record_id)
    table = overlay.tables.get(record_id, LegacyTableOverlay())
    parsed_topics = tuple(topic for topic in row["topics"].split(",") if topic)
    topics = parsed_topics or overlay.topics.get(record_id, ()) or (conclusion.topics if conclusion else ())
    key_conclusion = row["key_conclusion"] or (conclusion.text if conclusion else "")
    date = row["created_at"] or (conclusion.date if conclusion else "") or table.date
    title = row["title"] or table.title
    return Record(
        record_id=record_id,
        record_type=row["type"],
        date=date,
        title=title,
        status=row["status"],
        key_conclusion=key_conclusion,
        topics=topics,
        path=path,
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
        conclusions[record_id] = ConclusionOverlay(topics=topics, text=text, date=date)
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
        cells = tuple(cell.strip() for cell in match.group(1).split("|"))
        if cells and cells[0] != "Number" and cells[0] != "ID":
            rows.append(cells)
    return tuple(rows)


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
