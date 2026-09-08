from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANONICAL = ROOT / "packages" / "claude-skills" / "sybermem-record" / "SKILL.md"
MIRROR = ROOT / "skills" / "sybermem-record" / "SKILL.md"


def _relation_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for raw in text.splitlines():
        cells = [cell.strip().strip("`") for cell in raw.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] not in {
            "implements",
            "fixes",
            "related",
            "superseded-by",
            "crystallized-from",
        }:
            continue
        rows[cells[0]] = (cells[1], cells[2])
    return rows


def test_record_skill_mirrors_and_relation_mapping_are_canonical() -> None:
    canonical = CANONICAL.read_text(encoding="utf-8")
    mirror = MIRROR.read_text(encoding="utf-8")

    assert canonical == mirror
    assert _relation_rows(canonical) == {
        "implements": ("implements", "list"),
        "fixes": ("fixes", "list"),
        "related": ("related", "list"),
        "superseded-by": ("superseded_by", "single value"),
        "crystallized-from": ("crystallized_from", "list"),
    }


def test_record_skill_keeps_relation_write_safety_contract() -> None:
    text = CANONICAL.read_text(encoding="utf-8")

    required_tokens = (
        "frontmatter `record_id`",
        "source == target",
        "target record byte-for-byte",
        "symlinks or reparse points",
        "allowed canonical record roots",
        "revalidate that the source file",
        "project index build",
        "project index check",
    )
    for token in required_tokens:
        assert token in text


def test_record_skill_preserves_create_path_safety_and_scope() -> None:
    text = CANONICAL.read_text(encoding="utf-8")

    for classification in ("`digest`", "`no_write`", "`defer`", "`blocked`"):
        assert classification in text
    assert "Confirm write intent" in text
    assert "detect_record_intent.py --diagnose" in text
    assert "## When NOT to Record" in text
    assert "not permission to edit unrelated frontmatter" in text
