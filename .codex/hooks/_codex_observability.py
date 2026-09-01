"""Shared, fail-open observability journaling for SyberMem Codex hooks.

Codex hooks inject context and then exit; nothing records what was injected. This
module lets the Codex hooks write the SAME bounded JSONL journals the OpenCode
plugin writes, so `sybermem project memory-stats` can quantify Codex recall/lane
activity too.

Design constraints:
- Pure standard library. Hook processes cannot rely on sybermem_core being
  importable, so this stays dependency-free.
- Fail-open. Any write/parse error is swallowed; observability must never break
  injection or fail a hook.
- Schema parity with the OpenCode plugin (recall_debug.ts / memory_usage.ts /
  recall_outcome.ts) so Core's memory_usage_stats / memory_stats aggregate both
  hosts. The only intended difference is the source/host tag ("codex").
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Final

# Match OpenCode's boundedJsonlAppend cap so journals stay small and Core's
# MAX_JOURNAL_BYTES guard is never tripped in normal use.
MAX_JOURNAL_LINES: Final = 200
RECALL_DEBUG_FILE: Final = ".recall-debug.jsonl"
MEMORY_USAGE_FILE: Final = ".memory-usage.jsonl"
RECALL_OUTCOMES_FILE: Final = ".recall-outcomes.jsonl"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _bounded_append(root: Path, name: str, entry: dict) -> None:
    """Append one JSON line, keeping only the most recent MAX_JOURNAL_LINES.

    Fail-open: any error (unwritable dir, encoding, serialization) is swallowed so
    a journaling failure never propagates out of a hook.
    """
    try:
        path = root / ".sybermem" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: list[str] = []
        if path.is_file():
            existing = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        existing.append(json.dumps(entry, ensure_ascii=False))
        path.write_text("\n".join(existing[-MAX_JOURNAL_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        # Observability is advisory; never break the hook.
        pass


def append_recall_debug(
    root: Path,
    *,
    injected: bool,
    record_ids: list[str],
    match_classes: list[str],
    reason: str,
    timestamp: str | None = None,
) -> None:
    """Write one recall-debug row (schema parity with recall_debug.ts).

    `source: "codex-user-prompt"` distinguishes Codex rows from OpenCode's
    `opencode-chat-message`. Core's _recall_counts does not filter on source, so
    these rows are aggregated the same way.
    """
    ids = _bounded_ids(record_ids)
    _bounded_append(
        root,
        RECALL_DEBUG_FILE,
        {
            "source": "codex-user-prompt",
            "timestamp": timestamp or _now_iso(),
            "event": "inject" if injected else "abstain",
            "record_ids": ids,
            "has_digest": any(rid.startswith("digest-") for rid in ids),
            "match_classes": _bounded_ids(match_classes),
            "reason": reason,
        },
    )


def append_memory_usage_turn(
    root: Path,
    *,
    session_id: str,
    recall_items: int,
    recall_chars: int,
    habit_items: int,
    habit_chars: int,
    norm_items: int,
    norm_chars: int,
    startup_items: int = 0,
    startup_chars: int = 0,
    injected_ids: list[str] | None = None,
    timestamp: str | None = None,
) -> None:
    """Write one per-turn memory-usage row (schema parity with memory_usage.ts).

    Mirrors appendMemoryUsage: only writes when total_items > 0, so pure-abstain
    turns do not pollute lane statistics. host is "codex".
    """
    ids = _bounded_ids(injected_ids or [])
    total_items = recall_items + habit_items + norm_items + startup_items
    if total_items <= 0:
        return
    total_chars = recall_chars + habit_chars + norm_chars + startup_chars
    _bounded_append(
        root,
        MEMORY_USAGE_FILE,
        {
            "schema_version": 1,
            "timestamp": timestamp or _now_iso(),
            "host": "codex",
            "session_id": _bounded_session_id(session_id),
            "total_items": total_items,
            "total_chars": total_chars,
            "digest_items": sum(1 for rid in ids if rid.startswith("digest-")),
            "recall_items": recall_items,
            "recall_chars": recall_chars,
            "habit_items": habit_items,
            "habit_chars": habit_chars,
            "norm_items": norm_items,
            "norm_chars": norm_chars,
            "startup_items": startup_items,
            "startup_chars": startup_chars,
            "injected_ids": ids,
            "startup_present": startup_items > 0,
        },
    )


def append_session_outcome(
    root: Path,
    *,
    session_id: str,
    injected_ids: list[str],
    edited_files: int,
    evidence_available: bool,
    measurable: int,
    unmeasurable: int,
    hit: int,
    timestamp: str | None = None,
) -> None:
    """Write a session_outcome row + a recall-outcomes row (parity with recall_outcome.ts).

    Used by SessionEnd to record edit-alignment / precision. Fail-open at the
    caller: when evidence cannot be gathered in the tight SessionEnd budget, pass
    evidence_available=False and zero counts.
    """
    ts = timestamp or _now_iso()
    precision = (hit / measurable) if measurable else None
    _bounded_append(
        root,
        MEMORY_USAGE_FILE,
        {
            "schema_version": 1,
            "host": "codex",
            "event": "session_outcome",
            "timestamp": ts,
            "session_id": _bounded_session_id(session_id),
            "edited_files": edited_files,
            "recall_evidence_available": evidence_available,
            "recall_measurable": measurable,
            "recall_unmeasurable": unmeasurable,
            "recall_hit": hit,
            "recall_precision": precision,
        },
    )
    if not evidence_available or (measurable + unmeasurable) == 0:
        return
    _bounded_append(
        root,
        RECALL_OUTCOMES_FILE,
        {
            "timestamp": ts,
            "session": _bounded_session_id(session_id),
            "injected": measurable,
            "measurable": measurable,
            "unmeasurable": unmeasurable,
            "hit": hit,
            "precision": precision,
        },
    )


def _bounded_ids(values: list[str], limit: int = 40) -> list[str]:
    seen: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        lowered = value.strip().lower()
        if lowered and lowered not in seen:
            seen.append(lowered)
        if len(seen) >= limit:
            break
    return seen


def _bounded_session_id(session_id: str, max_chars: int = 80) -> str:
    text = session_id if isinstance(session_id, str) else ""
    return text[:max_chars]
