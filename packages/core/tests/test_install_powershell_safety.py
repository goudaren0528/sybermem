from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_powershell_installers_guard_recursive_managed_deletions() -> None:
    for relative_path in (
        Path("scripts/install.ps1"),
        Path("scripts/update.ps1"),
        Path("scripts/install-remote.ps1"),
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "function Remove-ManagedDirectory" in text
        assert "GetFullPath" in text
        assert "ReparsePoint" in text
        assert "rootItem" in text
        assert "Refusing linked managed root" in text
