from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core import next_step_router
from sybermem_core.next_step_router import recommend_next_step
from sybermem_core import memory_stats as memory_stats_module
from sybermem_core.memory_stats import recall_health
from sybermem_core.status import project_memory_stats, project_status


def test_project_status_returns_empty_snapshot_when_project_is_uninitialized(tmp_path: Path) -> None:
    # Given: a directory with no .sybermem project state
    project_root = tmp_path / "empty"
    project_root.mkdir()

    # When: current status is requested
    status = project_status(project_root)

    # Then: callers receive a bounded empty snapshot rather than an exception
    assert status["project_id"] == ""
    assert status["slug"] == "empty"
    assert status["phase"] == {"id": "", "name": "", "lifecycle": "active"}
    assert status["recent_records"] == []
    assert status["open_bugs"] == []
    assert status["open_requirements"] == []


def test_project_status_has_no_publication_field_after_team_removal(tmp_path: Path) -> None:
    # Given: an ordinary project (Team mode removed; decision-f780ec)
    project_root = tmp_path / "p"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")

    # When
    status = project_status(project_root)

    # Then: the Team publication contract is gone; ordinary status is unaffected
    assert "publication" not in status
    assert status["slug"] == "demo"
    assert status["open_bugs"] == []


def test_project_memory_stats_preserves_unavailable_memory_usage_status(tmp_path: Path) -> None:
    # Given: a managed project with a usage journal too large for advisory stats
    project_root = tmp_path / "p"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    (sybermem / ".memory-usage.jsonl").write_text("x" * 1_000_001, encoding="utf-8")

    # When
    stats = memory_stats_module.project_memory_stats(project_root)

    # Then
    assert stats["totals"]["memory_usage"]["status"] == "unavailable"
    assert stats["windows"]["7d"]["memory_usage"]["status"] == "unavailable"
    assert stats["windows"]["30d"]["memory_usage"]["status"] == "unavailable"


def test_project_status_ignores_legacy_team_block(tmp_path: Path) -> None:
    # Given: a project whose project.yaml still carries a legacy nested `team:` block
    # (from before Team mode was removed; decision-f780ec)
    project_root = tmp_path / "p"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text(
        "project_id: project-1\nslug: demo\nteam:\n  team_id: team-1\n  team_path: /some/old/team\n",
        encoding="utf-8",
    )

    # When / Then: the inert legacy block must not crash status and must not resurface
    # any Team/publication field.
    status = project_status(project_root)
    assert "publication" not in status
    assert status["slug"] == "demo"
    assert "team" not in status


def test_project_status_treats_fixed_bug_as_closed_but_statusless_as_open(tmp_path: Path) -> None:
    # Given: a project with one bug marked `fixed`, one marked `resolved`, and one with no status
    project_root = tmp_path / "project"
    bugs = project_root / ".sybermem" / "bugs"
    bugs.mkdir(parents=True)
    (project_root / ".sybermem" / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")

    def write_bug(name: str, status_line: str) -> None:
        frontmatter = ["---", "type: bug", "date: 2026-08-07", f"title: {name}", "severity: high"]
        if status_line:
            frontmatter.append(status_line)
        frontmatter.append("---")
        (bugs / f"2026-08-07-{name}.md").write_text("\n".join(frontmatter) + "\n\nbody\n", encoding="utf-8")

    write_bug("001-fixed", "status: fixed")
    write_bug("002-resolved", "status: resolved")
    write_bug("003-nostatus", "")

    # When: status enumerates open bugs
    status = project_status(project_root)

    # Then: fixed and resolved are closed; a status-less bug stays open (conservative)
    assert "bug-001" not in status["open_bugs"]
    assert "bug-002" not in status["open_bugs"]
    assert "bug-003" in status["open_bugs"]


def test_recommend_next_step_returns_phase_analyze_without_commit_probe(tmp_path: Path, monkeypatch) -> None:
    # Given: a SyberMem project with no phase index yet
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / ".sybermem").mkdir()
    (project_root / ".sybermem" / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")

    def fail_commit_probe(root: Path) -> int:
        raise AssertionError(f"commit probe should not run for {root}")

    monkeypatch.setattr(next_step_router, "_count_commits_since_last_record", fail_commit_probe)

    # When: routing decides the next step
    step = recommend_next_step(project_root)

    # Then: the structural prerequisite wins before any git-backed record gap check
    assert step["action"] == "/sybermem-phase-analyze"
    assert "phase index" in step["reason"]


def test_project_memory_stats_counts_records_by_type_and_window(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with records spread across recent and older windows
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")

    def write_record(folder: str, name: str, record_type: str, date: str) -> None:
        records = sybermem / folder
        records.mkdir(exist_ok=True)
        (records / f"{date}-{name}.md").write_text(
            "\n".join(
                [
                    "---",
                    f"type: {record_type}",
                    f"record_id: {record_type}-{name}",
                    f"date: {date}",
                    f"title: {name}",
                    "---",
                    "",
                    "body",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    write_record("changes", "recent", "change", "2026-08-13")
    write_record("decisions", "week", "decision", "2026-08-08")
    write_record("bugs", "month", "bug", "2026-07-20")
    write_record("requirements", "old", "requirement", "2026-06-01")
    write_record("digests", "digest", "digest", "2026-08-01")
    write_record("theme-digests", "theme", "theme-digest", "2026-08-10")
    write_record("changes", "future", "change", "2026-08-20")

    # When: memory stats are computed
    stats = project_memory_stats(project_root)

    # Then: totals and 7d/30d windows use canonical record dates and types
    assert stats["totals"]["records"]["total"] == 7
    assert stats["totals"]["records"]["by_type"] == {
        "change": 2,
        "decision": 1,
        "requirement": 1,
        "bug": 1,
        "norm": 0,
        "digest": 1,
        "theme-digest": 1,
    }
    assert stats["windows"]["7d"]["records"]["total"] == 3
    assert stats["windows"]["7d"]["records"]["by_type"]["bug"] == 0
    assert stats["windows"]["30d"]["records"]["total"] == 5
    assert stats["windows"]["30d"]["records"]["by_type"]["requirement"] == 0
    assert stats["windows"]["30d"]["records"]["by_type"]["change"] == 1


def test_project_memory_stats_counts_norm_records_in_totals(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with a change and a norm record
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-24T12:00:00+08:00")
    (sybermem / "changes").mkdir()
    (sybermem / "changes" / "2026-08-20-c.md").write_text("---\ntype: change\ndate: 2026-08-20\n---\n\nx\n", encoding="utf-8")
    (sybermem / "norms").mkdir()
    (sybermem / "norms" / "2026-08-21-n.md").write_text("---\ntype: norm\ndate: 2026-08-21\nscope: global\n---\n\nx\n", encoding="utf-8")

    # When
    stats = project_memory_stats(project_root)

    # Then: total and by_type agree — norm is a counted bucket (no phantom total)
    assert stats["totals"]["records"]["total"] == 2
    assert stats["totals"]["records"]["by_type"]["norm"] == 1
    assert stats["totals"]["records"]["by_type"]["change"] == 1


def test_project_memory_stats_exposes_digest_coverage(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with change records and one digest covering only some of them
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")

    from sybermem_core.digest_coverage import compute_coverage_hash

    changes = sybermem / "changes"
    changes.mkdir()
    for name, dt in (("a", "2026-08-01"), ("b", "2026-08-02"), ("c", "2026-08-03")):
        (changes / f"{dt}-{name}.md").write_text(f"---\ntype: change\ndate: {dt}\n---\n\nbody\n", encoding="utf-8")
    digests = sybermem / "digests"
    digests.mkdir()
    cov = compute_coverage_hash(project_root, ["changes/2026-08-01-a.md"])
    (digests / "2026-08-05-001-d.md").write_text(
        "\n".join(
            [
                "---",
                "type: digest",
                "date: 2026-08-05",
                "record_id: digest-001",
                "title: d",
                "source_records:",
                "  - changes/2026-08-01-a.md",
                f"coverage_hash: {cov}",
                "---",
                "",
                "## Core Conclusions\n- x",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When
    stats = project_memory_stats(project_root)

    # Then: digest coverage is surfaced as a snapshot alongside recall health
    coverage = stats["digest_coverage"]
    assert coverage["uncovered"] == 2
    assert coverage["total_records"] == 3
    assert coverage["has_digest"] is True
    assert coverage["latest_digest_date"] == "2026-08-05"


def test_project_memory_stats_summarizes_recall_debug_windows(tmp_path: Path, monkeypatch) -> None:
    # Given: recall debug entries with injects, abstains, match classes, and malformed lines
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")
    (sybermem / ".recall-debug.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"timestamp": "2026-08-14T09:00:00+08:00", "event": "inject", "record_ids": ["change-a", "change-a"], "match_classes": ["topic"], "reason": "high-signal-recall"}),
                json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "no-high-signal-recall"}),
                json.dumps({"timestamp": "2026-07-20T09:00:00+08:00", "event": "inject", "record_ids": ["decision-b"], "match_classes": ["record-id", "topic"], "reason": "high-signal-recall"}),
                json.dumps({"timestamp": "2026-08-20T09:00:00+08:00", "event": "inject", "record_ids": ["change-future"], "match_classes": ["semantic"], "reason": "high-signal-recall"}),
                "not json",
                json.dumps({"timestamp": "2026-06-01T09:00:00+08:00", "event": "inject", "record_ids": ["bug-old"], "match_classes": ["keyword"], "reason": "high-signal-recall"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # When: memory stats are computed
    stats = project_memory_stats(project_root)

    # Then: recall rates and distributions are computed per window from valid log entries
    recall_7d = stats["windows"]["7d"]["recall"]
    assert recall_7d["status"] == "available"
    assert recall_7d["events"] == 2
    assert recall_7d["injected"] == 1
    assert recall_7d["abstained"] == 1
    assert recall_7d["recall_rate"] == 0.5
    assert recall_7d["match_classes"] == {"topic": 1}
    assert recall_7d["top_matched_records"] == [{"record_id": "change-a", "count": 2}]
    assert recall_7d["abstain_reasons"] == {"no-high-signal-recall": 1}

    recall_30d = stats["windows"]["30d"]["recall"]
    assert recall_30d["events"] == 3
    assert recall_30d["injected"] == 2
    assert recall_30d["recall_rate"] == 2 / 3
    assert recall_30d["match_classes"] == {"topic": 2, "record-id": 1}
    assert recall_30d["top_matched_records"] == [{"record_id": "change-a", "count": 2}, {"record_id": "decision-b", "count": 1}]
    assert recall_30d["malformed_lines"] == 1


def test_project_memory_stats_marks_recall_unavailable_without_debug_log(tmp_path: Path, monkeypatch) -> None:
    # Given: a SyberMem project with no recall debug log
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")

    # When: memory stats are computed
    stats = project_memory_stats(project_root)

    # Then: recall stats are explicitly unavailable rather than fabricated as zero activity
    assert stats["totals"]["recall"]["status"] == "no_log"
    assert stats["windows"]["7d"]["recall"]["events"] == 0
    assert stats["windows"]["7d"]["recall"]["recall_rate"] is None
    assert stats["windows"]["30d"]["recall"]["status"] == "no_log"
    assert stats["recall_health"]["status"] == "no_log"


def test_project_memory_stats_includes_mixed_memory_usage_and_outcome_coverage(tmp_path: Path, monkeypatch) -> None:
    # Given: a mixed OpenCode usage journal with one turn and one session outcome
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    (sybermem / ".memory-usage.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"schema_version": 1, "host": "opencode", "timestamp": "2026-08-14T09:00:00+08:00", "session_id": "s1", "total_items": 2, "total_chars": 40, "recall_items": 1, "recall_chars": 20, "habit_items": 1, "habit_chars": 20, "norm_items": 0, "norm_chars": 0, "startup_items": 0, "startup_chars": 0}),
                json.dumps({"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-14T09:01:00+08:00", "recall_evidence_available": True, "recall_measurable": 1, "recall_unmeasurable": 1, "recall_hit": 1}),
            ],
        ) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")

    # When: the public project stats payload is built
    stats = project_memory_stats(project_root)

    # Then: usage is measured from turns only and outcome coverage is explicit
    assert stats["windows"]["7d"]["memory_usage"]["turns"] == 1
    assert stats["windows"]["30d"]["memory_usage"]["chars"] == 40
    assert stats["windows"]["7d"]["relevance"] == {
        "sessions": 1,
        "injected": 1,
        "measurable": 1,
        "unmeasurable": 1,
        "hit": 1,
        "precision": 1.0,
        "evidence_available": True,
    }


def _make_recall_health_project(
    tmp_path: Path,
    lines: list[str],
    monkeypatch,
    outcome_lines: list[str] | None = None,
    usage_outcome_lines: list[str] | None = None,
) -> Path:
    project_root = tmp_path / "project"
    sybermem = project_root / ".sybermem"
    sybermem.mkdir(parents=True)
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")
    monkeypatch.setattr(memory_stats_module, "now_iso", lambda: "2026-08-14T12:00:00+08:00")
    if lines:
        (sybermem / ".recall-debug.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if outcome_lines:
        (sybermem / ".recall-outcomes.jsonl").write_text("\n".join(outcome_lines) + "\n", encoding="utf-8")
    if usage_outcome_lines:
        (sybermem / ".memory-usage.jsonl").write_text("\n".join(usage_outcome_lines) + "\n", encoding="utf-8")
    return project_root


def _healthy_recall_lines() -> list[str]:
    # Recent 7d window with a strong injection rate so relevance, not frequency,
    # decides the verdict.
    return [
        json.dumps({"timestamp": f"2026-08-1{day}T09:00:00+08:00", "event": "inject", "record_ids": ["change-a"], "match_classes": ["topic"], "reason": "high-signal-recall"})
        for day in range(0, 4)
    ]


def test_recall_health_reports_no_log_when_debug_log_missing(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with no recall debug log
    project_root = _make_recall_health_project(tmp_path, [], monkeypatch)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: it is explicitly unavailable, not a zero-rate claim
    assert health["status"] == "no_log"
    assert health["hint"]


def test_recall_health_reports_no_activity_when_no_recent_events(tmp_path: Path, monkeypatch) -> None:
    # Given: a debug log whose only entry is far outside the 30d window
    lines = [json.dumps({"timestamp": "2026-05-01T09:00:00+08:00", "event": "inject", "record_ids": ["change-a"], "match_classes": ["topic"], "reason": "high-signal-recall"})]
    project_root = _make_recall_health_project(tmp_path, lines, monkeypatch)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: no recent activity is distinguished from a low-signal problem
    assert health["status"] == "no_activity"
    assert health["hint"]


def test_recall_health_reports_healthy_when_recent_injection_rate_is_strong(tmp_path: Path, monkeypatch) -> None:
    # Given: recent windows with mostly successful injections
    lines = [
        json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "event": "inject", "record_ids": ["change-a"], "match_classes": ["topic"], "reason": "high-signal-recall"}),
        json.dumps({"timestamp": "2026-08-12T09:00:00+08:00", "event": "inject", "record_ids": ["decision-b"], "match_classes": ["record-id"], "reason": "high-signal-recall"}),
        json.dumps({"timestamp": "2026-08-11T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "no candidate records matched the prompt"}),
    ]
    project_root = _make_recall_health_project(tmp_path, lines, monkeypatch)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: a strong recent injection rate is healthy
    assert health["status"] == "healthy"


def test_recall_health_reports_low_signal_when_abstains_dominate_recent_window(tmp_path: Path, monkeypatch) -> None:
    # Given: recent windows dominated by low-signal abstentions (0/5 injected in 7d)
    lines = [
        json.dumps({"timestamp": "2026-08-14T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "matched rows were keyword-only and below the high-signal floor"}),
        json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "matches did not cross compact recall reliability threshold"}),
        json.dumps({"timestamp": "2026-08-12T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "matched rows were keyword-only and below the high-signal floor"}),
        json.dumps({"timestamp": "2026-08-11T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "no candidate records matched the prompt"}),
        json.dumps({"timestamp": "2026-08-10T09:00:00+08:00", "event": "abstain", "record_ids": [], "match_classes": [], "reason": "matched rows were keyword-only and below the high-signal floor"}),
    ]
    project_root = _make_recall_health_project(tmp_path, lines, monkeypatch)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: the low injection rate is flagged as low_signal with an actionable hint
    assert health["status"] == "low_signal"
    assert health["hint"]


def test_relevance_counts_aggregate_precision_across_outcome_windows(tmp_path: Path, monkeypatch) -> None:
    # Given: recall-outcome sessions with injected/hit counts in and out of window
    outcome_lines = [
        json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "session": "s1", "injected": 3, "hit": 1, "precision": 1 / 3}),
        json.dumps({"timestamp": "2026-08-12T09:00:00+08:00", "session": "s2", "injected": 2, "hit": 2, "precision": 1.0}),
        json.dumps({"timestamp": "2026-07-20T09:00:00+08:00", "session": "s3", "injected": 4, "hit": 0, "precision": 0.0}),
        "not json",
    ]
    project_root = _make_recall_health_project(tmp_path, _healthy_recall_lines(), monkeypatch, outcome_lines)

    # When: memory stats are computed
    stats = project_memory_stats(project_root)

    # Then: 7d precision counts only in-window sessions; 30d includes the older one
    # (30d window = today-29d = 2026-07-16, so the 2026-07-20 session is in 30d only)
    relevance_7d = stats["windows"]["7d"]["relevance"]
    assert relevance_7d["injected"] == 5
    assert relevance_7d["hit"] == 3
    assert relevance_7d["precision"] == 3 / 5
    relevance_30d = stats["windows"]["30d"]["relevance"]
    assert relevance_30d["injected"] == 9
    assert relevance_30d["hit"] == 3
    assert relevance_30d["precision"] == 3 / 9
    # Totals include every valid session regardless of window.
    assert stats["totals"]["relevance"]["injected"] == 9


def test_recall_health_reports_low_relevance_when_injected_records_miss_edits(tmp_path: Path, monkeypatch) -> None:
    # Given: a healthy injection rate but injected records rarely match edited files
    outcome_lines = [
        json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "session": "s1", "injected": 4, "hit": 1, "precision": 0.25}),
        json.dumps({"timestamp": "2026-08-12T09:00:00+08:00", "session": "s2", "injected": 4, "hit": 0, "precision": 0.0}),
    ]
    project_root = _make_recall_health_project(tmp_path, _healthy_recall_lines(), monkeypatch, outcome_lines)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: high frequency with low precision is flagged as low_relevance, not healthy
    assert health["status"] == "low_relevance"
    assert health["precision"] == 1 / 8
    assert health["hint"]


def test_recall_health_reports_low_measurability_when_anchors_are_sparse(tmp_path: Path, monkeypatch) -> None:
    # Given: recall fires at a healthy rate, but most injected records cannot be checked
    # against edits because they lack usable related_files anchors.
    outcome_lines = [
        json.dumps({"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-13T09:00:00+08:00", "recall_evidence_available": True, "recall_measurable": 2, "recall_unmeasurable": 3, "recall_hit": 2}),
        json.dumps({"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-12T09:00:00+08:00", "recall_evidence_available": True, "recall_measurable": 1, "recall_unmeasurable": 3, "recall_hit": 1}),
    ]
    project_root = _make_recall_health_project(tmp_path, _healthy_recall_lines(), monkeypatch, usage_outcome_lines=outcome_lines)

    # When: recall health is derived.
    health = recall_health(project_root)

    # Then: sparse anchors get their own advisory instead of being mislabeled as relevance.
    assert health["status"] == "low_measurability"
    assert health["precision"] == 1.0
    assert "related_files" in health["hint"]


def test_recall_health_does_not_report_low_measurability_without_edit_evidence(tmp_path: Path, monkeypatch) -> None:
    # Given: unmeasurable rows exist, but the host had no edited-file evidence to compare.
    outcome_lines = [
        json.dumps({"schema_version": 1, "host": "opencode", "event": "session_outcome", "timestamp": "2026-08-13T09:00:00+08:00", "recall_evidence_available": False, "recall_measurable": 0, "recall_unmeasurable": 4, "recall_hit": 0}),
    ]
    project_root = _make_recall_health_project(tmp_path, _healthy_recall_lines(), monkeypatch, usage_outcome_lines=outcome_lines)

    # When: recall health is derived.
    health = recall_health(project_root)

    # Then: absence of edit evidence is not blamed on record anchor quality.
    assert health["status"] == "healthy"


def test_recall_health_stays_healthy_when_precision_sample_is_too_small(tmp_path: Path, monkeypatch) -> None:
    # Given: a healthy injection rate but only 2 injected-record samples (below floor)
    outcome_lines = [
        json.dumps({"timestamp": "2026-08-13T09:00:00+08:00", "session": "s1", "injected": 2, "hit": 0, "precision": 0.0}),
    ]
    project_root = _make_recall_health_project(tmp_path, _healthy_recall_lines(), monkeypatch, outcome_lines)

    # When: recall health is derived
    health = recall_health(project_root)

    # Then: a couple of misses never look like a systemic problem; precision stays advisory-only
    assert health["status"] == "healthy"
    assert health["precision"] is None
