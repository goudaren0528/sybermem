from __future__ import annotations

import argparse
import sys

from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root, ensure_project_yaml
from sybermem_core.registry import register_project
from sybermem_core.identity import git_remote


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


def main() -> int:
    parser = argparse.ArgumentParser(prog="sybermem")
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    init = project_sub.add_parser("init")
    init.add_argument("--register", action="store_true")
    init.add_argument("--format", choices=["text", "json"], default="text")
    init.set_defaults(func=cmd_project_init)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
