from __future__ import annotations


def render_project_memory_stats_text(payload: dict) -> None:
    print(f"Memory stats for {payload['slug']}")
    print("")
    _print_table(
        ["Window", "Records", "Recall Events", "Injected", "Abstained", "Recall Rate", "Edit Alignment"],
        [
            _window_summary_row("7d", payload["windows"]["7d"]),
            _window_summary_row("30d", payload["windows"]["30d"]),
        ],
    )
    print("")
    print("Records by type")
    _print_table(
        ["Type", "Total", "7d", "30d"],
        [
            [
                record_type,
                str(payload["totals"]["records"]["by_type"].get(record_type, 0)),
                str(payload["windows"]["7d"]["records"]["by_type"].get(record_type, 0)),
                str(payload["windows"]["30d"]["records"]["by_type"].get(record_type, 0)),
            ]
            for record_type in ["change", "decision", "requirement", "bug", "norm", "digest", "theme-digest"]
        ],
    )
    if payload["totals"]["recall"].get("status") == "no_log":
        print("")
        print("Recall debug log: unavailable (.sybermem/.recall-debug.jsonl not found)")
        _print_relevance(payload)
        _print_memory_usage(payload)
        _print_recall_health(payload)
        _print_digest_coverage(payload)
        return
    _print_recall_detail_tables(payload)
    _print_relevance(payload)
    _print_memory_usage(payload)
    _print_recall_health(payload)
    _print_digest_coverage(payload)


def _print_digest_coverage(payload: dict) -> None:
    coverage = payload.get("digest_coverage")
    if not coverage:
        return
    print("")
    uncovered = coverage.get("uncovered", 0)
    total = coverage.get("total_records", 0)
    covered = max(total - uncovered, 0)
    if coverage.get("has_digest"):
        age = coverage.get("days_since_latest_digest", 0)
        latest = coverage.get("latest_digest_date", "")
        print(f"Digest coverage: {covered}/{total} records covered, {uncovered} uncovered (latest digest {latest}, {age}d ago)")
    else:
        print(f"Digest coverage: no digest yet, {uncovered}/{total} records uncovered")
    _print_norm_coverage(payload)


def _print_norm_coverage(payload: dict) -> None:
    coverage = payload.get("norm_coverage")
    if not coverage:
        return
    active = coverage.get("active", 0)
    if active == 0:
        print("Project norms: none")
        return
    used = coverage.get("constitution_used", 0)
    cap = coverage.get("constitution_max", 0)
    print(
        f"Project norms: {active} active ({coverage.get('global_', 0)} global, "
        f"{coverage.get('scoped', 0)} scoped); constitution {used}/{cap}"
    )


def _print_recall_health(payload: dict) -> None:
    health = payload.get("recall_health")
    if not health:
        return
    print("")
    hint = health.get("hint", "")
    precision = health.get("precision")
    precision_note = f" (edit alignment {_format_rate(precision)})" if precision is not None else ""
    line = f"Recall health: {health.get('status', 'unknown')}{precision_note}"
    print(f"{line} — {hint}" if hint else line)


def _print_relevance(payload: dict) -> None:
    print("")
    print("Edit Alignment")
    _print_table(
        ["Window", "Hit", "Measurable", "Unmeasurable", "Precision", "Evidence"],
        [_relevance_row("7d", payload["windows"]["7d"].get("relevance", {})), _relevance_row("30d", payload["windows"]["30d"].get("relevance", {}))],
    )


def _relevance_row(label: str, relevance: dict) -> list[str]:
    evidence = relevance.get("evidence_available")
    evidence_label = "available" if evidence is True else "unavailable" if evidence is False else "n/a"
    return [
        label,
        str(relevance.get("hit", 0)),
        str(relevance.get("measurable", relevance.get("injected", 0))),
        str(relevance.get("unmeasurable", 0)),
        _format_rate(relevance.get("precision")),
        evidence_label,
    ]


def _print_memory_usage(payload: dict) -> None:
    print("")
    print("Memory injection")
    _print_table(
        ["Window", "Turns", "Items", "Chars", "Avg chars/turn", "P95 chars/turn"],
        [_memory_usage_row("7d", payload["windows"]["7d"].get("memory_usage", {})), _memory_usage_row("30d", payload["windows"]["30d"].get("memory_usage", {}))],
    )
    usage = payload.get("totals", {}).get("memory_usage", {})
    if usage.get("status") == "no_log":
        print("Memory usage journal: unavailable (.sybermem/.memory-usage.jsonl not found)")
        return
    print("")
    print("Memory injection lanes (30d)")
    _print_table(
        ["Lane", "Items", "Chars"],
        [[lane, str(values.get("items", 0)), str(values.get("chars", 0))] for lane, values in usage.get("lanes", {}).items()],
    )


def _memory_usage_row(label: str, usage: dict) -> list[str]:
    available = usage.get("status") == "available"
    return [
        label,
        str(usage.get("turns", 0)) if available else "n/a",
        str(usage.get("items", 0)) if available else "n/a",
        str(usage.get("chars", 0)) if available else "n/a",
        _format_number(usage.get("avg_chars_per_turn")) if available else "n/a",
        str(usage.get("p95_chars_per_turn")) if available else "n/a",
    ]


def _window_summary_row(label: str, window: dict) -> list[str]:
    recall = window["recall"]
    precision = window.get("relevance", {}).get("precision")
    if recall.get("status") == "no_log":
        return [label, str(window["records"]["total"]), "n/a", "n/a", "n/a", "n/a", _format_rate(precision)]
    return [
        label,
        str(window["records"]["total"]),
        str(recall["events"]),
        str(recall["injected"]),
        str(recall["abstained"]),
        _format_rate(recall.get("recall_rate")),
        _format_rate(precision),
    ]


def _print_recall_detail_tables(payload: dict) -> None:
    print("")
    print("Recall match classes")
    _print_table(["Class", "7d", "30d"], _counter_rows(payload, "match_classes"))
    print("")
    print("Top matched records")
    _print_table(["Record ID", "7d", "30d"], _top_record_rows(payload))
    print("")
    print("Abstain reasons")
    _print_table(["Reason", "7d", "30d"], _counter_rows(payload, "abstain_reasons"))


def _counter_rows(payload: dict, key: str) -> list[list[str]]:
    counts_7d = payload["windows"]["7d"]["recall"].get(key, {})
    counts_30d = payload["windows"]["30d"]["recall"].get(key, {})
    names = sorted(set(counts_7d) | set(counts_30d))
    return [[name, str(counts_7d.get(name, 0)), str(counts_30d.get(name, 0))] for name in names] or [["none", "0", "0"]]


def _top_record_rows(payload: dict) -> list[list[str]]:
    counts_7d = {row["record_id"]: row["count"] for row in payload["windows"]["7d"]["recall"].get("top_matched_records", [])}
    counts_30d = {row["record_id"]: row["count"] for row in payload["windows"]["30d"]["recall"].get("top_matched_records", [])}
    names = sorted(set(counts_7d) | set(counts_30d))
    return [[name, str(counts_7d.get(name, 0)), str(counts_30d.get(name, 0))] for name in names] or [["none", "0", "0"]]


def _format_rate(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _format_number(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.1f}".rstrip("0").rstrip(".")


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)).rstrip())
    print("  ".join("-" * width for width in widths).rstrip())
    for row in rows:
        print("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip())
