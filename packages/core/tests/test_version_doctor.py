from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.version import compare_versions, is_outdated, get_installed_version, project_needs_update
from sybermem_core.doctor import version_report
from sybermem_core.project_refresh import refresh_project


def test_compare_versions_orders_numerically() -> None:
    assert compare_versions("0.1.0", "0.2.0") == -1
    assert compare_versions("0.2.0", "0.1.0") == 1
    assert compare_versions("0.2.0", "0.2.0") == 0
    assert compare_versions("0.2", "0.2.0") == 0
    assert compare_versions("1.0.0", "0.9.9") == 1
    # Non-numeric suffixes truncate to leading digits, so ordering stays sane.
    assert compare_versions("0.2.0rc1", "0.2.0") == 0


def test_is_outdated_is_failsafe_on_missing_versions() -> None:
    assert is_outdated("0.1.0", "0.2.0") is True
    assert is_outdated("0.2.0", "0.2.0") is False
    assert is_outdated("0.3.0", "0.2.0") is False
    # Unknown/empty never nags.
    assert is_outdated("", "0.2.0") is False
    assert is_outdated("0.1.0", "") is False


def test_project_needs_update_bootstraps_old_projects() -> None:
    # Managed project stamped older -> needs update.
    assert project_needs_update(is_managed=True, project_version="0.1.0", installed_version="0.2.0") is True
    # Managed project with NO stamp yet (predates the field) -> needs update (bootstrap).
    assert project_needs_update(is_managed=True, project_version="", installed_version="0.2.0") is True
    # Managed project already current -> no nudge.
    assert project_needs_update(is_managed=True, project_version="0.2.0", installed_version="0.2.0") is False
    # Managed project ahead of installed -> no nudge.
    assert project_needs_update(is_managed=True, project_version="0.3.0", installed_version="0.2.0") is False
    # Not a managed project -> never nudge, even with no stamp.
    assert project_needs_update(is_managed=False, project_version="", installed_version="0.2.0") is False
    # No installed marker -> can't judge -> never nudge.
    assert project_needs_update(is_managed=True, project_version="0.1.0", installed_version="") is False


def test_version_report_flags_outdated_project(tmp_path: Path) -> None:
    # Given: a project stamped with an older version than installed
    root = tmp_path / "project"
    (root / ".sybermem").mkdir(parents=True)
    installed = get_installed_version()
    (root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nproject_id: prj_x\nslug: demo\nsybermem_version: 0.0.1\n",
        encoding="utf-8",
    )

    # When
    report = version_report(root)

    # Then
    assert report["installed"] == installed
    assert report["project"] == "0.0.1"
    assert report["outdated"] is True
    assert report["recommendation"] == "/sybermem-update"


def test_version_report_current_project_not_outdated(tmp_path: Path) -> None:
    root = tmp_path / "project"
    (root / ".sybermem").mkdir(parents=True)
    installed = get_installed_version()
    (root / ".sybermem" / "project.yaml").write_text(
        f"schema_version: 1\nproject_id: prj_x\nslug: demo\nsybermem_version: {installed}\n",
        encoding="utf-8",
    )
    report = version_report(root)
    assert report["outdated"] is False
    assert report["recommendation"] == ""


def test_version_report_no_root_reports_installed_only() -> None:
    report = version_report(None)
    assert report["installed"] == get_installed_version()
    assert report["project"] == ""
    assert report["outdated"] is False


def test_version_report_flags_old_project_without_version_field(tmp_path: Path) -> None:
    # Given: a MANAGED project whose project.yaml predates the sybermem_version field
    root = tmp_path / "project"
    (root / ".sybermem").mkdir(parents=True)
    (root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nproject_id: prj_x\nslug: demo\n",  # no sybermem_version
        encoding="utf-8",
    )

    # When
    report = version_report(root)

    # Then: it is flagged outdated so the old user is nudged to bootstrap version tracking
    assert report["project"] == ""
    assert report["outdated"] is True
    assert report["recommendation"] == "/sybermem-update"


def test_version_report_unmanaged_project_not_flagged(tmp_path: Path) -> None:
    # Given: a directory with .sybermem/ but NO project.yaml (not a managed identity)
    root = tmp_path / "project"
    (root / ".sybermem").mkdir(parents=True)

    # When
    report = version_report(root)

    # Then: never nudge an unmanaged project
    assert report["outdated"] is False
    assert report["recommendation"] == ""


def _seed_minimal(project_root: Path, template_root: Path) -> None:
    (project_root / ".sybermem").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (project_root / ".sybermem" / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    template_root.mkdir(parents=True, exist_ok=True)


def test_refresh_stamps_sybermem_version_on_new_project(tmp_path: Path) -> None:
    # Given: a fresh project with no project.yaml
    project_root = tmp_path / "project"
    template_root = tmp_path / "templates"
    _seed_minimal(project_root, template_root)

    # When
    refresh_project(project_root, template_roots=(template_root,))

    # Then: project.yaml carries the installed version stamp
    yaml_text = (project_root / ".sybermem" / "project.yaml").read_text(encoding="utf-8")
    assert f"sybermem_version: {get_installed_version()}" in yaml_text


def test_refresh_updates_stale_sybermem_version_on_existing_project(tmp_path: Path) -> None:
    # Given: an existing project.yaml stamped with an old version
    project_root = tmp_path / "project"
    template_root = tmp_path / "templates"
    _seed_minimal(project_root, template_root)
    (project_root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nproject_id: prj_x\nslug: demo\nsybermem_version: 0.0.1\n",
        encoding="utf-8",
    )

    # When
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the stamp is bumped to the installed version
    yaml_text = (project_root / ".sybermem" / "project.yaml").read_text(encoding="utf-8")
    assert f"sybermem_version: {get_installed_version()}" in yaml_text
    assert "sybermem_version: 0.0.1" not in yaml_text
    assert "update sybermem_version in .sybermem/project.yaml" in report["actions_applied"]


def test_refresh_adds_sybermem_version_when_field_absent(tmp_path: Path) -> None:
    # Given: an existing project.yaml WITHOUT a sybermem_version field (older schema)
    project_root = tmp_path / "project"
    template_root = tmp_path / "templates"
    _seed_minimal(project_root, template_root)
    (project_root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nproject_id: prj_x\nslug: demo\n",
        encoding="utf-8",
    )

    # When
    report = refresh_project(project_root, template_roots=(template_root,))

    # Then: the field is appended
    yaml_text = (project_root / ".sybermem" / "project.yaml").read_text(encoding="utf-8")
    assert f"sybermem_version: {get_installed_version()}" in yaml_text
    assert "add sybermem_version to .sybermem/project.yaml" in report["actions_applied"]


def test_refresh_does_not_stamp_version_if_migration_step_fails(tmp_path: Path, monkeypatch) -> None:
    # Given: an existing project stamped with an old version, and a later migration
    # step (gitignore) that will raise. The version stamp must run LAST so a failed
    # migration leaves the stamp stale -> the next session-start still nudges.
    import sybermem_core.project_refresh as pr

    project_root = tmp_path / "project"
    template_root = tmp_path / "templates"
    _seed_minimal(project_root, template_root)
    (project_root / ".sybermem" / "project.yaml").write_text(
        "schema_version: 1\nproject_id: prj_x\nslug: demo\nsybermem_version: 0.0.1\n",
        encoding="utf-8",
    )

    def boom(_root):
        raise RuntimeError("simulated gitignore failure mid-migration")

    monkeypatch.setattr(pr, "_ensure_gitignore", boom)

    # When / Then: refresh raises, and the stale version stamp is NOT bumped
    try:
        refresh_project(project_root, template_roots=(template_root,))
        raised = False
    except RuntimeError:
        raised = True
    assert raised is True
    yaml_text = (project_root / ".sybermem" / "project.yaml").read_text(encoding="utf-8")
    assert "sybermem_version: 0.0.1" in yaml_text  # still stale -> nudge will retry
    assert f"sybermem_version: {get_installed_version()}" not in yaml_text
