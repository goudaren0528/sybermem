from __future__ import annotations

from pathlib import Path
import re


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


def parse_record_file(path: Path, project_id: str, slug: str) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    title = ""
    rtype = ""
    date = ""
    topics: list[str] = []
    record_id = ""
    status = ""
    superseded_by = ""
    for line in text.splitlines():
        if line.startswith("type:"):
            rtype = line.split(":", 1)[1].strip()
        elif line.startswith("date:"):
            date = line.split(":", 1)[1].strip()
        elif line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("status:"):
            status = line.split(":", 1)[1].strip()
        elif line.startswith("superseded_by:"):
            superseded_by = line.split(":", 1)[1].strip()
    # Extract #topic tags from the full text (e.g. "#architecture #foundation")
    topics = re.findall(r"#([a-zA-Z][a-zA-Z0-9_-]*)", text)
    m = re.match(r"\d{4}-\d{2}-\d{2}-(\d{3})-", path.name)
    if m and rtype:
        record_id = f"{rtype}-{m.group(1)}"
    return {
        "project_id": project_id,
        "slug": slug,
        "record_id": record_id,
        "type": rtype,
        "title": title,
        "content": text,
        "topics": ",".join(topics),
        "path": str(path).replace('\\', '/'),
        "created_at": date,
        "status": status,
        "superseded_by": superseded_by,
    }
