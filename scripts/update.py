from __future__ import annotations

from pathlib import Path
import sys

from _install_common import install_from_checkout


def main() -> int:
    """Refresh the global install from the current SyberMem checkout."""
    root = Path(__file__).resolve().parent.parent
    print("=== SyberMem Python Update ===")
    install_from_checkout(root)
    print("Available Skills:")
    for name in ("sybermem-init-project", "sybermem-record", "sybermem-summary", "sybermem-resume", "sybermem-digest", "sybermem-phase-analyze", "using-sybermem", "sybermem-update", "sybermem-search", "sybermem-link", "sybermem-theme-digest", "sybermem-habit", "sybermem-uninstall"):
        print(f"  /{name}")
    print("=== Update Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
