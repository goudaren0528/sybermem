#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from importlib import import_module
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import sys


DIAGNOSTIC_ARG = "--diagnose"
CORE_UNAVAILABLE_DIAGNOSTIC = (
    "SyberMem record-intent capture is unavailable because the Core classifier could not be loaded. "
    "No prompt content was stored. Retry after /sybermem-update or reinstalling the managed UserPromptSubmit hook.\n"
)


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
    re.compile(r"remind me to .*\bsybermem-record\b", re.IGNORECASE),
    re.compile(r"remind me to record (this|the) (round|session|work)", re.IGNORECASE),
    re.compile(r"after (this|the) .*(round|session).* remind me to record", re.IGNORECASE),
    re.compile(r"let'?s record (this|the) (round|work) (to|in) sybermem", re.IGNORECASE),
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
    # English fallback
    if "remind me" in text.lower() and "record" in text.lower():
        return True, "fallback:remind+record"
    return False, ""


def load_core_classifier():
    core_path = Path(__file__).resolve().parents[2] / "packages" / "core"
    candidate_paths = [
        core_path,
        Path.home() / '.claude' / 'sybermem' / 'cli' / 'venv' / 'Lib' / 'site-packages',
        Path.home() / '.claude' / 'sybermem' / 'cli' / 'venv' / 'lib' / 'python3.10' / 'site-packages',
    ]
    for path in candidate_paths:
        if not path.is_dir():
            continue
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
        try:
            return getattr(import_module("sybermem_core.next_step_router"), "classify_record_intent")
        except (AttributeError, ImportError):
            sys.modules.pop("sybermem_core.next_step_router", None)
            sys.modules.pop("sybermem_core", None)
            continue
    return None


def should_capture_classification(classification: str) -> bool:
    return classification in {"change", "decision", "requirement", "bug", "digest"}


def diagnostics_requested(argv: list[str]) -> bool:
    return DIAGNOSTIC_ARG in argv[1:]


def emit_core_unavailable_diagnostic() -> None:
    sys.stderr.write(CORE_UNAVAILABLE_DIAGNOSTIC)


def main() -> int:
    root = resolve_sybermem_root()
    intent_path = root / ".sybermem" / ".record-intent.json"

    raw = sys.stdin.buffer.read()
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    user_text = payload.get("prompt", "") or payload.get("userPrompt", "") or ""

    classifier = load_core_classifier()
    if classifier is not None:
        try:
            candidate = classifier(root, user_text)
        except Exception:  # noqa: BROAD_EXCEPT_OK - top-level hook boundary must fail open.
            return 0
        classification = candidate.get("classification", "")
        if not should_capture_classification(classification):
            return 0
        intent_path.write_text(json.dumps({
            "record_intent": True,
            "source": "user-declared",
            "created_at": now_iso(),
            "classification": classification,
            "action": candidate.get("action", "/sybermem-record"),
            "reason": candidate.get("reason", ""),
            "matched_pattern": "classifier",
            "phrase": "",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return 0
    if diagnostics_requested(sys.argv):
        emit_core_unavailable_diagnostic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
