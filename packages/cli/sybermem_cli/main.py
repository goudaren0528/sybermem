from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path
from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root, ensure_project_yaml
from sybermem_core.project_refresh import refresh_project
from sybermem_core.project_index import RECORD_TYPES, DuplicateRecordIdError, InvalidRecordMetadataError, check_project_index, write_project_index
from sybermem_core.phase_index import PhaseApplyError, analyze_phases, apply_phase_payload, resolve_record_paths
from sybermem_core.digest_coverage import compute_coverage_hash
from sybermem_core.records import generate_record_id, related_files_by_record
from sybermem_core.registry import register_project
from sybermem_core.identity import git_remote
from sybermem_core.index import rebuild_index
from sybermem_core.search import ProjectRootNotFoundError, WorkspaceIndexIncompatibleError, search_project, search_workspace, workspace_index_staleness
from sybermem_core.status import project_memory_stats, project_status
from sybermem_core.resume import build_resume_checkpoint
from sybermem_core.next_step_router import classify_record_intent, recommend_next_step
from sybermem_core.digest_governance import build_digest_governance_report, latest_digest_summary
from sybermem_core.norms import constitution, nominate_norm_candidates, norm_conflicts, scoped_norms
from sybermem_core.portfolio import build_portfolio
from sybermem_core.team import init_team_repo
from sybermem_core.publish_bootstrap import bootstrap_publish_status
from sybermem_core.team_summary import build_team_management_summary
from sybermem_core.uninstall import deactivate_project_sybermem
from sybermem_core.version import get_installed_version
from sybermem_core.doctor import version_report
from sybermem_cli.habits import register_habit_commands
from sybermem_cli.context import register_context_commands
from sybermem_cli.memory_stats_render import render_project_memory_stats_text
from sybermem_cli.publish_render import render_publish_status_text
from sybermem_cli.search_render import render_search_text


def cmd_project_init(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found. Run /sybermem-init-project first.", file=sys.stderr)
        return 1
    status, project_id, slug = ensure_project_yaml(root)
    if args.register:
        register_project(project_id, slug, root)
    payload = {
        "status": status,
        "project_id": project_id,
        "slug": slug,
        "path": str(root).replace('\\', '/'),
        "remote": git_remote(root),
    }
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"{status}: {slug} ({project_id}) @ {payload['path']}")
    return 0


def cmd_index_build(args: argparse.Namespace) -> int:
    result = rebuild_index(args.project)
    if args.format == "json":
        print(dump_json(result))
    else:
        print(f"indexed {result['projects']} projects, {result['records']} records")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    stale: list[dict] = []
    if args.scope == "workspace":
        try:
            results = search_workspace(args.query, project=args.project, type_=args.type, project_status=args.project_status)
        except (FileNotFoundError, WorkspaceIndexIncompatibleError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        stale = workspace_index_staleness()
    else:
        try:
            results = search_project(args.query)
        except ProjectRootNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    payload = {
        "query": args.query,
        "scope": args.scope,
        "filters": {
            "project": args.project,
            "type": args.type,
            "project_status": args.project_status,
        },
        "results": results,
    }
    if args.scope == "workspace":
        payload["index_staleness"] = stale
    if args.format == "json":
        print(dump_json(payload))
    else:
        render_search_text(results)
        if stale:
            slugs = ", ".join(entry.get("slug", entry.get("project_id", "")) for entry in stale)
            print(
                f"note: {len(stale)} project(s) have a stale workspace index "
                f"(indexed HEAD != current HEAD); run 'sybermem index build' to refresh: {slugs}",
                file=sys.stderr,
            )
    return 0


def cmd_record_id(args: argparse.Namespace) -> int:
    record_id = generate_record_id(args.type)
    if args.format == "json":
        print(dump_json({"record_id": record_id, "type": args.type}))
    else:
        print(record_id)
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    checkpoint = build_resume_checkpoint(root, mode=args.mode)
    if args.format == "json":
        print(dump_json(checkpoint))
        return 0

    phase = checkpoint["active_phase"]
    phase_label = phase.get("id") or phase.get("name") or "(no phase)"
    project = checkpoint["project"]
    print(f"[{project['slug']}] resume ({checkpoint['mode']})")
    for line in checkpoint.get("brief", []):
        print(f"  {line}")
    print(f"- current phase: {phase_label} {phase.get('name', '')}".rstrip())
    print(f"- confidence: {checkpoint['confidence']}  freshness: {checkpoint['freshness']}")

    progress = checkpoint["progress"]
    if progress:
        print("- recent progress:")
        for item in progress:
            print(f"  - [{item['record_id']}] {item['title']}")

    risks = checkpoint["risks"]
    if risks:
        print("- risks:")
        for risk in risks:
            print(f"  - {risk.get('summary', risk)}")

    action = checkpoint["next_action"]
    print(f"- next action: {action['action']} — {action['reason']}")

    if checkpoint.get("read_targets"):
        print("- read targets:")
        for target in checkpoint["read_targets"]:
            print(f"  - {target}")
    return 0


def cmd_next_step(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        payload = {
            "action": "/sybermem-init-project",
            "reason": "No SyberMem project root found. Initialize the project first.",
        }
        if args.format == "json":
            print(dump_json(payload))
        else:
            print(f"next: {payload['action']} — {payload['reason']}")
        return 0
    payload = recommend_next_step(root)
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"next: {payload['action']} — {payload['reason']}")
    return 0


def cmd_digest_status(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    report = build_digest_governance_report(root)
    if args.format == "json":
        print(dump_json(report))
    else:
        if report["total"] == 0:
            print("No digests found.")
            return 0
        print(
            f"digests: {report['total']} total — "
            f"{report['stale']} stale, {report['unknown']} unknown, {report['current']} current"
        )
        for digest in report["digests"]:
            marker = {"stale": "⚠ ", "unknown": "? ", "current": "✓ "}.get(digest["verdict"], "")
            print(f"{marker}[{digest['record_id']}] {digest['title']} — {digest['verdict']}")
            if digest["verdict"] != "current":
                print(f"    {digest['reason']}")
                for drift in digest["drifted_sources"]:
                    print(f"    - {drift['state']}: {drift['path']}")
    # Non-zero exit when any digest is stale, so scripts/CI can gate on governance health.
    return 1 if report["stale"] > 0 else 0


def cmd_digest_latest(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    summary = latest_digest_summary(root)
    if args.format == "json":
        print(dump_json(summary or {}))
    else:
        if not summary:
            print("No digest found.")
            return 0
        print(f"[{summary['record_id']}] {summary['title']} ({summary['date']})")
        for line in summary["conclusions"]:
            print(line)
    return 0


def cmd_norms_list(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    if args.scope == "global":
        norms = constitution(root)
    elif args.scope == "scoped":
        norms = scoped_norms(root, args.context)
    else:
        # "all": the constitution plus, when a context is given, the relevant scoped norms.
        norms = constitution(root)
        if args.context:
            seen = {n["record_id"] for n in norms}
            norms = norms + [n for n in scoped_norms(root, args.context) if n["record_id"] not in seen]
    if args.format == "json":
        print(dump_json({"norms": norms}))
    else:
        if not norms:
            print("No matching norms.")
            return 0
        for norm in norms:
            print(f"[{norm['record_id']}] ({norm['scope'] or 'unscoped'}) {norm['statement']}")
    return 0


def cmd_norms_nominate(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    nominations = nominate_norm_candidates(root)
    if args.format == "json":
        print(dump_json({"nominations": nominations}))
    else:
        if not nominations:
            print("No norm nominations.")
            return 0
        for nom in nominations:
            print(f"({nom['occurrences']}x) {nom['sample']}")
            print(f"    evidence: {', '.join(nom['evidence'])}")
    return 0


def cmd_norms_doctor(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    conflicts = norm_conflicts(root)
    if args.format == "json":
        print(dump_json({"conflicts": conflicts}))
    else:
        if not conflicts:
            print("No norm conflicts.")
            return 0
        for c in conflicts:
            print(f"[{c['scope']}] conflict: {', '.join(c['norms'])}")
            print(f"    {c['reason']}")
    # Non-zero exit when conflicts exist so scripts/CI can gate on norm governance health.
    return 1 if conflicts else 0


def cmd_project_status(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    payload = project_status(root)
    if args.format == "json":
        print(dump_json(payload))
    else:
        phase = payload["phase"]
        print(f"[{payload['slug']}] {phase['id'] or phase['name']}")
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    installed = get_installed_version()
    if args.format == "json":
        print(dump_json({"installed": installed}))
    else:
        print(installed)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    report = version_report(root)
    if args.format == "json":
        print(dump_json(report))
        return 0
    installed = report["installed"]
    project = report["project"] or "(not stamped)"
    print(f"SyberMem installed: {installed}")
    print(f"This project:       {project}")
    if report["outdated"]:
        print(f"⭐ This project trails the installed SyberMem — run {report['recommendation']} to apply updates.")
    else:
        print("This project is current with the installed SyberMem.")
    return 0


def cmd_portfolio(args: argparse.Namespace) -> int:
    payload = build_portfolio()
    if args.format == "json":
        print(dump_json(payload))
    else:
        buckets = {"active": [], "stale": [], "missing": []}
        for p in payload["projects"]:
            buckets.setdefault(p["status"], []).append(p)

        for status_key in ["active", "stale", "missing"]:
            items = buckets.get(status_key, [])
            if not items:
                continue
            print(f"[{status_key}]")
            for p in items:
                if status_key == "missing":
                    print(f"- {p['slug']} → {p['reason']}")
                else:
                    phase = p["phase"]
                    phase_label = phase.get("id") or phase.get("name") or "(no phase)"
                    phase_name = phase.get("name", "")
                    head = f"{phase_label} {phase_name}".strip() if (phase_name and phase.get("id")) else phase_label
                    signals = []
                    if p.get("open_bugs"):
                        signals.append(f"{p['open_bugs']} open bug(s)")
                    if p.get("open_requirements"):
                        signals.append(f"{p['open_requirements']} open req(s)")
                    if p.get("digest_uncovered"):
                        signals.append(f"{p['digest_uncovered']} undigested")
                    if p.get("latest_record_date"):
                        signals.append(f"last {p['latest_record_date']}")
                    suffix = f"  [{'; '.join(signals)}]" if signals else ""
                    print(f"- {p['slug']} → {head}{suffix}")
            print("")
    return 0


def cmd_team_init(args: argparse.Namespace) -> int:
    try:
        payload = init_team_repo(Path(args.path), args.team_id, args.name, args.remote)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Initialized team repo:")
        print(f"- team_id: {payload['team_id']}")
        print(f"- name: {payload['name']}")
        print(f"- path: {payload['path']}")
        print(f"- remote: {payload['remote']}")
    return 0


def cmd_publish_status(args: argparse.Namespace) -> int:
    try:
        tp = Path(args.team_path) if args.team_path else None
        payload = bootstrap_publish_status(tp, preview=args.preview, preview_source_hash=args.preview_source_hash)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(dump_json(payload))
        if payload.get("status") in {"stale_preview", "blocked"}:
            return 1
    else:
        return render_publish_status_text(payload)
    return 0


def cmd_project_memory_stats(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    payload = project_memory_stats(root)
    if args.format == "json":
        print(dump_json(payload))
    else:
        render_project_memory_stats_text(payload)
    return 0


def cmd_record_intent(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    candidate = classify_record_intent(root, args.prompt)
    bounded = {
        "classification": candidate["classification"],
        "action": candidate.get("action", ""),
        "reason": candidate.get("reason", ""),
    }
    if args.format == "json":
        print(dump_json(bounded))
    else:
        print(bounded["classification"])
    return 0


def cmd_team_summary(args: argparse.Namespace) -> int:
    try:
        result = build_team_management_summary(Path(args.team_path))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = result["payload"]
    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Generated Team management summary:")
        print(f"- team: {result['team_id']}")
        print(f"- markdown: {result['summary_markdown']}")
        print(f"- json: {result['summary_json']}")
        print(f"- baseline state: {result['summary_state']}")
        if payload.get("deep_review_candidates"):
            print("- suggested deeper review: inspect the projects listed under Worth Deeper Review")
    return 0


def cmd_project_uninstall(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    try:
        payload = deactivate_project_sybermem(root)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Deactivated SyberMem runtime in this project:")
        print(f"- project root: {payload['root']}")
        print("- history preserved: yes")
        if payload['changed_files']:
            print("- changed files:")
            for f in payload['changed_files']:
                print(f"  - {f}")
    return 0


def _project_index_path(root: Path) -> str:
    return str(root / ".sybermem" / "INDEX.md").replace('\\', '/')


def _project_index_payload(root: Path, status: str) -> dict[str, str]:
    return {"status": status, "path": _project_index_path(root)}


def cmd_project_index_build(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1

    try:
        updated = write_project_index(root)
    except (DuplicateRecordIdError, InvalidRecordMetadataError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = _project_index_payload(root, "updated" if updated else "unchanged")
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"{payload['status']}: {payload['path']}")
    return 0


def cmd_project_index_check(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1

    index_path = root / ".sybermem" / "INDEX.md"
    try:
        is_current = check_project_index(root)
    except (DuplicateRecordIdError, InvalidRecordMetadataError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    status = "current" if is_current else ("missing" if not index_path.is_file() else "stale")
    payload = _project_index_payload(root, status)
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"{payload['status']}: {payload['path']}")
    return 0 if is_current else 1


def cmd_project_refresh(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1

    try:
        report = refresh_project(root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.format == "json":
        print(dump_json(report))
    else:
        print(
            f"{report['overall']}: applied {len(report['actions_applied'])} action(s), "
            f"skipped {len(report['actions_skipped'])}, "
            f"preserved custom {len(report['preserved_custom'])}"
        )
    return 0


def cmd_project_record_files(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1

    ids = [item.strip() for item in (args.ids or "").split(",") if item.strip()] or None
    mapping = related_files_by_record(root, ids)
    if args.format == "json":
        print(dump_json({"records": mapping}))
    else:
        for record_id, files in sorted(mapping.items()):
            print(f"{record_id}: {', '.join(files) if files else '(none)'}")
    return 0


def cmd_project_phase_analyze(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    if args.from_json is not None:
        # Semantic path (primary): the agent provides a higher-quality grouping than
        # mechanical bucketing. Core validates coverage and persists deterministically.
        try:
            raw = sys.stdin.read() if args.from_json == "-" else Path(args.from_json).read_text(encoding="utf-8")
            payload = json.loads(raw)
        except (OSError, ValueError) as exc:
            print(f"Failed to read phase payload: {exc}", file=sys.stderr)
            return 1
        try:
            result = apply_phase_payload(root, payload)
        except PhaseApplyError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        # Mechanical fallback: month + primary-topic buckets. Never needs an agent.
        result = analyze_phases(root)
    if args.format == "json":
        print(dump_json(result))
    else:
        print(f"{result['status']}: {len(result['phases'])} phase(s)")
    return 0


def cmd_project_coverage_hash(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    source_records: list[str]
    if args.source_records:
        source_records = [item.strip() for item in args.source_records.split(",") if item.strip()]
    elif args.phase_id:
        idx = (root / ".sybermem" / "analysis" / "phase-index.md")
        if not idx.is_file():
            print("No phase index found; run phase analyze first.", file=sys.stderr)
            return 1
        text = idx.read_text(encoding="utf-8")
        record_ids = _covered_records_for_phase(text, args.phase_id)
        if record_ids is None:
            print(f"phase {args.phase_id} not found in phase index.", file=sys.stderr)
            return 1
        mapping = resolve_record_paths(root, record_ids)
        missing = [rid for rid in record_ids if rid not in mapping]
        source_records = [mapping[rid] for rid in record_ids if rid in mapping]
    else:
        print("Provide --source-records <relpaths> or --phase-id <phase-NNN>.", file=sys.stderr)
        return 1
    if not source_records:
        print("No source records resolved.", file=sys.stderr)
        return 1
    coverage_hash = compute_coverage_hash(root, source_records)
    result = {"source_records": source_records, "coverage_hash": coverage_hash}
    if args.format == "json":
        print(dump_json(result))
    else:
        print(coverage_hash)
    return 0


def _covered_records_for_phase(phase_index_text: str, phase_id: str) -> list[str] | None:
    """Return the covered record ids for a phase block, or None if the phase is absent."""
    import re as _re

    phase_re = _re.compile(r"^- phase_id: (phase-\d+)")
    lines = phase_index_text.splitlines()
    current_phase: str | None = None
    in_covered = False
    records: list[str] = []
    for line in lines:
        stripped = line.strip()
        phase_match = phase_re.match(stripped)
        if phase_match:
            # We've left the target phase: return what we collected for it (if any).
            if current_phase == phase_id:
                return records if records else None
            current_phase = phase_match.group(1)
            in_covered = False
            records = []
            continue
        if current_phase != phase_id:
            continue
        if stripped == "- covered_records:":
            in_covered = True
            continue
        if in_covered:
            if not line.startswith("  - "):
                in_covered = False
                continue
            item = stripped
            if item.startswith("- "):
                item = item[2:].strip()
            records.append(item)
    return records if records else None


def main() -> int:
    # Emit UTF-8 regardless of console locale. Record titles/conclusions and governance
    # markers can contain non-ASCII (CJK titles, ⚠/✓/⭐), which a locale like GBK on
    # Chinese Windows would otherwise fail to encode, crashing otherwise-correct output.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass

    parser = argparse.ArgumentParser(prog="sybermem")
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    init = project_sub.add_parser("init")
    init.add_argument("--register", action="store_true")
    init.add_argument("--format", choices=["text", "json"], default="text")
    init.set_defaults(func=cmd_project_init)

    status_cmd = project_sub.add_parser("status")
    status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    status_cmd.set_defaults(func=cmd_project_status)

    memory_stats_cmd = project_sub.add_parser("memory-stats")
    memory_stats_cmd.add_argument("--format", choices=["text", "json"], default="text")
    memory_stats_cmd.set_defaults(func=cmd_project_memory_stats)

    uninstall_cmd = project_sub.add_parser("uninstall")
    uninstall_cmd.add_argument("--format", choices=["text", "json"], default="text")
    uninstall_cmd.set_defaults(func=cmd_project_uninstall)

    refresh_cmd = project_sub.add_parser("refresh")
    refresh_cmd.add_argument("--format", choices=["text", "json"], default="text")
    refresh_cmd.set_defaults(func=cmd_project_refresh)

    record_files_cmd = project_sub.add_parser("record-files")
    record_files_cmd.add_argument("--ids", default="", help="Comma-separated record ids; empty means all records.")
    record_files_cmd.add_argument("--format", choices=["text", "json"], default="text")
    record_files_cmd.set_defaults(func=cmd_project_record_files)

    project_phase = project_sub.add_parser("phase")
    project_phase_sub = project_phase.add_subparsers(dest="project_phase_command", required=True)
    phase_analyze = project_phase_sub.add_parser("analyze")
    phase_analyze.add_argument(
        "--from-json",
        default=None,
        help="Path to a JSON phase payload {phases:[{title,covered_records}]}; use '-' for stdin. Semantic agent grouping (primary). Omit for mechanical fallback grouping.",
    )
    phase_analyze.add_argument("--format", choices=["text", "json"], default="text")
    phase_analyze.set_defaults(func=cmd_project_phase_analyze)

    coverage_hash_cmd = project_sub.add_parser("coverage-hash")
    coverage_hash_cmd.add_argument("--source-records", default="", help="Comma-separated project-relative source record paths.")
    coverage_hash_cmd.add_argument("--phase-id", default="", help="Resolve source records from this phase (e.g. phase-001) and hash them.")
    coverage_hash_cmd.add_argument("--format", choices=["text", "json"], default="text")
    coverage_hash_cmd.set_defaults(func=cmd_project_coverage_hash)

    project_index = project_sub.add_parser("index")
    project_index_sub = project_index.add_subparsers(dest="project_index_command", required=True)
    project_index_build = project_index_sub.add_parser("build")
    project_index_build.add_argument("--format", choices=["text", "json"], default="text")
    project_index_build.set_defaults(func=cmd_project_index_build)

    project_index_check = project_index_sub.add_parser("check")
    project_index_check.add_argument("--format", choices=["text", "json"], default="text")
    project_index_check.set_defaults(func=cmd_project_index_check)

    index = sub.add_parser("index")
    index_sub = index.add_subparsers(dest="index_command", required=True)
    build = index_sub.add_parser("build")
    build.add_argument("--project")
    build.add_argument("--format", choices=["text", "json"], default="text")
    build.set_defaults(func=cmd_index_build)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--scope", choices=["project", "workspace"], default="project")
    search.add_argument("--project")
    search.add_argument("--type")
    search.add_argument("--project-status")
    search.add_argument("--format", choices=["text", "json"], default="text")
    search.set_defaults(func=cmd_search)

    portfolio = sub.add_parser("portfolio")
    portfolio.add_argument("--format", choices=["text", "json"], default="text")
    portfolio.set_defaults(func=cmd_portfolio)

    resume = sub.add_parser("resume")
    resume.add_argument("--mode", choices=["fast", "standard", "deep"], default="fast")
    resume.add_argument("--format", choices=["text", "json"], default="text")
    resume.set_defaults(func=cmd_resume)

    next_step = sub.add_parser("next-step")
    next_step.add_argument("--format", choices=["text", "json"], default="text")
    next_step.set_defaults(func=cmd_next_step)

    digest = sub.add_parser("digest")
    digest_sub = digest.add_subparsers(dest="digest_command", required=True)
    digest_status_cmd = digest_sub.add_parser("status")
    digest_status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    digest_status_cmd.set_defaults(func=cmd_digest_status)

    digest_latest_cmd = digest_sub.add_parser("latest")
    digest_latest_cmd.add_argument("--format", choices=["text", "json"], default="text")
    digest_latest_cmd.set_defaults(func=cmd_digest_latest)

    norms = sub.add_parser("norms")
    norms_sub = norms.add_subparsers(dest="norms_command", required=True)
    norms_list = norms_sub.add_parser("list")
    norms_list.add_argument("--scope", choices=["all", "global", "scoped"], default="all")
    norms_list.add_argument("--context", default="")
    norms_list.add_argument("--format", choices=["text", "json"], default="text")
    norms_list.set_defaults(func=cmd_norms_list)

    norms_nominate = norms_sub.add_parser("nominate")
    norms_nominate.add_argument("--format", choices=["text", "json"], default="text")
    norms_nominate.set_defaults(func=cmd_norms_nominate)

    norms_doctor = norms_sub.add_parser("doctor")
    norms_doctor.add_argument("--format", choices=["text", "json"], default="text")
    norms_doctor.set_defaults(func=cmd_norms_doctor)

    record = sub.add_parser("record")
    record_sub = record.add_subparsers(dest="record_command", required=True)
    record_id = record_sub.add_parser("id")
    record_id.add_argument("--type", required=True, choices=sorted(RECORD_TYPES))
    record_id.add_argument("--format", choices=["text", "json"], default="text")
    record_id.set_defaults(func=cmd_record_id)

    record_intent = record_sub.add_parser("intent")
    record_intent.add_argument("--prompt", required=True)
    record_intent.add_argument("--format", choices=["text", "json"], default="text")
    record_intent.set_defaults(func=cmd_record_intent)

    team = sub.add_parser("team")
    team_sub = team.add_subparsers(dest="team_command", required=True)
    team_init = team_sub.add_parser("init")
    team_init.add_argument("--path", required=True)
    team_init.add_argument("--team-id", required=True)
    team_init.add_argument("--name", required=True)
    team_init.add_argument("--remote", required=True)
    team_init.add_argument("--format", choices=["text", "json"], default="text")
    team_init.set_defaults(func=cmd_team_init)

    team_summary = team_sub.add_parser("summary")
    team_summary.add_argument("--team-path", required=True)
    team_summary.add_argument("--format", choices=["text", "json"], default="text")
    team_summary.set_defaults(func=cmd_team_summary)

    publish = sub.add_parser("publish")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)
    publish_status_cmd = publish_sub.add_parser("status")
    publish_status_cmd.add_argument("--team-path", default=None)
    publish_status_cmd.add_argument("--preview", action="store_true")
    publish_status_cmd.add_argument("--preview-source-hash", default=None)
    publish_status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    publish_status_cmd.set_defaults(func=cmd_publish_status)

    version_cmd = sub.add_parser("version")
    version_cmd.add_argument("--format", choices=["text", "json"], default="text")
    version_cmd.set_defaults(func=cmd_version)

    doctor_cmd = sub.add_parser("doctor")
    doctor_cmd.add_argument("--format", choices=["text", "json"], default="text")
    doctor_cmd.set_defaults(func=cmd_doctor)

    register_context_commands(sub)
    register_habit_commands(sub)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
