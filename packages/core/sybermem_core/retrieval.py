from __future__ import annotations

import re


AUTO_TRAIL_MARKERS = (
    'Auto-record workspace file changes on stop',
    'Auto-recorded workspace file changes at session stop',
    'Auto-generated from workspace changes detected at session stop.',
)


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
    if lifecycle in {'resolved', 'superseded', 'archived'}:
        return 'historical'
    return 'stale'


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
