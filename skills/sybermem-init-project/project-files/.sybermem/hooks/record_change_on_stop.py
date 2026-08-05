#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import date
from importlib import import_module
from pathlib import Path

def resolve_sybermem_root() -> Path:
    """Walk up from cwd to find the nearest SyberMem project root.

    A directory is considered a SyberMem root if it contains .sybermem/ and
    at least one of:
      - .claude/settings.json  (normal project checkout)
      - .sybermem/INDEX.md     (worktree or checkout where settings.json is untracked)

    Stops at the git repository root or filesystem root, whichever comes first.
    Returns the resolved project root, or falls back to cwd if no SyberMem root is found.
    """
    current = Path.cwd().resolve()
    git_root = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
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
        # Stop at git root boundary
        if git_root and current == git_root:
            break
        # Stop at filesystem root
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: no SyberMem root found, return cwd so the hook exits gracefully
    return Path.cwd()


ROOT = resolve_sybermem_root()
GIT_CWD = ROOT
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

NUDGE_STATE_PATH = SYBERMEM_DIR / ".nudge-state.json"
LEGACY_NUDGE_STATE_PATH = SYBERMEM_DIR / ".auto-nudge-state.json"
RECORD_FILE_THRESHOLD = 5
RECORD_COOLDOWN_KEYS = {"record", "digest"}
# Bounded recent-window: only the last N same-theme record-writing stops are
# kept. Digest cluster detection is based on this window, not lifetime totals.
THEME_WINDOW_SIZE = 10
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
        cwd=GIT_CWD,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def record_mode() -> str:
    mode = os.environ.get("SYBERMEM_RECORD_MODE", "auto").strip().lower()
    return mode if mode in {"auto", "remind"} else "auto"


def should_auto_record() -> bool:
    return record_mode() == "auto"


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
    edits. When mixed with substantive changes they are included normally.
    """
    non_soft = [f for f in files if f not in SOFT_SKIP_FILES]
    if non_soft:
        return files
    return []


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
    """Load unified nudge state, migrating from legacy files if needed."""
    if NUDGE_STATE_PATH.exists():
        try:
            return json.loads(NUDGE_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Migrate from legacy .auto-nudge-state.json if it exists
    if LEGACY_NUDGE_STATE_PATH.exists():
        try:
            data = json.loads(LEGACY_NUDGE_STATE_PATH.read_text(encoding="utf-8"))
            # Save to new path; leave legacy file on disk (cleaned by /sybermem-update)
            save_nudge_state(data)
            return data
        except Exception:
            pass
    return {}


def save_nudge_state(state: dict) -> None:
    NUDGE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


RECORD_INTENT_PATH = SYBERMEM_DIR / ".record-intent.json"


def load_record_intent() -> dict:
    if not RECORD_INTENT_PATH.exists():
        return {}
    try:
        return json.loads(RECORD_INTENT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_record_intent(intent: dict) -> None:
    RECORD_INTENT_PATH.write_text(json.dumps(intent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clear_record_intent() -> None:
    try:
        RECORD_INTENT_PATH.unlink()
    except FileNotFoundError:
        pass


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "workspace-change"


INTENT_PATTERNS = [
    re.compile(r"这轮.*提醒我.*记录"),
    re.compile(r"这次.*要记.*record", re.IGNORECASE),
    re.compile(r"做完.*沉淀一下"),
    re.compile(r"完成后.*提醒我.*/sybermem-record"),
    re.compile(r"这轮工作.*记录到.*sybermem", re.IGNORECASE),
]


def detect_record_intent_from_text(text: str) -> bool:
    return any(pattern.search(text) for pattern in INTENT_PATTERNS)


def matches_high_signal(file_path: str) -> bool:
    return any(pattern.search(file_path) for pattern in HIGH_SIGNAL_PATTERNS)


def detect_high_level_areas(files: list[str]) -> set[str]:
    matched: set[str] = set()
    for file_path in files:
        for name, pattern in HIGH_LEVEL_AREAS:
            if pattern.search(file_path):
                matched.add(name)
    return matched


COMMIT_GAP_THRESHOLD = 5


def count_commits_since_last_record() -> int:
    """Count commits since the most recent record file date across all record directories."""
    latest_date: str = ""
    for subdir in ("changes", "decisions", "requirements", "bugs"):
        record_dir = SYBERMEM_DIR / subdir
        if not record_dir.is_dir():
            continue
        for path in record_dir.glob("*.md"):
            match = re.match(r"(\d{4}-\d{2}-\d{2})-", path.name)
            if match and match.group(1) > latest_date:
                latest_date = match.group(1)
    if not latest_date:
        return 0
    count_str = run_git("rev-list", "--count", f"--since={latest_date}", "HEAD")
    try:
        return int(count_str)
    except (ValueError, TypeError):
        return 0


DIGEST_CLUSTER_THRESHOLD = 2
DIGEST_SIGNAL_FILE_FLOOR = 3


AUTO_TRAIL_DEDUP_WINDOW = 3
AUTO_TRAIL_OVERLAP_THRESHOLD = 0.8


def overlaps_recent_auto_trails(files: list[str]) -> bool:
    """Check if the current file set overlaps >80% with any of the last 3 auto trails."""
    if not CHANGES_DIR.is_dir():
        return False
    trails = sorted(CHANGES_DIR.glob("*.md"), key=lambda p: p.name, reverse=True)
    current_set = set(files)
    checked = 0
    for trail_path in trails:
        if checked >= AUTO_TRAIL_DEDUP_WINDOW:
            break
        try:
            content = trail_path.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only check auto-generated trails (they have the "Auto-generated" marker)
        if "Auto-generated from workspace changes" not in content:
            continue
        checked += 1
        # Extract related_files from frontmatter
        fm_match = re.search(r"^related_files:\s*(.+)$", content, re.MULTILINE)
        if not fm_match:
            continue
        trail_files = {f.strip() for f in fm_match.group(1).split(",")}
        if not trail_files or not current_set:
            continue
        overlap = len(current_set & trail_files) / max(len(current_set), len(trail_files))
        if overlap >= AUTO_TRAIL_OVERLAP_THRESHOLD:
            return True
    return False


def get_theme_recent_stops(theme_key: str, nudge_state: dict) -> list[str]:
    """Return the bounded list of ISO dates for same-theme record-writing stops."""
    windows: dict = nudge_state.get("theme_recent_stops", {})
    return list(windows.get(theme_key, []))


def append_theme_recent_stop(theme_key: str, nudge_state: dict, today: str) -> dict:
    """Return updated nudge_state with today appended; capped at THEME_WINDOW_SIZE.

    Replaces lifetime-cumulative theme_record_counts so cluster detection is
    always based on recent activity only.
    """
    windows: dict = dict(nudge_state.get("theme_recent_stops", {}))
    current: list[str] = list(windows.get(theme_key, []))
    current.append(today)
    windows[theme_key] = current[-THEME_WINDOW_SIZE:]
    return {**nudge_state, "theme_recent_stops": windows}


def detect_recent_theme_overlap(theme_key: str, nudge_state: dict) -> bool:
    """Return True only when a credible same-theme cluster exists.

    Uses the bounded theme_recent_stops list instead of lifetime-cumulative
    theme_record_counts, so ancient activity does not pollute the signal. The
    cluster must reach DIGEST_CLUSTER_THRESHOLD entries within the bounded
    window before a digest nudge fires.
    """
    recent = get_theme_recent_stops(theme_key, nudge_state)
    return len(recent) >= DIGEST_CLUSTER_THRESHOLD


def present_stop_qualifies_for_digest(
    files: list[str],
    high_signal_hits: list[str],
    areas: set[str],
) -> bool:
    """Return True when the *current* stop has enough signal to warrant a digest nudge.

    Prevents over-triggering on tiny low-signal stops once a theme's accumulated
    count has crossed DIGEST_CLUSTER_THRESHOLD. Any one of the following is
    sufficient:
    - strong signal: at least one high-signal file is present
    - cross-area: the current stop touches two or more high-level areas
    - moderate file count: the current stop changes at least DIGEST_SIGNAL_FILE_FLOOR files
    """
    return bool(high_signal_hits) or len(areas) >= 2 or len(files) >= DIGEST_SIGNAL_FILE_FLOOR


def already_nudged_digest_for_theme(theme_key: str, nudge_state: dict) -> bool:
    """Return True when a digest nudge was already emitted for this theme and the
    underlying evidence has not grown meaningfully since then.

    Uses nudge_state["digest_nudged_at_window_len"] (a dict mapping theme_key to the
    window length at the time of the last digest nudge) instead of the
    volatile `last_nudge_type` field, so that intervening low-signal stops
    (which would overwrite last_nudge_type to "none") do not reset the cooldown.

    The cooldown is lifted once the theme recent window has grown by at least
    one entry beyond the length recorded at nudge time, giving a fresh prompt
    after genuinely new same-theme activity.
    """
    nudged_at: dict = nudge_state.get("digest_nudged_at_window_len", {})
    if theme_key not in nudged_at:
        return False
    current_len = len(get_theme_recent_stops(theme_key, nudge_state))
    return current_len <= nudged_at[theme_key]


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

    last_type = nudge_state.get("last_nudge_type")
    last_theme = nudge_state.get("last_theme")

    already_digested_this_theme = already_nudged_digest_for_theme(theme_key, nudge_state)
    if recent_overlap and present_stop_qualifies_for_digest(files, high_signal_hits, areas) and not already_digested_this_theme:
        return "digest", theme_key, "SyberMem note: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point."

    cross_area = len(areas) >= 2
    strong_signal = bool(high_signal_hits)
    large_change = file_count >= RECORD_FILE_THRESHOLD
    commit_count = count_commits_since_last_record()
    commit_gap = commit_count >= COMMIT_GAP_THRESHOLD
    if (strong_signal or cross_area or large_change or commit_gap) and not (last_type == "record" and last_theme == theme_key):
        gap_note = f" ({commit_count} commits since last record)" if commit_gap else ""
        return "record", theme_key, f"SyberMem note: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved more clearly.{gap_note}"

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
    row = f"| {number} | {record_date} | Auto-record workspace file changes on stop | implemented | [link](changes/{link_name}) |\n"
    # Auto-trail records only go into the Feature Changes table, NOT Key Conclusions.
    # Key Conclusions should only contain meaningful manually-created records.
    insert_before_marker(INDEX_PATH, "<!-- add new records here -->", row)


def main() -> int:
    mode = record_mode()
    if mode not in {"auto", "remind"}:
        return 0
    if not INDEX_PATH.exists() or not CHANGES_DIR.exists():
        return 0

    all_files = list_changed_files()
    record_intent = load_record_intent()
    intent_active = bool(record_intent.get("record_intent"))

    # Even with no changed files, honor explicit record intent
    if not all_files:
        if intent_active:
            print("You marked this work as worth recording earlier. If this round is complete, run /sybermem-record now.")
            clear_record_intent()
        return 0

    files = trail_files(all_files)
    nudge_state = load_nudge_state()
    followup_hint, theme_key, nudge_message = classify_followup(all_files, nudge_state)
    theme_key = theme_key or "misc"
    try:
        import sys
        from pathlib import Path as _Path
        for p in [
            _Path.home() / '.claude' / 'sybermem' / 'cli' / 'venv' / 'Lib' / 'site-packages',
            _Path.home() / '.claude' / 'sybermem' / 'cli' / 'venv' / 'lib' / 'python3.10' / 'site-packages',
        ]:
            if p.exists() and str(p) not in sys.path:
                sys.path.insert(0, str(p))
        recommend_next_step = getattr(import_module("sybermem_core.next_step_router"), "recommend_next_step")
        router_hint = recommend_next_step(ROOT)
    except Exception:
        router_hint = None

    def emit_reminder() -> None:
        if intent_active:
            action = record_intent.get("action") or "/sybermem-record"
            reason = record_intent.get("reason") or "You marked this work as worth recording earlier."
            if action == "/sybermem-record":
                classification = record_intent.get("classification") or "record"
                print(f"Recommended next step: /sybermem-record — {reason} Classification: {classification}.")
            elif action:
                print(f"Recommended next step: {action} — {reason}")
            clear_record_intent()
        elif router_hint:
            print(f"Recommended next step: {router_hint['action']} — {router_hint['reason']}")
        elif nudge_message:
            print(nudge_message)

    if not files:
        updated_nudge_state = {
            **nudge_state,
            "last_nudge": {
                "platform": "claude-code",
                "type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
                "theme": theme_key,
                "date": date.today().isoformat(),
            },
            "last_theme": theme_key,
            "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
        }
        if followup_hint == "digest":
            digest_nudged_at: dict = dict(nudge_state.get("digest_nudged_at_window_len", {}))
            digest_nudged_at[theme_key] = len(get_theme_recent_stops(theme_key, nudge_state))
            updated_nudge_state["digest_nudged_at_window_len"] = digest_nudged_at
        save_nudge_state(updated_nudge_state)
        emit_reminder()
        return 0

    fingerprint = json.dumps(files, ensure_ascii=False)
    state = load_state()
    if state.get("last_fingerprint") == fingerprint:
        if intent_active:
            emit_reminder()
        return 0

    # Auto-trail dedup: skip if >80% overlap with recent auto trails
    if overlaps_recent_auto_trails(files):
        save_state({"last_fingerprint": fingerprint, "last_record": state.get("last_record", "")})
        emit_reminder()
        return 0

    record_date = date.today().isoformat()
    number = next_change_id()
    slug = make_title(files)
    author = run_git("config", "user.name") or "Claude"
    record_path = CHANGES_DIR / f"{record_date}-{number}-{slug}.md"
    if mode == "auto":
        record_path.write_text(render_record(record_date, number, slug.replace("-", " "), files, author, followup_hint), encoding="utf-8")
        update_index(record_date, number, slug.replace("-", " "), slug)
        save_state({"last_fingerprint": fingerprint, "last_record": record_path.name})
    else:
        save_state({"last_fingerprint": fingerprint, "last_record": state.get("last_record", "")})

    today = record_date
    nudge_state = append_theme_recent_stop(theme_key, nudge_state, today)
    updated_nudge_state = {
        **nudge_state,
        "last_nudge": {
            "platform": "claude-code",
            "type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
            "theme": theme_key,
            "date": date.today().isoformat(),
        },
        "last_theme": theme_key,
        "last_nudge_type": followup_hint if followup_hint in RECORD_COOLDOWN_KEYS else "none",
        "last_record": record_path.name,
    }
    if followup_hint == "digest":
        digest_nudged_at: dict = dict(nudge_state.get("digest_nudged_at_window_len", {}))
        digest_nudged_at[theme_key] = len(get_theme_recent_stops(theme_key, nudge_state))
        updated_nudge_state["digest_nudged_at_window_len"] = digest_nudged_at
    save_nudge_state(updated_nudge_state)
    emit_reminder()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
