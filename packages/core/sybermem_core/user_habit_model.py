from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, NewType, TypedDict


HabitId = NewType("HabitId", str)
Scope = Literal["user"]


class InvalidHabitError(Exception):
    """Raised when habit data cannot be parsed into the supported schema."""


class HabitType(str, Enum):
    WORKFLOW = "workflow"
    STYLE = "style"
    TOOLING = "tooling"
    COMMUNICATION = "communication"
    REVIEW = "review"
    AVOIDANCE = "avoidance"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HabitStatus(str, Enum):
    ACTIVE = "active"
    DRAFT = "draft"
    PAUSED = "paused"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DELETED = "deleted"


class InjectionPolicy(str, Enum):
    MANUAL_ONLY = "manual_only"
    COMPACTION_OK = "compaction_ok"
    PROMPT_OK_WHEN_SUPPORTED = "prompt_ok_when_supported"


class SourceRef(TypedDict):
    kind: str
    ref: str


class HabitEvent(TypedDict, total=False):
    event: str
    habit_id: str
    scope: Scope
    habit_type: str
    statement: str
    source_kind: str
    source_refs: list[SourceRef]
    confidence: str
    status: str
    applies_to: list[str]
    not_applies_to: list[str]
    last_confirmed_at: str
    review_after: str | None
    injection_policy: str
    superseded_by: str | None
    created_at: str


@dataclass(frozen=True, slots=True)
class Habit:
    habit_id: str
    scope: Scope
    habit_type: HabitType
    statement: str
    source_kind: str
    source_refs: tuple[SourceRef, ...]
    confidence: Confidence
    status: HabitStatus
    applies_to: tuple[str, ...]
    not_applies_to: tuple[str, ...]
    last_confirmed_at: str
    review_after: str | None
    injection_policy: InjectionPolicy
    superseded_by: str | None


@dataclass(frozen=True, slots=True)
class HabitSearchResult:
    habit: Habit
    score: int
