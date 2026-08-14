from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module


def _memory_stats_payload(project_root: Path) -> dict:
    return {
        "project_id": "project-1",
        "slug": "demo",
        "root": str(project_root).replace("\\", "/"),
        "as_of": "2026-08-14T12:00:00+08:00",
        "totals": {
            "records": {"total": 4, "by_type": {"change": 2, "decision": 1, "requirement": 0, "bug": 1, "digest": 0, "theme-digest": 0}},
            "recall": {"status": "available", "events": 5, "injected": 3, "abstained": 2, "recall_rate": 0.6, "malformed_lines": 0},
        },
        "windows": {
            "7d": {
                "records": {"total": 2, "by_type": {"change": 1, "decision": 1, "requirement": 0, "bug": 0, "digest": 0, "theme-digest": 0}},
                "recall": {"status": "available", "events": 2, "injected": 1, "abstained": 1, "recall_rate": 0.5, "match_classes": {"topic": 1}, "top_matched_records": [{"record_id": "change-a", "count": 2}], "abstain_reasons": {"no-high-signal-recall": 1}, "malformed_lines": 0},
            },
            "30d": {
                "records": {"total": 4, "by_type": {"change": 2, "decision": 1, "requirement": 0, "bug": 1, "digest": 0, "theme-digest": 0}},
                "recall": {"status": "available", "events": 5, "injected": 3, "abstained": 2, "recall_rate": 0.6, "match_classes": {"topic": 2, "record-id": 1}, "top_matched_records": [{"record_id": "change-a", "count": 3}], "abstain_reasons": {"no-high-signal-recall": 2}, "malformed_lines": 0},
            },
        },
    }


def test_cli_project_memory_stats_json_calls_core_and_emits_json_only(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: a SyberMem project root and a Core memory stats payload
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload = _memory_stats_payload(project_root)
    called: dict[str, Path] = {}

    def fake_memory_stats(root: Path) -> dict:
        called["root"] = root
        return payload

    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "project_memory_stats", fake_memory_stats)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "memory-stats", "--format", "json"])

    # When: the memory-stats command is invoked through the parser boundary
    exit_code = main_module.main()

    # Then: it calls Core with the resolved root and writes only JSON to stdout
    captured = capsys.readouterr()
    assert exit_code == 0
    assert called == {"root": project_root}
    assert json.loads(captured.out) == payload
    assert captured.err == ""


def test_cli_project_memory_stats_text_prints_tables(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core returns populated 7d and 30d memory/recall stats
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "project_memory_stats", lambda root: _memory_stats_payload(root))
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "memory-stats"])

    # When: text mode is used
    exit_code = main_module.main()

    # Then: the terminal output contains the summary table and recall details
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Memory stats for demo" in captured.out
    assert "Window" in captured.out
    assert "7d" in captured.out
    assert "30d" in captured.out
    assert "Recall Rate" in captured.out
    assert "change-a" in captured.out


def test_cli_project_memory_stats_text_reports_missing_recall_log(tmp_path: Path, monkeypatch, capsys) -> None:
    # Given: Core reports memory counts but no recall debug log
    project_root = tmp_path / "project"
    project_root.mkdir()
    payload = _memory_stats_payload(project_root)
    for window in payload["windows"].values():
        window["recall"] = {"status": "no_log", "events": 0, "injected": 0, "abstained": 0, "recall_rate": None, "match_classes": {}, "top_matched_records": [], "abstain_reasons": {}, "malformed_lines": 0}
    payload["totals"]["recall"] = {"status": "no_log", "events": 0, "injected": 0, "abstained": 0, "recall_rate": None, "malformed_lines": 0}
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(main_module, "project_memory_stats", lambda root: payload)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "memory-stats"])

    # When: text mode is used
    exit_code = main_module.main()

    # Then: recall observability is marked unavailable rather than displayed as a zero-rate claim
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "7d      2        n/a" in captured.out
    assert "30d     4        n/a" in captured.out
    assert "Recall debug log: unavailable (.sybermem/.recall-debug.jsonl not found)" in captured.out


def test_cli_project_memory_stats_returns_1_without_project_root(monkeypatch, capsys) -> None:
    # Given: the command is invoked outside any SyberMem project
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: None)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "memory-stats"])

    # When: the parser dispatches the memory-stats command
    exit_code = main_module.main()

    # Then: it fails with a concise stderr message
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"
