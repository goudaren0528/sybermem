from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from typing import Final

from .identity import now_iso
from .records import iter_record_files, parse_project_yaml, parse_record_file


RECORD_TYPES: Final = ("change", "decision", "requirement", "bug", "digest", "theme-digest")
WINDOWS: Final = {"7d": 7, "30d": 30}


def project_memory_stats(root: Path) -> dict:
    meta = parse_project_yaml(root)
    today = _current_date()
    records = _record_rows(root, meta.get("project_id", ""), meta.get("slug", root.name))
    recall_entries, malformed_lines, recall_status = _recall_debug_entries(root)
    windows = {}
    for label, days in WINDOWS.items():
        since = today - timedelta(days=days - 1)
        windows[label] = {
            "records": _record_counts([row for row in records if _date_in_window(row.get("created_at", ""), since, today)]),
            "recall": _recall_counts([entry for entry in recall_entries if _date_in_window(str(entry.get("timestamp", "")), since, today)], malformed_lines, recall_status),
        }
    return {
        "project_id": meta.get("project_id", ""),
        "slug": meta.get("slug", root.name),
        "root": str(root).replace("\\", "/"),
        "as_of": now_iso(),
        "totals": {
            "records": _record_counts(records),
            "recall": _recall_counts(recall_entries, malformed_lines, recall_status),
        },
        "windows": windows,
    }


def _current_date() -> date:
    return _parse_date(now_iso()) or date.today()


def _record_rows(root: Path, project_id: str, slug: str) -> list[dict[str, str]]:
    rows = []
    for path in iter_record_files(root):
        row = parse_record_file(path, project_id, slug)
        folder_type = _type_from_folder(path)
        if folder_type:
            row["type"] = folder_type
        rows.append(row)
    return rows


def _type_from_folder(path: Path) -> str:
    parent = path.parent.name
    if parent == "digests":
        return "digest"
    if parent == "theme-digests":
        return "theme-digest"
    return ""


def _record_counts(records: list[dict[str, str]]) -> dict:
    by_type = _empty_counts()
    for row in records:
        rtype = row.get("type", "")
        if rtype in by_type:
            by_type[rtype] += 1
    return {"total": len(records), "by_type": by_type}


def _empty_counts() -> dict[str, int]:
    return {record_type: 0 for record_type in RECORD_TYPES}


def _recall_debug_entries(root: Path) -> tuple[list[dict], int, str]:
    path = root / ".sybermem" / ".recall-debug.jsonl"
    if not path.is_file():
        return [], 0, "no_log"
    entries = []
    malformed_lines = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            malformed_lines += 1
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
        else:
            malformed_lines += 1
    return entries, malformed_lines, "available"


def _recall_counts(entries: list[dict], malformed_lines: int, status: str) -> dict:
    events = len(entries)
    injected = sum(1 for entry in entries if entry.get("event") == "inject")
    abstained = sum(1 for entry in entries if entry.get("event") == "abstain")
    match_classes: Counter[str] = Counter()
    matched_records: Counter[str] = Counter()
    abstain_reasons: Counter[str] = Counter()
    for entry in entries:
        match_classes.update(_string_list(entry.get("match_classes")))
        matched_records.update(_string_list(entry.get("record_ids")))
        reason = entry.get("reason")
        if entry.get("event") == "abstain" and isinstance(reason, str) and reason:
            abstain_reasons[reason] += 1
    return {
        "status": status,
        "events": events,
        "injected": injected,
        "abstained": abstained,
        "recall_rate": injected / events if events else None,
        "match_classes": dict(sorted(match_classes.items())),
        "top_matched_records": [
            {"record_id": record_id, "count": count}
            for record_id, count in matched_records.most_common(5)
        ],
        "abstain_reasons": dict(sorted(abstain_reasons.items())),
        "malformed_lines": malformed_lines,
    }


def _string_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _date_in_window(value: str, since: date, today: date) -> bool:
    parsed = _parse_date(value)
    return parsed is not None and since <= parsed <= today


def _parse_date(value: str) -> date | None:
    if len(value) < 10:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None
