from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import NoReturn

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.memory_usage_stats import aggregate_memory_usage, nearest_rank_p95, read_memory_usage_journal


def _write_journal(root: Path, lines: list[dict | str]) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / ".memory-usage.jsonl").write_text(
        "\n".join(line if isinstance(line, str) else json.dumps(line) for line in lines) + "\n",
        encoding="utf-8",
    )


def _turn(timestamp: str, chars: int, items: int = 1, **lanes: int) -> dict:
    return {
        "schema_version": 1,
        "timestamp": timestamp,
        "host": "opencode",
        "session_id": "session-1",
        "total_items": items,
        "total_chars": chars,
        "recall_items": lanes.get("recall_items", 0),
        "recall_chars": lanes.get("recall_chars", 0),
        "habit_items": lanes.get("habit_items", 0),
        "habit_chars": lanes.get("habit_chars", 0),
        "norm_items": lanes.get("norm_items", 0),
        "norm_chars": lanes.get("norm_chars", 0),
        "startup_items": lanes.get("startup_items", 0),
        "startup_chars": lanes.get("startup_chars", 0),
    }


def test_nearest_rank_p95_uses_boundary_rank() -> None:
    # Given: small and even samples where interpolation would produce a different value
    # When: the deterministic nearest-rank p95 is computed
    # Then: the rank is ceil(0.95 * n), clamped to the sample bounds
    assert nearest_rank_p95([10]) == 10
    assert nearest_rank_p95([10, 20]) == 20
    assert nearest_rank_p95([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]) == 100
    assert nearest_rank_p95([]) is None


def test_memory_usage_journal_skips_malformed_unknown_and_outcome_rows(tmp_path: Path) -> None:
    # Given: a mixed bounded journal with valid turns, an outcome, and invalid variants
    lines = [
        _turn("2026-08-14T09:00:00+08:00", 10),
        {"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-14T09:01:00+08:00", "recall_measurable": 2, "recall_unmeasurable": 1, "recall_hit": 1, "recall_evidence_available": True},
        {**_turn("2026-08-14T09:02:00+08:00", 20), "schema_version": 2},
        {**_turn("2026-08-14T09:03:00+08:00", 30), "host": "claude"},
        {**_turn("2026-08-14T09:04:00+08:00", 40), "event": "unknown"},
        "not json",
    ]
    _write_journal(tmp_path, lines)

    # When: the journal is parsed
    turns, outcomes, status = read_memory_usage_journal(tmp_path)

    # Then: only valid OpenCode turn/outcome variants survive parsing
    assert status == "available"
    assert len(turns) == 1
    assert len(outcomes) == 1


def test_memory_usage_aggregates_lanes_and_p95_without_outcome_double_counting(tmp_path: Path) -> None:
    # Given: three valid turns and one session outcome in the 7d window
    _write_journal(
        tmp_path,
        [
            _turn("2026-08-14T09:00:00+08:00", 10, recall_items=1, recall_chars=4),
            _turn("2026-08-13T09:00:00+08:00", 20, habit_items=1, habit_chars=7),
            _turn("2026-08-12T09:00:00+08:00", 30, norm_items=1, norm_chars=9, startup_items=1, startup_chars=5),
            {"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-14T09:01:00+08:00", "memory_turns": 99, "memory_chars": 999},
        ],
    )

    # When: usage is aggregated
    result = aggregate_memory_usage(tmp_path, "2026-08-14")

    # Then: turn metrics use only per-turn rows and preserve lane item/char totals
    assert result["status"] == "available"
    assert result["turns"] == 3
    assert result["items"] == 3
    assert result["chars"] == 60
    assert result["avg_chars_per_turn"] == 20
    assert result["p95_chars_per_turn"] == 30
    assert result["lanes"] == {
        "recall": {"items": 1, "chars": 4},
        "habit": {"items": 1, "chars": 7},
        "norm": {"items": 1, "chars": 9},
        "startup": {"items": 1, "chars": 5},
    }


def test_memory_usage_is_explicitly_unavailable_when_journal_is_missing(tmp_path: Path) -> None:
    # Given: a project without the bounded usage journal
    # When: usage is aggregated
    result = aggregate_memory_usage(tmp_path, "2026-08-14")

    # Then: absence is distinct from a measured zero
    assert result == {
        "status": "no_log",
        "turns": 0,
        "items": 0,
        "chars": 0,
        "avg_chars_per_turn": None,
        "p95_chars_per_turn": None,
        "lanes": {
            "recall": {"items": 0, "chars": 0},
            "habit": {"items": 0, "chars": 0},
            "norm": {"items": 0, "chars": 0},
            "startup": {"items": 0, "chars": 0},
        },
    }


def test_memory_usage_is_unavailable_when_journal_read_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: the usage journal exists but cannot be read
    _write_journal(tmp_path, [_turn("2026-08-14T09:00:00+08:00", 10)])

    def fail_read_text(self: Path, encoding: str | None = None) -> NoReturn:  # noqa: ARG001
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    # When
    turns, outcomes, status = read_memory_usage_journal(tmp_path)

    # Then
    assert turns == []
    assert outcomes == []
    assert status == "unavailable"


def test_memory_usage_is_unavailable_when_journal_is_not_utf8(tmp_path: Path) -> None:
    # Given: a usage journal with invalid UTF-8 bytes
    sybermem = tmp_path / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / ".memory-usage.jsonl").write_bytes(b"\xff\xfe\xfd")

    # When
    result = aggregate_memory_usage(tmp_path, "2026-08-14")

    # Then
    assert result["status"] == "unavailable"
    assert result["turns"] == 0


def test_memory_usage_is_unavailable_when_journal_is_oversized(tmp_path: Path) -> None:
    # Given: a usage journal larger than the parser cap
    sybermem = tmp_path / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / ".memory-usage.jsonl").write_text("x" * 1_000_001, encoding="utf-8")

    # When
    turns, outcomes, status = read_memory_usage_journal(tmp_path)

    # Then
    assert turns == []
    assert outcomes == []
    assert status == "unavailable"
