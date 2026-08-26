from __future__ import annotations

from importlib import metadata

# Bundled fallback, kept in sync with the repo-root VERSION file by
# scripts/sync-version.py. importlib.metadata is the source of truth when the
# package is installed; this constant only backstops editable/source checkouts.
FALLBACK_VERSION = "0.2.0"


def get_installed_version() -> str:
    """Return the installed sybermem-core version, or the bundled fallback."""
    try:
        return metadata.version("sybermem-core")
    except metadata.PackageNotFoundError:
        return FALLBACK_VERSION
    except Exception:
        return FALLBACK_VERSION


def _parse(version: str) -> tuple[int, ...]:
    """Parse a dotted version into an int tuple; non-numeric parts become 0.

    Trailing pre-release/build suffixes on a component (e.g. ``1rc2``) are
    truncated to their leading digits so ``0.2.0`` and ``0.2.0rc1`` still order
    sensibly without a full PEP 440 parser.
    """
    parts: list[int] = []
    for raw in version.strip().split("."):
        digits = ""
        for ch in raw:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def compare_versions(a: str, b: str) -> int:
    """Return -1 if a<b, 0 if equal, 1 if a>b (numeric, dot-separated)."""
    pa, pb = _parse(a), _parse(b)
    width = max(len(pa), len(pb))
    pa += (0,) * (width - len(pa))
    pb += (0,) * (width - len(pb))
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def is_outdated(project_version: str, installed_version: str) -> bool:
    """True when a project was last refreshed by an older sybermem than installed.

    Fail-safe: unknown/empty project version is NOT treated as outdated to avoid
    nagging brand-new or unmanaged projects.

    NOTE: this is the pure version-string comparison. To decide whether to nudge a
    MANAGED project, use `project_needs_update`, which also treats a managed project
    that has no `sybermem_version` stamp yet (predates the field) as needing update.
    """
    if not project_version or not installed_version:
        return False
    return compare_versions(project_version, installed_version) < 0


def project_needs_update(
    *, is_managed: bool, project_version: str, installed_version: str
) -> bool:
    """Decide whether a managed project should be nudged to run /sybermem-update.

    Tri-state, so old projects can bootstrap into version tracking:
    - installed unknown (no VERSION marker) -> False (can't judge; fail-safe).
    - not a managed project (no `.sybermem/project.yaml`) -> False.
    - managed but no `sybermem_version` stamp (project predates the field) -> True.
    - managed and stamp < installed -> True.
    - managed and stamp >= installed -> False.
    """
    if not installed_version or not is_managed:
        return False
    if not project_version:
        return True
    return compare_versions(project_version, installed_version) < 0
