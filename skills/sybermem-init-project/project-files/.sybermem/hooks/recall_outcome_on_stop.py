#!/usr/bin/env python3
"""Fail-open Claude Stop-hook recall outcome collector.

This intentionally mirrors the Codex SessionEnd collector: injected record ids
come from the per-turn memory journal, while edit evidence comes from git.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys

GIT_TIMEOUT_SECONDS = 2
CLI_TIMEOUT_SECONDS = 3
MAX_JOURNAL_LINES = 200


def _root() -> Path | None:
    current = Path.cwd().resolve()
    while True:
        if (current / ".sybermem").is_dir() and ((current / ".sybermem" / "project.yaml").is_file() or (current / ".claude" / "settings.json").is_file()):
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _payload(raw: str) -> str:
    try:
        data = json.loads(raw or "{}")
    except Exception:
        return ""
    if not isinstance(data, dict):
        return ""
    value = data.get("session_id") or data.get("sessionId") or ""
    return value if isinstance(value, str) else ""


def _injected_ids(root: Path, session_id: str) -> list[str]:
    path = root / ".sybermem" / ".memory-usage.jsonl"
    ids: list[str] = []
    if not path.is_file():
        return ids
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict) or row.get("host") != "claude" or row.get("event") == "session_outcome":
                continue
            if session_id and row.get("session_id") != session_id:
                continue
            for record_id in row.get("injected_ids", []) or []:
                if isinstance(record_id, str) and record_id and record_id not in ids:
                    ids.append(record_id)
    except Exception:
        return []
    return ids


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=GIT_TIMEOUT_SECONDS)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def _edited_files(root: Path) -> set[str]:
    files: set[str] = set()
    for output in (_git(root, "diff", "--name-only"), _git(root, "diff", "--cached", "--name-only"), _git(root, "ls-files", "--others", "--exclude-standard")):
        files.update(line.strip().replace("\\", "/") for line in output.splitlines() if line.strip())
    return files


def _related_files(ids: list[str]) -> dict[str, list[str]]:
    launcher = shutil.which("sybermem")
    fixed = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".claude" / "sybermem" / "cli" / ("sybermem.cmd" if os.name == "nt" else "sybermem")
    command = [str(fixed)] if fixed.is_file() else ([launcher] if launcher else None)
    if not command or not ids:
        return {}
    try:
        result = subprocess.run([*command, "project", "record-files", "--ids", ",".join(ids), "--format", "json"], text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=CLI_TIMEOUT_SECONDS)
        payload = json.loads(result.stdout) if result.returncode == 0 else {}
        records = payload.get("records", {}) if isinstance(payload, dict) else {}
        return {str(key).lower(): [item.replace("\\", "/") for item in value if isinstance(item, str)] for key, value in records.items() if isinstance(value, list)}
    except Exception:
        return {}


def _compute_outcome(injected: list[str], related: dict[str, list[str]], edited: set[str]) -> tuple[int, int, int]:
    measurable = unmeasurable = hit = 0
    for record_id in injected:
        files = related.get(record_id.lower(), [])
        if not files:
            unmeasurable += 1
        else:
            measurable += 1
            hit += int(any(path in edited for path in files))
    return measurable, unmeasurable, hit


def _append(root: Path, name: str, row: dict) -> None:
    try:
        path = root / ".sybermem" / name
        existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
        existing.append(json.dumps(row, ensure_ascii=False))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(existing[-MAX_JOURNAL_LINES:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def _write_outcome(root: Path, session_id: str, injected: list[str], edited: int, evidence: bool, measurable: int, unmeasurable: int, hit: int) -> None:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    precision = hit / measurable if measurable else None
    _append(root, ".memory-usage.jsonl", {"schema_version": 1, "host": "claude", "event": "session_outcome", "timestamp": timestamp, "session_id": session_id[:80], "edited_files": edited, "recall_evidence_available": evidence, "recall_measurable": measurable, "recall_unmeasurable": unmeasurable, "recall_hit": hit, "recall_precision": precision})
    if evidence and measurable + unmeasurable:
        _append(root, ".recall-outcomes.jsonl", {"timestamp": timestamp, "session": session_id[:80], "injected": measurable, "measurable": measurable, "unmeasurable": unmeasurable, "hit": hit, "precision": precision})


def main() -> int:
    try:
        session_id = _payload(sys.stdin.read())
        root = _root()
        if root is None:
            return 0
        injected = _injected_ids(root, session_id)
        if not injected:
            return 0
        edited = _edited_files(root)
        related = _related_files(injected)
        if not related:
            _write_outcome(root, session_id, injected, len(edited), False, 0, 0, 0)
        else:
            _write_outcome(root, session_id, injected, len(edited), True, *_compute_outcome(injected, related, edited))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
