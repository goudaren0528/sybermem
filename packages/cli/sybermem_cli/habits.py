from __future__ import annotations

import argparse
import sys

from sybermem_core.formats import dump_json
from sybermem_cli.habit_diagnostic_cli import register_habit_diagnostic_commands
from sybermem_core.user_habit_model import Habit, HabitSearchResult
from sybermem_core.user_habits import (
    InvalidHabitError,
    add_habit,
    capture_habit_intent,
    clear_habit_intent,
    delete_habit,
    discard_habit_candidate,
    habit_awareness_summary,
    list_habit_candidates,
    list_habits,
    pause_habit,
    pending_habit_reminder,
    read_habit_intent,
    render_habit_markdown,
    render_habit_reminder_markdown,
    search_habits,
)


def habit_payload(habit: Habit) -> dict[str, str | list[str] | None]:
    return {
        "habit_id": habit.habit_id,
        "scope": habit.scope,
        "habit_type": habit.habit_type.value,
        "statement": habit.statement,
        "source_kind": habit.source_kind,
        "confidence": habit.confidence.value,
        "status": habit.status.value,
        "applies_to": list(habit.applies_to),
        "not_applies_to": list(habit.not_applies_to),
        "last_confirmed_at": habit.last_confirmed_at,
        "review_after": habit.review_after,
        "injection_policy": habit.injection_policy.value,
        "superseded_by": habit.superseded_by,
    }


def search_payload(result: HabitSearchResult) -> dict[str, int | dict[str, str | list[str] | None]]:
    return {"score": result.score, "habit": habit_payload(result.habit)}


def cmd_habit_add(args: argparse.Namespace) -> int:
    try:
        habit = add_habit(
            statement=args.statement,
            habit_type=args.type,
            applies_to=tuple(args.applies_to),
            not_applies_to=tuple(args.not_applies_to),
            injection_policy=args.injection_policy,
        )
    except InvalidHabitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"habit": habit_payload(habit)}
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"added {habit.habit_id}: {habit.statement}")
    return 0


def cmd_habit_list(args: argparse.Namespace) -> int:
    status = None if args.all else args.status
    try:
        habits = list_habits(status=status)
    except InvalidHabitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"habits": [habit_payload(habit) for habit in habits]}
    if args.format == "json":
        print(dump_json(payload))
    else:
        for habit in habits:
            print(f"[{habit.habit_id}] {habit.status.value} {habit.statement}")
    return 0


def cmd_habit_search(args: argparse.Namespace) -> int:
    results = search_habits(args.query)
    payload = {"query": args.query, "results": [search_payload(result) for result in results]}
    if args.format == "json":
        print(dump_json(payload))
    else:
        for result in results:
            habit = result.habit
            print(f"[{habit.habit_id}] score={result.score} {habit.status.value} {habit.statement}")
    return 0


def cmd_habit_pause(args: argparse.Namespace) -> int:
    try:
        pause_habit(args.habit_id)
    except InvalidHabitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"status": "paused", "habit_id": args.habit_id}
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"paused {args.habit_id}")
    return 0


def cmd_habit_delete(args: argparse.Namespace) -> int:
    try:
        delete_habit(args.habit_id)
    except InvalidHabitError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"status": "deleted", "habit_id": args.habit_id}
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"deleted {args.habit_id}")
    return 0


def cmd_habit_inject(args: argparse.Namespace) -> int:
    markdown = render_habit_markdown(context=args.context, higher_authority_text=args.higher_authority_text)
    if args.format == "markdown":
        if markdown:
            print(markdown, end="")
    elif args.format == "json":
        injected = [line.split("]", 1)[0][3:] for line in markdown.splitlines() if line.startswith("- [habit-")]
        print(dump_json({"injected": injected, "markdown": markdown}))
    else:
        print(markdown, end="")
    return 0


def cmd_habit_remind(args: argparse.Namespace) -> int:
    markdown = render_habit_reminder_markdown(context=args.context, higher_authority_text=args.higher_authority_text)
    if args.format == "markdown":
        if markdown:
            print(markdown, end="")
    elif args.format == "json":
        reminded = [line.split("]", 1)[0][3:] for line in markdown.splitlines() if line.startswith("- [habit-")]
        print(dump_json({"reminded": reminded, "markdown": markdown}))
    else:
        print(markdown, end="")
    return 0


def cmd_habit_intent(args: argparse.Namespace) -> int:
    metadata = capture_habit_intent(args.prompt)
    payload = {"captured": metadata is not None, "candidate": metadata}
    if args.format == "json":
        print(dump_json(payload))
    elif metadata is not None:
        print(f"captured habit candidate ({metadata['habit_type']}): confirm with /sybermem-habit")
    return 0


def cmd_habit_intent_status(args: argparse.Namespace) -> int:
    candidates = list_habit_candidates()
    # Keep the legacy single `candidate` field (newest) for backward compatibility while
    # exposing the full bounded list so the skill can present a selectable status view.
    payload = {
        "pending": len(candidates) > 0,
        "count": len(candidates),
        "candidates": candidates,
        "candidate": candidates[0] if candidates else None,
    }
    if args.format == "json":
        print(dump_json(payload))
    elif candidates:
        print(f"{len(candidates)} pending habit candidate(s): confirm or discard with /sybermem-habit")
        for cand in candidates:
            summary = str(cand.get("summary", "") or "").strip()
            quoted = f' "{summary}"' if summary else ""
            print(f"- [{cand.get('candidate_id', '?')}] ({cand.get('habit_type', 'workflow')}/{cand.get('suggested_scope', 'ambiguous')}){quoted}")
    else:
        print("no pending habit candidate")
    return 0


def cmd_habit_intent_discard(args: argparse.Namespace) -> int:
    discarded = discard_habit_candidate(args.candidate_id)
    payload = {"discarded": discarded, "candidate_id": args.candidate_id}
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(f"discarded habit candidate {args.candidate_id}" if discarded else f"no habit candidate with id {args.candidate_id}")
    return 0 if discarded else 1


def cmd_habit_intent_clear(args: argparse.Namespace) -> int:
    cleared = clear_habit_intent()
    payload = {"cleared": cleared}
    if args.format == "json":
        print(dump_json(payload))
    else:
        print("cleared all pending habit candidates" if cleared else "no pending habit candidate to clear")
    return 0


def cmd_habit_awareness(args: argparse.Namespace) -> int:
    summary = habit_awareness_summary()
    # Attach the durable pending-candidate reminder so every host (OpenCode startup,
    # Claude/Codex SessionStart) surfaces the SAME "confirm your habit candidate" line
    # from one source of truth instead of each reinventing the wording.
    reminder = pending_habit_reminder()
    if reminder is not None:
        summary = {**summary, "pending_reminder": reminder}
    if args.format == "json":
        print(dump_json(summary))
    else:
        if summary["active"] == 0 and not summary["pending_intent"]:
            print("no active user habits")
        else:
            types = ", ".join(f"{name} {count}" for name, count in summary["by_type"].items())
            pending_count = summary.get("pending_count", 1 if summary["pending_intent"] else 0)
            pending = f" ({pending_count} pending candidate{'s' if pending_count != 1 else ''})" if summary["pending_intent"] else ""
            print(f"{summary['active']} active user habits [{types}]{pending}")
    return 0


def register_habit_commands(sub) -> None:
    habit = sub.add_parser("habit")
    habit_sub = habit.add_subparsers(dest="habit_command", required=True)

    add = habit_sub.add_parser("add")
    add.add_argument("statement")
    add.add_argument("--type", required=True, choices=["workflow", "style", "tooling", "communication", "review", "avoidance"])
    add.add_argument("--applies-to", action="append", default=[])
    add.add_argument("--not-applies-to", action="append", default=[])
    add.add_argument("--injection-policy", choices=["manual_only", "compaction_ok", "prompt_ok_when_supported"], default="prompt_ok_when_supported")
    add.add_argument("--format", choices=["text", "json"], default="text")
    add.set_defaults(func=cmd_habit_add)

    list_cmd = habit_sub.add_parser("list")
    list_cmd.add_argument("--status", default="active", choices=["active", "draft", "paused", "superseded", "expired", "deleted"])
    list_cmd.add_argument("--all", action="store_true")
    list_cmd.add_argument("--format", choices=["text", "json"], default="text")
    list_cmd.set_defaults(func=cmd_habit_list)

    search = habit_sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--format", choices=["text", "json"], default="text")
    search.set_defaults(func=cmd_habit_search)

    pause = habit_sub.add_parser("pause")
    pause.add_argument("habit_id")
    pause.add_argument("--format", choices=["text", "json"], default="text")
    pause.set_defaults(func=cmd_habit_pause)

    delete = habit_sub.add_parser("delete")
    delete.add_argument("habit_id")
    delete.add_argument("--format", choices=["text", "json"], default="text")
    delete.set_defaults(func=cmd_habit_delete)

    inject = habit_sub.add_parser("inject")
    inject.add_argument("--context", required=True)
    inject.add_argument("--higher-authority-text", default="")
    inject.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    inject.set_defaults(func=cmd_habit_inject)

    remind = habit_sub.add_parser("remind")
    remind.add_argument("--context", required=True)
    remind.add_argument("--higher-authority-text", default="")
    remind.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    remind.set_defaults(func=cmd_habit_remind)

    register_habit_diagnostic_commands(habit_sub)

    intent = habit_sub.add_parser("intent")
    intent.add_argument("--prompt", required=True)
    intent.add_argument("--format", choices=["text", "json"], default="text")
    intent.set_defaults(func=cmd_habit_intent)

    intent_status = habit_sub.add_parser("intent-status")
    intent_status.add_argument("--format", choices=["text", "json"], default="text")
    intent_status.set_defaults(func=cmd_habit_intent_status)

    intent_clear = habit_sub.add_parser("intent-clear")
    intent_clear.add_argument("--format", choices=["text", "json"], default="text")
    intent_clear.set_defaults(func=cmd_habit_intent_clear)

    intent_discard = habit_sub.add_parser("intent-discard")
    intent_discard.add_argument("candidate_id")
    intent_discard.add_argument("--format", choices=["text", "json"], default="text")
    intent_discard.set_defaults(func=cmd_habit_intent_discard)

    awareness = habit_sub.add_parser("awareness")
    awareness.add_argument("--format", choices=["text", "json"], default="text")
    awareness.set_defaults(func=cmd_habit_awareness)
