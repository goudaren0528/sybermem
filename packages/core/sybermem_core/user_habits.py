from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from enum import Enum
import json
import os
from pathlib import Path
import re
from typing import Final, TypeVar
from uuid import uuid4

from sybermem_core.user_habit_model import (
    Confidence,
    Habit,
    HabitEvent,
    HabitSearchResult,
    HabitStatus,
    HabitType,
    InjectionPolicy,
    InvalidHabitError,
)

EnumValue = TypeVar("EnumValue", bound=Enum)

HABIT_DIR: Final = "user-habits"
HABITS_FILE: Final = "habits.jsonl"
INJECTION_LOG_FILE: Final = "injection-log.jsonl"
# Candidate-only intent capture. Lives at the user-level SyberMem home (next to
# user-habits/), never in a project's .sybermem/, because habits are user-scoped
# and must not pollute project memory. Capturing writes a candidate for the user
# to confirm via /sybermem-habit; it NEVER creates an active habit on its own.
HABIT_INTENT_FILE: Final = ".habit-intent.json"
MAX_INJECTED_HABITS: Final = 3
MAX_LOG_EVENTS: Final = 200
MAX_STATEMENT_CHARS: Final = 300
# Bounded candidate list. Passive capture keeps only the most recent few candidates so a
# stale, unrelated candidate cannot mask the one the user actually wants to confirm, and
# candidates older than the expiry window are pruned on read/write. These are still
# user-originated prompt fragments, so the retention is deliberately small and short-lived.
MAX_HABIT_CANDIDATES: Final = 5
HABIT_CANDIDATE_EXPIRY_DAYS: Final = 10
# Bounded, blocklist-filtered summary of the triggering prompt stored on a candidate so the
# confirm step can propose a normalized statement from the user's own words. Mirrors the
# record_intent summary contract (bounded + secret/control filtered), NOT raw unbounded text.
MAX_CANDIDATE_SUMMARY_CHARS: Final = 160
HABIT_INTENT_TERMS: Final = {
    # ASCII single-word triggers (matched as tokens via _terms()).
    "always",
    "habit",
    "preference",
    "prefer",
    "remember",
    "usually",
    "default",
    "convention",
    # CJK triggers (matched as substrings via the fallback in _looks_like_habit_intent,
    # since CJK has no whitespace token boundaries). Kept multi-char so they stay
    # specific and do not fire on incidental single characters.
    "以后",
    "偏好",
    "习惯",
    "记住",
    "总是",
    "每次",
    "默认",
    "一律",
    "记得",
    "尽量",
    "规范",
    "约定",
}
_DURABLE_PREFERENCE_RE: Final = re.compile(
    r"(\b(always\s+(?:prefer|use|reply|respond|run|keep|write|ask|show|include|avoid)|"
    r"usually\s+(?:i\s+)?(?:prefer|use|want|ask|run|keep|write)|"
    r"(?:please\s+)?remember\s+(?:that\s+)?(?:i\s+)?(?:prefer|want|usually|always)|"
    r"i\s+prefer\b|i\s+usually\b|by\s+default\b|make\s+this\s+the\s+default\b|"
    r"from\s+now\s+on\b)|"
    r"以后(?:都|请|记得|默认|一律)?|请记住|帮我记住|记住我|我(?:习惯|偏好|希望)|"
    r"每次都|默认(?:用|先|都)?|一律(?:用|先|都)?|总是(?:用|先|都)?)",
    re.IGNORECASE,
)
_NOISY_HABIT_DISCUSSION_RE: Final = re.compile(
    r"(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|"
    r"为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中).{0,80}"
    r"(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定)|"
    r"(habit|preference|memory|norm|习惯|偏好|记忆|规范|约定).{0,80}"
    r"(why|debug|investigate|research|review|analy[sz]e|improve|design|logic|classifier|candidate|capture|"
    r"为什么|怎么|调研|研究|评审|审查|改进|设计|逻辑|候选|捕获|命中)",
    re.IGNORECASE,
)
_AGENT_PROMPT_PREFIX_RE: Final = re.compile(r"^\s*(?:TASK|CONTEXT|AXIS|EXPECTED OUTCOME|MUST DO|MUST NOT DO|REQUEST):", re.IGNORECASE)
_ONE_OFF_WORK_RE: Final = re.compile(
    r"(fix|repair|update|submit|publish|release|commit|create\s+pr|修复|更新|提交|发布|上线).{0,80}"
    r"(pr|readme|docs?|todo|ui|bug|文档|待办|规范|约定|项目|下拉|按钮)",
    re.IGNORECASE,
)
# Signals that a preference is PROJECT-specific (belongs in a decision/requirement
# record via /sybermem-record) rather than a cross-project USER habit. Deliberately
# conservative: only fire on phrasing that clearly scopes to "this repo / this project".
PROJECT_SCOPE_HINTS: Final = (
    "this project",
    "this repo",
    "this repository",
    "this codebase",
    "in this repo",
    "本项目",
    "这个项目",
    "本仓库",
    "这个仓库",
    "该项目",
    "该仓库",
    "这个代码库",
)
# Signals that a preference is a cross-project USER habit (communication/tooling/style
# that follows the person everywhere), so it belongs in user-habit memory.
USER_SCOPE_HINTS: Final = (
    "always",
    "usually",
    "in general",
    "everywhere",
    "cross-project",
    "my",
    "i prefer",
    "i like",
    "我",
    "我的",
    "跨项目",
    "一律",
    "总是",
    "习惯",
    "偏好",
)
# Map an intent phrase to a habit_type so the captured candidate is pre-classified.
HABIT_TYPE_HINTS: Final = (
    ("review", ("review", "pr", "评审", "审查", "代码审查")),
    ("tooling", ("tool", "cli", "command", "工具", "命令", "脚本")),
    ("communication", ("reply", "message", "language", "沟通", "回复", "语言", "中文", "english")),
    ("style", ("style", "format", "naming", "风格", "格式", "命名", "缩进")),
    ("avoidance", ("never", "avoid", "don't", "do not", "不要", "禁止", "避免")),
)
# Never persist secrets or prompt-injection control text as a habit candidate.
# Mirrors the OpenCode record-intent guard so capture stays privacy-safe.
_BLOCKED_INTENT_RE: Final = re.compile(
    r"(password\s*=|token\s*=|secret\s*=|bearer\s+[a-z0-9._-]+|api[_ -]?key\s*=|"
    r"begin\s+(?:rsa\s+)?private\s+key|ignore\s+(?:all\s+)?previous|system\s+prompt|"
    r"developer\s+message|</?(?:system|developer|tool)[^>]*>)",
    re.IGNORECASE,
)


# Legacy user home used by older installers/launchers, which FORCED
# SYBERMEM_HOME=~/.claude/sybermem/cli. That path is install-managed runtime state
# (a reinstall/uninstall can wipe it), whereas ~/.sybermem is the documented,
# user-owned data home. We now treat ~/.sybermem as canonical and import any habit
# data left behind in the legacy location once, non-destructively.
def _legacy_user_home() -> Path | None:
    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if not home:
        return None
    return Path(home) / ".claude" / "sybermem" / "cli"


def _sybermem_base() -> tuple[Path, bool]:
    # Returns (base, is_default_home). An explicit SYBERMEM_HOME still wins (tests and
    # advanced/custom setups rely on it), EXCEPT the legacy launcher value which we
    # deliberately ignore so the launcher and a bare `sybermem` resolve to the SAME
    # canonical home. Without this the two diverge and a habit added via one path is
    # invisible to the other. `is_default_home` is True only when we fell through to the
    # documented ~/.sybermem — that gates the one-time legacy import so an explicit,
    # non-legacy SYBERMEM_HOME (e.g. an isolated test home) is never migrated into.
    home = os.environ.get("SYBERMEM_HOME")
    if home:
        resolved = Path(home).expanduser()
        legacy = _legacy_user_home()
        try:
            is_legacy = legacy is not None and resolved.resolve() == legacy.resolve()
        except OSError:
            is_legacy = False
        if not is_legacy:
            return resolved, False
    return Path.home() / ".sybermem", True


def user_habit_home() -> Path:
    base, is_default_home = _sybermem_base()
    if is_default_home:
        _import_legacy_habit_data(base)
    return base / HABIT_DIR


def _import_legacy_habit_data(base: Path) -> None:
    """One-time, non-destructive import of habit data from the legacy launcher home.

    Older installs stored habits under ~/.claude/sybermem/cli/ because the launcher
    forced SYBERMEM_HOME there. When the canonical ~/.sybermem/ is missing a given file
    but the legacy home has it, copy it so upgrading users do not silently "lose" their
    confirmed habits OR a pending candidate awaiting confirmation. Each file is imported
    INDEPENDENTLY: a user can have a pending candidate with zero active habits (the exact
    case that made habit reminders invisible), so importing the candidate must NOT be
    gated on habits.jsonl having content. We never overwrite existing canonical data and
    never delete the legacy source, so the operation is idempotent and recoverable.
    Fail-open: any error leaves both intact.
    """
    legacy_base = _legacy_user_home()
    if legacy_base is None:
        return
    try:
        if base.resolve() == legacy_base.resolve():
            return  # canonical IS the legacy home (custom setup); nothing to import
    except OSError:
        return
    # One-time marker: without it the import would run on EVERY access and re-copy a
    # candidate the user just cleared (clear deletes canonical -> "canonical missing" ->
    # re-import from the still-present legacy file, an infinite loop). The marker makes
    # the migration genuinely one-time and idempotent.
    marker = base / ".habit-legacy-imported"
    try:
        if marker.exists():
            return
    except OSError:
        return
    try:
        # (legacy source, canonical target) for each independently-imported file.
        pairs = [
            (legacy_base / HABIT_DIR / HABITS_FILE, base / HABIT_DIR / HABITS_FILE),
            # The candidate intent lives BESIDE user-habits/, not inside it.
            (legacy_base / HABIT_INTENT_FILE, base / HABIT_INTENT_FILE),
            (legacy_base / HABIT_DIR / INJECTION_LOG_FILE, base / HABIT_DIR / INJECTION_LOG_FILE),
        ]
        for legacy_path, canonical_path in pairs:
            # Skip when canonical already has real content, or legacy has nothing to give.
            if canonical_path.exists() and canonical_path.stat().st_size > 0:
                continue
            if not (legacy_path.is_file() and legacy_path.stat().st_size > 0):
                continue
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            canonical_path.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
        # Mark migration done so it never re-imports (esp. re-copying a cleared candidate).
        base.mkdir(parents=True, exist_ok=True)
        marker.write_text(_now() + "\n", encoding="utf-8")
    except OSError:
        return


def add_habit(
    *,
    statement: str,
    habit_type: HabitType | str,
    applies_to: tuple[str, ...] = (),
    not_applies_to: tuple[str, ...] = (),
    injection_policy: InjectionPolicy | str = InjectionPolicy.PROMPT_OK_WHEN_SUPPORTED,
    source_ref: str | None = None,
) -> Habit:
    # Default to PROMPT_OK_WHEN_SUPPORTED so a user-confirmed habit is perceptible
    # at prompt time on supported hosts (OpenCode/Claude/Codex) by default, not only
    # during compaction. Confirmation-first still holds: add_habit is reached only
    # AFTER the user confirmed the habit, so this controls WHERE a confirmed habit
    # surfaces, never WHETHER it may be remembered. Existing serialized habits keep
    # their stored policy; only newly created habits adopt the new default.
    habit = Habit(
        habit_id=f"habit-{uuid4().hex}",
        scope="user",
        habit_type=_parse_enum(HabitType, habit_type, "habit_type"),
        statement=_single_line(statement),
        source_kind="explicit_user",
        source_refs=({"kind": "manual", "ref": source_ref or "explicit user request"},),
        confidence=Confidence.HIGH,
        status=HabitStatus.ACTIVE,
        applies_to=tuple(_single_line(tag).lower() for tag in applies_to if tag.strip()),
        not_applies_to=tuple(_single_line(tag).lower() for tag in not_applies_to if tag.strip()),
        last_confirmed_at=date.today().isoformat(),
        review_after=None,
        injection_policy=_parse_enum(InjectionPolicy, injection_policy, "injection_policy"),
        superseded_by=None,
    )
    _append_event(_habit_to_event(habit, "add"))
    return habit


def list_habits(*, status: HabitStatus | str | None = HabitStatus.ACTIVE) -> list[Habit]:
    habits = _replay_habits()
    if status is None:
        return habits
    target = _parse_enum(HabitStatus, status, "status")
    return [habit for habit in habits if habit.status is target]


def search_habits(query: str) -> list[HabitSearchResult]:
    terms = _terms(query)
    if not terms:
        return []
    results = []
    for habit in list_habits(status=None):
        if habit.status is HabitStatus.DELETED:
            continue
        score = _score_habit(habit, terms)
        if score > 0:
            results.append(HabitSearchResult(habit=habit, score=score))
    return sorted(results, key=lambda result: (-result.score, result.habit.last_confirmed_at, result.habit.habit_id))


def pause_habit(habit_id: str) -> None:
    _append_status_event(habit_id, HabitStatus.PAUSED)


def delete_habit(habit_id: str) -> None:
    events = _read_events()
    if habit_id not in {event.get("habit_id", "") for event in events}:
        raise InvalidHabitError(f"unknown habit id: {habit_id}")
    _write_events([event for event in events if event.get("habit_id") != habit_id])


def render_habit_markdown(*, context: str, higher_authority_text: str = "") -> str:
    selected = _select_injectable(context, higher_authority_text)
    if not selected:
        _log_injection([], "no_matching_habits")
        return ""
    _log_injection([habit.habit_id for habit in selected], None)
    lines = ["## User Habit Memory", ""]
    for habit in selected:
        lines.append(f"- [{habit.habit_id}] {habit.statement}. Source: {habit.source_kind}. Confidence: {habit.confidence.value}.")
    return "\n".join(lines) + "\n"


def render_habit_reminder_markdown(*, context: str, higher_authority_text: str = "") -> str:
    selected = _select_remindable(context, higher_authority_text)
    if selected:
        _log_injection([habit.habit_id for habit in selected], None)
        lines = ["## User Habit Reminder", ""]
        for habit in selected:
            lines.append(f"- [{habit.habit_id}] This user habit may apply: {habit.statement}.")
        lines.append("- To manage habit memory, use `/sybermem-habit` or `sybermem habit list`.")
        return "\n".join(lines) + "\n"

    if higher_authority_text or not _looks_like_habit_intent(context):
        _log_injection([], "no_matching_habits")
        return ""

    _log_injection([], "habit_preference_candidate")
    return "\n".join(
        [
            "## User Habit Reminder",
            "",
            "- This looks like a reusable user preference. If you want SyberMem to remember it, confirm it with `/sybermem-habit`.",
        ]
    ) + "\n"


def _select_injectable(context: str, higher_authority_text: str) -> list[Habit]:
    context_terms = _terms(context)
    authority_terms = _terms(higher_authority_text)
    if authority_terms:
        return []
    candidates = []
    for habit in list_habits():
        if habit.confidence is not Confidence.HIGH or habit.injection_policy is InjectionPolicy.MANUAL_ONLY:
            continue
        if habit.review_after and habit.review_after < date.today().isoformat():
            continue
        if habit.not_applies_to and context_terms.intersection(habit.not_applies_to):
            continue
        if habit.applies_to and not context_terms.intersection(habit.applies_to):
            continue
        habit_terms = _terms(habit.statement)
        if authority_terms and len(habit_terms.intersection(authority_terms)) >= 3:
            continue
        score = _score_habit(habit, context_terms)
        if score > 0:
            candidates.append(HabitSearchResult(habit=habit, score=score))
    ranked = sorted(candidates, key=lambda result: (-result.score, result.habit.last_confirmed_at, result.habit.habit_id))
    return [result.habit for result in ranked[:MAX_INJECTED_HABITS]]


def _select_remindable(context: str, higher_authority_text: str) -> list[Habit]:
    context_terms = _terms(context)
    if not context_terms or higher_authority_text:
        return []
    candidates = []
    for habit in list_habits():
        if habit.confidence is not Confidence.HIGH or habit.injection_policy is not InjectionPolicy.PROMPT_OK_WHEN_SUPPORTED:
            continue
        if habit.review_after and habit.review_after < date.today().isoformat():
            continue
        # not_applies_to stays a HARD exclusion; higher_authority already handled above.
        if habit.not_applies_to and context_terms.intersection(habit.not_applies_to):
            continue
        # applies_to is no longer a hard filter (it killed all Chinese contexts); it is
        # now a strong boost inside the weighted relevance floor, so a directly relevant
        # habit surfaces while an unrelated/untagged one still stays silent.
        score = _prompt_relevance(habit, context_terms)
        if score >= _PROMPT_RELEVANCE_FLOOR:
            candidates.append(HabitSearchResult(habit=habit, score=score))
    ranked = sorted(candidates, key=lambda result: (-result.score, result.habit.last_confirmed_at, result.habit.habit_id))
    return [result.habit for result in ranked[:MAX_INJECTED_HABITS]]


def _looks_like_habit_intent(context: str) -> bool:
    return _DURABLE_PREFERENCE_RE.search(context) is not None and not _is_noisy_habit_candidate(context)


def _is_noisy_habit_candidate(context: str) -> bool:
    return (
        _AGENT_PROMPT_PREFIX_RE.search(context) is not None
        or _NOISY_HABIT_DISCUSSION_RE.search(context) is not None
        or _ONE_OFF_WORK_RE.search(context) is not None
    )


def _append_status_event(habit_id: str, status: HabitStatus) -> None:
    ids = {habit.habit_id for habit in list_habits(status=None)}
    if habit_id not in ids:
        raise InvalidHabitError(f"unknown habit id: {habit_id}")
    _append_event({"event": "status", "habit_id": habit_id, "status": status.value, "created_at": _now()})


def _replay_habits() -> list[Habit]:
    habits: dict[str, Habit] = {}
    for event in _read_events():
        if event.get("event") == "add":
            try:
                habit = _parse_habit(event)
            except (KeyError, InvalidHabitError, AttributeError, TypeError):
                continue
            if habit.status is not HabitStatus.DELETED:
                habits[habit.habit_id] = habit
        elif event.get("event") == "status":
            habit_id = event.get("habit_id", "")
            if habit_id in habits:
                try:
                    status = _parse_enum(HabitStatus, event.get("status", ""), "status")
                except InvalidHabitError:
                    continue
                habits[habit_id] = _replace_status(habits[habit_id], status)
    return list(habits.values())


def _replace_status(habit: Habit, status: HabitStatus) -> Habit:
    data = asdict(habit)
    data["status"] = status
    return Habit(**data)


def _parse_habit(event: HabitEvent) -> Habit:
    return Habit(
        habit_id=event["habit_id"],
        scope="user",
        habit_type=_parse_enum(HabitType, event["habit_type"], "habit_type"),
        statement=_single_line(event["statement"]),
        source_kind=event["source_kind"],
        source_refs=tuple(event.get("source_refs", [])),
        confidence=_parse_enum(Confidence, event["confidence"], "confidence"),
        status=_parse_enum(HabitStatus, event["status"], "status"),
        applies_to=_string_tuple(event.get("applies_to", [])),
        not_applies_to=_string_tuple(event.get("not_applies_to", [])),
        last_confirmed_at=event["last_confirmed_at"],
        review_after=event.get("review_after"),
        injection_policy=_parse_enum(InjectionPolicy, event["injection_policy"], "injection_policy"),
        superseded_by=event.get("superseded_by"),
    )


def _habit_to_event(habit: Habit, event: str) -> HabitEvent:
    return {
        "event": event,
        "habit_id": habit.habit_id,
        "scope": habit.scope,
        "habit_type": habit.habit_type.value,
        "statement": habit.statement,
        "source_kind": habit.source_kind,
        "source_refs": list(habit.source_refs),
        "confidence": habit.confidence.value,
        "status": habit.status.value,
        "applies_to": list(habit.applies_to),
        "not_applies_to": list(habit.not_applies_to),
        "last_confirmed_at": habit.last_confirmed_at,
        "review_after": habit.review_after,
        "injection_policy": habit.injection_policy.value,
        "superseded_by": habit.superseded_by,
        "created_at": _now(),
    }


def _read_events() -> list[HabitEvent]:
    path = user_habit_home() / HABITS_FILE
    if not path.is_file():
        return []
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                events.append(parsed)
    return events


def _append_event(event: HabitEvent) -> None:
    home = user_habit_home()
    home.mkdir(parents=True, exist_ok=True)
    with (home / HABITS_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _write_events(events: list[HabitEvent]) -> None:
    home = user_habit_home()
    home.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events)
    (home / HABITS_FILE).write_text(text, encoding="utf-8")


def _log_injection(injected_ids: list[str], abstention_reason: str | None) -> None:
    home = user_habit_home()
    home.mkdir(parents=True, exist_ok=True)
    path = home / INJECTION_LOG_FILE
    entry = {"created_at": _now(), "injected_ids": injected_ids, "abstention_reason": abstention_reason}
    existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    existing.append(json.dumps(entry, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(existing[-MAX_LOG_EVENTS:]) + "\n", encoding="utf-8")


def _parse_enum(enum_type: type[EnumValue], value: EnumValue | str, field: str) -> EnumValue:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except ValueError as exc:
        raise InvalidHabitError(f"invalid {field}: {value}") from exc


def _single_line(value: str) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= MAX_STATEMENT_CHARS:
        return normalized
    return normalized[: MAX_STATEMENT_CHARS - 3].rstrip() + "..."


def _string_tuple(values: list[str]) -> tuple[str, ...]:
    return tuple(_single_line(value).lower() for value in values)


# CJK unified ideographs (plus common extension-A). Chinese has no whitespace word
# boundaries, so re.findall(r"[\w-]+") collapses a whole run into ONE token that can
# only match another identical run. We additionally emit per-character and adjacent
# bigram tokens so a Chinese prompt can intersect Chinese habit statements/tags the
# way English word tokens already do.
_CJK_RE: Final = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def _cjk_grams(value: str) -> set[str]:
    grams: set[str] = set()
    for run in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", value):
        for idx, ch in enumerate(run):
            grams.add(ch)
            if idx + 1 < len(run):
                grams.add(run[idx : idx + 2])
    return grams


def _terms(value: str) -> set[str]:
    terms: set[str] = set()
    for term in re.findall(r"[\w-]+", value):
        if not term.strip():
            continue
        if _CJK_RE.search(term):
            # A mixed run like "abc中文" tokenizes as one blob that only matches an
            # identical blob. Split it: keep the ASCII/latin sub-runs as real tokens
            # (so English applies_to tags still match) and drop the CJK blob itself
            # (CJK chars/bigrams are emitted separately by _cjk_grams below).
            for ascii_run in re.findall(r"[0-9a-zA-Z_-]+", term):
                terms.add(ascii_run.lower())
        else:
            terms.add(term.lower())
    return terms | _cjk_grams(value)


def _score_habit(habit: Habit, terms: set[str]) -> int:
    haystack = _terms(" ".join((habit.statement, habit.habit_type.value, *habit.applies_to)))
    return len(haystack.intersection(terms))


# Prompt-time relevance floor. Unlike the recall path (score floor 12 on a different
# scale), habit statements are short, so we use a small weighted score: an explicit
# applies_to match is a strong signal (+3), and distinct STRONG statement/type overlaps
# add +1 each (capped). A "strong" overlap is a multi-character token (a CJK bigram or
# an ASCII word), NOT a single CJK character — common function characters like 我/的 must
# not qualify an unrelated habit. A habit qualifies only when it either matched an
# applies_to tag OR cleared the floor via >=2 distinct STRONG overlaps. This fixes
# "never injects for Chinese" without letting an unrelated/untagged habit inject on
# every Chinese prompt via shared function characters.
#
# Floor is 2 so that exactly two STRONG overlaps (e.g. bigrams 回复+简洁) qualify a
# legitimate untagged habit — consistent with _MIN_STRONG_OVERLAPS. An applies_to tag
# match adds +3 and always clears the floor on its own.
_PROMPT_RELEVANCE_FLOOR: Final = 2
_APPLIES_TO_BOOST: Final = 3
_MAX_GENERIC_OVERLAP: Final = 3
_MIN_STRONG_OVERLAPS: Final = 2


def _is_strong_token(token: str) -> bool:
    # Multi-character tokens carry real signal; a single character (esp. a common CJK
    # function char) is too weak to establish relevance on its own.
    return len(token) >= 2


def _prompt_relevance(habit: Habit, context_terms: set[str]) -> int:
    applies_match = bool(habit.applies_to and context_terms.intersection(habit.applies_to))
    generic = _terms(" ".join((habit.statement, habit.habit_type.value)))
    strong_overlap = sum(1 for token in generic.intersection(context_terms) if _is_strong_token(token))
    score = (_APPLIES_TO_BOOST if applies_match else 0) + min(strong_overlap, _MAX_GENERIC_OVERLAP)
    # Untagged/non-tag-matching habits must clear the floor on STRONG overlap alone;
    # a single strong token (or only weak single-char overlaps) is never enough.
    if not applies_match and strong_overlap < _MIN_STRONG_OVERLAPS:
        return 0
    return score


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _habit_intent_path() -> Path:
    # One level above user-habits/ so it sits at the SyberMem user home root.
    return user_habit_home().parent / HABIT_INTENT_FILE


def _classify_habit_type(text: str) -> str:
    terms = _terms(text)
    lowered = text.lower()
    for habit_type, hints in HABIT_TYPE_HINTS:
        for hint in hints:
            # ASCII single-word hints match a tokenized term; multi-word and CJK
            # hints match as a substring (CJK has no term boundaries under _terms).
            if hint in terms or (not hint.isascii() and hint in lowered) or (" " in hint and hint in lowered):
                return habit_type
    return "workflow"


def _hint_hit(text: str, hints: tuple[str, ...]) -> bool:
    terms = _terms(text)
    lowered = text.lower()
    for hint in hints:
        if hint in terms or (not hint.isascii() and hint in text) or (" " in hint and hint in lowered):
            return True
    return False


def _classify_scope(text: str) -> str:
    """Suggest where a candidate preference belongs: user habit vs project record.

    Returns "user", "project", or "ambiguous". This is only a suggestion surfaced
    to the user at confirmation time — the user always decides. When both or neither
    signal is present we return "ambiguous" so the confirm step asks one question
    instead of guessing wrong.
    """
    project = _hint_hit(text, PROJECT_SCOPE_HINTS)
    user = _hint_hit(text, USER_SCOPE_HINTS)
    # An explicit "this repo / this project" phrase is a strong scope marker and wins
    # over a bare durability word like "always"/"总是" (which only signals the
    # preference is standing, not WHERE it belongs). A first-person marker ("my"/"我")
    # is the one user signal strong enough to keep it ambiguous against a project hint.
    if project:
        first_person = _hint_hit(text, ("my", "i prefer", "i like", "我", "我的"))
        return "ambiguous" if first_person else "project"
    if user:
        return "user"
    return "ambiguous"


def classify_habit_intent(text: str) -> dict | None:
    """Return a candidate-only habit-intent classification, or None.

    A match means the prompt LOOKS like a durable personal preference worth
    remembering. It is deliberately candidate-only: the returned metadata never
    contains an active habit and callers must not auto-create one. Blocked
    (secret / injection) text is never classified.
    """
    if not text or _BLOCKED_INTENT_RE.search(text):
        return None
    if not _looks_like_habit_intent(text):
        return None
    return {
        "habit_intent": True,
        "candidate_only": True,
        "action": "/sybermem-habit",
        # Stable id so a specific candidate can be selected/discarded from the list.
        "candidate_id": f"cand-{uuid4().hex[:8]}",
        "habit_type": _classify_habit_type(text),
        # Suggested routing for the confirm step: "user" (cross-project habit),
        # "project" (belongs in a /sybermem-record decision/requirement), or
        # "ambiguous" (ask the user). Never auto-routes; suggestion only.
        "suggested_scope": _classify_scope(text),
        # Bounded, blocklist-filtered summary of the user's own words so the confirm step
        # can propose a statement instead of guessing. Already past _BLOCKED_INTENT_RE
        # above (secrets/injection are never classified), and bounded to a short prefix.
        "summary": _candidate_summary(text),
        "reason": "prompt looks like a reusable user preference",
        "created_at": _now(),
    }


def _candidate_summary(text: str) -> str:
    """Bounded, whitespace-compacted prompt summary for a habit candidate.

    Mirrors record_intent's summary contract: a short, compacted prefix of the triggering
    prompt (never the full/unbounded prompt). Callers only reach this AFTER the secret /
    prompt-injection blocklist has rejected sensitive text, so this stores a filtered,
    bounded fragment of the user's own words — the documented exception to "no raw prompt".
    """
    compact = " ".join(text.split())
    return compact[:MAX_CANDIDATE_SUMMARY_CHARS]


def _parse_candidate_created(candidate: dict) -> datetime | None:
    raw = candidate.get("created_at")
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _is_expired_candidate(candidate: dict, now: datetime) -> bool:
    created = _parse_candidate_created(candidate)
    if created is None:
        return False  # keep undated candidates rather than silently dropping them
    return now - created > timedelta(days=HABIT_CANDIDATE_EXPIRY_DAYS)


def _read_candidate_list() -> list[dict]:
    """Read the candidate list, tolerating the legacy single-object format.

    Old installs wrote a single candidate object to .habit-intent.json; new installs write
    {"candidates": [...]}. We accept both so upgrading users keep their pending candidate.
    Expired and malformed entries are pruned on read.
    """
    path = _habit_intent_path()
    if not path.is_file():
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(parsed, dict) and isinstance(parsed.get("candidates"), list):
        raw_candidates = parsed["candidates"]
    elif isinstance(parsed, dict) and parsed.get("habit_intent"):
        raw_candidates = [parsed]  # legacy single-object format
    else:
        return []
    now = datetime.now(timezone.utc)
    return [c for c in raw_candidates if isinstance(c, dict) and not _is_expired_candidate(c, now)]


def _write_candidate_list(candidates: list[dict]) -> bool:
    path = _habit_intent_path()
    try:
        if not candidates:
            if path.is_file():
                path.unlink()
            return True
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"candidates": candidates[:MAX_HABIT_CANDIDATES]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return True
    except OSError:
        return False


def capture_habit_intent(text: str) -> dict | None:
    """Append a candidate-only habit intent to the bounded user-level candidate list.

    Writes ~/.sybermem/.habit-intent.json (or SYBERMEM_HOME/.habit-intent.json) as
    {"candidates": [...]}. Never creates an active habit. Keeps at most MAX_HABIT_CANDIDATES
    most-recent candidates, dedupes by summary (refreshing the existing one instead of piling
    up duplicates), and prunes expired entries. Returns the captured candidate metadata, or
    None when the prompt does not look like a durable preference. Fail-open: a write error
    yields None rather than raising into the caller's hot path.
    """
    metadata = classify_habit_intent(text)
    if metadata is None:
        return None
    try:
        candidates = _read_candidate_list()
        summary = metadata.get("summary", "")
        # Dedupe by summary: drop an existing candidate with the same summary so a repeated
        # phrase refreshes (moves to newest) rather than accumulating duplicates.
        if summary:
            candidates = [c for c in candidates if c.get("summary") != summary]
        candidates.append(metadata)
        # Newest-last in storage; keep only the most recent MAX_HABIT_CANDIDATES.
        candidates = candidates[-MAX_HABIT_CANDIDATES:]
        if not _write_candidate_list(candidates):
            return None
    except OSError:
        return None
    return metadata


def list_habit_candidates() -> list[dict]:
    """Return pending habit candidates, newest first, expired entries pruned."""
    return list(reversed(_read_candidate_list()))


def read_habit_intent() -> dict | None:
    """Read the most recent pending candidate, or None. Backward-compatible helper.

    Retained so existing single-candidate callers (awareness, reminder) keep working after
    the migration to a bounded list. Returns the newest candidate.
    """
    candidates = list_habit_candidates()
    return candidates[0] if candidates else None


def discard_habit_candidate(candidate_id: str) -> bool:
    """Discard ONE pending candidate by id. Returns True when one was removed."""
    if not candidate_id:
        return False
    candidates = _read_candidate_list()
    remaining = [c for c in candidates if c.get("candidate_id") != candidate_id]
    if len(remaining) == len(candidates):
        return False
    _write_candidate_list(remaining)
    return True


def clear_habit_intent() -> bool:
    """Delete ALL pending candidates (the whole intent file). Returns True if anything existed."""
    path = _habit_intent_path()
    existed = bool(_read_candidate_list()) or path.is_file()
    _write_candidate_list([])
    return existed


def habit_awareness_summary() -> dict:
    """Return a bounded, privacy-safe snapshot of user-habit state for hosts.

    Surfaces habit presence in awareness surfaces (startup context, memory
    stats, resume) WITHOUT exposing statements on the hot path: only counts, a
    type distribution, the most recent confirmation date, and whether a
    candidate intent is pending.
    """
    active = list_habits(status=HabitStatus.ACTIVE)
    by_type: dict[str, int] = {}
    latest_confirmed = ""
    for habit in active:
        by_type[habit.habit_type.value] = by_type.get(habit.habit_type.value, 0) + 1
        if habit.last_confirmed_at > latest_confirmed:
            latest_confirmed = habit.last_confirmed_at
    candidates = list_habit_candidates()
    return {
        "active": len(active),
        "by_type": dict(sorted(by_type.items())),
        "latest_confirmed_at": latest_confirmed,
        "pending_intent": len(candidates) > 0,
        "pending_count": len(candidates),
    }


def pending_habit_reminder() -> dict | None:
    """Return a bounded, privacy-safe pending-candidate reminder, or None.

    A passively captured candidate (`.habit-intent.json`) is NOT an active habit and
    is never injected on its own — the user must confirm it via `/sybermem-habit`.
    The old surfacing (a per-key throttled toast) was effectively swallowed after its
    first fire, so users never learned a candidate was waiting and thus never
    confirmed one, leaving habit injection permanently silent. This helper is the
    single source of truth every host uses to surface "you have a habit candidate to
    confirm" on a durable, non-throttled surface (SessionStart / startup context).

    Returns a dict with a short human `message`, the number of pending candidates, and the
    newest candidate's `scope` / `created_at` (so hosts can dedupe by the candidate set).
    Only exposes the bounded candidate summary, never the raw prompt. None when nothing is
    pending.
    """
    candidates = list_habit_candidates()
    if not candidates:
        return None
    newest = candidates[0]
    count = len(candidates)
    scope = str(newest.get("suggested_scope", "") or "").strip()
    created_at = str(newest.get("created_at", "") or "").strip()
    summary = str(newest.get("summary", "") or "").strip()
    quoted = f' ("{summary}")' if summary else ""
    plural = "s" if count > 1 else ""
    lead = f"SyberMem has {count} habit candidate{plural} awaiting confirmation" if count > 1 else "SyberMem captured a reusable preference"
    if scope == "project" and count == 1:
        message = (
            f"{lead}{quoted}. Confirm it as a decision/requirement with /sybermem-record, "
            "or as a personal habit with /sybermem-habit."
        )
    elif scope == "user" and count == 1:
        message = f"{lead}{quoted}. Confirm it with /sybermem-habit so it can be injected in future sessions."
    else:
        message = f"{lead}{quoted}. Review and confirm or discard with /sybermem-habit."
    return {
        "pending": True,
        "count": count,
        "scope": scope or "ambiguous",
        "created_at": created_at,
        "message": message,
        # Stable fingerprint of the whole candidate set for host-side per-session dedup.
        "fingerprint": "|".join(str(c.get("candidate_id") or c.get("created_at") or "") for c in candidates),
    }
