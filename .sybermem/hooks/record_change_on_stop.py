#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path.cwd()
SYBERMEM_DIR = ROOT / ".sybermem"
INDEX_PATH = SYBERMEM_DIR / "INDEX.md"
CHANGES_DIR = SYBERMEM_DIR / "changes"
STATE_PATH = SYBERMEM_DIR / ".auto-change-state.json"
MAX_FILES_IN_TITLE = 3
SKIP_PREFIXES = (
    ".git/",
    ".sybermem/",
    "ADR/",
    ".claude/",
    "node_modules/",
)
# Hard-skip: never included in changed-file lists or trail records.
SKIP_FILES: set[str] = set()
# Soft-skip: included for high-signal detection, but excluded from the
# auto-record trail when they are the *only* files changed (to avoid
# self-referential noise from lone meta-file edits).
SOFT_SKIP_FILES = {
    "CLAUDE.md",
    "AGENTS.md",
}

NUDGE_STATE_PATH = SYBERMEM_DIR / ".auto-nudge-state.json"
RECORD_FILE_THRESHOLD = 5
RECORD_COOLDOWN_KEYS = {"record", "digest"}
HIGH_SIGNAL_PATTERNS = (
    re.compile(r"^README(?:\..+)?$", re.IGNORECASE),
    re.compile(r"^INSTALL(?:\..+)?$", re.IGNORECASE),
    re.compile(r"^CLAUDE\.md$", re.IGNORECASE),
    re.compile(r"^AGENTS\.md$", re.IGNORECASE),
    re.compile(r"^packages/claude-skills/.+/SKILL\.md$", re.IGNORECASE),
    re.compile(r"^\.sybermem/hooks/", re.IGNORECASE),
    re.compile(r"^scripts/install", re.IGNORECASE),
    re.compile(r"^scripts/update", re.IGNORECASE),
    re.compile(r"^docs/superpowers/specs/", re.IGNORECASE),
)
HIGH_LEVEL_AREAS = (
    ("skills", re.compile(r"^packages/claude-skills/", re.IGNORECASE)),
    ("scripts", re.compile(r"^scripts/", re.IGNORECASE)),
    ("docs", re.compile(r"^(docs/|README|INSTALL)", re.IGNORECASE)),
    ("instructions", re.compile(r"^(CLAUDE\.md|AGENTS\.md)$", re.IGNORECASE)),
    ("sybermem", re.compile(r"^\.sybermem/", re.IGNORECASE)),
)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def should_auto_record() -> bool:
    return os.environ.get("SYBERMEM_RECORD_MODE", "auto") == "auto"


def list_changed_files() -> list[str]:
    """Return all changed files for signal detection (includes soft-skip files)."""
    files: list[str] = []
    outputs = [
        run_git("diff", "--name-only"),
        run_git("diff", "--cached", "--name-only"),
        run_git("ls-files", "--others", "--exclude-standard"),
    ]
    for output in outputs:
        for line in output.splitlines():
            normalized = line.strip().replace("\\", "/")
            if not normalized:
                continue
            if normalized.startswith(SKIP_PREFIXES):
                continue
            if normalized in SKIP_FILES:
                continue
            files.append(normalized)
    seen: list[str] = []
    for item in files:
        if item not in seen:
            seen.append(item)
    return seen


def trail_files(files: list[str]) -> list[str]:
    """Return the subset of files to include in an auto-record trail entry.

    Soft-skip files (CLAUDE.md, AGENTS.md) are excluded when they are the
    *only* files present, to avoid self-referential noise from lone meta-file
    edits.  When mixed with substantive changes they are included normally.
    """
    non_soft = [f for f in files if f not in SOFT_SKIP_FILES]
    if non_soft:
        return files  # substantive changes present — include everything
    return []  # only soft-skip files — suppress the auto-record entirely


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_nudge_state() -> dict:
    if not NUDGE_STATE_PATH.exists():
        return {}
    try:
        return json.loads(NUDGE_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_nudge_state(state: dict) -> None:
    NUDGE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "workspace-change"


def matches_high_signal(file_path: str) -> bool:
    return any(pattern.search(file_path) for pattern in HIGH_SIGNAL_PATTERNS)


def detect_high_level_areas(files: list[str]) -> set[str]:
    matched: set[str] = set()
    for file_path in files:
        for name, pattern in HIGH_LEVEL_AREAS:
            if pattern.search(file_path):
                matched.add(name)
    return matched


DIGEST_CLUSTER_THRESHOLD = 2  # min same-theme records accumulated to suggest a digest
# Present-stop file count that satisfies the signal floor for a digest nudge.
DIGEST_SIGNAL_FILE_FLOOR = 3


def detect_recent_theme_overlap(theme_key: str, nudge_state: dict) -> bool:
    """Return True only when a credible same-theme cluster exists.

    Reads per-theme record counts stored in nudge_state["theme_record_counts"].
    Only the current theme's count is consulted, so a burst of activity in one
    area (e.g. "scripts") cannot trigger a digest nudge for an unrelated area
    (e.g. "skills" or "instructions").  The count must reach
    DIGEST_CLUSTER_THRESHOLD before a digest nudge fires.
    """
    counts: dict = nudge_state.get("theme_record_counts", {})
    return counts.get(theme_key, 0) >= DIGEST_CLUSTER_THRESHOLD


def present_stop_qualifies_for_digest(
    files: list[str],
    high_signal_hits: list[str],
    areas: set[str],
) -> bool:
    """Return True when the *current* stop has enough signal to warrant a digest nudge.

    Prevents over-triggering on tiny low-signal stops once a theme's accumulated
    count has crossed DIGEST_CLUSTER_THRESHOLD.  Any one of the following is
    sufficient:
    - strong signal: at least one high-signal file is present
    - cross-area: the current stop touches two or more high-level areas
    - moderate file count: the current stop changes at least DIGEST_SIGNAL_FILE_FLOOR files
    """
    return bool(high_signal_hits) or len(areas) >= 2 or len(files) >= DIGEST_SIGNAL_FILE_FLOOR


def already_nudged_digest_for_theme(theme_key: str, nudge_state: dict) -> bool:
    """Return True when a digest nudge was already emitted for this theme and the
    underlying evidence has not grown meaningfully since then.

    Uses nudge_state["digest_nudged_at_count"] (a dict mapping theme_key to the
    theme_record_count at the time of the last digest nudge) instead of the
    volatile ``last_nudge_type`` field, so that intervening low-signal stops
    (which would overwrite last_nudge_type to "none") do not reset the cooldown.

    The cooldown is lifted once the theme accumulates at least one new record
    beyond the count recorded at nudge time, giving the user a fresh prompt
    after genuinely new same-theme activity.
    """
    nudged_at: dict = nudge_state.get("digest_nudged_at_count", {})
    if theme_key not in nudged_at:
        return False
    counts: dict = nudge_state.get("theme_record_counts", {})
    current_count = counts.get(theme_key, 0)
    # Cooldown holds as long as no new records have accumulated since the nudge.
    return current_count <= nudged_at[theme_key]


def next_change_number() -> int:
    numbers = []
    for path in CHANGES_DIR.glob("*.md"):
        match = re.match(r"\d{4}-\d{2}-\d{2}-(\d{3})-", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return (max(numbers) + 1) if numbers else 1


def next_change_id() -> str:
    return f"{next_change_number():03d}"


def make_title(files: list[str]) -> str:
    names = [Path(file).stem.replace("_", "-") for file in files[:MAX_FILES_IN_TITLE]]
    if not names:
        return "workspace-change"
    if len(files) > MAX_FILES_IN_TITLE:
        names.append("and-more")
    return slugify("-".join(names))


def classify_followup(files: list[str], nudge_state: dict) -> tuple[str, str | None, str | None]:
    file_count = len(files)
    high_signal_hits = [file for file in files if matches_high_signal(file)]
    areas = detect_high_level_areas(files)
    theme_key = slugify("-".join(sorted(areas)) or "misc")
    recent_overlap = detect_recent_theme_overlap(theme_key, nudge_state)

    # Digest cooldown: theme-aware, survives intervening non-digest stops.
    if (recent_overlap
            and present_stop_qualifies_for_digest(files, high_signal_hits, areas)
            and not already_nudged_digest_for_theme(theme_key, nudge_state)):
        return "digest", theme_key, "SyberMem note: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point."

    last_type = nudge_state.get("last_nudge_type")
    last_theme = nudge_state.get("last_theme")

    cross_area = len(areas) >= 2
    strong_signal = bool(high_signal_hits)
    large_change = file_count >= RECORD_FILE_THRESHOLD
    if (strong_signal or cross_area or large_change) and not (last_type == "record" and last_theme == theme_key):
        return "record", theme_key, "SyberMem note: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved more clearly."

    return "none", theme_key, None


def render_related_files(files: list[str]) -> str:
    return ", ".join(files)


def render_change_content(files: list[str]) -> str:
    bullets = "\n".join(f"- Updated `{file}`" for file in files)
    return f"Auto-generated from workspace changes detected at session stop.\n\n{bullets}"


def render_reason(files: list[str]) -> str:
    return f"Persist the current workspace change set in SyberMem without requiring a manual /sybermem-record step. {len(files)} file(s) changed."


def render_impact(files: list[str]) -> str:
    return "\n".join([
        "- Project history: keeps a lightweight change trail in `.sybermem/changes/`",
        f"- Current workspace: captures {len(files)} changed file(s) at stop time",
    ])


def render_implementation(files: list[str]) -> str:
    return "\n".join(f"- `{file}`" for file in files)


def render_test_verification() -> str:
    return "Auto-generated from git workspace status; no extra verification was captured by the stop hook."


def render_notes(followup_hint: str) -> str:
    return "\n".join([
        "Automatic mode only writes basic `change` records. Use `/sybermem-record` for decisions, requirements, bugs, or richer summaries.",
        f"followup_hint: {followup_hint}",
    ])


def render_record(record_date: str, number: str, title: str, files: list[str], author: str, followup_hint: str) -> str:
    return f"""---
type: change
date: {record_date}
number: {number}
title: {title}
status: implemented
author: {author}
related_files: {render_related_files(files)}
---

## Change Content
{render_change_content(files)}

## Reason for Change
{render_reason(files)}

## Impact Scope
{render_impact(files)}

## Implementation
{render_implementation(files)}

## Test Verification
{render_test_verification()}

## Notes
{render_notes(followup_hint)}
"""


def insert_before_marker(path: Path, marker: str, addition: str) -> None:
    content = path.read_text(encoding="utf-8")
    updated = content.replace(marker, addition + marker, 1)
    path.write_text(updated, encoding="utf-8")


def update_index(record_date: str, number: str, title: str, slug: str) -> None:
    link_name = f"{record_date}-{number}-{slug}.md"
    conclusion = f"- [change-{number}] Auto-recorded workspace file changes at session stop so the project keeps a lightweight change trail without manual recording ({record_date})\n"
    row = f"| {number} | {record_date} | Auto-record workspace file changes on stop | implemented | [link](changes/{link_name}) |\n"
    insert_before_marker(INDEX_PATH, "<!-- add new conclusions here -->", conclusion)
    insert_before_marker(INDEX_PATH, "<!-- add new records here -->", row)


def main() -> int:
    if not should_auto_record():
        return 0
    if not INDEX_PATH.exists() or not CHANGES_DIR.exists():
        return 0

    all_files = list_changed_files()
    if not all_files:
        return 0

    # Determine which files go into the trail record (excludes lone soft-skip files).
    files = trail_files(all_files)

    # Load nudge state before classify so theme_record_counts is available.
    nudge_state = load_nudge_state()
    # Use all_files for signal detection even when trail is suppressed.
    followup_hint, theme_key, nudge_message = classify_followup(all_files, nudge_state)

    if not files:
        # Only soft-skip files changed — emit nudge if warranted, but skip record.
        if nudge_message:
            print(nudge_message)
        return 0

    fingerprint = json.dumps(files, ensure_ascii=False)
    state = load_state()
    if state.get("last_fingerprint") == fingerprint:
        return 0

    record_date = date.today().isoformat()
    number = next_change_id()
    slug = make_title(files)
    author = run_git("config", "user.name") or "Claude"
    record_path = CHANGES_DIR / f"{record_date}-{number}-{slug}.md"
    record_path.write_text(render_record(record_date, number, slug.replace("-", " "), files, author, followup_hint), encoding="utf-8")
    update_index(record_date, number, slug.replace("-", " "), slug)
    save_state({"last_fingerprint": fingerprint, "last_record": record_path.name})

    # Increment the per-theme record count so digest thresholds are theme-accurate.
    theme_counts: dict = dict(nudge_state.get("theme_record_counts", {}))
    theme_counts[theme_key] = theme_counts.get(theme_key, 0) + 1
    # Persist digest nudge memory durably so intervening quiet stops cannot erase it.
    digest_nudged_at: dict = dict(nudge_state.get("digest_nudged_at_count", {}))
    if followup_hint == "digest":
        digest_nudged_at[theme_key] = theme_counts[theme_key]
    save_nudge_state({
        **nudge_state,
        "last_theme": theme_key,
        "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
        "last_record": record_path.name,
        "theme_record_counts": theme_counts,
        "digest_nudged_at_count": digest_nudged_at,
    })
    if nudge_message:
        print(nudge_message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
