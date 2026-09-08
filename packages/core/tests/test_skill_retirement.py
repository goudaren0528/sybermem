from __future__ import annotations

import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parents[3]
CHECK_SCRIPT = ROOT / "scripts" / "check-plugin-package.py"


def distribution_script_text(relative_path: Path) -> str:
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    if relative_path.suffix == ".py":
        text += (ROOT / "scripts" / "_install_common.py").read_text(encoding="utf-8")
    return text


def test_link_is_retired_across_distribution_inventories() -> None:
    # Given: source trees, installer constants, and the manifest define skill membership.
    checker = runpy.run_path(str(CHECK_SCRIPT))
    install_common = runpy.run_path(str(ROOT / "scripts" / "_install_common.py"))
    manifest = json.loads((ROOT / "scripts" / "managed-install.json").read_text(encoding="utf-8"))
    source_names = {path.name for path in (ROOT / "packages" / "claude-skills").iterdir() if path.is_dir()}

    # When / Then: active names equal source directories and retired names stay disjoint.
    active = set(install_common["SKILLS"])
    retired = set(install_common["RETIRED_SKILLS"])
    assert checker["RETIRED_SKILL_NAMES"] == [
        "sybermem-phase-confirm",
        "sybermem-team-publish",
        "sybermem-team-summary",
        "sybermem-link",
    ]
    assert active == set(manifest["skills"]) == source_names
    assert retired == set(manifest["retired_skills"])
    assert active.isdisjoint(retired)
    assert "sybermem-link" not in active

    for relative_path in checker["DISTRIBUTION_SCRIPTS"]:
        text = distribution_script_text(relative_path)
        if relative_path.name.startswith("uninstall"):
            assert "managed-install.json" in text
            continue
        assert "sybermem-link" in text


def test_python_skill_sync_retires_link_from_all_hosts_idempotently(tmp_path, capsys) -> None:
    # Given: all three supported homes still contain the retired skill from an old install.
    install_common = runpy.run_path(str(ROOT / "scripts" / "_install_common.py"))
    sync_skills = install_common["_sync_skills"]
    home = tmp_path / "home"
    skill_roots = (
        home / ".claude" / "skills",
        home / ".config" / "opencode" / "skills",
        home / ".agents" / "skills",
    )
    for skill_root in skill_roots:
        legacy = skill_root / "sybermem-link"
        legacy.mkdir(parents=True)
        (legacy / "SKILL.md").write_text("legacy\n", encoding="utf-8")

    source = ROOT / "packages" / "claude-skills"
    remover = ROOT / "scripts" / "safe-managed-remove.py"

    # When: the shared installer/update skill path runs twice.
    sync_skills(source, home, remover)
    sync_skills(source, home, remover)

    # Then: every legacy copy stays removed, record is installed, and link is not advertised.
    output = capsys.readouterr().out
    for skill_root in skill_roots:
        assert not (skill_root / "sybermem-link").exists()
        assert (skill_root / "sybermem-record" / "SKILL.md").is_file()
    assert "updated: /sybermem-link" not in output
