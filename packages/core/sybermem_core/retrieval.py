from __future__ import annotations


def classify_source_kind(path: str) -> str:
    normalized = path.replace('\\', '/')
    if '/digests/' in normalized or '/theme-digests/' in normalized:
        return 'digest'
    return 'manual'


def classify_authority(source_kind: str, title: str, content: str) -> str:
    if source_kind == 'digest':
        return 'summarized'
    if (
        'Auto-record workspace file changes on stop' in title
        or 'Auto-recorded workspace file changes at session stop' in content
        or 'Auto-generated from workspace changes detected at session stop.' in content
    ):
        return 'evidence'
    return 'authoritative'


def classify_lifecycle(status: str, superseded_by: str, archived: bool) -> str:
    normalized = (status or '').strip().lower()
    if superseded_by:
        return 'superseded'
    if archived:
        return 'archived'
    if normalized in {'resolved', 'implemented', 'completed', 'done', 'accepted', 'decided'}:
        return 'resolved'
    return 'active'


def classify_freshness(lifecycle: str) -> str:
    if lifecycle == 'active':
        return 'current'
    if lifecycle in {'resolved', 'superseded', 'archived'}:
        return 'historical'
    return 'stale'
