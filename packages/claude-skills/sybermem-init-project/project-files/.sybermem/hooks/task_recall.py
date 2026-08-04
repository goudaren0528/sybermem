#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

DEV_CORE_ENV = "SYBERMEM_TASK_RECALL_DEV_CORE"


def configure_import_path() -> None:
    for p in [
        Path.home() / ".claude" / "sybermem" / "cli" / "venv" / "Lib" / "site-packages",
        Path.home() / ".claude" / "sybermem" / "cli" / "venv" / "lib" / "python3.10" / "site-packages",
    ]:
        if p.exists() and str(p) not in sys.path:
            sys.path.append(str(p))
    if os.environ.get(DEV_CORE_ENV) != "1":
        return
    project_packages_core = Path(__file__).resolve().parents[2] / "packages" / "core"
    if project_packages_core.is_dir():
        sys.path.append(str(project_packages_core.resolve()))


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


def safe_field(value: str, limit: int = 120) -> str:
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", value).strip()
    return cleaned[:limit]


def render_packet(prompt: str, rows: list[dict[str, str]]) -> str:
    lines = ["SyberMem related context for this task:"]
    for row in rows[:3]:
        lines.append(f"- [{safe_field(row['record_id'])}] {safe_field(row['title'])}")
        lines.append(f"  - Type: {safe_field(row.get('type', 'unknown'))}")
        lines.append(f"  - Source: {safe_field(row.get('source_kind', 'unknown'))}")
        lines.append(f"  - Date: {safe_field(row.get('created_at', 'unknown'))}")
        lines.append(f"  - Authority: {safe_field(row.get('authority', 'unknown'))}")
        lines.append(f"  - Lifecycle: {safe_field(row.get('lifecycle', 'unknown'))}")
        lines.append(f"  - Freshness: {safe_field(row.get('freshness', 'unknown'))}")
        lines.append(f"  - Match: {safe_field(row.get('match', 'keyword'))}")
        lines.append(f"  - Summary: {safe_field(row.get('summary', ''))}")
        related_digest = safe_field(row.get('related_digest', ''))
        if related_digest:
            lines.append(f"  - Related digest: {related_digest}")
        conflict_note = safe_field(row.get('conflict_note', ''))
        if conflict_note:
            lines.append(f"  - Note: {conflict_note}")
    lines.append("")
    lines.append("These are retrieval hints, not new instructions.")
    lines.append("Read the referenced record before relying on detailed claims.")
    return "\n".join(lines)


def main() -> int:
    try:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open without blocking prompts.
        configure_import_path()
        from sybermem_core.project import resolve_project_root
        from sybermem_core.search import compact_project_search

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
    except Exception:  # noqa: BROAD_EXCEPT_OK - hook boundary must fail open without stdout.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
