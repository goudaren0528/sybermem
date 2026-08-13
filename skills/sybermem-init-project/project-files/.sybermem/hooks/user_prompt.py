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
    """Replicate task_recall behavior and return additionalContext on success.

    Routes through the SAME high-signal gate (E1) and inject/abstain logging (E6) as
    task_recall.main, so the merged production hook and the standalone hook behave
    identically. Uses task_recall's helpers as the single source of truth.
    """
    try:
        from sybermem_core.search import high_signal_recall_hints

        if recall_hook.should_skip(prompt):
            return
        rows, abstention_reason = high_signal_recall_hints(prompt, limit=3)
        if not rows:
            if abstention_reason:
                recall_hook.log_recall_event(root, "abstain", reason=recall_hook.safe_field(abstention_reason, 160))
            return ""
        injected = [
            {"record_id": recall_hook.safe_field(row.get("record_id", ""), 60), "match": recall_hook.safe_field(row.get("match", row.get("match_reason", "")), 24)}
            for row in rows[:3]
        ]
        recall_hook.log_recall_event(root, "inject", records=injected)
        return recall_hook.render_packet(prompt, rows)
    except Exception:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open.
        return ""


def _run_habit_reminder(prompt: str) -> str:
    """Return bounded User Habit Memory reminders; never persist raw prompt text."""
    try:
        from sybermem_core.user_habits import render_habit_reminder_markdown

        return render_habit_reminder_markdown(context=prompt)
    except Exception:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open.
        return ""


def _write_additional_context(parts: list[str]) -> None:
    packet = "\n\n".join(part.strip() for part in parts if part.strip())
    if not packet:
        return
    payload = json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": packet,
            }
        },
        ensure_ascii=False,
    )
    # Write UTF-8 to the byte buffer directly: the packet can carry non-ASCII (⭐ aha
    # markers, CJK titles), and a console locale like GBK would otherwise raise
    # UnicodeEncodeError and make this wired hook silently emit nothing.
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


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
        _write_additional_context([_run_recall(root, prompt), _run_habit_reminder(prompt)])
        return 0
    except Exception:  # noqa: BROAD_EXCEPT_OK - fail open, never block a prompt.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
