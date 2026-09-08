"""Test-only structural validators for the SyberMem skill discovery surface.

These helpers exist so Skill/document instruction artifacts can be locked by
structure instead of prose snapshots. They intentionally assert only:

* headings and machine-consumed command names,
* exact membership sets against the distribution manifest,
* required safety / launcher tokens,
* structured catalog rows and reassessment table fields.

They never assert whole-paragraph wording and never import runtime modules.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# --- using-sybermem orientation contract -----------------------------------

DEFAULT_FLOW_HEADING = "## Default orientation flow"
ADVANCED_DIAGNOSTICS_HEADING = "## Advanced diagnostics"

DEFAULT_FLOW_REQUIRED = (
    "sybermem next-step --format json",
    "project root",
    "installation status",
    "project status",
    "Do not run downstream actions",
)

ADVANCED_DIAGNOSTICS_REQUIRED = (
    "hooks",
    "anchors",
    "legacy protocol",
)

WINDOWS_LAUNCHER_FRAGMENT = r"$env:USERPROFILE\.claude\sybermem\cli\sybermem.cmd"
UNIX_LAUNCHER_FRAGMENT = "$HOME/.claude/sybermem/cli/sybermem"

FILE_REQUIRED = (
    WINDOWS_LAUNCHER_FRAGMENT,
    UNIX_LAUNCHER_FRAGMENT,
    "$SyberMemCli",
    "SYBERMEM_CLI",
    "Do not modify persistent PATH automatically",
)

# --- Core / Advanced discovery catalog -------------------------------------

CORE_HEADING = "### Core entrypoints"
ADVANCED_HEADING = "### Advanced / lifecycle"

CATALOG_ROW = re.compile(r"^- `(?P<name>[A-Za-z0-9._/-]+)`: (?P<description>\S.*)$")

FORBIDDEN_ADVANCED_TOKENS = ("retired", "deprecated")

# --- terminal reassessment table -------------------------------------------

REASSESSMENT_COLUMNS = (
    "Candidate",
    "Verdict",
    "User impact",
    "Compatibility impact",
    "Migration need",
    "Evidence",
)

REASSESSMENT_CANDIDATES = (
    "phase-analyze/digest",
    "summary/resume",
    "theme-digest/digest",
    "using-sybermem/doctor-update",
)

ALLOWED_VERDICTS = ("retain", "propose future change", "reject")

FORBIDDEN_REASSESSMENT_DIRECTIVES = ("retire now", "remove manifest", "delete skill")


def _read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def _heading_level(line: str) -> int | None:
    match = re.match(r"^(#{1,6})\s", line)
    if match is None:
        return None
    return len(match.group(1))


def _section_lines(text: str, heading: str) -> list[str]:
    """Return the lines under ``heading`` up to the next equal/higher heading."""

    level = _heading_level(heading + " ")
    if level is None:
        raise AssertionError(f"not a heading: {heading!r}")

    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        raise AssertionError(f"missing heading: {heading!r}")

    collected: list[str] = []
    for line in lines[start:]:
        current = _heading_level(line)
        if current is not None and current <= level:
            break
        collected.append(line)
    return collected


def _heading_index(text: str, heading: str) -> int:
    for index, line in enumerate(text.splitlines()):
        if line.strip() == heading:
            return index
    raise AssertionError(f"missing heading: {heading!r}")


def validate_using_skill(path: Path) -> None:
    """Assert the using-sybermem orientation contract for one Skill file."""

    text = _read(path)

    default_index = _heading_index(text, DEFAULT_FLOW_HEADING)
    advanced_index = _heading_index(text, ADVANCED_DIAGNOSTICS_HEADING)
    if default_index >= advanced_index:
        raise AssertionError(
            f"{path}: {DEFAULT_FLOW_HEADING!r} must appear before {ADVANCED_DIAGNOSTICS_HEADING!r}"
        )

    default_section = "\n".join(_section_lines(text, DEFAULT_FLOW_HEADING))
    for token in DEFAULT_FLOW_REQUIRED:
        if token not in default_section:
            raise AssertionError(f"{path}: default orientation flow missing {token!r}")

    advanced_section = "\n".join(_section_lines(text, ADVANCED_DIAGNOSTICS_HEADING))
    for token in ADVANCED_DIAGNOSTICS_REQUIRED:
        if token not in advanced_section:
            raise AssertionError(f"{path}: advanced diagnostics missing {token!r}")

    for token in FILE_REQUIRED:
        if token not in text:
            raise AssertionError(f"{path}: skill file missing required token {token!r}")


def parse_skill_catalog(path: Path) -> dict[str, tuple[str, ...]]:
    """Parse the Core/Advanced bullet catalog from one document.

    Returns ``{"core": (...), "advanced": (...)}`` preserving document order.
    """

    text = _read(path)
    catalog: dict[str, tuple[str, ...]] = {}
    for key, heading in (("core", CORE_HEADING), ("advanced", ADVANCED_HEADING)):
        names: list[str] = []
        for line in _section_lines(text, heading):
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            match = CATALOG_ROW.match(stripped)
            if match is None:
                raise AssertionError(f"{path}: malformed catalog row under {heading!r}: {stripped!r}")
            name = match.group("name").strip("`")
            if not match.group("description").strip():
                raise AssertionError(f"{path}: empty description for {name!r}")
            if name in names:
                raise AssertionError(f"{path}: duplicate catalog entry {name!r} under {heading!r}")
            names.append(name)
        if not names:
            raise AssertionError(f"{path}: no catalog rows under {heading!r}")
        catalog[key] = tuple(names)

    overlap = set(catalog["core"]) & set(catalog["advanced"])
    if overlap:
        raise AssertionError(f"{path}: skills listed in both tiers: {sorted(overlap)}")

    advanced_section = "\n".join(_section_lines(text, ADVANCED_HEADING)).lower()
    for token in FORBIDDEN_ADVANCED_TOKENS:
        if token in advanced_section:
            raise AssertionError(f"{path}: advanced tier must not imply {token!r} status")

    return catalog


def validate_taxonomy(paths: tuple[Path, ...], manifest_path: Path) -> None:
    """Assert every document exposes the same complete Core/Advanced taxonomy."""

    if not paths:
        raise AssertionError("validate_taxonomy requires at least one document")

    manifest = json.loads(_read(manifest_path))
    manifest_skills = set(manifest["skills"])

    reference: dict[str, tuple[str, ...]] | None = None
    reference_path: Path | None = None
    for path in paths:
        catalog = parse_skill_catalog(path)
        if reference is None:
            reference, reference_path = catalog, path
        elif catalog != reference:
            raise AssertionError(
                f"taxonomy mismatch between {reference_path} and {path}: "
                f"{reference} != {catalog}"
            )

    assert reference is not None
    union = list(reference["core"]) + list(reference["advanced"])
    if len(union) != len(set(union)):
        raise AssertionError(f"taxonomy contains duplicate skills: {union}")
    if set(union) != manifest_skills:
        missing = sorted(manifest_skills - set(union))
        extra = sorted(set(union) - manifest_skills)
        raise AssertionError(
            f"taxonomy must equal manifest skills; missing={missing} extra={extra}"
        )


def validate_reassessment(path: Path) -> None:
    """Assert the terminal reassessment table records evidence without directives."""

    text = _read(path)
    lowered = text.lower()
    for directive in FORBIDDEN_REASSESSMENT_DIRECTIVES:
        if directive in lowered:
            raise AssertionError(f"{path}: reassessment must not contain directive {directive!r}")

    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != len(REASSESSMENT_COLUMNS):
            continue
        if all(set(cell) <= {"-", ":"} and cell for cell in cells):
            continue
        rows.append(cells)

    if not rows:
        raise AssertionError(f"{path}: no reassessment table found")

    header, *body = rows
    if tuple(header) != REASSESSMENT_COLUMNS:
        raise AssertionError(
            f"{path}: reassessment columns must be {list(REASSESSMENT_COLUMNS)}, got {header}"
        )

    candidates = [row[0] for row in body]
    if len(candidates) != len(REASSESSMENT_CANDIDATES):
        raise AssertionError(
            f"{path}: expected {len(REASSESSMENT_CANDIDATES)} candidate rows, got {len(candidates)}"
        )
    if sorted(candidates) != sorted(REASSESSMENT_CANDIDATES):
        raise AssertionError(
            f"{path}: candidates must be {sorted(REASSESSMENT_CANDIDATES)}, got {sorted(candidates)}"
        )

    for row in body:
        candidate, verdict = row[0], row[1]
        if verdict not in ALLOWED_VERDICTS:
            raise AssertionError(
                f"{path}: verdict for {candidate!r} must be one of {list(ALLOWED_VERDICTS)}, got {verdict!r}"
            )
        for column, cell in zip(REASSESSMENT_COLUMNS, row):
            if not cell:
                raise AssertionError(f"{path}: empty {column!r} field for candidate {candidate!r}")
