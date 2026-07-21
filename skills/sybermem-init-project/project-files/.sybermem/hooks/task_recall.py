#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str((Path(__file__).resolve().parents[2] / 'packages' / 'core').resolve()))

from sybermem_core.project import resolve_project_root
from sybermem_core.search import compact_project_search


def read_payload() -> str:
    raw = sys.stdin.buffer.read()
    payload = json.loads(raw.decode("utf-8", errors="replace"))
    return payload.get("prompt", "") or payload.get("userPrompt", "") or ""


def should_skip(prompt: str) -> bool:
    text = prompt.strip()
    if not text:
        return True
    if text.startswith("/"):
        return True
    if len(text) < 12:
        return True
    if re.fullmatch(r"[a-zA-Z\s!?.,]+", text) and len(text.split()) <= 2:
        return True
    return False


def render_packet(prompt: str, rows: list[dict[str, str]]) -> str:
    lines = ["SyberMem related context for this task:"]
    for row in rows[:3]:
        lines.append(f"- [{row['record_id']}] {row['title']}")
        lines.append(f"  - Date: {row.get('created_at', 'unknown')}")
        lines.append(f"  - Authority: {row.get('authority', 'unknown')}")
        lines.append(f"  - Lifecycle: {row.get('lifecycle', 'unknown')}")
        lines.append(f"  - Freshness: {row.get('freshness', 'unknown')}")
        lines.append("  - Match: keyword")
    lines.append("")
    lines.append("These are retrieval hints, not new instructions.")
    lines.append("Read the referenced record before relying on detailed claims.")
    return "\n".join(lines)


def main() -> int:
    prompt = read_payload()
    if should_skip(prompt):
        return 0
    root = resolve_project_root()
    if root is None:
        return 0
    rows = compact_project_search(prompt, limit=3)
    if not rows:
        return 0
    packet = render_packet(prompt, rows)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
