from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import context as context_module
from sybermem_cli import main as main_module


def run_cli(argv: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(sys, "argv", ["sybermem", *argv])
    return main_module.main()


def test_cli_context_session_json_uses_resume_checkpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: a SyberMem project and a deterministic resume checkpoint
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(context_module, "resolve_project_root", lambda: project_root)
    monkeypatch.setattr(
        context_module,
        "build_resume_checkpoint",
        lambda root, mode: {
            "mode": mode,
            "project": {"slug": "demo", "path": str(root)},
            "brief": ["line one", "line two"],
            "next_action": {"action": "/sybermem-record", "reason": "record useful work"},
        },
    )

    # When: session context is requested through the real CLI parser
    exit_code = run_cli(["context", "session", "--format", "json"], monkeypatch)

    # Then: the payload is explicit that this is a manual context helper
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["delivery"] == "manual"
    assert payload["kind"] == "session"
    assert payload["project"] == "demo"
    assert payload["brief"] == ["line one", "line two"]
    assert payload["next_action"]["action"] == "/sybermem-record"


def test_cli_context_prompt_markdown_uses_project_search(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: project search returns one relevant record
    monkeypatch.setattr(
        context_module,
        "search_project",
        lambda query: [
            {
                "record_id": "change-123",
                "title": "Fix auth flow",
                "type": "change",
                "score": 7,
            }
        ],
    )

    # When: prompt context is requested as Markdown
    exit_code = run_cli(["context", "prompt", "--query", "auth", "--format", "markdown"], monkeypatch)

    # Then: the output is copy/paste-safe and names matching record IDs
    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("## SyberMem Manual Prompt Context")
    assert "Delivery: manual" in output
    assert "[change-123]" in output


def test_cli_context_habit_json_delegates_to_reminder_renderer(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: the habit reminder renderer returns one matching habit row
    monkeypatch.setattr(
        context_module,
        "render_habit_reminder_markdown",
        lambda context, higher_authority_text="": "## User Habit Reminder\n- [habit-abc] keep plans short\n",
    )

    # When: habit context is requested through the manual context helper
    exit_code = run_cli(["context", "habit", "--context", "planning", "--format", "json"], monkeypatch)

    # Then: the helper remains a manual delivery surface and exposes habit IDs structurally
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["delivery"] == "manual"
    assert payload["kind"] == "habit"
    assert payload["reminded"] == ["habit-abc"]


def test_cli_context_habit_json_defaults_to_manual_delivery_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: the reminder renderer returns one matching habit row
    monkeypatch.setattr(
        context_module,
        "render_habit_reminder_markdown",
        lambda context, higher_authority_text="": "## User Habit Reminder\n- [habit-abc] keep plans short\n",
    )

    # When: habit context is requested without an explicit delivery override
    exit_code = run_cli(["context", "habit", "--context", "planning", "--format", "json"], monkeypatch)

    # Then: the JSON contract stays manual by default and includes reminder metadata
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "habit"
    assert payload["delivery"] == "manual"
    assert payload["delivery_metadata"] == {"mode": "manual"}
    assert payload["reminded"] == ["habit-abc"]


def test_cli_context_habit_json_supports_prompt_time_delivery_metadata(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: the reminder renderer returns one matching habit row
    monkeypatch.setattr(
        context_module,
        "render_habit_reminder_markdown",
        lambda context, higher_authority_text="": "## User Habit Reminder\n- [habit-xyz] restate acceptance criteria\n",
    )

    # When: habit context is requested for prompt-time delivery
    exit_code = run_cli(
        ["context", "habit", "--context", "planning", "--delivery", "prompt-time", "--format", "json"],
        monkeypatch,
    )

    # Then: the JSON contract reports prompt-time delivery while preserving reminder IDs
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "habit"
    assert payload["delivery"] == "prompt-time"
    assert payload["delivery_metadata"] == {"mode": "prompt-time"}
    assert payload["reminded"] == ["habit-xyz"]


def test_cli_record_intent_json_uses_core_classifier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: a SyberMem project root is available to the CLI classifier route
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: project_root)

    # When: record intent is classified through the real CLI parser
    exit_code = run_cli(["record", "intent", "--prompt", "Record this decision about plugin modules", "--format", "json"], monkeypatch)

    # Then: the route exposes bounded classifier metadata without prompt text
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["classification"] == "decision"
    assert payload["action"] == "/sybermem-record"
    assert "plugin modules" not in json.dumps(payload)


def test_cli_context_returns_error_without_project_root(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: the command is invoked outside a SyberMem project
    monkeypatch.setattr(context_module, "resolve_project_root", lambda: None)

    # When: session context is requested
    exit_code = run_cli(["context", "session"], monkeypatch)

    # Then: the CLI reports the standard concise root-not-found error
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def test_cli_context_recall_markdown_uses_high_signal_hints_with_markers(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: high-signal recall returns one aha (record-id) and one non-aha (topic) row
    monkeypatch.setattr(
        context_module,
        "high_signal_recall_hints",
        lambda query, limit=3: (
            [
                {
                    "record_id": "change-abc",
                    "title": "Exact id hit",
                    "type": "change",
                    "score": 100,
                    "match": "record-id",
                    "match_reason": "record-id",
                },
                {
                    "record_id": "change-def",
                    "title": "Topic hit below floor",
                    "type": "change",
                    "score": 10,
                    "match": "topic",
                    "match_reason": "topic",
                },
            ],
            "",
        ),
    )

    # When: recall context is requested as Markdown through the real CLI parser
    exit_code = run_cli(["context", "recall", "--query", "auth", "--format", "markdown"], monkeypatch)

    # Then: the packet is gated and carries ⭐ for high-signal and 💡 for ordinary rows
    output = capsys.readouterr().out
    assert exit_code == 0
    assert output.startswith("## SyberMem Recall Hints")
    assert "Delivery: prompt-time automatic recall" in output
    assert "⭐ [change-abc] Exact id hit" in output
    assert "💡 [change-def] Topic hit below floor" in output


def test_cli_context_recall_json_includes_explanation_without_markdown_bloat(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: high-signal recall returns bounded scoring metadata from core.
    row = {
        "record_id": "change-abc",
        "title": "Explainable recall",
        "type": "change",
        "score": 12,
        "match": "keyword",
        "match_reason": "keyword",
        "matched_fields_detail": ["key_conclusion", "related_files"],
        "score_breakdown": {"key_conclusion": 4.0, "related_files": 2.0, "title": 4.0, "body": 2.0},
        "expanded_from": "requirement-001",
        "expansion_relation": "implements",
    }
    monkeypatch.setattr(context_module, "high_signal_recall_hints", lambda query, limit=3: ([row], ""))

    # When: JSON and Markdown recall surfaces render the same hit.
    json_exit = run_cli(["context", "recall", "--query", "auth", "--format", "json"], monkeypatch)
    json_payload = json.loads(capsys.readouterr().out)
    markdown_exit = run_cli(["context", "recall", "--query", "auth", "--format", "markdown"], monkeypatch)
    markdown = capsys.readouterr().out

    # Then: machine-readable JSON explains scoring, while prompt Markdown stays compact.
    assert json_exit == 0
    assert markdown_exit == 0
    assert json_payload["results"][0]["explanation"]["matched_fields"] == ["key_conclusion", "related_files"]
    assert json_payload["results"][0]["explanation"]["score_breakdown"]["key_conclusion"] == 4.0
    assert json_payload["results"][0]["expanded_from"] == "requirement-001"
    assert json_payload["results"][0]["expansion_relation"] == "implements"
    assert "key_conclusion" not in markdown
    assert "score_breakdown" not in markdown
    assert "expanded_from" not in markdown
    assert "expansion_relation" not in markdown
    assert "requirement-001" not in markdown
    assert "implements" not in markdown


def test_cli_context_recall_json_reports_abstention_when_gate_blocks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: high-signal recall returns no rows with an abstention reason
    monkeypatch.setattr(
        context_module,
        "high_signal_recall_hints",
        lambda query, limit=3: ([], "matched rows were keyword-only and below the high-signal floor"),
    )

    # When: recall context is requested as JSON
    exit_code = run_cli(["context", "recall", "--query", "weak", "--format", "json"], monkeypatch)

    # Then: the payload exposes the gate decision without pretending a hit occurred
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["kind"] == "recall"
    assert payload["results"] == []
    assert "below the high-signal floor" in payload["abstention"]


def test_cli_context_recall_propagates_project_root_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given: the recall command is invoked outside a SyberMem project
    monkeypatch.setattr(
        context_module,
        "high_signal_recall_hints",
        lambda query, limit=3: (_raise_project_root_error(), ""),
    )

    # When: recall context is requested
    exit_code = run_cli(["context", "recall", "--query", "auth"], monkeypatch)

    # Then: the CLI reports the standard root-not-found error without a traceback
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "No SyberMem project root found.\n"


def _raise_project_root_error() -> list:
    from sybermem_core.search import ProjectRootNotFoundError

    raise ProjectRootNotFoundError()
