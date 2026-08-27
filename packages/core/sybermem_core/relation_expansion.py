from __future__ import annotations

import re
from typing import Final, TypeAlias

from .records import RECORD_ID_SUFFIX


SearchValue: TypeAlias = str | float | list[str] | dict[str, float]
SearchRow: TypeAlias = dict[str, SearchValue]

RELATION_FIELDS: Final = ("implements", "fixes", "related", "superseded_by", "supersedes")
MAX_EXPLICIT_RELATION_EXPANSIONS: Final = 20
RECORD_ID_RE: Final = re.compile(rf"(?:change|decision|requirement|bug|norm|digest)-{RECORD_ID_SUFFIX}")


def expand_typed_relations(
    all_rows: list[SearchRow],
    direct_rows: list[SearchRow],
) -> tuple[list[SearchRow], frozenset[str]]:
    """Return copied one-hop relation rows and direct row IDs they replace."""
    exact_seeds = [row for row in direct_rows if _text(row, "match") == "record-id"]
    seeds = exact_seeds or [row for row in direct_rows if _text(row, "match") == "relation"]
    if not seeds:
        return [], frozenset()

    rows_by_id = {_text(row, "record_id"): row for row in all_rows if _text(row, "record_id")}
    direct_by_id = {_text(row, "record_id"): row for row in direct_rows if _text(row, "record_id")}
    adjacency = _relation_adjacency(all_rows)
    expanded: list[SearchRow] = []
    replaced_ids: set[str] = set()

    for seed in seeds:
        seed_id = _text(seed, "record_id")
        for target_id, relation in adjacency.get(seed_id, ()):
            direct = direct_by_id.get(target_id, {})
            if (direct and _text(direct, "match") != "relation") or target_id in replaced_ids:
                continue
            target = rows_by_id.get(target_id)
            if target is None:
                continue
            copied = dict(target)
            copied["score"] = float(direct.get("score", 0.0) or 0.0)
            copied["matched_fields"] = _text(direct, "matched_fields") or "0"
            copied["expanded_from"] = seed_id
            copied["expansion_relation"] = relation
            copied["match"] = "relation-expanded"
            copied["match_reason"] = "relation-expanded"
            expanded.append(copied)
            replaced_ids.add(target_id)
            if len(expanded) >= MAX_EXPLICIT_RELATION_EXPANSIONS:
                return expanded, frozenset(replaced_ids)

    return expanded, frozenset(replaced_ids)


def _relation_adjacency(rows: list[SearchRow]) -> dict[str, list[tuple[str, str]]]:
    adjacency: dict[str, list[tuple[str, str]]] = {}
    known_ids = {_text(row, "record_id") for row in rows}
    for row in rows:
        source_id = _text(row, "record_id")
        if not source_id:
            continue
        for relation in RELATION_FIELDS:
            for target_id in RECORD_ID_RE.findall(_text(row, relation)):
                if target_id == source_id or target_id not in known_ids:
                    continue
                adjacency.setdefault(source_id, []).append((target_id, relation))
                adjacency.setdefault(target_id, []).append((source_id, relation))
    return adjacency


def _text(row: SearchRow, key: str) -> str:
    value = row.get(key, "")
    return value if isinstance(value, str) else str(value)
