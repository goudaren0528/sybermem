from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_powershell_installers_use_central_managed_remover_and_manifest() -> None:
    for relative_path in (
        Path("scripts/install.ps1"),
        Path("scripts/update.ps1"),
        Path("scripts/install-remote.ps1"),
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "safe-managed-remove.py" in text
        assert "managed-install.json" in text
        assert "& python $RemoverSource child" in text
        assert "Copy-Item -Path $ManifestSource" in text
        assert "Copy-Item -Path $RemoverSource" in text
