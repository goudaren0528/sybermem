from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli import main as main_module
from sybermem_core.digest_coverage import compute_coverage_hash


def _init_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "changes").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def _write_record(root: Path, rel: str, text: str) -> None:
    path = root / ".sybermem" / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_phase_index(root: Path, text: str) -> None:
    path = root / ".sybermem" / "analysis" / "phase-index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cli_coverage_hash_by_source_records_matches_core(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _init_project(root)
    _write_record(root, "changes/a.md", "---\ntype: change\n---\n\norig\n")
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["sybermem", "project", "coverage-hash", "--source-records", "changes/a.md", "--format", "json"],
    )

    exit_code = main_module.main()
    captured = capsys.readouterr()
    assert exit_code == 0
    expected = compute_coverage_hash(root, ["changes/a.md"])
    payload = json.loads(captured.out)
    assert payload == {"source_records": ["changes/a.md"], "coverage_hash": expected}


def test_cli_coverage_hash_from_phase_id_resolves_records(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _init_project(root)
    _write_record(root, "changes/a.md", "---\ntype: change\nrecord_id: change-001\n---\n\naa\n")
    _write_record(root, "bugs/b.md", "---\ntype: bug\nrecord_id: bug-001\n---\n\nbb\n")
    _write_phase_index(
        root,
        "\n".join(
            [
                "## Confirmed Phases",
                "### Phase: Auth",
                "- phase_id: phase-001",
                "- status: confirmed",
                "- lifecycle: active",
                "- covered_records:",
                "  - change-001",
                "  - bug-001",
            ]
        )
        + "\n",
    )
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["sybermem", "project", "coverage-hash", "--phase-id", "phase-001", "--format", "json"],
    )

    exit_code = main_module.main()
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    # source_records preserve the phase's covered_records order
    assert payload["source_records"] == ["changes/a.md", "bugs/b.md"]
    expected = compute_coverage_hash(root, ["bugs/b.md", "changes/a.md"])
    assert payload["coverage_hash"] == expected


def test_cli_coverage_hash_no_sources_exits_1(monkeypatch, capsys) -> None:
    root = Path("irrelevant")
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "coverage-hash"])
    exit_code = main_module.main()
    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Provide --source-records" in captured.err


def test_cli_coverage_hash_phase_not_found_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "project"
    root.mkdir()
    _init_project(root)
    _write_phase_index(root, "## Confirmed Phases\n### Phase: Auth\n- phase_id: phase-001\n- covered_records:\n  - change-001\n")
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    monkeypatch.setattr(sys, "argv", ["sybermem", "project", "coverage-hash", "--phase-id", "phase-999", "--format", "json"])
    exit_code = main_module.main()
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "phase-999 not found" in captured.err


def test_cli_coverage_hash_from_phase_id_handles_multiple_phases(tmp_path: Path, monkeypatch, capsys) -> None:
    # Regression: a phase that is NOT the last one in the index must still resolve.
    root = tmp_path / "project"
    root.mkdir()
    _init_project(root)
    _write_record(root, "changes/a.md", "---\ntype: change\nrecord_id: change-001\n---\n\naa\n")
    _write_record(root, "changes/b.md", "---\ntype: change\nrecord_id: change-002\n---\n\nbb\n")
    _write_phase_index(
        root,
        "\n".join(
            [
                "## Confirmed Phases",
                "### Phase: First",
                "- phase_id: phase-001",
                "- covered_records:",
                "  - change-001",
                "### Phase: Second",
                "- phase_id: phase-002",
                "- covered_records:",
                "  - change-002",
            ]
        )
        + "\n",
    )
    monkeypatch.setattr(main_module, "resolve_project_root", lambda: root)
    monkeypatch.setattr(
        sys,
        "argv",
        ["sybermem", "project", "coverage-hash", "--phase-id", "phase-001", "--format", "json"],
    )

    exit_code = main_module.main()
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["source_records"] == ["changes/a.md"]
    expected = compute_coverage_hash(root, ["changes/a.md"])
    assert payload["coverage_hash"] == expected
