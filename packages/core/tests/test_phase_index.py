from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from sybermem_core import phase_index as phase_index_module
from sybermem_core.phase_index import PhaseConfirmError, analyze_phases, confirm_phases_from_payload
from sybermem_core.status import project_status


PHASE_PATH = Path(".sybermem") / "analysis" / "phase-index.md"


def _init_project(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "project"
    sybermem = root / ".sybermem"
    (sybermem / "analysis").mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(phase_index_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")
    return root


def _write_record(root: Path, folder: str, name: str, record_type: str, date: str, topics: str = "") -> None:
    records = root / ".sybermem" / folder
    records.mkdir(exist_ok=True)
    lines = ["---", f"type: {record_type}", f"record_id: {record_type}-{name}", f"date: {date}", f"title: {name}"]
    if topics:
        lines.append(f"topics: [{topics}]")
    lines += ["---", "", "body"]
    (records / f"{date}-{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_analyze_phases_persists_confirmed_structure_and_marks_analyzed(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with several records but a not_yet_analyzed phase index
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13", topics="auth")
    _write_record(root, "changes", "002", "change", "2026-08-13", topics="auth")
    _write_record(root, "bugs", "001", "bug", "2026-06-01", topics="ui")

    # When: deterministic analysis runs
    result = analyze_phases(root)

    # Then: the phase index is written with analyzed status and at least one confirmed phase
    text = (root / PHASE_PATH).read_text(encoding="utf-8")
    assert "status: analyzed" in text
    assert "### Phase:" in text
    assert result["status"] == "analyzed"
    assert result["phases"]
    # And every record is covered exactly once across confirmed phases
    covered = [rid for phase in result["phases"] for rid in phase["covered_records"]]
    assert sorted(covered) == ["bug-001", "change-001", "change-002"]
    assert len(covered) == len(set(covered))


def test_analyze_phases_output_is_read_by_project_status(tmp_path: Path, monkeypatch) -> None:
    # Given: an analyzed project
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")
    analyze_phases(root)

    # When: project status reads the phase index
    status = project_status(root)

    # Then: an active phase is surfaced (round-trip with the canonical reader)
    assert status["phase"]["id"]
    assert status["phase"]["lifecycle"] == "active"


def test_analyze_phases_with_no_records_stays_not_yet_analyzed(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with no records
    root = _init_project(tmp_path, monkeypatch)

    # When: analysis runs
    result = analyze_phases(root)

    # Then: it does not fabricate phases and stays not_yet_analyzed
    assert result["status"] == "not_yet_analyzed"
    assert result["phases"] == []
    text = (root / PHASE_PATH).read_text(encoding="utf-8")
    assert "status: not_yet_analyzed" in text


def test_confirm_phases_from_payload_writes_canonical_phases(tmp_path: Path, monkeypatch) -> None:
    # Given: an agent-produced high-quality grouping payload
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")
    _write_record(root, "changes", "002", "change", "2026-08-12")
    payload = {
        "phases": [
            {"title": "Auth foundation", "covered_records": ["change-001", "change-002"]},
        ]
    }

    # When: the payload is confirmed
    result = confirm_phases_from_payload(root, payload)

    # Then: the phase index carries the semantic title and both records
    text = (root / PHASE_PATH).read_text(encoding="utf-8")
    assert "### Phase: Auth foundation" in text
    assert "status: analyzed" in text
    assert result["phases"][0]["covered_records"] == ["change-001", "change-002"]
    status = project_status(root)
    assert status["phase"]["name"] == "Auth foundation"


def test_confirm_phases_rejects_unknown_record_ids(tmp_path: Path, monkeypatch) -> None:
    # Given: a payload referencing a record that does not exist
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")
    payload = {"phases": [{"title": "Bad", "covered_records": ["change-999"]}]}

    # When / Then: confirmation is rejected with a typed error naming the bad id
    with pytest.raises(PhaseConfirmError) as exc:
        confirm_phases_from_payload(root, payload)
    assert "change-999" in str(exc.value)


def test_confirm_phases_rejects_non_dict_payload(tmp_path: Path, monkeypatch) -> None:
    # Given: valid JSON that is not an object (e.g. a list or string)
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")

    # When / Then: confirmation raises a typed error instead of an AttributeError
    for bad in ([], "x", 5):
        with pytest.raises(PhaseConfirmError):
            confirm_phases_from_payload(root, bad)


def test_confirm_phases_rejects_incomplete_coverage(tmp_path: Path, monkeypatch) -> None:
    # Given: two records but a payload covering only one
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")
    _write_record(root, "changes", "002", "change", "2026-08-12")
    payload = {"phases": [{"title": "Partial", "covered_records": ["change-001"]}]}

    # When / Then: confirmation refuses to persist an analyzed index that orphans records
    with pytest.raises(PhaseConfirmError) as exc:
        confirm_phases_from_payload(root, payload)
    assert "change-002" in str(exc.value)


def test_confirm_phases_rejects_duplicate_coverage(tmp_path: Path, monkeypatch) -> None:
    # Given: a payload covering the same record in two phases
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")
    payload = {
        "phases": [
            {"title": "A", "covered_records": ["change-001"]},
            {"title": "B", "covered_records": ["change-001"]},
        ]
    }

    # When / Then: confirmation is rejected for duplicate coverage
    with pytest.raises(PhaseConfirmError) as exc:
        confirm_phases_from_payload(root, payload)
    assert "change-001" in str(exc.value)


def test_analyze_phases_writes_atomically_without_leaving_temp_files(tmp_path: Path, monkeypatch) -> None:
    # Given: an analyzed project
    root = _init_project(tmp_path, monkeypatch)
    _write_record(root, "changes", "001", "change", "2026-08-13")

    # When: analysis runs
    analyze_phases(root)

    # Then: no temp/partial files are left in the analysis directory
    analysis_dir = root / ".sybermem" / "analysis"
    leftovers = [p.name for p in analysis_dir.iterdir() if p.name != "phase-index.md"]
    assert leftovers == []
