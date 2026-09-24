from __future__ import annotations

from pathlib import Path

from .records import parse_project_yaml
from .version import get_installed_version, project_needs_update


def version_report(root: Path | None) -> dict[str, object]:
    """Report installed vs project SyberMem version and whether an update is due.

    - ``installed``: the sybermem-core version currently on this machine.
    - ``project``: the version stamped in ``.sybermem/project.yaml`` (or empty).
    - ``outdated``: True when a MANAGED project trails installed OR has no stamp
      yet (an old project that predates the version field — it still needs a
      one-time /sybermem-update to bootstrap version tracking and migrations).
    - ``recommendation``: the action to surface when outdated.

    Fail-open: any error reading/parsing project.yaml yields an empty project
    version and unmanaged state (never outdated), so a malformed file cannot
    crash `doctor`.
    """
    installed = get_installed_version()
    project = ""
    is_managed = False
    if root is not None:
        is_managed = (root / ".sybermem" / "project.yaml").is_file()
        if is_managed:
            try:
                project = parse_project_yaml(root).get("sybermem_version", "")
            except Exception:
                project = ""
                is_managed = False  # unreadable identity -> treat as not judgeable
    outdated = project_needs_update(
        is_managed=is_managed, project_version=project, installed_version=installed
    )
    return {
        "installed": installed,
        "project": project,
        "outdated": outdated,
        "recommendation": "/sybermem-update" if outdated else "",
    }


def runtime_report(root: Path | None, version: dict[str, object]) -> dict[str, object]:
    """Bounded, read-only evidence for this CLI invocation, not a host probe.

    No host/session/turn identity is available to a standalone CLI process. Do
    not promote project stamps, old journals, or on-disk plugins to live proof.
    """
    return {
        "installation": {
            "status": "available",
            "version": version["installed"],
            "evidence": "currently executing SyberMem CLI/core; version from sybermem-core package metadata or bundled fallback",
            "reason": "Only this CLI/core invocation is proven; host installation is not checked.",
        },
        "project_stamp": {
            "status": "not_found" if root is None else ("stamped" if version["project"] else "unknown"),
            "version": version["project"],
            "outdated": version["outdated"],
            "reason": "Project version is an on-disk stamp, not proof of host installation or loading.",
        },
        "host_loaded": {
            "status": "unknown",
            "reason": "No live host identity or host receipt evidence is available to this CLI invocation.",
            "next_check": "In the current host session, check host-native plugin or hook loading evidence.",
        },
        "current_turn_delivery": {
            "status": "unknown",
            "reason": "No live turn identity or host context delivery receipt is available to this CLI invocation.",
            "next_check": "In the current host turn, inspect host-native context delivery evidence; delivery does not prove model use.",
        },
    }
