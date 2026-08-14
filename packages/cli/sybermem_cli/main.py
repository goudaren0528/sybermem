from __future__ import annotations

import argparse
import sys

from pathlib import Path
from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root, ensure_project_yaml
from sybermem_core.project_refresh import refresh_project
from sybermem_core.project_index import RECORD_TYPES, DuplicateRecordIdError, InvalidRecordMetadataError, check_project_index, write_project_index
from sybermem_core.records import generate_record_id
from sybermem_core.registry import register_project
from sybermem_core.identity import git_remote
from sybermem_core.index import rebuild_index
from sybermem_core.search import ProjectRootNotFoundError, WorkspaceIndexIncompatibleError, search_project, search_workspace, workspace_index_staleness
from sybermem_core.status import project_status
from sybermem_core.resume import build_resume_checkpoint
from sybermem_core.next_step_router import classify_record_intent, recommend_next_step
from sybermem_core.digest_governance import build_digest_governance_report
from sybermem_core.portfolio import build_portfolio
from sybermem_core.team import init_team_repo
from sybermem_core.publish_bootstrap import bootstrap_publish_status
from sybermem_core.team_summary import build_team_management_summary
from sybermem_core.uninstall import deactivate_project_sybermem
from sybermem_cli.habits import register_habit_commands
from sybermem_cli.context import register_context_commands
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
                    if phase_name and phase.get("id"):
                        print(f"- {p['slug']} → {phase_label} {phase_name}")
                    else:
                        print(f"- {p['slug']} → {phase_label}")
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

    uninstall_cmd = project_sub.add_parser("uninstall")
    uninstall_cmd.add_argument("--format", choices=["text", "json"], default="text")
    uninstall_cmd.set_defaults(func=cmd_project_uninstall)

    refresh_cmd = project_sub.add_parser("refresh")
    refresh_cmd.add_argument("--format", choices=["text", "json"], default="text")
    refresh_cmd.set_defaults(func=cmd_project_refresh)

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

    register_context_commands(sub)
    register_habit_commands(sub)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
