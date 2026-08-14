from __future__ import annotations

from typing import Final
from pathlib import Path
import re
import uuid


LEGACY_RECORD_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"\d{4}-\d{2}-\d{2}-(\d{3})-")
TOPIC_TAG_PATTERN: Final[re.Pattern[str]] = re.compile(r"#([a-zA-Z][a-zA-Z0-9_-]*)")
TOPIC_LIST_ITEM_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s*-\s+(.*)")

# Canonical record-id suffix: legacy 3-digit numeric or UUID4 hex (32 chars).
# Shared so every ID parser accepts the same shape; see project_index.RECORD_ID_PATTERN
# (anchored, record-type subset) and retrieval.RECORD_ID_RE (embedded, includes digest).
RECORD_ID_SUFFIX: Final[str] = r"(?:\d{3}|[0-9a-f]{32})"


def generate_record_id(record_type: str) -> str:
    """Return a canonical UUID-backed SyberMem record identifier."""
    return f"{record_type}-{uuid.uuid4().hex}"


def unwrap_scalar(value: str) -> str:
    """Trim a scalar and strip one matching layer of surrounding quotes.

    Zero-dependency YAML-subset scalar handling: `'x'` and `"x"` both yield `x`.
    Type inference is deliberately NOT performed — every value stays a string so
    downstream code that does `.strip().lower()`, joins, and comparisons keeps its
    contract (see the Oracle decision to avoid YAML type coercion).
    """
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ("'", '"'):
        return stripped[1:-1]
    return stripped


def _split_inline_list(value: str) -> list[str]:
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    return [unwrap_scalar(item) for item in inner.split(",") if item.strip()]


def parse_simple_yaml_metadata(text: str) -> dict[str, object]:
    """Parse a small, well-defined YAML subset SyberMem actually emits/reads.

    Supported shapes (nothing more — unsupported constructs like anchors, tags,
    multiline scalars, or deep nesting are not interpreted):
    - top-level ``key: value`` scalars, with `'...'`/`"..."` unquoting
    - inline lists ``key: [a, b]`` -> ``list[str]``
    - block lists under ``key:`` using indented ``- item`` -> ``list[str]``
    - one level of nested map (``key:`` then indented ``child: value``) -> ``dict[str, str]``

    Return values are ``str`` | ``list[str]`` | ``dict[str, str]`` only; callers keep
    treating fields as strings unless they opted into a known list/map key.
    """
    out: dict[str, object] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        raw = lines[i]
        # Only top-level (unindented) keys open a new entry.
        if not raw.strip() or raw[0] in (" ", "\t") or ":" not in raw:
            i += 1
            continue
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest.startswith("[") and rest.endswith("]"):
            out[key] = _split_inline_list(rest)
            i += 1
            continue
        if rest:
            out[key] = unwrap_scalar(rest)
            i += 1
            continue
        # rest is empty: look ahead for an indented block list or nested map.
        block_items: list[str] = []
        nested: dict[str, str] = {}
        j = i + 1
        while j < len(lines):
            child = lines[j]
            if not child.strip():
                j += 1
                continue
            if child[0] not in (" ", "\t"):
                break
            content = child.strip()
            if content.startswith("- "):
                block_items.append(unwrap_scalar(content[2:]))
            elif ":" in content:
                ck, _, cv = content.partition(":")
                nested[ck.strip()] = unwrap_scalar(cv)
            j += 1
        if block_items:
            out[key] = block_items
        elif nested:
            out[key] = nested
        else:
            out[key] = ""
        i = j
    return out


def parse_project_yaml(root: Path) -> dict[str, str]:
    """Return top-level project.yaml scalars as strings (back-compat shape).

    Uses the shared YAML-subset parser so quoted values are unwrapped and nested
    maps like ``repository:`` no longer leak their child lines as bogus top-level
    keys. Only scalar values are surfaced here to preserve the historical
    ``dict[str, str]`` contract; nested maps/lists are reachable via
    ``parse_project_yaml_full``.
    """
    proj = root / ".sybermem" / "project.yaml"
    if not proj.is_file():
        return {}
    parsed = parse_simple_yaml_metadata(proj.read_text(encoding="utf-8"))
    return {k: v for k, v in parsed.items() if isinstance(v, str)}


def parse_project_yaml_full(root: Path) -> dict[str, object]:
    """Return the full parsed project.yaml, including nested maps and lists."""
    proj = root / ".sybermem" / "project.yaml"
    if not proj.is_file():
        return {}
    return parse_simple_yaml_metadata(proj.read_text(encoding="utf-8"))


def iter_record_files(root: Path) -> list[Path]:
    syb = root / ".sybermem"
    files: list[Path] = []
    for sub in ["changes", "decisions", "requirements", "bugs", "digests", "theme-digests"]:
        d = syb / sub
        if d.is_dir():
            files.extend(sorted(d.glob("*.md")))
    return files


def _frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return []
    for index in range(1, len(lines)):
        if lines[index] == "---":
            return lines[1:index]
    return []


def _parse_topic_items(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("[") and stripped.endswith("]"):
        stripped = stripped[1:-1]
    return [unwrap_scalar(item) for item in stripped.split(",") if item.strip()]


def parse_record_file(path: Path, project_id: str, slug: str) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    title = ""
    rtype = ""
    date = ""
    topics: list[str] = []
    record_id = ""
    key_conclusion = ""
    status = ""
    source = ""
    priority = ""
    severity = ""
    superseded_by = ""
    fixes = ""
    implements = ""
    related = ""
    related_files: list[str] = []
    source_kind = ""
    authority = ""
    lifecycle = ""
    explicit_topics = False
    frontmatter = _frontmatter_lines(text)
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if line.startswith("type:"):
            rtype = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("date:"):
            date = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("title:"):
            title = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("record_id:"):
            record_id = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("key_conclusion:"):
            key_conclusion = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("topics:"):
            explicit_topics = True
            topics_value = line.split(":", 1)[1]
            topics = _parse_topic_items(topics_value)
            if not topics:
                collected_topics: list[str] = []
                next_index = index + 1
                while next_index < len(frontmatter):
                    match = TOPIC_LIST_ITEM_PATTERN.fullmatch(frontmatter[next_index])
                    if match is None:
                        break
                    collected_topics.append(unwrap_scalar(match.group(1)))
                    next_index += 1
                topics = collected_topics
                index = next_index - 1
        elif line.startswith("status:"):
            status = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("source:"):
            source = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("priority:"):
            priority = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("severity:"):
            severity = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("superseded_by:"):
            superseded_by = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("fixes:"):
            fixes = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("implements:"):
            implements = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("related_files:"):
            related_files_value = line.split(":", 1)[1]
            related_files = _parse_topic_items(related_files_value)
            if not related_files:
                collected_files: list[str] = []
                next_index = index + 1
                while next_index < len(frontmatter):
                    match = TOPIC_LIST_ITEM_PATTERN.fullmatch(frontmatter[next_index])
                    if match is None:
                        break
                    collected_files.append(unwrap_scalar(match.group(1)))
                    next_index += 1
                related_files = collected_files
                index = next_index - 1
        elif line.startswith("related:"):
            related = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("source_kind:"):
            source_kind = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("authority:"):
            authority = unwrap_scalar(line.split(":", 1)[1])
        elif line.startswith("lifecycle:"):
            lifecycle = unwrap_scalar(line.split(":", 1)[1])
        index += 1
    # Extract #topic tags from the full text (e.g. "#architecture #foundation")
    if not explicit_topics:
        topics = TOPIC_TAG_PATTERN.findall(text)
    m = LEGACY_RECORD_ID_PATTERN.match(path.name)
    if not record_id and m and rtype:
        record_id = f"{rtype}-{m.group(1)}"
    return {
        "project_id": project_id,
        "slug": slug,
        "record_id": record_id,
        "type": rtype,
        "title": title,
        "content": text,
        "key_conclusion": key_conclusion,
        "topics": ",".join(topics),
        "path": str(path).replace('\\', '/'),
        "created_at": date,
        "status": status,
        "source": source,
        "priority": priority,
        "severity": severity,
        "superseded_by": superseded_by,
        "fixes": fixes,
        "implements": implements,
        "related": related,
        "related_files": ",".join(related_files),
        "source_kind": source_kind,
        "authority": authority,
        "lifecycle": lifecycle,
    }
