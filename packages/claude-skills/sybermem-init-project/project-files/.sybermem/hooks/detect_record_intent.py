#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import sys


def resolve_sybermem_root() -> Path:
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            git_root = Path(result.stdout.strip()).resolve()
    except Exception:
        pass

    while True:
        has_sybermem = (current / ".sybermem").is_dir()
        has_settings = (current / ".claude" / "settings.json").is_file()
        has_index = (current / ".sybermem" / "INDEX.md").is_file()
        if has_sybermem and (has_settings or has_index):
            return current
        if git_root and current == git_root:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.cwd()


INTENT_PATTERNS = [
    re.compile(r"这轮.*提醒我.*记录"),
    re.compile(r"这轮.*提醒我"),
    re.compile(r"这次.*要记.*record", re.IGNORECASE),
    re.compile(r"做完.*提醒我.*/sybermem-record"),
    re.compile(r"做完.*提醒我"),
    re.compile(r"这轮工作.*记录到.*sybermem", re.IGNORECASE),
]


def now_iso() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).isoformat(timespec="seconds")


def detect_record_intent(text: str) -> tuple[bool, str]:
    for pattern in INTENT_PATTERNS:
        if pattern.search(text):
            return True, pattern.pattern
    # Extra defensive fallback for terminals that garble some CJK bytes:
    if "这轮" in text and "提醒我" in text:
        return True, "fallback:这轮+提醒我"
    if "做完" in text and "提醒我" in text:
        return True, "fallback:做完+提醒我"
    return False, ""


def main() -> int:
    root = resolve_sybermem_root()
    intent_path = root / ".sybermem" / ".record-intent.json"

    payload = json.load(sys.stdin)
    user_text = payload.get("prompt", "") or payload.get("userPrompt", "") or ""

    matched_ok, matched = detect_record_intent(user_text)
    if not matched_ok:
        return 0

    intent_path.write_text(json.dumps({
        "record_intent": True,
        "source": "user-declared",
        "created_at": now_iso(),
        "phrase": user_text,
        "matched_pattern": matched,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
