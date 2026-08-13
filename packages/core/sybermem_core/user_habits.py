from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, timezone
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
MAX_INJECTED_HABITS: Final = 3
MAX_LOG_EVENTS: Final = 200
MAX_STATEMENT_CHARS: Final = 300
HABIT_INTENT_TERMS: Final = {
    "always",
    "habit",
    "preference",
    "prefer",
    "remember",
    "以后",
    "偏好",
    "习惯",
    "记住",
}


def user_habit_home() -> Path:
    home = os.environ.get("SYBERMEM_HOME")
    base = Path(home).expanduser() if home else Path.home() / ".sybermem"
    return base / HABIT_DIR


def add_habit(
    *,
    statement: str,
    habit_type: HabitType | str,
    applies_to: tuple[str, ...] = (),
    not_applies_to: tuple[str, ...] = (),
    injection_policy: InjectionPolicy | str = InjectionPolicy.COMPACTION_OK,
    source_ref: str | None = None,
) -> Habit:
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
        if habit.not_applies_to and context_terms.intersection(habit.not_applies_to):
            continue
        if habit.applies_to and not context_terms.intersection(habit.applies_to):
            continue
        score = _score_habit(habit, context_terms)
        if score > 0:
            candidates.append(HabitSearchResult(habit=habit, score=score))
    ranked = sorted(candidates, key=lambda result: (-result.score, result.habit.last_confirmed_at, result.habit.habit_id))
    return [result.habit for result in ranked[:MAX_INJECTED_HABITS]]


def _looks_like_habit_intent(context: str) -> bool:
    terms = _terms(context)
    if terms.intersection(HABIT_INTENT_TERMS):
        return True
    return any(term in context for term in HABIT_INTENT_TERMS if not term.isascii())


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


def _terms(value: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[\w-]+", value) if term.strip()}


def _score_habit(habit: Habit, terms: set[str]) -> int:
    haystack = _terms(" ".join((habit.statement, habit.habit_type.value, *habit.applies_to)))
    return len(haystack.intersection(terms))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
