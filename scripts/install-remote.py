from __future__ import annotations

import io
from pathlib import Path
import sys
import tempfile
import urllib.request
import zipfile


REPO_ZIP = "https://github.com/goudaren0528/sybermem/archive/main.zip"


def main() -> int:
    """Download and install SyberMem without spawning PowerShell."""
    print("=== SyberMem Remote Python Install ===")
    with urllib.request.urlopen(REPO_ZIP) as response:
        archive = response.read()
    with tempfile.TemporaryDirectory(prefix="sybermem-install-") as temporary:
        root = Path(temporary) / "sybermem-main"
        with zipfile.ZipFile(io.BytesIO(archive)) as package:
            package.extractall(temporary)
        if not (root / "packages" / "claude-skills").is_dir():
            raise RuntimeError("Skills not found in downloaded archive")
        sys.path.insert(0, str(root / "scripts"))
        from _install_common import install_from_checkout

        install_from_checkout(root)
    print("Available Skills: /sybermem-init-project /sybermem-update /using-sybermem")
    print("=== Installation Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
