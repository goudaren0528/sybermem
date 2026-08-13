from __future__ import annotations

import argparse
import sys

from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root
from sybermem_core.resume import build_resume_checkpoint
from sybermem_core.search import ProjectRootNotFoundError, search_project
from sybermem_core.user_habits import render_habit_reminder_markdown


def _habit_ids(markdown: str) -> list[str]:
    return [line.split("]", 1)[0][3:] for line in markdown.splitlines() if line.startswith("- [habit-")]


def _search_item(record: dict) -> dict[str, str | int]:  # noqa: DICT_OK
    return {
        "record_id": str(record.get("record_id", "")),
        "type": str(record.get("type", "")),
        "title": str(record.get("title", "")),
        "score": int(record.get("score", 0) or 0),
    }


def _print_markdown_session(payload: dict) -> None:  # noqa: DICT_OK
    print("## SyberMem Manual Session Context")
    print("Delivery: manual")
    print(f"Project: {payload['project']}")
    print("")
    for line in payload["brief"]:
        print(f"- {line}")
    action = payload["next_action"]
    print(f"- Next action: {action['action']} — {action['reason']}")


def _print_markdown_prompt(payload: dict) -> None:  # noqa: DICT_OK
    print("## SyberMem Manual Prompt Context")
    print("Delivery: manual")
    print(f"Query: {payload['query']}")
    print("")
    if not payload["results"]:
        print("No matching SyberMem records found.")
        return
    print("Relevant records:")
    for item in payload["results"]:
        print(f"- [{item['record_id']}] {item['title']} ({item['type']}, score={item['score']})")


def _print_json_or_markdown(args: argparse.Namespace, payload: dict, markdown: str | None = None) -> None:  # noqa: DICT_OK
    if args.format == "json":
        print(dump_json(payload))
    elif markdown is not None:
        print(markdown, end="")


def cmd_context_session(args: argparse.Namespace) -> int:
    root = resolve_project_root()
    if root is None:
        print("No SyberMem project root found.", file=sys.stderr)
        return 1
    checkpoint = build_resume_checkpoint(root, mode=args.mode)
    payload = {
        "kind": "session",
        "delivery": "manual",
        "project": checkpoint["project"]["slug"],
        "mode": checkpoint["mode"],
        "brief": list(checkpoint.get("brief", [])),
        "next_action": checkpoint["next_action"],
    }
    if args.format == "json":
        print(dump_json(payload))
    else:
        _print_markdown_session(payload)
    return 0


def cmd_context_prompt(args: argparse.Namespace) -> int:
    try:
        results = [_search_item(record) for record in search_project(args.query)[: args.limit]]
    except ProjectRootNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {
        "kind": "prompt",
        "delivery": "manual",
        "query": args.query,
        "results": results,
    }
    if args.format == "json":
        print(dump_json(payload))
    else:
        _print_markdown_prompt(payload)
    return 0


def cmd_context_habit(args: argparse.Namespace) -> int:
    markdown = render_habit_reminder_markdown(
        context=args.context,
        higher_authority_text=args.higher_authority_text,
    )
    payload = {
        "kind": "habit",
        "delivery": "manual",
        "context": args.context,
        "reminded": _habit_ids(markdown),
        "markdown": markdown,
    }
    _print_json_or_markdown(args, payload, markdown)
    return 0


def register_context_commands(sub) -> None:
    context = sub.add_parser("context")
    context_sub = context.add_subparsers(dest="context_command", required=True)

    session = context_sub.add_parser("session")
    session.add_argument("--mode", choices=["fast", "standard", "deep"], default="fast")
    session.add_argument("--format", choices=["json", "markdown"], default="markdown")
    session.set_defaults(func=cmd_context_session)

    prompt = context_sub.add_parser("prompt")
    prompt.add_argument("--query", required=True)
    prompt.add_argument("--limit", type=int, default=5)
    prompt.add_argument("--format", choices=["json", "markdown"], default="markdown")
    prompt.set_defaults(func=cmd_context_prompt)

    habit = context_sub.add_parser("habit")
    habit.add_argument("--context", required=True)
    habit.add_argument("--higher-authority-text", default="")
    habit.add_argument("--format", choices=["json", "markdown"], default="markdown")
    habit.set_defaults(func=cmd_context_habit)
