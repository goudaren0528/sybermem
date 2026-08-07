from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CHECK_SCRIPT = ROOT / "scripts" / "check-plugin-package.py"


def test_package_integrity_checks_all_runtime_refresh_scripts() -> None:
    # Given: package integrity checks are the distribution contract for runtime refresh wiring
    checker = runpy.run_path(str(CHECK_SCRIPT))

    # When / Then: both local and remote install/update scripts are covered by the runtime refresh check
    assert checker["RUNTIME_REFRESH_SCRIPTS"] == [
        Path("scripts/install.sh"),
        Path("scripts/install.ps1"),
        Path("scripts/install-remote.sh"),
        Path("scripts/install-remote.ps1"),
        Path("scripts/update.sh"),
        Path("scripts/update.ps1"),
    ]


def test_local_install_and_update_scripts_force_refresh_core_and_cli_packages() -> None:
    # Given: local install/update scripts are supported runtime refresh entrypoints
    scripts = (
        ROOT / "scripts" / "install.sh",
        ROOT / "scripts" / "install.ps1",
        ROOT / "scripts" / "update.sh",
        ROOT / "scripts" / "update.ps1",
    )

    # When / Then: they force reinstall both Core and CLI packages just like remote installers
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        core_fragment = "packages/core" if script.suffix == ".sh" else "packages\\core"
        cli_fragment = "packages/cli" if script.suffix == ".sh" else "packages\\cli"
        assert core_fragment in text
        assert cli_fragment in text
        assert "--upgrade" in text
        assert "--force-reinstall" in text
