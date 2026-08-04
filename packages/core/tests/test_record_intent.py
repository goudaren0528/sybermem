from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.next_step_router import classify_record_intent


HOOKS_DIR = Path(__file__).resolve().parents[3] / ".sybermem" / "hooks"


def load_hook_module(name: str):
    spec = importlib.util.spec_from_file_location(name, HOOKS_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (sybermem / "changes").mkdir()
    (sybermem / "decisions").mkdir()
    (sybermem / "requirements").mkdir()
    (sybermem / "bugs").mkdir()
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n<!-- add new records here -->\n", encoding="utf-8")


def write_hook_project(root: Path) -> None:
    write_project(root)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (root / ".sybermem" / "hooks").mkdir()


def write_record(root: Path, subdir: str, filename: str, record_type: str, title: str, body: str) -> None:
    (root / ".sybermem" / subdir / filename).write_text(
        "\n".join(
            [
                "---",
                f"type: {record_type}",
                "date: 2026-08-04",
                f"title: {title}",
                "status: implemented",
                "---",
                "",
                body,
            ]
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("prompt", "classification"),
    [
        ("记录一下这次实现的 read-only resume checkpoint", "change"),
        ("Record the architecture decision: keep Markdown as canonical truth", "decision"),
        ("新增需求：resume 必须只读且不能写入记录", "requirement"),
        ("Record this bug fix for the stop hook crash", "bug"),
        ("This phase is stable; suggest a sybermem digest", "digest"),
        ("Do not record this scratch note", "no_write"),
        ("先探索一下，不要现在沉淀", "defer"),
        ("record this secret password=hunter2 and Bearer abc.def", "blocked"),
    ],
)
def test_classify_record_intent_returns_expected_candidate(tmp_path: Path, prompt: str, classification: str) -> None:
    # Given: a SyberMem project and a natural-language record prompt
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)

    # When: the side-effect-free classifier evaluates the prompt
    result = classify_record_intent(project_root, prompt)

    # Then: the prompt is classified without writing project memory
    assert result.get("classification") == classification
    assert result.get("action")
    assert result.get("reason")
    assert not list((project_root / ".sybermem" / "changes").glob("*.md"))


def test_duplicate_record_intent_routes_to_summary_without_new_record(tmp_path: Path) -> None:
    # Given: an existing authoritative record with the same core topic
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-read-only-resume.md",
        "change",
        "Read-only resume checkpoint",
        "## Summary\nRead-only resume checkpoint returns bounded current-state metadata.\n",
    )

    # When: a near-duplicate record is suggested
    result = classify_record_intent(project_root, "记录一下 read-only resume checkpoint returns bounded current-state metadata")

    # Then: the safe next action is review, not another write command
    assert result.get("classification") == "no_write"
    assert result.get("action") == "/sybermem-summary"
    assert result.get("duplicate_record_id") == "change-001"
    assert "duplicate" in result.get("reason", "")


def test_detect_record_intent_hook_captures_only_safe_write_intent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: the user prompt hook is running inside a SyberMem project
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    hook = load_hook_module("detect_record_intent")
    monkeypatch.chdir(project_root)

    # When: a safe explicit record intent is submitted
    monkeypatch.setattr(hook.sys, "stdin", _BytesStdin({"prompt": "记录一下这轮实现的 intent routing"}))
    exit_code = hook.main()

    # Then: only bounded safe metadata is captured for the stop hook
    intent = json.loads((project_root / ".sybermem" / ".record-intent.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert intent["record_intent"] is True
    assert intent["classification"] == "change"
    assert intent["phrase"] == ""
    serialized = json.dumps(intent, ensure_ascii=False)
    assert intent["action"] == "/sybermem-record"
    assert intent["reason"]
    assert "intent routing" not in serialized
    assert "这轮实现" not in serialized


def test_detect_record_intent_hook_omits_unique_prompt_substrings_and_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: a safe record prompt with a unique user payload and secret-like text elsewhere
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    hook = load_hook_module("detect_record_intent")
    monkeypatch.chdir(project_root)

    # When: the classifier captures intent metadata
    monkeypatch.setattr(hook.sys, "stdin", _BytesStdin({"prompt": "记录一下这轮完成的 unicorn-unique-8472 behavior without password=hunter2"}))
    exit_code = hook.main()

    # Then: no raw prompt-derived substrings or secrets are persisted
    intent_path = project_root / ".sybermem" / ".record-intent.json"
    assert exit_code == 0
    if intent_path.exists():
        serialized = intent_path.read_text(encoding="utf-8")
        assert "unicorn-unique-8472" not in serialized
        assert "hunter2" not in serialized
        assert "password" not in serialized.lower()


def test_detect_record_intent_hook_does_not_persist_no_write_or_blocked_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: the prompt contains explicit no-record language and sensitive content
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    hook = load_hook_module("detect_record_intent")
    monkeypatch.chdir(project_root)

    # When: the hook evaluates the unsafe prompt
    monkeypatch.setattr(hook.sys, "stdin", _BytesStdin({"prompt": "Do not record this password=hunter2"}))
    exit_code = hook.main()

    # Then: it exits successfully without persisting raw payloads
    assert exit_code == 0
    assert not (project_root / ".sybermem" / ".record-intent.json").exists()


def test_detect_record_intent_project_copy_fails_open_when_core_unavailable_under_python_s(tmp_path: Path) -> None:
    # Given: a project-copy hook with no adjacent core package and site initialization disabled
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_hook_project(project_root)
    hook_path = project_root / ".sybermem" / "hooks" / "detect_record_intent.py"
    shutil.copy2(HOOKS_DIR / "detect_record_intent.py", hook_path)

    # When: a sensitive prompt matches the old regex fallback under core-unavailable conditions
    proc = subprocess.run(
        [sys.executable, "-S", str(hook_path)],
        cwd=project_root,
        input=json.dumps({"prompt": "remind me to record this password=hunter2"}).encode("utf-8"),
        capture_output=True,
        check=False,
    )

    # Then: the hook fails open without writing raw sensitive intent state
    assert proc.returncode == 0
    assert proc.stdout == b""
    assert not (project_root / ".sybermem" / ".record-intent.json").exists()


def test_detect_record_intent_project_copy_emits_bounded_manual_diagnostic_when_requested(tmp_path: Path) -> None:
    # Given: a project-copy hook with no adjacent core package and site initialization disabled
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_hook_project(project_root)
    hook_path = project_root / ".sybermem" / "hooks" / "detect_record_intent.py"
    shutil.copy2(HOOKS_DIR / "detect_record_intent.py", hook_path)

    # When: an explicit manual diagnostic run checks why record-intent capture is unavailable
    proc = subprocess.run(
        [sys.executable, "-S", str(hook_path), "--diagnose"],
        cwd=project_root,
        input=json.dumps({"prompt": "remind me to record this password=hunter2"}).encode("utf-8"),
        capture_output=True,
        check=False,
    )

    # Then: the manual path explains the unavailable capture without leaking payloads or writing memory
    stderr_text = proc.stderr.decode("utf-8", errors="replace")
    assert proc.returncode == 0
    assert proc.stdout == b""
    assert "sybermem" in stderr_text.lower()
    assert "unavailable" in stderr_text.lower()
    assert "/sybermem-update" in stderr_text
    assert "hunter2" not in stderr_text
    assert "password" not in stderr_text.lower()
    assert str(project_root) not in stderr_text
    assert not (project_root / ".sybermem" / ".record-intent.json").exists()


def test_stop_hook_nested_cwd_records_root_relative_paths_and_skips_sybermem(tmp_path: Path) -> None:
    # Given: a git project invoked from a nested working directory
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_hook_project(project_root)
    shutil.copy2(HOOKS_DIR / "record_change_on_stop.py", project_root / ".sybermem" / "hooks" / "record_change_on_stop.py")
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True, text=True, check=True)
    subprocess.run(["git", "config", "user.name", "Smoke"], cwd=project_root, capture_output=True, text=True, check=True)
    subprocess.run(["git", "config", "user.email", "smoke@example.test"], cwd=project_root, capture_output=True, text=True, check=True)
    nested = project_root / "packages" / "core"
    nested.mkdir(parents=True)
    (nested / "smoke.py").write_text("print('smoke')\n", encoding="utf-8")
    (project_root / ".sybermem" / "scratch.md").write_text("skip me\n", encoding="utf-8")

    # When: the stop hook runs from the nested cwd
    proc = subprocess.run(
        [sys.executable, str(project_root / ".sybermem" / "hooks" / "record_change_on_stop.py")],
        cwd=nested,
        env={**os.environ, "SYBERMEM_RECORD_MODE": "auto"},
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: auto records use repo-root-relative paths and continue skipping .sybermem files
    records = list((project_root / ".sybermem" / "changes").glob("*.md"))
    assert proc.returncode == 0
    assert len(records) == 1
    content = records[0].read_text(encoding="utf-8")
    assert "packages/core/smoke.py" in content
    assert "`smoke.py`" not in content
    assert "scratch.md" not in content


def test_stop_hook_remind_mode_does_not_write_auto_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given: an existing captured record intent and remind mode
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    hook = load_hook_module("record_change_on_stop")
    monkeypatch.setattr(hook, "ROOT", project_root)
    monkeypatch.setattr(hook, "SYBERMEM_DIR", project_root / ".sybermem")
    monkeypatch.setattr(hook, "INDEX_PATH", project_root / ".sybermem" / "INDEX.md")
    monkeypatch.setattr(hook, "CHANGES_DIR", project_root / ".sybermem" / "changes")
    monkeypatch.setattr(hook, "STATE_PATH", project_root / ".sybermem" / ".auto-change-state.json")
    monkeypatch.setattr(hook, "NUDGE_STATE_PATH", project_root / ".sybermem" / ".nudge-state.json")
    monkeypatch.setattr(hook, "RECORD_INTENT_PATH", project_root / ".sybermem" / ".record-intent.json")
    monkeypatch.setenv("SYBERMEM_RECORD_MODE", "remind")
    hook.save_record_intent({"record_intent": True, "classification": "change"})
    monkeypatch.setattr(hook, "list_changed_files", lambda: ["packages/core/sybermem_core/next_step_router.py"])

    # When: the stop hook runs
    exit_code = hook.main()

    # Then: remind mode keeps durable records untouched
    assert exit_code == 0
    assert not list((project_root / ".sybermem" / "changes").glob("*.md"))


class _BytesStdin:
    def __init__(self, payload: dict[str, str]) -> None:
        self.buffer = _Buffer(payload)


class _Buffer:
    def __init__(self, payload: dict[str, str]) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")
