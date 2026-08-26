#!/usr/bin/env python3
"""SyberMem release orchestrator.

Fixes the release chain into one deterministic, un-skippable sequence so the
distributed package on `main` can never drift from the source or the version:

    1. write VERSION = X.Y.Z (single source of truth)
    2. scripts/sync-version.py         -> fan the version into all 9 manifests
    3. bun scripts/build-opencode-plugin.mjs -> rebundle the OpenCode plugin
    4. cut CHANGELOG.md: "## Unreleased" -> "## X.Y.Z - YYYY-MM-DD", open a fresh
       empty "## Unreleased" on top
    5. scripts/check-plugin-package.py  -> consistency guard (version + bundle)

Distribution model note: SyberMem ships via `archive/main.zip` (no git tags / no
GitHub Releases). "Publishing" is therefore: run this script, then commit and push
the resulting VERSION bump to `main`. The remote-version signal reads
`main/VERSION`, so pushing is what makes users see the new version.

Usage:
    python scripts/release.py X.Y.Z            # perform the release chain
    python scripts/release.py X.Y.Z --dry-run  # show what would change, mutate nothing

This script only prepares the working tree. It never commits, tags, or pushes.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
UNRELEASED_RE = re.compile(r"(?m)^##\s+Unreleased\s*$")

# Empty Unreleased scaffold opened on top after a cut.
FRESH_UNRELEASED = "## Unreleased\n"


class ReleaseError(RuntimeError):
    pass


def _log(msg: str) -> None:
    print(f"[release] {msg}")


def read_current_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.is_file() else ""


def parse_semver(version: str) -> tuple[int, int, int]:
    if not SEMVER_RE.match(version):
        raise ReleaseError(f"version must be X.Y.Z (semver), got {version!r}")
    a, b, c = version.split(".")
    return int(a), int(b), int(c)


def validate_bump(new_version: str) -> None:
    """Reject a non-increasing version so a release can't silently go backwards."""
    new = parse_semver(new_version)
    current = read_current_version()
    if not current:
        return
    if not SEMVER_RE.match(current):
        _log(f"warning: current VERSION {current!r} is not semver; skipping monotonicity check")
        return
    cur = parse_semver(current)
    if new <= cur:
        raise ReleaseError(
            f"new version {new_version} must be greater than current {current} "
            f"(this script only moves versions forward)"
        )


def cut_changelog(new_version: str, *, today: str, dry_run: bool) -> str:
    """Turn the top '## Unreleased' section into '## X.Y.Z - today' and open a fresh
    empty '## Unreleased' above it. Returns a human summary. Idempotency-safe:
    refuses to cut when Unreleased has no content (nothing to release)."""
    if not CHANGELOG_FILE.is_file():
        raise ReleaseError("CHANGELOG.md not found")
    text = CHANGELOG_FILE.read_text(encoding="utf-8")

    m = UNRELEASED_RE.search(text)
    if not m:
        raise ReleaseError("no '## Unreleased' section found in CHANGELOG.md")

    # Slice the Unreleased body: from end of the heading line to the next '## ' heading.
    body_start = m.end()
    next_heading = re.search(r"(?m)^##\s+", text[body_start:])
    body_end = body_start + next_heading.start() if next_heading else len(text)
    unreleased_body = text[body_start:body_end].strip("\n")

    if not unreleased_body.strip():
        raise ReleaseError(
            "## Unreleased is empty — nothing to release. Add changelog entries first."
        )

    before = text[: m.start()]
    after = text[body_end:]
    versioned_heading = f"## {new_version} - {today}\n"
    new_section = f"{FRESH_UNRELEASED}\n{versioned_heading}\n{unreleased_body}\n"
    new_text = f"{before}{new_section}\n{after.lstrip(chr(10))}"

    if dry_run:
        return f"would cut ## Unreleased -> ## {new_version} - {today} (fresh Unreleased opened on top)"
    CHANGELOG_FILE.write_text(new_text, encoding="utf-8")
    return f"cut ## Unreleased -> ## {new_version} - {today} (fresh Unreleased opened on top)"


def write_version(new_version: str, *, dry_run: bool) -> str:
    if dry_run:
        return f"would write VERSION = {new_version} (currently {read_current_version() or 'unset'})"
    VERSION_FILE.write_text(new_version + "\n", encoding="utf-8")
    return f"wrote VERSION = {new_version}"


def run(cmd: list[str], *, dry_run: bool, label: str) -> str:
    if dry_run:
        return f"would run: {' '.join(cmd)}"
    _log(f"running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.rstrip(), file=sys.stderr)
        raise ReleaseError(f"{label} failed (exit {result.returncode})")
    return f"{label} ok"


def main() -> int:
    parser = argparse.ArgumentParser(description="SyberMem release orchestrator")
    parser.add_argument("version", help="new version, e.g. 0.2.0")
    parser.add_argument("--dry-run", action="store_true", help="show actions, mutate nothing")
    args = parser.parse_args()

    try:
        validate_bump(args.version)
        today = _dt.date.today().isoformat()

        _log(f"=== SyberMem release {args.version}{' (dry-run)' if args.dry_run else ''} ===")

        # In dry-run, do the CHANGELOG check FIRST so an empty Unreleased fails fast
        # before we would touch anything. In a real run, order is: VERSION -> sync ->
        # bundle -> changelog -> guard, but we still pre-validate the changelog cut.
        _log(cut_changelog(args.version, today=today, dry_run=True))  # validate only

        _log(write_version(args.version, dry_run=args.dry_run))
        _log(run([sys.executable, "scripts/sync-version.py"], dry_run=args.dry_run, label="sync-version"))
        _log(run(["bun", "scripts/build-opencode-plugin.mjs"], dry_run=args.dry_run, label="build-bundle"))
        _log(cut_changelog(args.version, today=today, dry_run=args.dry_run))
        _log(run([sys.executable, "scripts/check-plugin-package.py"], dry_run=args.dry_run, label="guard"))

        if args.dry_run:
            _log("dry-run complete; no files changed.")
        else:
            _log("release prepared. Next: review the diff, then commit and push to main:")
            _log(f'    git add -A && git commit -m "release: v{args.version}" && git push')
            _log("pushing VERSION to main is what publishes the release (remote-version signal reads main/VERSION).")
        return 0
    except ReleaseError as e:
        print(f"[release] ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
