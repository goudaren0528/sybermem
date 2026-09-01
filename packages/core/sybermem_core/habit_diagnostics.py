from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final, Literal, TypedDict

from sybermem_core.user_habit_model import Confidence, Habit, HabitSearchResult, HabitStatus, InjectionPolicy


PromptHabitDecision = Literal["selected", "not_selected", "excluded"]


class PromptHabitDiagnostic(TypedDict):
    habit_id: str
    habit_type: str
    status: str
    confidence: str
    injection_policy: str
    review_after: str | None
    applies_to: list[str]
    not_applies_to: list[str]
    matched_applies_to: list[str]
    matched_not_applies_to: list[str]
    score: int
    floor: int
    strong_overlap_count: int
    decision: PromptHabitDecision
    reasons: list[str]


class PromptHabitEvaluation(TypedDict):
    status: str
    delivery: str
    context_terms_count: int
    active_habits: int
    evaluated: int
    selected: int
    floor: int
    pending_candidates: int
    context_summary: str
    habits: list[PromptHabitDiagnostic]


@dataclass(frozen=True, slots=True)
class PromptHabitContext:
    terms: frozenset[str]
    blocked_by_authority: bool


EXCLUSION_REASONS: Final = {
    "empty_context",
    "blocked_by_higher_authority",
    "excluded_status_not_active",
    "excluded_confidence_not_high",
    "excluded_policy_not_prompt_ok",
    "excluded_review_expired",
    "excluded_not_applies_to_match",
}


def evaluate_prompt_habits(*, context: str, higher_authority_text: str = "") -> PromptHabitEvaluation:
    """Explain prompt-time user-habit reminder selection without side effects."""
    from sybermem_core import user_habits

    # Same-package coupling is intentional: diagnostics must reuse production scoring
    # helpers so dry-runs and real prompt-time reminders cannot drift.
    prompt = PromptHabitContext(terms=frozenset(user_habits._terms(context)), blocked_by_authority=bool(higher_authority_text))
    habits = [habit for habit in user_habits.list_habits(status=None) if habit.status is not HabitStatus.DELETED]
    rows = [_diagnose_prompt_habit(habit, prompt) for habit in habits]
    selected_ids = _selected_prompt_habit_ids(rows, habits)
    explained: list[PromptHabitDiagnostic] = [
        {**row, "decision": "selected", "reasons": [*row["reasons"], "selected"]}
        if row["habit_id"] in selected_ids else row
        for row in rows
    ]
    return {
        "status": "ok",
        "delivery": "prompt-time",
        "context_terms_count": len(prompt.terms),
        "active_habits": sum(1 for habit in habits if habit.status is HabitStatus.ACTIVE),
        "evaluated": len(habits),
        "selected": len(selected_ids),
        "floor": user_habits._PROMPT_RELEVANCE_FLOOR,
        "pending_candidates": len(user_habits.list_habit_candidates()),
        "context_summary": user_habits._diagnostic_context_summary(context),
        "habits": explained,
    }


def _diagnose_prompt_habit(habit: Habit, prompt: PromptHabitContext) -> PromptHabitDiagnostic:
    from sybermem_core import user_habits

    matched_applies = sorted(set(habit.applies_to).intersection(prompt.terms))
    matched_not_applies = sorted(set(habit.not_applies_to).intersection(prompt.terms))
    strong_overlap = user_habits._prompt_strong_overlap(habit, prompt.terms)
    score = user_habits._prompt_relevance(habit, prompt.terms)
    reasons = _prompt_exclusion_reasons(habit, prompt, matched_applies, matched_not_applies, score)
    return {
        "habit_id": habit.habit_id,
        "habit_type": habit.habit_type.value,
        "status": habit.status.value,
        "confidence": habit.confidence.value,
        "injection_policy": habit.injection_policy.value,
        "review_after": habit.review_after,
        "applies_to": list(habit.applies_to),
        "not_applies_to": list(habit.not_applies_to),
        "matched_applies_to": matched_applies,
        "matched_not_applies_to": matched_not_applies,
        "score": score,
        "floor": user_habits._PROMPT_RELEVANCE_FLOOR,
        "strong_overlap_count": strong_overlap,
        "decision": _prompt_decision(reasons),
        "reasons": reasons,
    }


def _prompt_exclusion_reasons(
    habit: Habit,
    prompt: PromptHabitContext,
    matched_applies: list[str],
    matched_not_applies: list[str],
    score: int,
) -> list[str]:
    from sybermem_core import user_habits

    reasons: list[str] = []
    if not prompt.terms:
        reasons.append("empty_context")
    if prompt.blocked_by_authority:
        reasons.append("blocked_by_higher_authority")
    if habit.status is not HabitStatus.ACTIVE:
        reasons.append("excluded_status_not_active")
    if habit.confidence is not Confidence.HIGH:
        reasons.append("excluded_confidence_not_high")
    if habit.injection_policy is not InjectionPolicy.PROMPT_OK_WHEN_SUPPORTED:
        reasons.append("excluded_policy_not_prompt_ok")
    if habit.review_after and habit.review_after < date.today().isoformat():
        reasons.append("excluded_review_expired")
    if matched_not_applies:
        reasons.append("excluded_not_applies_to_match")
    if matched_applies:
        reasons.append("applies_to_match")
    else:
        reasons.append("no_applies_to_match")
    if reasons in (["no_applies_to_match"], ["applies_to_match"]):
        if score >= user_habits._PROMPT_RELEVANCE_FLOOR:
            reasons.append("score_met_floor")
        else:
            reasons.append("score_below_floor")
    elif score < user_habits._PROMPT_RELEVANCE_FLOOR:
        reasons.append("score_below_floor")
    return reasons


def _prompt_decision(reasons: list[str]) -> PromptHabitDecision:
    return "excluded" if EXCLUSION_REASONS.intersection(reasons) else "not_selected"


def _selected_prompt_habit_ids(rows: list[PromptHabitDiagnostic], habits: list[Habit]) -> set[str]:
    from sybermem_core import user_habits

    habit_by_id = {habit.habit_id: habit for habit in habits}
    eligible = [
        HabitSearchResult(habit=habit_by_id[row["habit_id"]], score=row["score"])
        for row in rows
        if row["habit_id"] in habit_by_id and _is_prompt_selected(row)
    ]
    ranked = sorted(eligible, key=lambda result: (-result.score, result.habit.last_confirmed_at, result.habit.habit_id))
    return {result.habit.habit_id for result in ranked[: user_habits.MAX_INJECTED_HABITS]}


def _is_prompt_selected(row: PromptHabitDiagnostic) -> bool:
    return row["decision"] == "not_selected" and row["score"] >= row["floor"] and "score_met_floor" in row["reasons"]
