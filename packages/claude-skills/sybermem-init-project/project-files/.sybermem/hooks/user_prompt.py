#!/usr/bin/env python3
"""Merged UserPromptSubmit hook.

Combines record-intent capture and task recall into a single process so the
per-prompt cost is one Python startup + one root resolution + one core import
instead of two. Reuses the existing hook modules' pure helpers as the single
source of truth; only the orchestration lives here.

Contract:
- Reads stdin payload once.
- Resolves the project root once, imports core once.
- Intent capture runs first and only writes `.record-intent.json` (never stdout).
- Recall runs second and is the ONLY stdout writer (an `additionalContext` JSON).
- Fails open: any exception, bad input, or missing root returns 0 with no stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

import detect_record_intent as intent_hook  # noqa: E402
import task_recall as recall_hook  # noqa: E402


def _read_payload(raw: bytes) -> str:
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return ""
    if not isinstance(payload, dict):
        return ""
    return payload.get("prompt", "") or payload.get("userPrompt", "") or ""


def _run_intent_capture(root: Path, prompt: str) -> None:
    """Replicate detect_record_intent behavior; never writes stdout."""
    try:
        classifier = intent_hook.load_core_classifier()
        if classifier is None:
            return
        candidate = classifier(root, prompt)
        classification = candidate.get("classification", "")
        if not intent_hook.should_capture_classification(classification):
            return
        intent_path = root / ".sybermem" / ".record-intent.json"
        intent_path.write_text(
            json.dumps(
                {
                    "record_intent": True,
                    "source": "user-declared",
                    "created_at": intent_hook.now_iso(),
                    "classification": classification,
                    "action": candidate.get("action", "/sybermem-record"),
                    "reason": candidate.get("reason", ""),
                    "matched_pattern": "classifier",
                    "phrase": "",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open.
        return


def _run_recall(root: Path, prompt: str) -> None:
    """Replicate task_recall behavior; the only stdout writer on success."""
    try:
        from sybermem_core.search import compact_project_search

        if recall_hook.should_skip(prompt):
            return
        rows = compact_project_search(prompt, limit=3)
        if not rows:
            return
        packet = recall_hook.render_packet(prompt, rows)
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": packet,
                    }
                },
                ensure_ascii=False,
            )
        )
    except Exception:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open.
        return


def main() -> int:
    try:  # noqa: BROAD_EXCEPT_OK - top-level hook boundary must fail open.
        recall_hook.configure_import_path()
        from sybermem_core.project import resolve_project_root

        raw = sys.stdin.buffer.read()
        prompt = _read_payload(raw)

        root = resolve_project_root()
        if root is None:
            return 0

        _run_intent_capture(root, prompt)
        _run_recall(root, prompt)
        return 0
    except Exception:  # noqa: BROAD_EXCEPT_OK - fail open, never block a prompt.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
