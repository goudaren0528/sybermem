from __future__ import annotations

from pathlib import Path
import re
from typing import Final, Literal, TypedDict

from .records import iter_record_files, parse_project_yaml, parse_record_file


RecordClassification = Literal["change", "decision", "requirement", "bug", "digest", "no_write", "defer", "blocked"]


class RecordCandidate(TypedDict, total=False):
    classification: RecordClassification
    action: str
    reason: str
    summary: str
    duplicate_record_id: str


WRITE_CLASSIFICATIONS: Final[set[RecordClassification]] = {"change", "decision", "requirement", "bug"}
TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"[a-z0-9][a-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", re.IGNORECASE)
SECRET_RE: Final[re.Pattern[str]] = re.compile(
    r"(password\s*=|api[_-]?key\s*=|secret\s*=|token\s*=|bearer\s+[a-z0-9._-]+|begin\s+(?:rsa\s+)?private\s+key)",
    re.IGNORECASE,
)
CONTROL_RE: Final[re.Pattern[str]] = re.compile(
    r"(ignore\s+(?:all\s+)?previous|system\s+prompt|developer\s+message|<\/?(?:system|developer|tool)[^>]*>|/sybermem-record\s+--)",
    re.IGNORECASE,
)
NO_WRITE_RE: Final[re.Pattern[str]] = re.compile(
    r"(do\s+not\s+record|don'?t\s+record|no\s+record|without\s+recording|不要记录|不用记录|别记录|不要沉淀|无需记录)",
    re.IGNORECASE,
)
DEFER_RE: Final[re.Pattern[str]] = re.compile(
    r"(explor(?:e|atory|ation)|investigat(?:e|ion)|brainstorm|draft|wip|not\s+final|scratch|maybe|先看看|探索|讨论|草稿|未定|不(?:要)?现在沉淀)",
    re.IGNORECASE,
)
NO_OP_RE: Final[re.Pattern[str]] = re.compile(
    r"(formatting[-\s]?only|comment[-\s]?only|no\s+functional\s+impact|只是?格式|仅(?:注释|格式)|无功能影响)",
    re.IGNORECASE,
)
CLASSIFICATION_PATTERNS: Final[tuple[tuple[RecordClassification, re.Pattern[str]], ...]] = (
    ("digest", re.compile(r"(digest|phase\s+summary|theme\s+summary|阶段.*(?:沉淀|总结)|主题.*(?:沉淀|总结))", re.IGNORECASE)),
    ("bug", re.compile(r"(bug|fix(?:ed)?|crash|error|regression|root\s+cause|修复|缺陷|故障|报错)", re.IGNORECASE)),
    ("decision", re.compile(r"(decision|decide[sd]?|chose|chosen|adopt(?:ed)?|architecture|trade[-\s]?off|option|决策|决定|架构|取舍|选择)", re.IGNORECASE)),
    ("requirement", re.compile(r"(requirement|must|should|need(?:s|ed)?|spec|acceptance|用户.*(?:需要|希望)|需求|必须|应该)", re.IGNORECASE)),
    ("change", re.compile(r"(record|记录|沉淀|implemented|changed|added|updated|built|完成|实现|新增|改动)", re.IGNORECASE)),
)
STOP_TOKENS: Final[set[str]] = {
    "record",
    "this",
    "that",
    "the",
    "and",
    "with",
    "for",
    "一下",
    "记录",
    "这轮",
    "这次",
}


def _summary(text: str) -> str:
    compact = " ".join(text.split())
    return compact[:160]


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOP_TOKENS}


def _duplicate_record_id(root: Path, text: str) -> str:
    tokens = _tokens(text)
    if len(tokens) < 3:
        return ""
    meta = parse_project_yaml(root)
    best_id = ""
    best_score = 0.0
    for path in iter_record_files(root):
        record = parse_record_file(path, meta.get("project_id", ""), meta.get("slug", root.name))
        if record.get("type") not in {"change", "decision", "requirement", "bug"}:
            continue
        record_tokens = _tokens(f"{record.get('title', '')} {record.get('content', '')}")
        if not record_tokens:
            continue
        score = len(tokens & record_tokens) / len(tokens)
        if score > best_score:
            best_score = score
            best_id = record.get("record_id", "")
    return best_id if best_score >= 0.6 else ""


def _base_classification(text: str) -> RecordClassification:
    for classification, pattern in CLASSIFICATION_PATTERNS:
        if pattern.search(text):
            return classification
    return "defer"


def route_record_candidate(candidate: RecordCandidate) -> dict[str, str]:
    classification = candidate.get("classification", "defer")
    reason = candidate.get("reason", "No stable record action is available yet.")
    match classification:
        case "change" | "decision" | "requirement" | "bug":
            return {"action": "/sybermem-record", "reason": reason}
        case "digest":
            return {"action": "/sybermem-digest", "reason": reason}
        case "no_write":
            return {"action": "/sybermem-summary", "reason": reason}
        case "defer":
            return {"action": "/sybermem-summary", "reason": reason}
        case "blocked":
            return {"action": "blocked", "reason": reason}


def classify_record_intent(root: Path, text: str) -> RecordCandidate:
    if SECRET_RE.search(text) or CONTROL_RE.search(text):
        return {
            "classification": "blocked",
            "action": "blocked",
            "reason": "Sensitive or untrusted control-like input was blocked; no record candidate was stored.",
        }
    if NO_WRITE_RE.search(text) or NO_OP_RE.search(text):
        return {
            "classification": "no_write",
            "action": "/sybermem-summary",
            "reason": "The prompt explicitly says not to create a durable SyberMem record.",
            "summary": _summary(text),
        }
    if DEFER_RE.search(text):
        return {
            "classification": "defer",
            "action": "/sybermem-summary",
            "reason": "The prompt looks exploratory or unstable, so recording is deferred until the work settles.",
            "summary": _summary(text),
        }

    classification = _base_classification(text)
    if classification in WRITE_CLASSIFICATIONS:
        duplicate = _duplicate_record_id(root, text)
        if duplicate:
            return {
                "classification": "no_write",
                "action": "/sybermem-summary",
                "reason": f"A likely duplicate record already exists ({duplicate}); review current memory instead of writing another record.",
                "summary": _summary(text),
                "duplicate_record_id": duplicate,
            }

    candidate: RecordCandidate = {
        "classification": classification,
        "summary": _summary(text),
    }
    routed = route_record_candidate({**candidate, "reason": _reason_for(classification)})
    candidate["action"] = routed["action"]
    candidate["reason"] = routed["reason"]
    return candidate


def _reason_for(classification: RecordClassification) -> str:
    match classification:
        case "change":
            return "The prompt asks to preserve completed work as a durable change record."
        case "decision":
            return "The prompt contains a decision or architecture rationale that should be recorded deliberately."
        case "requirement":
            return "The prompt captures a requirement that should be preserved as project memory."
        case "bug":
            return "The prompt describes a bug or fix whose root cause and verification should be recorded."
        case "digest":
            return "The prompt asks for a phase or theme digest rather than a single record."
        case "no_write":
            return "The prompt explicitly opts out of durable record creation."
        case "defer":
            return "The prompt is exploratory or unstable, so recording should wait."
        case "blocked":
            return "Sensitive or untrusted control-like input was blocked."
