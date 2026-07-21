from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.retrieval import classify_authority


def test_classify_authority_marks_auto_generated_stop_hook_records_as_evidence() -> None:
    content = "Auto-generated from workspace changes detected at session stop."

    assert classify_authority("manual", "skill skill", content) == "evidence"
