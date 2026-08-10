from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final, Literal, TypeAlias


# E3: mechanical digest staleness. A digest is a compressed, AI-authored summary of a
# fixed set of source records. If any of those sources change after the digest is
# written, the digest can silently drift out of date while still reading as
# authoritative. `coverage_hash` is a deterministic fingerprint over the *current*
# content of the digest's declared source_records; recomputing and comparing it turns
# "is this digest still accurate?" from an AI judgement into a mechanical check.
#
# Contract:
#   - Only digests that declare a `coverage_hash` frontmatter field are checkable.
#     Legacy digests without it return verdict "unknown" (never a false "stale").
#   - The hash covers exactly the source files listed under `source_records`, by
#     relative path plus SHA-256 of bytes, order-independent. A missing source file
#     is itself a coverage change (it participates as an explicit "<missing>" marker).

CoverageVerdict: TypeAlias = Literal["current", "stale", "unknown"]

COVERAGE_HASH_FIELD: Final[str] = "coverage_hash"
SOURCE_RECORDS_FIELD: Final[str] = "source_records"


def _frontmatter_lines(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return []
    for index in range(1, len(lines)):
        if lines[index] == "---":
            return lines[1:index]
    return []


def parse_digest_coverage(digest_text: str) -> tuple[list[str], str]:
    """Return (source_records relative paths, stored coverage_hash) from a digest.

    stored coverage_hash is "" when the digest predates the field.
    """
    frontmatter = _frontmatter_lines(digest_text)
    source_records: list[str] = []
    stored_hash = ""
    in_sources = False
    for line in frontmatter:
        stripped = line.strip()
        if stripped.startswith(f"{COVERAGE_HASH_FIELD}:"):
            stored_hash = stripped.split(":", 1)[1].strip()
            in_sources = False
            continue
        if stripped == f"{SOURCE_RECORDS_FIELD}:":
            in_sources = True
            continue
        if in_sources and stripped.startswith("-"):
            source_records.append(stripped.lstrip("- ").strip())
            continue
        if in_sources and stripped and not line.startswith(" "):
            in_sources = False
    return source_records, stored_hash


def compute_coverage_hash(root: Path, source_records: list[str]) -> str:
    """Return a deterministic, order-independent hash over the current source files."""
    parts: list[str] = []
    for rel_path in sorted(source_records):
        source = root / ".sybermem" / rel_path
        if source.is_file():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
        else:
            digest = "<missing>"
        parts.append(f"{rel_path}:{digest}")
    joined = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def digest_coverage_verdict(root: Path, digest_text: str) -> CoverageVerdict:
    """Classify a digest as current/stale/unknown by mechanical coverage comparison."""
    source_records, stored_hash = parse_digest_coverage(digest_text)
    if not stored_hash:
        return "unknown"
    if not source_records:
        return "unknown"
    return "current" if compute_coverage_hash(root, source_records) == stored_hash else "stale"
