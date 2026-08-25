from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_shell_installers_use_central_managed_remover_and_manifest() -> None:
    for relative_path in (
        Path("scripts/install.sh"),
        Path("scripts/update.sh"),
        Path("scripts/install-remote.sh"),
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "safe-managed-remove.py" in text
        assert "managed-install.json" in text
        assert 'python "$REMOVER_SOURCE" child' in text
        assert 'cp "$MANIFEST_SOURCE" "$MANIFEST_PATH"' in text
        assert 'cp "$REMOVER_SOURCE" "$REMOVER_PATH"' in text
        assert 'rm -rf "$target/' not in text
