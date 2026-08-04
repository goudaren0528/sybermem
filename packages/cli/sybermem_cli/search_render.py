from __future__ import annotations

from sybermem_core.search import SearchRow


def render_search_text(results: list[SearchRow]) -> None:
    current_project = None
    for row in results:
        if row["slug"] != current_project:
            current_project = row["slug"]
            print(f"[{current_project}]")
        print(f"- [{row['record_id']}] {row['title']}")
        print(f"  - Source: {row.get('source_kind', 'unknown')}")
        print(f"  - Authority: {row.get('authority', 'unknown')}")
        print(f"  - Lifecycle: {row.get('lifecycle', 'unknown')}")
        print(f"  - Freshness: {row.get('freshness', 'unknown')}")
        print(f"  - Match: {row.get('match', 'keyword')}")
        if row.get('related_digest'):
            print(f"  - Related digest: {row['related_digest']}")
        if row.get('conflict_note'):
            print(f"  - Conflict: {row['conflict_note']}")
        if row.get('successor_record'):
            print(f"  - Successor: {row['successor_record']} {row.get('successor_title', '')}".rstrip())
        if row.get('current_guidance'):
            print(f"  - Current guidance: {row['current_guidance']}")
    if not results:
        print("No matches.")
