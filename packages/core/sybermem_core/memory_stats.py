from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta
import json
from pathlib import Path
from typing import Final

from .identity import now_iso
from .digest_governance import digest_backlog
from .norms import norm_coverage
from .records import iter_record_files, parse_project_yaml, parse_record_file
from .memory_usage_stats import aggregate_memory_outcomes, aggregate_memory_usage_window, read_memory_usage_journal


RECORD_TYPES: Final = ("change", "decision", "requirement", "bug", "norm", "digest", "theme-digest")
WINDOWS: Final = {"7d": 7, "30d": 30}
# Recent recall injection rate below this is treated as low-signal: prompts are
# arriving but the high-signal gate rarely finds anything worth injecting.
LOW_SIGNAL_RECALL_RATE: Final = 0.2
# Recent recall precision below this is treated as low-relevance: recall is
# injecting records, but few of them line up with what was actually edited.
LOW_RELEVANCE_PRECISION: Final = 0.34
# Minimum injected-record samples before precision can lower the verdict. Below
# this, precision stays advisory-only so a couple of misses never look like a
# systemic relevance problem.
MIN_PRECISION_SAMPLES: Final = 3


def project_memory_stats(root: Path) -> dict:
    meta = parse_project_yaml(root)
    today = _current_date()
    records = _record_rows(root, meta.get("project_id", ""), meta.get("slug", root.name))
    recall_entries, malformed_lines, recall_status = _recall_debug_entries(root)
    outcome_entries = _recall_outcome_entries(root)
    usage_turns, usage_outcomes, usage_status = read_memory_usage_journal(root)
    windows = {}
    for label, days in WINDOWS.items():
        since = today - timedelta(days=days - 1)
        window_usage_outcomes = aggregate_memory_outcomes(usage_outcomes, since, today)
        windows[label] = {
            "records": _record_counts([row for row in records if _date_in_window(row.get("created_at", ""), since, today)]),
            "recall": _recall_counts([entry for entry in recall_entries if _date_in_window(str(entry.get("timestamp", "")), since, today)], malformed_lines, recall_status),
            "relevance": _relevance_for_window([entry for entry in outcome_entries if _date_in_window(str(entry.get("timestamp", "")), since, today)], window_usage_outcomes),
            "memory_usage": aggregate_memory_usage_window(usage_turns, since, today) if usage_status == "available" else _empty_memory_usage(usage_status),
        }
    total_usage_outcomes = aggregate_memory_outcomes(usage_outcomes)
    return {
        "project_id": meta.get("project_id", ""),
        "slug": meta.get("slug", root.name),
        "root": str(root).replace("\\", "/"),
        "as_of": now_iso(),
        "totals": {
            "records": _record_counts(records),
            "recall": _recall_counts(recall_entries, malformed_lines, recall_status),
            "relevance": _relevance_for_window(outcome_entries, total_usage_outcomes),
            "memory_usage": aggregate_memory_usage_window(usage_turns, today - timedelta(days=29), today) if usage_status == "available" else _empty_memory_usage(usage_status),
        },
        "windows": windows,
        "recall_health": _recall_health_from_windows(windows, recall_status),
        # Snapshot (not windowed): how much undigested work has accumulated. Makes the
        # compression layer's health as visible as recall health.
        "digest_coverage": digest_backlog(root),
        # Snapshot: active norm count, global/scoped split, and constitution budget usage.
        "norm_coverage": norm_coverage(root),
    }


def recall_health(root: Path) -> dict:
    """Return an advisory recall-health verdict for the project.

    Derives status from the same 7d/30d recall windows the stats command exposes,
    so hosts can surface a bounded, actionable signal without re-reading the log.
    """
    return project_memory_stats(root)["recall_health"]


def _recall_health_from_windows(windows: dict, recall_status: str) -> dict:
    if recall_status == "no_log":
        return {
            "status": "no_log",
            "recall_rate": None,
            "precision": None,
            "hint": "No recall debug log yet (.sybermem/.recall-debug.jsonl); recall observability is unavailable until prompts run on a recall-capable host.",
        }
    recall_7d = windows["7d"]["recall"]
    recall_30d = windows["30d"]["recall"]
    events_7d = recall_7d["events"]
    events_30d = recall_30d["events"]
    if events_7d == 0 and events_30d == 0:
        return {
            "status": "no_activity",
            "recall_rate": None,
            "precision": None,
            "hint": "No prompt-time recall events in the last 30 days; recent recall quality cannot be assessed yet.",
        }
    window = recall_7d if events_7d > 0 else recall_30d
    rate = window["recall_rate"]
    if rate is not None and rate < LOW_SIGNAL_RECALL_RATE:
        return {
            "status": "low_signal",
            "recall_rate": rate,
            "precision": None,
            "hint": "Recent recall injection rate is low; consider adding topics to key records or running /sybermem-digest so high-signal recall can match more prompts.",
        }
    # Injection rate looks healthy; now check whether injected records line up
    # with what was actually edited (relevance), using the recall-outcome log.
    relevance_7d = windows["7d"].get("relevance", {})
    relevance_30d = windows["30d"].get("relevance", {})
    relevance = relevance_7d if relevance_7d.get("injected", 0) > 0 else relevance_30d
    precision = relevance.get("precision")
    injected_samples = relevance.get("injected", 0)
    if precision is not None and injected_samples >= MIN_PRECISION_SAMPLES and precision < LOW_RELEVANCE_PRECISION:
        return {
            "status": "low_relevance",
            "recall_rate": rate,
            "precision": precision,
            "hint": "Recall is firing, but most injected records did not line up with edited files; refresh stale related_files on key records or tighten high-signal recall so noise drops.",
        }
    return {
        "status": "healthy",
        "recall_rate": rate,
        "precision": precision if injected_samples >= MIN_PRECISION_SAMPLES else None,
        "hint": "Recent recall injection rate is healthy.",
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


def _recall_outcome_entries(root: Path) -> list[dict]:
    """Read bounded recall-outcome entries; malformed/non-dict lines are skipped.

    Absence of the log is not an error: it just means no edit-aware relevance
    evidence has been produced yet, so relevance stays unknown (fail-open).
    """
    path = root / ".sybermem" / ".recall-outcomes.jsonl"
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
    return entries


def _relevance_counts(entries: list[dict]) -> dict:
    """Aggregate injected/hit counts into a precision measure.

    precision = hit injected records / all injected records across the window.
    Returns precision=None when there is no injected-record evidence, so callers
    never divide by zero and unknown relevance stays explicitly unknown.
    """
    injected = 0
    hit = 0
    for entry in entries:
        injected += _non_negative_int(entry.get("injected"))
        hit += _non_negative_int(entry.get("hit"))
    return {
        "sessions": len(entries),
        "injected": injected,
        "measurable": injected,
        "unmeasurable": 0,
        "hit": hit,
        "precision": hit / injected if injected else None,
        "evidence_available": bool(entries) if entries else None,
    }


def _relevance_for_window(legacy_entries: list[dict], usage_outcomes: dict) -> dict:
    if usage_outcomes.get("sessions", 0) > 0:
        return usage_outcomes
    return _relevance_counts(legacy_entries)


def _empty_memory_usage(status: str) -> dict:
    return {
        "status": status,
        "turns": 0,
        "items": 0,
        "chars": 0,
        "digest_items": 0,
        "avg_chars_per_turn": None,
        "p95_chars_per_turn": None,
        "lanes": {lane: {"items": 0, "chars": 0} for lane in ("recall", "habit", "norm", "startup")},
    }


def _non_negative_int(value) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _recall_counts(entries: list[dict], malformed_lines: int, status: str) -> dict:
    events = len(entries)
    injected = sum(1 for entry in entries if entry.get("event") == "inject")
    digest_injected = sum(1 for entry in entries if entry.get("event") == "inject" and entry.get("has_digest") is True)
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
        "digest_injected": digest_injected,
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
