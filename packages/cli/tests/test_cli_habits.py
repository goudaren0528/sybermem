from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import main


def run_cli(argv: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(sys, "argv", ["sybermem", *argv])
    return main()


def test_cli_habit_add_and_list_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: a clean user habit home
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))

    # When: a habit is added and listed through the real CLI parser
    add_code = run_cli(
        ["habit", "add", "--type", "workflow", "--applies-to", "planning", "--format", "json", "Prefer plans before implementation"],
        monkeypatch,
    )
    added = json.loads(capsys.readouterr().out)
    list_code = run_cli(["habit", "list", "--format", "json"], monkeypatch)
    listed = json.loads(capsys.readouterr().out)

    # Then: JSON output is machine-readable and stable
    assert add_code == 0
    assert list_code == 0
    assert added["habit"]["habit_id"].startswith("habit-")
    assert listed["habits"][0]["statement"] == "Prefer plans before implementation"
    assert listed["habits"][0]["scope"] == "user"


def test_cli_habit_search_pause_and_delete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: one recorded habit
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "add", "--type", "review", "--applies-to", "review", "--format", "json", "Prefer review before handoff"], monkeypatch) == 0
    habit_id = json.loads(capsys.readouterr().out)["habit"]["habit_id"]

    # When: the habit is searched, paused, and deleted through CLI commands
    assert run_cli(["habit", "search", "review", "--format", "json"], monkeypatch) == 0
    search_before = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "pause", habit_id, "--format", "json"], monkeypatch) == 0
    paused = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "delete", habit_id, "--format", "json"], monkeypatch) == 0
    deleted = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "list", "--format", "json"], monkeypatch) == 0
    listed_after_delete = json.loads(capsys.readouterr().out)

    # Then: state-changing commands are structured and default list excludes deleted habits
    assert search_before["results"][0]["habit"]["habit_id"] == habit_id
    assert paused == {"status": "paused", "habit_id": habit_id}
    assert deleted == {"status": "deleted", "habit_id": habit_id}
    assert listed_after_delete["habits"] == []


def test_cli_habit_inject_markdown_and_json_abstention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: an eligible habit for planning context
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "add", "--type", "workflow", "--applies-to", "planning", "Prefer plans before implementation"], monkeypatch) == 0
    capsys.readouterr()

    # When: manual injection is requested in markdown and JSON modes
    assert run_cli(["habit", "inject", "--context", "planning", "--format", "markdown"], monkeypatch) == 0
    markdown = capsys.readouterr().out
    assert run_cli(["habit", "inject", "--context", "frontend", "--format", "json"], monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)

    # Then: markdown contains transparent habit metadata and JSON abstention is explicit
    assert markdown.startswith("## User Habit Memory")
    assert "Source: explicit_user" in markdown
    assert payload == {"injected": [], "markdown": ""}


def test_cli_habit_remind_markdown_and_json_abstention(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: a prompt-approved habit for planning context
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(
        [
            "habit",
            "add",
            "--type",
            "workflow",
            "--applies-to",
            "planning",
            "--injection-policy",
            "prompt_ok_when_supported",
            "Prefer plans before implementation",
        ],
        monkeypatch,
    ) == 0
    capsys.readouterr()

    # When: visible reminders are requested in markdown and JSON modes
    assert run_cli(["habit", "remind", "--context", "planning", "--format", "markdown"], monkeypatch) == 0
    markdown = capsys.readouterr().out
    assert run_cli(["habit", "remind", "--context", "frontend", "--format", "json"], monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)

    # Then: markdown is user-facing and JSON abstention is explicit
    assert markdown.startswith("## User Habit Reminder")
    assert "This user habit may apply" in markdown
    assert payload == {"reminded": [], "markdown": ""}


def test_cli_habit_remind_suggests_visible_skill_without_creating_habit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: an empty user habit store
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))

    # When: the prompt looks like a reusable preference
    assert run_cli(["habit", "remind", "--context", "remember that I prefer plans", "--format", "json"], monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "list", "--all", "--format", "json"], monkeypatch) == 0
    listed = json.loads(capsys.readouterr().out)

    # Then: the CLI suggests the skill but does not create a habit
    assert payload["reminded"] == []
    assert "/sybermem-habit" in payload["markdown"]
    assert listed["habits"] == []


def test_cli_habit_intent_captures_candidate_and_status_and_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: a clean user habit home
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))

    # When: a preference-shaped prompt is passed to habit intent
    assert run_cli(["habit", "intent", "--prompt", "以后都用中文回复我", "--format", "json"], monkeypatch) == 0
    captured = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "intent-status", "--format", "json"], monkeypatch) == 0
    status = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "list", "--all", "--format", "json"], monkeypatch) == 0
    listed = json.loads(capsys.readouterr().out)

    # Then: a candidate is captured and visible, but NO habit is created
    assert captured["captured"] is True
    assert captured["candidate"]["candidate_only"] is True
    assert status["pending"] is True
    assert listed["habits"] == []

    # When: the candidate is cleared
    assert run_cli(["habit", "intent-clear", "--format", "json"], monkeypatch) == 0
    cleared = json.loads(capsys.readouterr().out)
    assert run_cli(["habit", "intent-status", "--format", "json"], monkeypatch) == 0
    status_after = json.loads(capsys.readouterr().out)

    # Then: the pending candidate is gone
    assert cleared["cleared"] is True
    assert status_after["pending"] is False


def test_cli_habit_intent_status_lists_multiple_candidates_with_ids_and_summaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    run_cli(["habit", "intent", "--prompt", "以后偏好甲保持这个做法", "--format", "json"], monkeypatch)
    capsys.readouterr()
    run_cli(["habit", "intent", "--prompt", "以后偏好乙保持这个做法", "--format", "json"], monkeypatch)
    capsys.readouterr()

    assert run_cli(["habit", "intent-status", "--format", "json"], monkeypatch) == 0
    status = json.loads(capsys.readouterr().out)

    assert status["pending"] is True
    assert status["count"] == 2
    assert len(status["candidates"]) == 2
    # Newest first, each with an id and a bounded summary.
    assert status["candidates"][0]["summary"] == "以后偏好乙保持这个做法"
    assert all(c["candidate_id"].startswith("cand-") for c in status["candidates"])
    # Legacy single `candidate` field still points at the newest for back-compat.
    assert status["candidate"]["summary"] == "以后偏好乙保持这个做法"


def test_cli_habit_intent_discard_removes_one_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    run_cli(["habit", "intent", "--prompt", "以后偏好甲保持这个做法", "--format", "json"], monkeypatch)
    capsys.readouterr()
    run_cli(["habit", "intent", "--prompt", "以后偏好乙保持这个做法", "--format", "json"], monkeypatch)
    capsys.readouterr()
    run_cli(["habit", "intent-status", "--format", "json"], monkeypatch)
    status = json.loads(capsys.readouterr().out)
    target = status["candidates"][0]["candidate_id"]

    # When: discarding that specific candidate
    assert run_cli(["habit", "intent-discard", target, "--format", "json"], monkeypatch) == 0
    discarded = json.loads(capsys.readouterr().out)
    assert discarded["discarded"] is True

    # Then: only the other candidate remains
    run_cli(["habit", "intent-status", "--format", "json"], monkeypatch)
    after = json.loads(capsys.readouterr().out)
    assert after["count"] == 1
    assert after["candidates"][0]["candidate_id"] != target

    # And: discarding an unknown id is a non-zero no-op
    assert run_cli(["habit", "intent-discard", "cand-nope", "--format", "json"], monkeypatch) == 1


def test_cli_habit_intent_ignores_non_preference_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "intent", "--prompt", "fix the crash", "--format", "json"], monkeypatch) == 0
    captured = json.loads(capsys.readouterr().out)
    assert captured == {"captured": False, "candidate": None}


def test_cli_habit_awareness_reports_counts_and_pending(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: one active habit and one pending candidate
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    run_cli(["habit", "add", "--type", "communication", "--format", "json", "Reply in Chinese"], monkeypatch)
    capsys.readouterr()
    run_cli(["habit", "intent", "--prompt", "always prefer plans", "--format", "json"], monkeypatch)
    capsys.readouterr()

    # When: awareness is requested
    assert run_cli(["habit", "awareness", "--format", "json"], monkeypatch) == 0
    summary = json.loads(capsys.readouterr().out)

    # Then: counts, type distribution, and the pending flag are surfaced
    assert summary["active"] == 1
    assert summary["by_type"] == {"communication": 1}
    assert summary["pending_intent"] is True


def test_cli_habit_test_json_explains_prompt_time_selection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: one prompt-time eligible habit
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "add", "--type", "workflow", "--applies-to", "planning", "--format", "json", "Prefer plans before implementation"], monkeypatch) == 0
    habit_id = json.loads(capsys.readouterr().out)["habit"]["habit_id"]

    # When: dry-run habit recall is tested through the real CLI parser
    assert run_cli(["habit", "test", "--context", "planning next steps", "--format", "json"], monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)

    # Then: the output is machine-readable and explains the selected habit
    assert payload["delivery"] == "prompt-time"
    assert payload["active_habits"] == 1
    assert payload["selected"] == 1
    assert payload["habits"][0]["habit_id"] == habit_id
    assert payload["habits"][0]["decision"] == "selected"
    assert "score_met_floor" in payload["habits"][0]["reasons"]


def test_cli_habit_test_markdown_reports_pending_without_selecting_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: only a pending habit candidate exists
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "intent", "--prompt", "always prefer plans before implementation", "--format", "json"], monkeypatch) == 0
    capsys.readouterr()

    # When: the dry-run diagnostic is rendered as Markdown by default
    assert run_cli(["habit", "test", "--context", "planning"], monkeypatch) == 0
    output = capsys.readouterr().out

    # Then: pending candidates are counted but never treated as active selected habits
    assert output.startswith("## User Habit Recall Test")
    assert "0 active, 0 evaluated, 0 selected, 1 pending candidate" in output
    assert "Pending candidates are not active habits" in output


def test_cli_habit_explain_json_returns_single_habit_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: two habits with different relevance
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "add", "--type", "workflow", "--applies-to", "planning", "--format", "json", "Prefer plans before implementation"], monkeypatch) == 0
    target_id = json.loads(capsys.readouterr().out)["habit"]["habit_id"]
    assert run_cli(["habit", "add", "--type", "review", "--applies-to", "review", "--format", "json", "Prefer review before handoff"], monkeypatch) == 0
    capsys.readouterr()

    # When: a single habit is explained
    assert run_cli(["habit", "explain", "--id", target_id, "--context", "planning", "--format", "json"], monkeypatch) == 0
    payload = json.loads(capsys.readouterr().out)

    # Then: only that habit diagnostic is returned
    assert payload["status"] == "ok"
    assert len(payload["habits"]) == 1
    assert payload["habits"][0]["habit_id"] == target_id
    assert payload["habits"][0]["decision"] == "selected"


def test_cli_habit_explain_unknown_id_is_concise_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: an empty habit store
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))

    # When: explaining an unknown habit as JSON and Markdown
    json_exit = run_cli(["habit", "explain", "--id", "habit-missing", "--context", "planning", "--format", "json"], monkeypatch)
    payload = json.loads(capsys.readouterr().out)
    markdown_exit = run_cli(["habit", "explain", "--id", "habit-missing", "--context", "planning"], monkeypatch)
    captured = capsys.readouterr()

    # Then: both surfaces fail without a traceback
    assert json_exit == 1
    assert payload == {"status": "unknown_habit", "habit_id": "habit-missing"}
    assert markdown_exit == 1
    assert "unknown habit id: habit-missing" in captured.err
    assert "Traceback" not in captured.err


def test_cli_habit_diagnostics_are_read_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: one habit and one pending candidate
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))
    assert run_cli(["habit", "add", "--type", "workflow", "--applies-to", "planning", "--format", "json", "Prefer plans before implementation"], monkeypatch) == 0
    habit_id = json.loads(capsys.readouterr().out)["habit"]["habit_id"]
    assert run_cli(["habit", "intent", "--prompt", "always prefer tests before commits", "--format", "json"], monkeypatch) == 0
    capsys.readouterr()
    habits_path = tmp_path / "user-habits" / "habits.jsonl"
    intent_path = tmp_path / ".habit-intent.json"
    before_habits = habits_path.read_text(encoding="utf-8")
    before_intent = intent_path.read_text(encoding="utf-8")

    # When: test and explain diagnostics run
    assert run_cli(["habit", "test", "--context", "planning", "--format", "json"], monkeypatch) == 0
    capsys.readouterr()
    assert run_cli(["habit", "explain", "--id", habit_id, "--context", "planning", "--format", "json"], monkeypatch) == 0
    capsys.readouterr()

    # Then: diagnostics do not mutate habits, candidates, or injection logs
    assert habits_path.read_text(encoding="utf-8") == before_habits
    assert intent_path.read_text(encoding="utf-8") == before_intent
    assert not (tmp_path / "user-habits" / "injection-log.jsonl").exists()


def test_cli_habit_pause_unknown_id_returns_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    # Given: an empty habit store
    monkeypatch.setenv("SYBERMEM_HOME", str(tmp_path))

    # When: an unknown habit id is paused
    exit_code = run_cli(["habit", "pause", "habit-missing"], monkeypatch)

    # Then: the CLI reports a concise non-traceback failure
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "unknown habit id" in captured.err
    assert "Traceback" not in captured.err
