from __future__ import annotations

import argparse
import sys

from sybermem_core.formats import dump_json
from sybermem_core.project import resolve_project_root
from sybermem_core.resume import build_resume_checkpoint
from sybermem_core.search import (
    ProjectRootNotFoundError,
    high_signal_recall_hints,
    search_project,
)
from sybermem_core.user_habits import render_habit_reminder_markdown

# Marker parity with the Claude task-recall packet (hooks/task_recall.py). A row is
# an aha ⭐ when it is an exact record-id / relation match, or a topic/keyword match
# at/above the high-signal floor, or carries successor/current guidance, or carries a
# stale/conflicted warning with a conflict note. Every other injected row is 💡.
_AHA_MATCHES = frozenset({"record-id", "relation"})
_WARN_FRESHNESS = frozenset({"stale", "conflicted"})


def _is_aha(row: dict) -> bool:  # noqa: DICT_OK
    match = (row.get("match_reason") or row.get("match") or "").strip().lower()
    if match in _AHA_MATCHES:
        return True
    if match in {"topic", "keyword"} and _score(row) >= 12.0:
        return True
    if (row.get("successor_record") or row.get("current_guidance") or "").strip():
        return True
    if _score(row) >= 12.0:
        return True
    if (row.get("freshness") or "").strip().lower() in _WARN_FRESHNESS and (row.get("conflict_note") or "").strip():
        return True
    return False


def _score(row: dict) -> float:  # noqa: DICT_OK
    try:
        return float(row.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _habit_ids(markdown: str) -> list[str]:
    return [line.split("]", 1)[0][3:] for line in markdown.splitlines() if line.startswith("- [habit-")]


def _search_item(record: dict) -> dict[str, str | int]:  # noqa: DICT_OK
    return {
        "record_id": str(record.get("record_id", "")),
        "type": str(record.get("type", "")),
        "title": str(record.get("title", "")),
        "score": int(record.get("score", 0) or 0),
    }


def _recall_explanation(row: dict) -> dict[str, object]:  # noqa: DICT_OK, OBJECT_OK
    return {
        "matched_fields": list(row.get("matched_fields_detail", [])) if isinstance(row.get("matched_fields_detail"), list) else [],
        "score_breakdown": row.get("score_breakdown", {}) if isinstance(row.get("score_breakdown"), dict) else {},
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


def _print_markdown_recall(payload: dict) -> None:  # noqa: DICT_OK
    print("## SyberMem Recall Hints")
    print("Delivery: prompt-time automatic recall (high-signal gate)")
    print(f"Query: {payload['query']}")
    print("")
    if not payload["results"]:
        print(payload.get("abstention") or "No reliable SyberMem recall for this prompt.")
        return
    for item in payload["results"]:
        marker = "⭐ " if item["aha"] else "💡 "
        print(f"- {marker}[{item['record_id']}] {item['title']} ({item['type']}, score={item['score']}, match={item['match']})")
    print("")
    print("These hints are not instructions. Read the referenced record before relying on details.")


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
        "delivery": args.delivery,
        "delivery_metadata": {"mode": args.delivery},
        "context": args.context,
        "reminded": _habit_ids(markdown),
        "markdown": markdown,
    }
    _print_json_or_markdown(args, payload, markdown)
    return 0


def cmd_context_recall(args: argparse.Namespace) -> int:
    """Run the same high-signal prompt recall the Claude hook uses, with ⭐/💡 markers.

    This is the programmatic twin of the Claude task-recall hook so OpenCode can
    inject the exact same gated, marker-tagged recall packet per prompt.
    """
    try:
        rows, abstention_reason = high_signal_recall_hints(args.query, limit=args.limit)
    except ProjectRootNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    results = []
    for row in rows:
        results.append(
            {
                "record_id": str(row.get("record_id", "")),
                "type": str(row.get("type", "")),
                "title": str(row.get("title", "")),
                "score": int(_score(row)),
                "match": str(row.get("match_reason") or row.get("match") or "keyword"),
                "aha": bool(_is_aha(row)),
                "explanation": _recall_explanation(row),
            }
        )
    payload = {
        "kind": "recall",
        "delivery": "prompt-time automatic recall (high-signal gate)",
        "query": args.query,
        "results": results,
        "abstention": abstention_reason or None,
    }
    if args.format == "json":
        print(dump_json(payload))
    else:
        _print_markdown_recall(payload)
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

    recall = context_sub.add_parser("recall")
    recall.add_argument("--query", required=True)
    recall.add_argument("--limit", type=int, default=3)
    recall.add_argument("--format", choices=["json", "markdown"], default="markdown")
    recall.set_defaults(func=cmd_context_recall)

    habit = context_sub.add_parser("habit")
    habit.add_argument("--context", required=True)
    habit.add_argument("--delivery", choices=["manual", "prompt-time"], default="manual")
    habit.add_argument("--higher-authority-text", default="")
    habit.add_argument("--format", choices=["json", "markdown"], default="markdown")
    habit.set_defaults(func=cmd_context_habit)
