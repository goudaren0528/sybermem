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


def parse_project_yaml(root: Path) -> dict[str, str]:
    proj = root / ".sybermem" / "project.yaml"
    if not proj.is_file():
        return {}
    out: dict[str, str] = {}
    for line in proj.read_text(encoding="utf-8").splitlines():
        if ":" in line and not line.startswith("  "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


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
    return [item.strip() for item in stripped.split(",") if item.strip()]


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
    authority = ""
    lifecycle = ""
    explicit_topics = False
    frontmatter = _frontmatter_lines(text)
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if line.startswith("type:"):
            rtype = line.split(":", 1)[1].strip()
        elif line.startswith("date:"):
            date = line.split(":", 1)[1].strip()
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("record_id:"):
            record_id = line.split(":", 1)[1].strip()
        elif line.startswith("key_conclusion:"):
            key_conclusion = line.split(":", 1)[1].strip()
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
                    collected_topics.append(match.group(1).strip())
                    next_index += 1
                topics = collected_topics
                index = next_index - 1
        elif line.startswith("status:"):
            status = line.split(":", 1)[1].strip()
        elif line.startswith("source:"):
            source = line.split(":", 1)[1].strip()
        elif line.startswith("priority:"):
            priority = line.split(":", 1)[1].strip()
        elif line.startswith("severity:"):
            severity = line.split(":", 1)[1].strip()
        elif line.startswith("superseded_by:"):
            superseded_by = line.split(":", 1)[1].strip()
        elif line.startswith("fixes:"):
            fixes = line.split(":", 1)[1].strip()
        elif line.startswith("implements:"):
            implements = line.split(":", 1)[1].strip()
        elif line.startswith("related:"):
            related = line.split(":", 1)[1].strip()
        elif line.startswith("authority:"):
            authority = line.split(":", 1)[1].strip()
        elif line.startswith("lifecycle:"):
            lifecycle = line.split(":", 1)[1].strip()
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
        "authority": authority,
        "lifecycle": lifecycle,
    }
