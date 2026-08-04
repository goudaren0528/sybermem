from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.retrieval import (
    classify_authority,
    classify_freshness,
    classify_lifecycle,
    classify_source_kind,
    derive_continuity_metadata,
)


def test_classify_source_kind_marks_auto_trail_records() -> None:
    content_path = "/repo/.sybermem/changes/2026-06-18-007-marketplace-plugin-hooks-and-more.md"

    assert classify_source_kind(content_path, "marketplace plugin hooks and more", "Auto-generated from workspace changes detected at session stop.") == "auto-trail"


def test_classify_authority_marks_auto_generated_stop_hook_records_as_evidence() -> None:
    content = "Auto-generated from workspace changes detected at session stop."

    assert classify_authority("auto-trail", "skill skill", content) == "evidence"


def test_current_lifecycle_keeps_authoritative_terminal_statuses_current() -> None:
    for status in ["accepted", "decided", "implemented"]:
        lifecycle = classify_lifecycle(status, "", False)
        assert lifecycle == "active"
        assert classify_freshness(lifecycle) == "current"


def test_derive_continuity_metadata_classifies_active_resolved_superseded_and_archived_records() -> None:
    # Given: canonical Markdown-derived row fields for the main lifecycle classes
    base = {
        "path": "/repo/.sybermem/changes/2026-08-04-001-active.md",
        "title": "Active record",
        "content": "## Summary\nActive continuity record.",
        "status": "implemented",
        "superseded_by": "",
    }

    # When: metadata is derived without adding canonical fields
    active = derive_continuity_metadata(base, match_reason="keyword")
    resolved = derive_continuity_metadata({**base, "status": "resolved"}, match_reason="keyword")
    superseded = derive_continuity_metadata({**base, "superseded_by": "decision-002"}, match_reason="relation")
    archived = derive_continuity_metadata({**base, "content": "## Summary\nArchived note. [archived]"}, match_reason="keyword")

    # Then: every hit exposes the shared additive continuity shape
    assert active == {
        "source_kind": "manual",
        "authority": "authoritative",
        "lifecycle": "active",
        "freshness": "current",
        "match_reason": "keyword",
        "related_digest": "",
        "conflict_note": "",
        "summary": "Active continuity record.",
    }
    assert resolved["lifecycle"] == "resolved"
    assert resolved["freshness"] == "historical"
    assert superseded["lifecycle"] == "superseded"
    assert superseded["freshness"] == "historical"
    assert archived["lifecycle"] == "archived"
    assert archived["freshness"] == "historical"
