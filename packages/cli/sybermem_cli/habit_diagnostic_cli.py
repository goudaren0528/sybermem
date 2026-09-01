from __future__ import annotations

import argparse
import sys

from sybermem_core.formats import dump_json
from sybermem_core.habit_diagnostics import PromptHabitEvaluation, evaluate_prompt_habits


def habit_diagnostic_markdown(payload: PromptHabitEvaluation) -> str:
    lines = ["## User Habit Recall Test", "", f"Context: {payload['context_summary']}", ""]
    pending = payload["pending_candidates"]
    plural = "" if pending == 1 else "s"
    lines.append(
        f"Summary: {payload['active_habits']} active, {payload['evaluated']} evaluated, "
        f"{payload['selected']} selected, {pending} pending candidate{plural}."
    )
    if pending:
        lines.append("")
        lines.append("Pending candidates are not active habits; confirm or discard them with /sybermem-habit.")
    rows = payload["habits"]
    if rows:
        lines.extend(["", "| Habit | Decision | Score | Reason |", "|---|---|---|---|"])
        for row in rows:
            lines.append(f"| {row['habit_id']} | {row['decision']} | {row['score']}/{row['floor']} | {'; '.join(row['reasons'])} |")
    return "\n".join(lines) + "\n"


def cmd_habit_test(args: argparse.Namespace) -> int:
    payload = evaluate_prompt_habits(context=args.context, higher_authority_text=args.higher_authority_text)
    if args.format == "json":
        print(dump_json(payload))
    else:
        print(habit_diagnostic_markdown(payload), end="")
    return 0


def cmd_habit_explain(args: argparse.Namespace) -> int:
    payload = evaluate_prompt_habits(context=args.context, higher_authority_text=args.higher_authority_text)
    rows = [row for row in payload["habits"] if row["habit_id"] == args.habit_id]
    if not rows:
        error = {"status": "unknown_habit", "habit_id": args.habit_id}
        if args.format == "json":
            print(dump_json(error))
        else:
            print(f"unknown habit id: {args.habit_id}", file=sys.stderr)
        return 1
    single: PromptHabitEvaluation = {**payload, "habits": rows, "selected": sum(1 for row in rows if row["decision"] == "selected")}
    if args.format == "json":
        print(dump_json(single))
    else:
        print(habit_diagnostic_markdown(single), end="")
    return 0


def register_habit_diagnostic_commands(habit_sub) -> None:
    test = habit_sub.add_parser("test")
    test.add_argument("--context", required=True)
    test.add_argument("--higher-authority-text", default="")
    test.add_argument("--format", choices=["json", "markdown"], default="markdown")
    test.set_defaults(func=cmd_habit_test)

    explain = habit_sub.add_parser("explain")
    explain.add_argument("--id", dest="habit_id", required=True)
    explain.add_argument("--context", required=True)
    explain.add_argument("--higher-authority-text", default="")
    explain.add_argument("--format", choices=["json", "markdown"], default="markdown")
    explain.set_defaults(func=cmd_habit_explain)
