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


def test_declared_frontmatter_overrides_inferred_trust_metadata() -> None:
    # Given: a manual-path record that explicitly declares digest/summarized/archived trust
    row = {
        "path": "/repo/.sybermem/changes/2026-08-07-x.md",
        "title": "Declared trust record",
        "content": "## Summary\nDeclared trust wins over path/status inference.",
        "status": "implemented",
        "superseded_by": "",
        "source_kind": "digest",
        "authority": "summarized",
        "lifecycle": "archived",
    }

    # When: continuity metadata is derived
    meta = derive_continuity_metadata(row, match_reason="keyword")

    # Then: the declared values win over what path/status would have inferred (manual/authoritative/active)
    assert meta["source_kind"] == "digest"
    assert meta["authority"] == "summarized"
    assert meta["lifecycle"] == "archived"
    assert meta["freshness"] == "historical"


def test_invalid_declared_trm_values_fall_back_to_inference() -> None:
    # Given: a record whose declared trust fields are typos/unknown values
    row = {
        "path": "/repo/.sybermem/changes/2026-08-07-y.md",
        "title": "Typo trust record",
        "content": "## Summary\nInvalid declarations must not corrupt classification.",
        "status": "implemented",
        "superseded_by": "",
        "source_kind": "bogus",
        "authority": "supreme",
        "lifecycle": "eternal",
    }

    # When: metadata is derived
    meta = derive_continuity_metadata(row, match_reason="keyword")

    # Then: unknown declarations are ignored and inference applies (manual/authoritative/active)
    assert meta["source_kind"] == "manual"
    assert meta["authority"] == "authoritative"
    assert meta["lifecycle"] == "active"
    assert meta["freshness"] == "current"


def test_declared_authority_can_demote_manual_record_to_evidence() -> None:
    # Given: a manual record the author explicitly marks as low-trust evidence
    assert classify_authority("manual", "t", "body", declared="evidence") == "evidence"
    # And: an unknown declaration is ignored
    assert classify_authority("manual", "t", "body", declared="nonsense") == "authoritative"


def test_declared_archived_lifecycle_wins_without_index_entry() -> None:
    # Given: a record that declares lifecycle: archived in its own frontmatter,
    # with no INDEX-derived archived flag and no [archived] body marker (G5).
    row = {
        "path": "/repo/.sybermem/changes/2026-08-07-z.md",
        "title": "Self-declared archived record",
        "content": "## Summary\nCanonical frontmatter is the source of archival truth.",
        "status": "implemented",
        "superseded_by": "",
        "lifecycle": "archived",
    }

    # When: metadata is derived without passing archived=True
    meta = derive_continuity_metadata(row, match_reason="keyword", archived=False)

    # Then: the declared lifecycle is authoritative — no INDEX section required
    assert meta["lifecycle"] == "archived"
    assert meta["freshness"] == "historical"


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
