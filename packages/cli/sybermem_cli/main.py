from __future__ import annotations

import argparse
import sys

from pathlib import Path
from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root, ensure_project_yaml
from sybermem_core.registry import register_project
from sybermem_core.identity import git_remote
from sybermem_core.index import rebuild_index
from sybermem_core.search import search_project, search_workspace
from sybermem_core.status import project_status
from sybermem_core.portfolio import build_portfolio
from sybermem_core.team import init_team_repo
from sybermem_core.publish import publish_status


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
    if args.scope == "workspace":
        try:
            results = search_workspace(args.query, project=args.project, type_=args.type, project_status=args.project_status)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    else:
        results = search_project(args.query)

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
    if args.format == "json":
        print(dump_json(payload))
    else:
        current_project = None
        for row in results:
            if row["slug"] != current_project:
                current_project = row["slug"]
                print(f"[{current_project}]")
            print(f"- {row['record_id']} {row['title']}")
        if not results:
            print("No matches.")
    return 0


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
        payload = publish_status(Path(args.team_path))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.format == "json":
        print(dump_json(payload))
    else:
        print("Published project status to Team repo:")
        print(f"- team: {payload['team_id']}")
        print(f"- project: {payload['slug']}")
        print("- files:")
        for f in payload["files"]:
            print(f"  - {f}")
    return 0


def main() -> int:
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

    team = sub.add_parser("team")
    team_sub = team.add_subparsers(dest="team_command", required=True)
    team_init = team_sub.add_parser("init")
    team_init.add_argument("--path", required=True)
    team_init.add_argument("--team-id", required=True)
    team_init.add_argument("--name", required=True)
    team_init.add_argument("--remote", required=True)
    team_init.add_argument("--format", choices=["text", "json"], default="text")
    team_init.set_defaults(func=cmd_team_init)

    publish = sub.add_parser("publish")
    publish_sub = publish.add_subparsers(dest="publish_command", required=True)
    publish_status_cmd = publish_sub.add_parser("status")
    publish_status_cmd.add_argument("--team-path", required=True)
    publish_status_cmd.add_argument("--format", choices=["text", "json"], default="text")
    publish_status_cmd.set_defaults(func=cmd_publish_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
