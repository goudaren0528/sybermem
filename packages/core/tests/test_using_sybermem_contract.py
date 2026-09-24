from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
ROOT = TESTS_DIR.parents[2]

sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(ROOT / "packages" / "core"))
sys.path.insert(0, str(ROOT / "packages" / "cli"))

from skill_discovery_contract_helpers import (  # noqa: E402
    parse_skill_catalog,
    validate_reassessment,
    validate_taxonomy,
    validate_using_skill,
    validate_refresh_scope,
)

CANONICAL_USING_SKILL = ROOT / "packages" / "claude-skills" / "using-sybermem" / "SKILL.md"
MIRROR_USING_SKILL = ROOT / "skills" / "using-sybermem" / "SKILL.md"
MANIFEST = ROOT / "scripts" / "managed-install.json"
INSTALL_COMMON = ROOT / "scripts" / "_install_common.py"
GEMINI_ENTRYPOINT = ROOT / "GEMINI.md"

EXPECTED_ACTIVE_SKILLS = frozenset(
    {
        "sybermem-init-project",
        "sybermem-record",
        "sybermem-summary",
        "sybermem-resume",
        "sybermem-digest",
        "sybermem-phase-analyze",
        "using-sybermem",
        "sybermem-update",
        "sybermem-search",
        "sybermem-theme-digest",
        "sybermem-habit",
        "sybermem-uninstall",
        "sybermem-install",
    }
)

VALID_CATALOG = """# Doc

### Core entrypoints

- `using-sybermem`: orientation entrypoint.
- `sybermem-init-project`: initialize project memory.

### Advanced / lifecycle

- `sybermem-summary`: status panel.
- `sybermem-install`: install runtime.

## Next section
"""


# --- validate_using_skill ---------------------------------------------------


@pytest.mark.parametrize("path", [CANONICAL_USING_SKILL, MIRROR_USING_SKILL])
def test_using_skill_satisfies_orientation_contract(path: Path) -> None:
    # Given: the shipped using-sybermem Skill (canonical and mirror)
    # When / Then: the structural orientation contract holds
    validate_using_skill(path)


def test_using_skill_mirrors_are_byte_identical() -> None:
    # Given: two distribution copies of the same Skill
    # When / Then: they are byte-for-byte equal
    assert CANONICAL_USING_SKILL.read_bytes() == MIRROR_USING_SKILL.read_bytes()


@pytest.mark.parametrize(
    "token",
    [
        "sybermem project refresh --format json",
        "not hot-loaded",
        "skip all CLI calls",
        "no live host/session identity",
        "sybermem doctor --runtime --format json",
        'sybermem project refresh --root "<confirmed-target>" --format json',
        "confirm the target existing directory",
        "independent nested project",
        "Do not execute refresh here",
        "never downgrade to a no-argument refresh",
    ],
)
def test_using_skill_rejects_missing_journey_or_evidence_boundary(tmp_path: Path, token: str) -> None:
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        CANONICAL_USING_SKILL.read_text(encoding="utf-8").replace(token, "removed"),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError):
        validate_using_skill(mutated)


def test_using_skill_rejects_runtime_diagnostics_in_default_flow(tmp_path: Path) -> None:
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        CANONICAL_USING_SKILL.read_text(encoding="utf-8").replace(
            "### Step 2: Report a compact state summary",
            "### Step 2: Report a compact state summary\n\nRun doctor --runtime every turn.",
        ),
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="on demand"):
        validate_using_skill(mutated)


@pytest.mark.parametrize("name", ["README.md", "README.en.md"])
def test_readme_exposes_journey_and_approved_runtime_command(name: str) -> None:
    text = (ROOT / name).read_text(encoding="utf-8")
    for token in (
        "/sybermem-init-project",
        "/using-sybermem",
        "/sybermem-resume",
        "/sybermem-record",
        "sybermem next-step --format json",
        "sybermem project refresh --format json",
        "sybermem doctor --runtime --format json",
        'sybermem project refresh --root "<confirmed-target>" --format json',
        '& $SyberMemCli project refresh --root "<confirmed-target>" --format json',
        "unknown",
    ):
        assert token in text


def test_using_skill_rejects_missing_next_step(tmp_path: Path) -> None:
    # Given: the Skill with canonical next-step routing removed
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        CANONICAL_USING_SKILL.read_text(encoding="utf-8").replace(
            "sybermem next-step --format json", "hand-derived guess"
        ),
        encoding="utf-8",
    )

    # When / Then: the contract fails
    with pytest.raises(AssertionError, match="next-step"):
        validate_using_skill(mutated)


@pytest.mark.parametrize("name", [
    "using-sybermem", "sybermem-install", "sybermem-init-project", "sybermem-update",
])
def test_project_setup_scope_and_mirror_contract(name: str) -> None:
    source = ROOT / "skills" / name / "SKILL.md"
    mirror = ROOT / "packages" / "claude-skills" / name / "SKILL.md"
    validate_refresh_scope(source)
    validate_refresh_scope(mirror)
    assert source.read_bytes() == mirror.read_bytes()


@pytest.mark.parametrize("token", [
    'project refresh --root "<confirmed-target>" --format json',
    "confirm the target existing directory",
    "independent nested project",
    "never downgrade to a no-argument refresh",
    "partial writes",
    "`root`",
    "`overall`",
])
def test_refresh_scope_rejects_missing_boundary(tmp_path: Path, token: str) -> None:
    text = (ROOT / "skills/sybermem-install/SKILL.md").read_text(encoding="utf-8")
    mutated = tmp_path / "install.md"
    mutated.write_text(text.replace(token, "removed"), encoding="utf-8")
    with pytest.raises(AssertionError):
        validate_refresh_scope(mutated)


def test_refresh_scope_rejects_missing_powershell_call_operator(tmp_path: Path) -> None:
    text = (ROOT / "skills/sybermem-install/SKILL.md").read_text(encoding="utf-8")
    mutated = tmp_path / "install.md"
    mutated.write_text(text.replace("& $SyberMemCli project refresh", "$SyberMemCli project refresh"), encoding="utf-8")
    with pytest.raises(AssertionError, match="explicit refresh contract"):
        validate_refresh_scope(mutated)


def test_refresh_scope_rejects_command_before_confirmation(tmp_path: Path) -> None:
    text = (ROOT / "skills/sybermem-install/SKILL.md").read_text(encoding="utf-8")
    mutated = tmp_path / "install.md"
    mutated.write_text(
        '& $SyberMemCli project refresh --root "<confirmed-target>" --format json\n' + text,
        encoding="utf-8",
    )
    with pytest.raises(AssertionError, match="confirm scope before"):
        validate_refresh_scope(mutated)


@pytest.mark.parametrize("token", [
    "symlink/reparse points", "ancestor Git worktree", "own independent repository",
    "unconfirmed Git boundary", "On rejection, stop", "never fall back to no-argument refresh",
    "nonempty `GIT_*` environment overrides", "fixed locale", "strictly recognize",
    "static exact-target check", "not an OS sandbox", "VM/OS isolation",
    "Normalize the user-confirmed target to an absolute path",
])
def test_refresh_scope_rejects_missing_filesystem_boundary(tmp_path: Path, token: str) -> None:
    text = (ROOT / "skills/sybermem-install/SKILL.md").read_text(encoding="utf-8")
    mutated = tmp_path / "install.md"
    mutated.write_text(text.replace(token, "removed"), encoding="utf-8")
    with pytest.raises(AssertionError):
        validate_refresh_scope(mutated)


def test_using_skill_rejects_missing_non_mutation_token(tmp_path: Path) -> None:
    # Given: the Skill with its explicit non-mutation rule removed
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        CANONICAL_USING_SKILL.read_text(encoding="utf-8").replace(
            "Do not run downstream actions", "Proceed automatically"
        ),
        encoding="utf-8",
    )

    # When / Then: the contract fails
    with pytest.raises(AssertionError, match="Do not run downstream actions"):
        validate_using_skill(mutated)


def test_using_skill_rejects_missing_powershell_call_operator(tmp_path: Path) -> None:
    text = CANONICAL_USING_SKILL.read_text(encoding="utf-8")
    command = "& $SyberMemCli next-step --format json"
    assert command in text
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(text.replace(command, command.removeprefix("& ")), encoding="utf-8")

    with pytest.raises(AssertionError, match=r"& \$SyberMemCli next-step"):
        validate_using_skill(mutated)


def test_using_skill_rejects_missing_launcher_guidance(tmp_path: Path) -> None:
    # Given: the Skill with fixed-launcher PATH safety guidance removed
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        CANONICAL_USING_SKILL.read_text(encoding="utf-8").replace(
            "Do not modify persistent PATH automatically", "Update PATH as needed"
        ),
        encoding="utf-8",
    )

    # When / Then: the contract fails
    with pytest.raises(AssertionError, match="persistent PATH"):
        validate_using_skill(mutated)


def test_using_skill_rejects_advanced_before_default(tmp_path: Path) -> None:
    # Given: a Skill whose advanced diagnostics precede the default flow
    text = CANONICAL_USING_SKILL.read_text(encoding="utf-8")
    default_start = text.index("\n## Default orientation flow\n") + 1
    advanced_start = text.index("\n## Advanced diagnostics\n") + 1
    output_start = text.index("\n## Output Style\n") + 1
    mutated = tmp_path / "using-sybermem.md"
    mutated.write_text(
        text[:default_start]
        + text[advanced_start:output_start]
        + text[default_start:advanced_start]
        + text[output_start:],
        encoding="utf-8",
    )

    # When / Then: heading order is enforced
    with pytest.raises(AssertionError, match="must appear before"):
        validate_using_skill(mutated)


# --- parse_skill_catalog / validate_taxonomy -------------------------------


def test_parse_skill_catalog_preserves_order(tmp_path: Path) -> None:
    # Given: a well-formed Core/Advanced catalog
    doc = tmp_path / "catalog.md"
    doc.write_text(VALID_CATALOG, encoding="utf-8")

    # When: the catalog is parsed
    catalog = parse_skill_catalog(doc)

    # Then: tiers keep document order and stay disjoint
    assert catalog["core"] == ("using-sybermem", "sybermem-init-project")
    assert catalog["advanced"] == ("sybermem-summary", "sybermem-install")


def test_parse_skill_catalog_rejects_duplicates(tmp_path: Path) -> None:
    # Given: a catalog repeating one Core skill
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-init-project`: initialize project memory.",
            "- `using-sybermem`: duplicated row.",
        ),
        encoding="utf-8",
    )

    # When / Then: duplicates are rejected
    with pytest.raises(AssertionError, match="duplicate"):
        parse_skill_catalog(doc)


def test_parse_skill_catalog_rejects_retired_language(tmp_path: Path) -> None:
    # Given: an advanced tier implying deprecation
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-install`: install runtime.",
            "- `sybermem-install`: deprecated legacy installer.",
        ),
        encoding="utf-8",
    )

    # When / Then: retired/deprecated language is rejected
    with pytest.raises(AssertionError, match="deprecated"):
        parse_skill_catalog(doc)


def test_parse_skill_catalog_rejects_wrapped_continuation(tmp_path: Path) -> None:
    # Given: a catalog row wrapped onto an indented continuation line
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-init-project`: initialize project memory.",
            "- `sybermem-init-project`: initialize project memory\n  and quietly do something else.",
        ),
        encoding="utf-8",
    )

    # When / Then: one row per line is enforced, so hidden continuations fail
    with pytest.raises(AssertionError, match="indented continuation"):
        parse_skill_catalog(doc)


def test_parse_skill_catalog_rejects_nested_sub_bullet(tmp_path: Path) -> None:
    # Given: a nested sub-bullet smuggling an extra entry into a tier
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-init-project`: initialize project memory.",
            "- `sybermem-init-project`: initialize project memory.\n  - `hidden-skill`: nested row.",
        ),
        encoding="utf-8",
    )

    # When / Then: nested rows are rejected rather than silently skipped
    with pytest.raises(AssertionError, match="indented continuation"):
        parse_skill_catalog(doc)


def test_parse_skill_catalog_ignores_headings_inside_fences(tmp_path: Path) -> None:
    # Given: a document whose fenced example block mimics the catalog headings
    doc = tmp_path / "catalog.md"
    doc.write_text(
        "# Doc\n\nExample rendering:\n\n"
        "```md\n"
        "### Core entrypoints\n\n- `fake`: not real.\n\n"
        "### Advanced / lifecycle\n\n- `fake2`: not real.\n"
        "```\n\n" + VALID_CATALOG.split("# Doc\n", 1)[1],
        encoding="utf-8",
    )

    # When: the catalog is parsed
    catalog = parse_skill_catalog(doc)

    # Then: only the real prose headings are used, never fenced examples
    assert catalog == {
        "core": ("using-sybermem", "sybermem-init-project"),
        "advanced": ("sybermem-summary", "sybermem-install"),
    }


def test_parse_skill_catalog_rejects_later_duplicate_heading(tmp_path: Path) -> None:
    # Given: a second, conflicting catalog heading later in the same document
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG + "\n### Core entrypoints\n\n- `sybermem-record`: conflicting catalog.\n",
        encoding="utf-8",
    )

    # When / Then: ambiguity is reported instead of silently taking the first
    with pytest.raises(AssertionError, match="ambiguous heading"):
        parse_skill_catalog(doc)


def test_parse_skill_catalog_allows_trailing_paragraph(tmp_path: Path) -> None:
    # Given: an explanatory paragraph after a blank line following the rows
    doc = tmp_path / "catalog.md"
    doc.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-install`: install runtime.",
            "- `sybermem-install`: install runtime.\n\nThis tier is specialized and fully supported.",
        ),
        encoding="utf-8",
    )

    # When / Then: separated trailing prose stays legal
    assert parse_skill_catalog(doc)["advanced"] == ("sybermem-summary", "sybermem-install")


def test_validate_taxonomy_rejects_incomplete_membership(tmp_path: Path) -> None:
    # Given: a catalog that does not cover the full manifest inventory
    doc = tmp_path / "catalog.md"
    doc.write_text(VALID_CATALOG, encoding="utf-8")

    # When / Then: membership must equal the manifest skills exactly
    with pytest.raises(AssertionError, match="must equal manifest skills"):
        validate_taxonomy((doc,), MANIFEST)


def test_validate_taxonomy_rejects_divergent_documents(tmp_path: Path) -> None:
    # Given: two catalogs that disagree on tier placement
    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text(VALID_CATALOG, encoding="utf-8")
    second.write_text(
        VALID_CATALOG.replace(
            "- `sybermem-summary`: status panel.", "- `sybermem-resume`: continuity view."
        ),
        encoding="utf-8",
    )

    # When / Then: cross-document equality is enforced before manifest checks
    with pytest.raises(AssertionError, match="taxonomy mismatch"):
        validate_taxonomy((first, second), MANIFEST)


# --- validate_reassessment -------------------------------------------------


VALID_REASSESSMENT = """# Reassessment

| Candidate | Verdict | User impact | Compatibility impact | Migration need | Evidence |
| --- | --- | --- | --- | --- | --- |
| phase-analyze/digest | retain | distinct jobs | none | none | task-7 evidence |
| summary/resume | retain | distinct jobs | none | none | task-7 evidence |
| theme-digest/digest | retain | distinct jobs | none | none | task-7 evidence |
| using-sybermem/doctor-update | propose future change | orientation overlap | none | none | task-8 evidence |
"""


def test_validate_reassessment_accepts_complete_table(tmp_path: Path) -> None:
    # Given: a complete four-candidate reassessment
    doc = tmp_path / "reassessment.md"
    doc.write_text(VALID_REASSESSMENT, encoding="utf-8")

    # When / Then: the structure validates
    validate_reassessment(doc)


def test_validate_reassessment_rejects_invalid_verdict(tmp_path: Path) -> None:
    # Given: a reassessment issuing a retirement directive
    doc = tmp_path / "reassessment.md"
    doc.write_text(VALID_REASSESSMENT.replace("| retain |", "| retire now |", 1), encoding="utf-8")

    # When / Then: directives are rejected
    with pytest.raises(AssertionError, match="retire now"):
        validate_reassessment(doc)


def test_validate_reassessment_rejects_missing_field(tmp_path: Path) -> None:
    # Given: a reassessment with an empty migration field
    doc = tmp_path / "reassessment.md"
    doc.write_text(
        VALID_REASSESSMENT.replace(
            "| summary/resume | retain | distinct jobs | none | none | task-7 evidence |",
            "| summary/resume | retain | distinct jobs | none |  | task-7 evidence |",
        ),
        encoding="utf-8",
    )

    # When / Then: empty required fields are rejected
    with pytest.raises(AssertionError, match="empty"):
        validate_reassessment(doc)


# --- no-project CLI orientation route --------------------------------------


def test_next_step_without_project_root_routes_to_init(monkeypatch, capsys) -> None:
    # Given: a shell with no resolvable SyberMem project root
    from sybermem_cli import main as cli_main

    monkeypatch.setattr(cli_main, "resolve_project_root", lambda: None)

    # When: the canonical orientation router runs in JSON mode
    exit_code = cli_main.cmd_next_step(argparse.Namespace(format="json"))
    payload = json.loads(capsys.readouterr().out)

    # Then: orientation routes to init-project and stays successful
    assert exit_code == 0
    assert payload["action"] == "/sybermem-init-project"


# --- Wave 2 no-retirement boundary ----------------------------------------


def test_active_skill_inventory_is_frozen_at_thirteen() -> None:
    # Given: manifest, installer constants, and the source tree define membership
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    install_common = runpy.run_path(str(INSTALL_COMMON))
    source_names = {
        path.name for path in (ROOT / "packages" / "claude-skills").iterdir() if path.is_dir()
    }

    # When / Then: all three agree on exactly the pre-Wave-2 inventory
    assert set(install_common["SKILLS"]) == EXPECTED_ACTIVE_SKILLS
    assert set(manifest["skills"]) == EXPECTED_ACTIVE_SKILLS
    assert source_names == EXPECTED_ACTIVE_SKILLS
    assert len(EXPECTED_ACTIVE_SKILLS) == 13


def test_retired_inventory_is_unchanged_and_disjoint() -> None:
    # Given: retired names recorded by installer constants and the manifest
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    install_common = runpy.run_path(str(INSTALL_COMMON))
    retired = set(install_common["RETIRED_SKILLS"])

    # When / Then: retirement stays frozen and never touches active skills
    assert retired == {
        "sybermem-phase-confirm",
        "sybermem-team-publish",
        "sybermem-team-summary",
        "sybermem-link",
    }
    assert retired == set(manifest["retired_skills"])
    assert retired.isdisjoint(EXPECTED_ACTIVE_SKILLS)


def test_using_sybermem_stays_active_and_gemini_addressable() -> None:
    # Given: the Skill source, its mirror, and the Gemini entrypoint
    gemini = GEMINI_ENTRYPOINT.read_text(encoding="utf-8")

    # When / Then: all three discovery surfaces still reference using-sybermem
    assert CANONICAL_USING_SKILL.is_file()
    assert MIRROR_USING_SKILL.is_file()
    assert "skills/using-sybermem/SKILL.md" in gemini
