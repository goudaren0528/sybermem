#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys


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


def main() -> int:
    prompt = read_payload()
    if should_skip(prompt):
        return 0
    # Task 3 only scaffolds the hook plumbing and safe skip behavior.
    # Read-only retrieval logic is implemented in Task 4.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
