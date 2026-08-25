from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
from math import ceil
from pathlib import Path
from typing import Final, TypedDict


LANES: Final = ("recall", "habit", "norm", "startup")
MAX_JOURNAL_BYTES: Final = 1_000_000


class LaneStats(TypedDict):
    items: int
    chars: int


class MemoryUsageStats(TypedDict):
    status: str
    turns: int
    items: int
    chars: int
    digest_items: int
    avg_chars_per_turn: float | None
    p95_chars_per_turn: int | None
    lanes: dict[str, LaneStats]


@dataclass(frozen=True, slots=True)
class UsageTurn:
    timestamp: date
    items: int
    chars: int
    digest_items: int
    lanes: dict[str, LaneStats]


@dataclass(frozen=True, slots=True)
class UsageOutcome:
    timestamp: date
    evidence_available: bool
    measurable: int
    unmeasurable: int
    hit: int


def read_memory_usage_journal(root: Path) -> tuple[list[UsageTurn], list[UsageOutcome], str]:
    """Parse valid OpenCode per-turn and session-outcome journal rows."""
    path = root / ".sybermem" / ".memory-usage.jsonl"
    if not path.is_file():
        return [], [], "no_log"
    try:
        if path.stat().st_size > MAX_JOURNAL_BYTES:
            return [], [], "unavailable"
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [], [], "unavailable"
    turns: list[UsageTurn] = []
    outcomes: list[UsageOutcome] = []
    for line in content.splitlines():
        parsed = _parse_line(line)
        if parsed is None:
            continue
        turn = _parse_turn(parsed)
        if turn is not None:
            turns.append(turn)
            continue
        outcome = _parse_outcome(parsed)
        if outcome is not None:
            outcomes.append(outcome)
    return turns, outcomes, "available"


def aggregate_memory_usage(root: Path, today_value: str) -> MemoryUsageStats:
    """Aggregate valid per-turn usage rows for the trailing 30-day window."""
    turns, _, status = read_memory_usage_journal(root)
    empty = _empty_stats(status)
    if status == "no_log":
        return empty
    today = _parse_date(today_value)
    if today is None:
        return empty
    selected = [turn for turn in turns if today - timedelta(days=29) <= turn.timestamp <= today]
    return _aggregate(selected, status)


def aggregate_memory_usage_window(turns: list[UsageTurn], since: date, today: date) -> MemoryUsageStats:
    """Aggregate already parsed turns in an inclusive date window."""
    return _aggregate([turn for turn in turns if since <= turn.timestamp <= today], "available")


def aggregate_memory_outcomes(outcomes: list[UsageOutcome], since: date | None = None, today: date | None = None) -> dict:
    """Aggregate measurable and unavailable relevance evidence from outcomes."""
    selected = [outcome for outcome in outcomes if since is None or today is None or since <= outcome.timestamp <= today]
    measurable = sum(outcome.measurable for outcome in selected)
    hit = sum(outcome.hit for outcome in selected)
    return {
        "sessions": len(selected),
        "injected": measurable,
        "measurable": measurable,
        "unmeasurable": sum(outcome.unmeasurable for outcome in selected),
        "hit": hit,
        "precision": hit / measurable if measurable else None,
        "evidence_available": all(outcome.evidence_available for outcome in selected) if selected else None,
    }


def nearest_rank_p95(values: list[int]) -> int | None:
    """Return p95 using the one-based nearest-rank definition."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, ceil(0.95 * len(ordered)))
    return ordered[min(rank, len(ordered)) - 1]


def _aggregate(turns: list[UsageTurn], status: str) -> MemoryUsageStats:
    chars = sum(turn.chars for turn in turns)
    lanes = {lane: {"items": 0, "chars": 0} for lane in LANES}
    for turn in turns:
        for lane in LANES:
            lanes[lane]["items"] += turn.lanes[lane]["items"]
            lanes[lane]["chars"] += turn.lanes[lane]["chars"]
    return {
        "status": status,
        "turns": len(turns),
        "items": sum(turn.items for turn in turns),
        "chars": chars,
        "digest_items": sum(turn.digest_items for turn in turns),
        "avg_chars_per_turn": chars / len(turns) if turns else None,
        "p95_chars_per_turn": nearest_rank_p95([turn.chars for turn in turns]),
        "lanes": lanes,
    }


def _empty_stats(status: str) -> MemoryUsageStats:
    return {
        "status": status,
        "turns": 0,
        "items": 0,
        "chars": 0,
        "digest_items": 0,
        "avg_chars_per_turn": None,
        "p95_chars_per_turn": None,
        "lanes": {lane: {"items": 0, "chars": 0} for lane in LANES},
    }


def _parse_line(line: str) -> dict[str, object] | None:
    try:
        parsed = json.loads(line)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_turn(row: dict[str, object]) -> UsageTurn | None:
    if row.get("schema_version") != 1 or row.get("host") != "opencode" or "event" in row:
        return None
    timestamp = _parse_date(row.get("timestamp"))
    numeric = {key: _non_negative_int(row.get(key)) for key in ("total_items", "total_chars")}
    digest_items = _non_negative_int(row.get("digest_items")) or 0
    if timestamp is None or numeric["total_items"] is None or numeric["total_chars"] is None:
        return None
    lanes = {
        lane: {"items": _non_negative_int(row.get(f"{lane}_items")) or 0, "chars": _non_negative_int(row.get(f"{lane}_chars")) or 0}
        for lane in LANES
    }
    return UsageTurn(timestamp, numeric["total_items"], numeric["total_chars"], digest_items, lanes)


def _parse_outcome(row: dict[str, object]) -> UsageOutcome | None:
    if row.get("schema_version") != 1 or row.get("host") != "opencode" or row.get("event") != "session_outcome":
        return None
    timestamp = _parse_date(row.get("timestamp"))
    measurable = _non_negative_int(row.get("recall_measurable"))
    unmeasurable = _non_negative_int(row.get("recall_unmeasurable"))
    hit = _non_negative_int(row.get("recall_hit"))
    evidence = row.get("recall_evidence_available")
    if timestamp is None or measurable is None or unmeasurable is None or hit is None or not isinstance(evidence, bool):
        return None
    return UsageOutcome(timestamp, evidence, measurable, unmeasurable, hit)


def _non_negative_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None
