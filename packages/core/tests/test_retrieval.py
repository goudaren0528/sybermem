from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.retrieval import classify_authority, classify_freshness, classify_lifecycle, classify_source_kind


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
