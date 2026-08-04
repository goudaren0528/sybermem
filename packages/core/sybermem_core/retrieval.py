from __future__ import annotations

import re
from typing import Mapping, MutableMapping, Sequence, TypeAlias, TypedDict


RetrievalValue: TypeAlias = str | float


AUTO_TRAIL_MARKERS = (
    'Auto-record workspace file changes on stop',
    'Auto-recorded workspace file changes at session stop',
    'Auto-generated from workspace changes detected at session stop.',
)


class ContinuityMetadata(TypedDict):
    source_kind: str
    authority: str
    lifecycle: str
    freshness: str
    match_reason: str
    related_digest: str
    conflict_note: str
    summary: str


RECORD_ID_RE = re.compile(r"(?:change|decision|requirement|bug|digest)-\d{3}")


def is_auto_trail(title: str, content: str) -> bool:
    text = f'{title}\n{content}'
    return any(marker in text for marker in AUTO_TRAIL_MARKERS)


def classify_source_kind(path: str, title: str = '', content: str = '') -> str:
    normalized = path.replace('\\', '/')
    if '/digests/' in normalized or '/theme-digests/' in normalized:
        return 'digest'
    if is_auto_trail(title, content):
        return 'auto-trail'
    return 'manual'


def classify_authority(source_kind: str, title: str, content: str) -> str:
    if source_kind == 'digest':
        return 'summarized'
    if source_kind == 'auto-trail' or is_auto_trail(title, content):
        return 'evidence'
    return 'authoritative'


def classify_lifecycle(status: str, superseded_by: str, archived: bool) -> str:
    normalized = (status or '').strip().lower()
    if superseded_by:
        return 'superseded'
    if archived:
        return 'archived'
    if normalized in {'resolved', 'completed', 'done'}:
        return 'resolved'
    return 'active'


def classify_freshness(lifecycle: str) -> str:
    if lifecycle == 'active':
        return 'current'
    if lifecycle == 'conflicted':
        return 'conflicted'
    if lifecycle in {'resolved', 'superseded', 'archived'}:
        return 'historical'
    return 'stale'


def derive_continuity_metadata(
    row: Mapping[str, RetrievalValue],
    *,
    match_reason: str = '',
    related_digest: str = '',
    conflict_note: str = '',
    archived: bool = False,
) -> ContinuityMetadata:
    title = _row_text(row, 'title')
    content = _row_text(row, 'content')
    source_kind = classify_source_kind(_row_text(row, 'path'), title, content)
    authority = classify_authority(source_kind, title, content)
    is_archived = archived or '[archived]' in content
    lifecycle = classify_lifecycle(_row_text(row, 'status'), _row_text(row, 'superseded_by'), is_archived)
    return {
        'source_kind': source_kind,
        'authority': authority,
        'lifecycle': lifecycle,
        'freshness': classify_freshness(lifecycle),
        'match_reason': match_reason,
        'related_digest': related_digest,
        'conflict_note': conflict_note,
        'summary': derive_summary(content, title),
    }


def apply_successor_guidance(rows: Sequence[MutableMapping[str, RetrievalValue]], all_rows: Sequence[Mapping[str, RetrievalValue]]) -> None:
    by_id = {_row_text(row, 'record_id'): row for row in all_rows if _row_text(row, 'record_id')}
    for row in rows:
        successor_id = _successor_id(row, by_id)
        if successor_id:
            row['successor_record'] = successor_id
            row['successor_title'] = _row_text(by_id.get(successor_id, {}), 'title')
            row['current_record'] = successor_id
            row['current_guidance'] = f'Prefer successor {successor_id} for current guidance.'
            continue
        fixed_id = _first_record_id(_row_text(row, 'fixes'))
        if fixed_id and _is_current_target(row):
            row['current_record'] = _row_text(row, 'record_id')
            row['current_guidance'] = f'This record resolves {fixed_id}.'


def compact_abstention_row(query: str, candidates: Sequence[Mapping[str, RetrievalValue]]) -> dict[str, RetrievalValue]:
    if all(_row_text(row, 'authority') == 'evidence' for row in candidates):
        reason = 'only auto-trail evidence matches were found'
    elif all(_row_text(row, 'freshness') not in {'current', 'conflicted'} for row in candidates):
        reason = 'only historical or stale matches were found'
    else:
        reason = 'matches did not cross compact recall reliability threshold'
    return {'result': 'no_reliable_recall', 'reason': reason, 'query': query}


def _successor_id(row: Mapping[str, RetrievalValue], by_id: Mapping[str, Mapping[str, RetrievalValue]]) -> str:
    direct = _first_record_id(_row_text(row, 'superseded_by'))
    if direct:
        return _resolve_current_id(direct, by_id, {_row_text(row, 'record_id')})
    return _fix_successor_id(_row_text(row, 'record_id'), by_id, {_row_text(row, 'record_id')})


def _resolve_current_id(record_id: str, by_id: Mapping[str, Mapping[str, RetrievalValue]], visited: set[str]) -> str:
    if not record_id or record_id in visited:
        return ''
    row = by_id.get(record_id)
    if row is None:
        return ''
    if _is_current_target(row):
        return record_id
    next_visited = {*visited, record_id}
    direct = _first_record_id(_row_text(row, 'superseded_by'))
    if direct:
        return _resolve_current_id(direct, by_id, next_visited)
    return _fix_successor_id(record_id, by_id, next_visited)


def _fix_successor_id(record_id: str, by_id: Mapping[str, Mapping[str, RetrievalValue]], visited: set[str]) -> str:
    candidates = [row for row in by_id.values() if record_id in _record_ids(_row_text(row, 'fixes'))]
    current = [row for row in candidates if _is_current_target(row)]
    if current:
        newest = max(current, key=lambda candidate: _row_text(candidate, 'created_at'))
        return _row_text(newest, 'record_id')
    for row in sorted(candidates, key=lambda candidate: _row_text(candidate, 'created_at'), reverse=True):
        resolved = _resolve_current_id(_row_text(row, 'record_id'), by_id, visited)
        if resolved:
            return resolved
    return ''


def _is_current_target(row: Mapping[str, RetrievalValue]) -> bool:
    return _row_text(row, 'authority') != 'evidence' and _row_text(row, 'lifecycle') == 'active' and _row_text(row, 'freshness') == 'current'


def _record_ids(value: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(RECORD_ID_RE.findall(value)))


def _first_record_id(value: str) -> str:
    ids = _record_ids(value)
    return ids[0] if ids else ''


def _row_text(row: Mapping[str, RetrievalValue], key: str) -> str:
    value = row.get(key, '')
    return value if isinstance(value, str) else str(value)


def derive_summary(content: str, title: str) -> str:
    in_frontmatter = False
    in_summary = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == '---':
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if stripped.startswith('## '):
            in_summary = stripped.lower() in {'## summary', '## change content', '## core conclusions'}
            continue
        if stripped.startswith('#'):
            continue
        if in_summary and stripped:
            return _clean_summary(stripped)
    for line in content.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(('#', '---')) and ':' not in stripped[:24]:
            return _clean_summary(stripped)
    return _clean_summary(title)


def _clean_summary(value: str) -> str:
    cleaned = re.sub(r'^[\-*\d.\s]+', '', value).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned[:180]
