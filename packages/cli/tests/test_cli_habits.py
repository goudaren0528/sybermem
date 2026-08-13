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
