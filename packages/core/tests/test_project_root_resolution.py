from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sybermem_core.project import resolve_project_root


def test_resolve_project_root_accepts_project_yaml_without_settings(tmp_path: Path) -> None:
    (tmp_path / ".sybermem").mkdir()
    (tmp_path / ".sybermem" / "project.yaml").write_text("project_id: test\n", encoding="utf-8")
    assert resolve_project_root(tmp_path / "nested") == tmp_path


def test_resolve_project_root_rejects_empty_sybermem(tmp_path: Path) -> None:
    (tmp_path / ".sybermem").mkdir()
    assert resolve_project_root(tmp_path) is None


def test_resolve_project_root_rejects_index_without_current_marker(tmp_path: Path) -> None:
    (tmp_path / ".sybermem").mkdir()
    (tmp_path / ".sybermem" / "INDEX.md").write_text("# legacy\n", encoding="utf-8")
    assert resolve_project_root(tmp_path) is None
