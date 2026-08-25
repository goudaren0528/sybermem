from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_shell_installers_guard_recursive_managed_deletions() -> None:
    for relative_path in (
        Path("scripts/install.sh"),
        Path("scripts/update.sh"),
        Path("scripts/install-remote.sh"),
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "safe_remove_managed_dir" in text
        assert "pwd -P" in text
        assert '[ -L "$target" ]' in text
        assert '[ ! -L "$root" ]' in text
        assert "Refusing linked managed root" in text
        assert 'rm -rf "$target/' not in text
