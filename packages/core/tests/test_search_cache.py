from pathlib import Path
import time

import sybermem_core.search as search_module
from sybermem_core.search import search_project, _ROW_CACHE


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "changes").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_record(root: Path, filename: str, title: str, body: str) -> None:
    (root / ".sybermem" / "changes" / filename).write_text(
        "\n".join([
            "---",
            "type: change",
            "date: 2026-08-05",
            f"title: {title}",
            "status: implemented",
            "---",
            "",
            body,
        ]) + "\n",
        encoding="utf-8",
    )


def test_second_search_reuses_cache(tmp_path: Path, monkeypatch) -> None:
    _ROW_CACHE.clear()
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(project_root, "2026-08-05-001-alpha.md", "alpha change", "cachetoken alpha body")
    monkeypatch.chdir(project_root)

    calls = {"n": 0}
    real_parse = search_module.parse_record_file

    def counting_parse(*args, **kwargs):
        calls["n"] += 1
        return real_parse(*args, **kwargs)

    monkeypatch.setattr(search_module, "parse_record_file", counting_parse)

    search_project("cachetoken")
    after_first = calls["n"]
    assert after_first >= 1

    search_project("cachetoken")
    # No new parse calls on the unchanged second search.
    assert calls["n"] == after_first


def test_touching_record_invalidates_cache(tmp_path: Path, monkeypatch) -> None:
    _ROW_CACHE.clear()
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(project_root, "2026-08-05-001-alpha.md", "alpha change", "cachetoken alpha body")
    monkeypatch.chdir(project_root)

    calls = {"n": 0}
    real_parse = search_module.parse_record_file

    def counting_parse(*args, **kwargs):
        calls["n"] += 1
        return real_parse(*args, **kwargs)

    monkeypatch.setattr(search_module, "parse_record_file", counting_parse)

    search_project("cachetoken")
    after_first = calls["n"]

    # Add a new record with a strictly newer mtime -> fingerprint changes.
    time.sleep(0.02)
    write_record(project_root, "2026-08-05-002-beta.md", "beta change", "cachetoken beta body")
    import os
    os.utime(project_root / ".sybermem" / "changes", None)

    search_project("cachetoken")
    assert calls["n"] > after_first


def test_cached_search_results_are_stable(tmp_path: Path, monkeypatch) -> None:
    _ROW_CACHE.clear()
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(project_root, "2026-08-05-001-alpha.md", "alpha change", "stabletoken body one")
    monkeypatch.chdir(project_root)

    first = search_project("stabletoken")
    second = search_project("stabletoken")

    assert [r["record_id"] for r in first] == [r["record_id"] for r in second]
    assert len(first) == len(second)
