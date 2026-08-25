from __future__ import annotations

from dataclasses import dataclass
import re


ASCII_STOP_TERMS = {
    "about",
    "check",
    "change",
    "for",
    "help",
    "please",
    "project",
    "record",
    "records",
    "show",
    "task",
    "tasks",
    "the",
}
CJK_STOP_CHARS = frozenset("的一是在和了与及或并应可相关")
ASCII_RE = re.compile(r"[a-zA-Z0-9_-]+")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


@dataclass(frozen=True, slots=True)
class QueryTerms:
    ascii: tuple[str, ...]
    cjk: tuple[str, ...]

    @property
    def all(self) -> tuple[str, ...]:
        return (*self.ascii, *self.cjk)

    @property
    def is_meaningful(self) -> bool:
        return len(self.all) >= 2


@dataclass(frozen=True, slots=True)
class OverlapScore:
    score: float
    match: str
    matched_fields: int


def query_terms(query: str) -> QueryTerms:
    ascii_terms = tuple(
        dict.fromkeys(term for term in ASCII_RE.findall(query.lower()) if len(term) >= 3 and term not in ASCII_STOP_TERMS)
    )
    cjk_terms = tuple(dict.fromkeys(term for run in CJK_RE.findall(query) for term in _cjk_terms(run)))
    return QueryTerms(ascii=ascii_terms, cjk=cjk_terms)


def fts_query(terms: QueryTerms) -> str:
    return " OR ".join(f'"{term.replace(chr(34), chr(34) * 2)}"' for term in terms.all)


def like_patterns(terms: QueryTerms) -> list[str]:
    return [f"%{term}%" for term in terms.all]


def score_row(row: dict[str, str], terms: QueryTerms) -> OverlapScore | None:
    record_id = row.get("record_id", "").lower()
    if record_id and record_id in terms.ascii:
        return OverlapScore(score=100.0, match="record-id", matched_fields=1)

    fields = {
        "title": row.get("title", "").lower(),
        "topic": row.get("topics", "").lower(),
        "relation": f"{row.get('fixes', '')} {row.get('implements', '')} {row.get('related', '')} {row.get('superseded_by', '')} {row.get('supersedes', '')}".lower(),
        "body": _body_text(row.get("content", "")).lower(),
    }
    weighted = {
        "title": _field_overlap(fields["title"], terms) * 4,
        "topic": _field_overlap(fields["topic"], terms) * 3,
        "relation": _field_overlap(fields["relation"], terms) * 3,
        "body": min(_field_overlap(fields["body"], terms), 3),
    }
    total = sum(weighted.values())
    matched_fields = sum(1 for value in weighted.values() if value)
    if total == 1 and len(terms.all) == 1 and "-" in terms.all[0]:
        return OverlapScore(score=5.0, match="keyword", matched_fields=matched_fields)
    if total < 2:
        return None
    for match in ("relation", "topic", "keyword"):
        if match == "keyword" and (weighted["title"] or weighted["body"]):
            return OverlapScore(score=float(min(total, 20)), match=match, matched_fields=matched_fields)
        if weighted.get(match, 0):
            return OverlapScore(score=float(min(total, 20)), match=match, matched_fields=matched_fields)
    return None


def _field_overlap(text: str, terms: QueryTerms) -> int:
    return sum(1 for term in terms.all if term in text)


def _body_text(content: str) -> str:
    lines = content.splitlines()
    if lines[:1] != ["---"]:
        return content
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[index + 1 :])
    return content


def _cjk_terms(run: str) -> tuple[str, ...]:
    chars = "".join(char for char in run if char not in CJK_STOP_CHARS)
    if len(chars) < 2:
        return ()
    upper = min(4, len(chars))
    return tuple(chars[index : index + size] for size in range(2, upper + 1) for index in range(0, len(chars) - size + 1))
