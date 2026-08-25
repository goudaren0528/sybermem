from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
RETIRED = ("sybermem-team-publish", "sybermem-team-summary")


def _seed_home(home: Path) -> Path:
    for root in (home / ".claude" / "skills", home / ".config" / "opencode" / "skills", home / ".agents" / "skills"):
        for name in RETIRED:
            path = root / name
            path.mkdir(parents=True, exist_ok=True)
            (path / "SKILL.md").write_text("retired\n", encoding="utf-8")
    runtime = home / ".claude" / "sybermem"
    (runtime / "cli").mkdir(parents=True)
    (runtime / "cli" / "sybermem").write_text("managed\n", encoding="utf-8")
    for name in ("launch_record_change_on_stop.py", "launch_session_start_context.py", "VERSION"):
        (runtime / name).write_text("managed\n", encoding="utf-8")
    sentinel = runtime / "user-notes.txt"
    sentinel.write_text("preserve me\n", encoding="utf-8")
    return sentinel


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is unavailable")
def test_uninstall_sh_preserves_unknown_files_and_cleans_all_skill_roots(tmp_path: Path) -> None:
    sentinel = _seed_home(tmp_path)
    result = subprocess.run(
        [shutil.which("bash") or "bash", str(ROOT / "scripts" / "uninstall.sh")],
        cwd=ROOT,
        env={**os.environ, "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert sentinel.read_text(encoding="utf-8") == "preserve me\n"
    assert not (tmp_path / ".claude" / "sybermem" / "cli").exists()
    for root in (tmp_path / ".claude" / "skills", tmp_path / ".config" / "opencode" / "skills", tmp_path / ".agents" / "skills"):
        for name in RETIRED:
            assert not (root / name).exists()
