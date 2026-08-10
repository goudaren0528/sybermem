from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.search import compact_project_search, high_signal_recall_hints, search_project


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    sybermem.mkdir()
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_record(root: Path, subdir: str, filename: str, frontmatter: list[str], body: str) -> None:
    records = root / ".sybermem" / subdir
    records.mkdir(exist_ok=True)
    (records / filename).write_text("\n".join(["---", *frontmatter, "---", "", body]) + "\n", encoding="utf-8")


def test_compact_project_search_excludes_auto_trail_evidence_but_explicit_search_returns_it(tmp_path: Path, monkeypatch) -> None:
    # Given: an authoritative manual record and a matching auto-trail evidence record
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-authoritative.md",
        ["type: change", "date: 2026-08-04", "title: Authoritative recall fix", "status: implemented"],
        "## Summary\nManual fix for recall-token retrieval.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-04-002-auto.md",
        ["type: change", "date: 2026-08-04", "title: Auto recall trail", "status: implemented"],
        "## Change Content\nAuto-generated from workspace changes detected at session stop. recall-token",
    )
    monkeypatch.chdir(project_root)

    # When: explicit and compact automatic searches run for the same query
    explicit_rows = search_project("recall-token")
    compact_rows = compact_project_search("recall-token", limit=3)

    # Then: evidence stays visible on explicit search but is excluded from automatic recall
    assert {row["authority"] for row in explicit_rows} == {"authoritative", "evidence"}
    assert [row["record_id"] for row in compact_rows] == ["change-001"]


def test_project_search_derives_summary_and_related_digest_from_markdown(tmp_path: Path, monkeypatch) -> None:
    # Given: a manual record covered by a digest through existing source_records metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-recall-contract.md",
        ["type: change", "date: 2026-08-04", "title: Recall contract", "status: implemented"],
        "## Summary\nRecall packets include bounded metadata only.\n\n## Details\nFull content should stay out of packets.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-05-001-recall-digest.md",
        [
            "type: digest",
            "kind: phase",
            "date: 2026-08-05",
            "number: 001",
            "title: recall digest",
            "status: completed",
            "source_records:",
            "  - changes/2026-08-04-001-recall-contract.md",
        ],
        "## Core Conclusions\n- Recall contract stabilized.",
    )
    monkeypatch.chdir(project_root)

    # When: project search returns the manual record
    rows = search_project("Recall packets")

    # Then: compact metadata is derived without requiring canonical format changes
    row = next(item for item in rows if item["record_id"] == "change-001")
    assert row["summary"] == "Recall packets include bounded metadata only."
    assert row["related_digest"] == "digest-001"
    assert row["match_reason"] == row["match"]
    assert {
        "source_kind",
        "authority",
        "lifecycle",
        "freshness",
        "match_reason",
        "related_digest",
        "conflict_note",
    }.issubset(row)


def test_project_search_derives_archived_lifecycle_from_index_archived_conclusions(tmp_path: Path, monkeypatch) -> None:
    # Given: a record archived only by the canonical INDEX archived-conclusions section
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    (project_root / ".sybermem" / "INDEX.md").write_text(
        "# SyberMem Index\n\n"
        "## Key Conclusions\n\n"
        "## Archived Conclusions\n\n"
        "- [change-001] #search — archived-index-token was compressed into later history (2026-08-04) [archived]\n",
        encoding="utf-8",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-index-archived.md",
        ["type: change", "date: 2026-08-04", "title: Index archived record", "status: implemented"],
        "## Summary\narchived-index-token appears without a body archived marker.",
    )
    monkeypatch.chdir(project_root)

    # When: search derives metadata from Markdown records and INDEX state
    rows = search_project("archived-index-token")

    # Then: INDEX archival marks the record historical without adding canonical record fields
    row = next(item for item in rows if item["record_id"] == "change-001")
    assert row["lifecycle"] == "archived"
    assert row["freshness"] == "historical"


def test_compact_project_search_notes_parallel_authoritative_conflicts(tmp_path: Path, monkeypatch) -> None:
    # Given: two equally current authoritative records matching the same conflict-bearing query
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-first-policy.md",
        ["type: decision", "date: 2026-08-04", "title: First conflict policy", "status: decided"],
        "## Summary\nconflict-token should use policy A.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-04-002-second-policy.md",
        ["type: decision", "date: 2026-08-04", "title: Second conflict policy", "status: decided"],
        "## Summary\nconflict-token should use policy B.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall sees equally strong authoritative candidates
    rows = compact_project_search("conflict-token", limit=3)

    # Then: the sources remain searchable and carry an explicit review note
    assert [row["record_id"] for row in rows] == ["decision-001", "decision-002"]
    assert {row["freshness"] for row in rows} == {"conflicted"}
    assert {row["conflict_note"] for row in rows} == {"parallel authoritative records match; review before relying on either"}


def test_compact_project_search_matches_english_terms_across_record_fields(tmp_path: Path, monkeypatch) -> None:
    # Given: a record whose meaningful prompt terms are spread across title, topics, relations, and body
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-workspace-recall.md",
        [
            "type: requirement",
            "date: 2026-08-04",
            "title: Workspace recall behavior",
            "status: accepted",
            "topics: [search, context]",
            "implements: decision-123",
        ],
        "## Summary\nNatural prompts should retrieve concise context without exact phrase matching.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-001-workspace-only.md",
        ["type: change", "date: 2026-08-05", "title: Workspace cleanup", "status: implemented"],
        "## Summary\nA newer single-term record should not crowd out the stronger overlap.",
    )
    monkeypatch.chdir(project_root)

    # When: a natural English prompt distributes terms across record fields
    rows = compact_project_search("retrieve workspace context for search decision", limit=3)

    # Then: the authoritative record is recalled without requiring an exact phrase match
    assert [row["record_id"] for row in rows] == ["requirement-001"]
    assert rows[0]["match"] in {"relation", "topic", "keyword"}


def test_compact_project_search_matches_natural_chinese_prompt(tmp_path: Path, monkeypatch) -> None:
    # Given: a Chinese requirement record with no ASCII query terms
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-cjk-recall.md",
        ["type: requirement", "date: 2026-08-04", "title: 中文任务召回", "status: accepted", "topics: [中文, 检索]"],
        "## Summary\n自然语言提示可以检索需求上下文并完成任务召回。",
    )
    monkeypatch.chdir(project_root)

    # When: a natural CJK prompt asks for the same retrieval behavior
    rows = compact_project_search("中文提示应该检索上下文并召回相关需求", limit=3)

    # Then: compact recall returns the matching authoritative requirement
    assert [row["record_id"] for row in rows] == ["requirement-001"]


def test_compact_project_search_ignores_low_signal_prompt(tmp_path: Path, monkeypatch) -> None:
    # Given: a project with content containing common words and isolated CJK characters
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-common.md",
        ["type: change", "date: 2026-08-04", "title: Common project change record", "status: implemented"],
        "## Summary\nThe project has a change record with 中文内容 for realistic fixtures.",
    )
    monkeypatch.chdir(project_root)

    # When: the prompt contains only low-signal short/common terms
    rows = compact_project_search("please check the project change record", limit=3)

    # Then: automatic recall stays quiet
    assert rows == []


def test_compact_project_search_can_explain_weak_abstention_without_hook_noise(tmp_path: Path, monkeypatch) -> None:
    # Given: a weak one-field overlap that explicit search can still inspect
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-weak.md",
        ["type: change", "date: 2026-08-04", "title: Weaknoise note", "status: implemented"],
        "## Summary\nA record with only one meaningful overlap.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall is used by hooks versus an explicit compact diagnostic caller
    silent_rows = compact_project_search("weaknoise unrelated", limit=3)
    diagnostic_rows = compact_project_search("weaknoise unrelated", limit=3, include_abstention=True)
    explicit_rows = search_project("weaknoise unrelated")

    # Then: hook-bound automatic recall remains silent, while diagnostics explain the abstention
    assert silent_rows == []
    assert diagnostic_rows == [
        {
            "result": "no_reliable_recall",
            "reason": "matches did not cross compact recall reliability threshold",
            "query": "weaknoise unrelated",
        }
    ]
    assert [row["record_id"] for row in explicit_rows] == ["change-001"]


def test_compact_project_search_abstains_from_stale_only_matches_but_explicit_search_shows_history(tmp_path: Path, monkeypatch) -> None:
    # Given: the only matching record is superseded historical evidence
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-old-policy.md",
        [
            "type: decision",
            "date: 2026-08-04",
            "title: Historical stale-token policy",
            "status: decided",
            "superseded_by: decision-002",
        ],
        "## Summary\nstale-token policy was replaced by a newer decision.",
    )
    monkeypatch.chdir(project_root)

    # When: automatic and explicit retrieval ask for the same historical fact
    silent_rows = compact_project_search("stale-token policy", limit=3)
    diagnostic_rows = compact_project_search("stale-token policy", limit=3, include_abstention=True)
    explicit_rows = search_project("stale-token policy")

    # Then: automatic recall abstains, but explicit search still exposes the evidence as historical
    assert silent_rows == []
    assert diagnostic_rows[0]["result"] == "no_reliable_recall"
    assert diagnostic_rows[0]["reason"] == "only historical or stale matches were found"
    assert [row["record_id"] for row in explicit_rows] == ["decision-001"]
    assert explicit_rows[0]["lifecycle"] == "superseded"
    assert explicit_rows[0]["freshness"] == "historical"


def test_project_search_adds_successor_guidance_for_superseded_records(tmp_path: Path, monkeypatch) -> None:
    # Given: an old decision points at its successor using existing superseded_by frontmatter
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-old-decision.md",
        [
            "type: decision",
            "date: 2026-08-04",
            "title: Old correction-token decision",
            "status: decided",
            "superseded_by: decision-002",
        ],
        "## Summary\ncorrection-token used the old approach.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-002-new-decision.md",
        ["type: decision", "date: 2026-08-05", "title: New correction-token decision", "status: decided"],
        "## Summary\ncorrection-token now uses the successor approach.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit historical search returns the superseded hit
    rows = search_project("old correction-token")

    # Then: the hit points at the current successor record without mutating history
    row = next(item for item in rows if item["record_id"] == "decision-001")
    assert row["successor_record"] == "decision-002"
    assert row["successor_title"] == "New correction-token decision"
    assert row["current_record"] == "decision-002"
    assert row["current_guidance"] == "Prefer successor decision-002 for current guidance."


def test_project_search_resolves_uuid_backed_superseded_successor(tmp_path: Path, monkeypatch) -> None:
    # Given: a UUID-backed old decision points at a UUID-backed successor via superseded_by
    old_id = "decision-6a3ab8a0e44e4c41843b66bde8b7134a"
    new_id = "decision-71c1f4bdc01a4b6cb07731667f1c08c7"
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        f"2026-08-04-{old_id}-old.md",
        [
            "type: decision",
            f"record_id: {old_id}",
            "date: 2026-08-04",
            "title: Old uuid-token decision",
            "status: decided",
            f"superseded_by: {new_id}",
        ],
        "## Summary\nuuid-token used the old approach.",
    )
    write_record(
        project_root,
        "decisions",
        f"2026-08-05-{new_id}-new.md",
        ["type: decision", f"record_id: {new_id}", "date: 2026-08-05", "title: New uuid-token decision", "status: decided"],
        "## Summary\nuuid-token now uses the successor approach.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit historical search returns the superseded UUID hit
    rows = search_project("old uuid-token")

    # Then: successor guidance resolves across UUID-backed ids (regression: RECORD_ID_RE numeric-only)
    row = next(item for item in rows if item["record_id"] == old_id)
    assert row["successor_record"] == new_id
    assert row["current_record"] == new_id
    assert row["current_guidance"] == f"Prefer successor {new_id} for current guidance."


def test_project_search_resolves_uuid_backed_fixes_relation(tmp_path: Path, monkeypatch) -> None:
    # Given: a resolved UUID-backed bug and a later change using a UUID-backed fixes relation
    bug_id = "bug-6a3ab8a0e44e4c41843b66bde8b7134a"
    fix_id = "change-71c1f4bdc01a4b6cb07731667f1c08c7"
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "bugs",
        f"2026-08-04-{bug_id}-resolved.md",
        ["type: bug", f"record_id: {bug_id}", "date: 2026-08-04", "title: Resolved uuidfix-token bug", "status: resolved"],
        "## Summary\nuuidfix-token bug was fixed after diagnosis.",
    )
    write_record(
        project_root,
        "changes",
        f"2026-08-05-{fix_id}-fix.md",
        ["type: change", f"record_id: {fix_id}", "date: 2026-08-05", "title: Fix uuidfix-token bug", "status: implemented", f"fixes: {bug_id}"],
        "## Summary\nuuidfix-token is fixed by the current change.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search finds both the resolved bug and the UUID-backed fixing change
    rows = search_project("uuidfix-token bug")

    # Then: fixes-based successor guidance resolves across UUID-backed ids
    bug = next(item for item in rows if item["record_id"] == bug_id)
    fix = next(item for item in rows if item["record_id"] == fix_id)
    assert bug["successor_record"] == fix_id
    assert bug["current_record"] == fix_id
    assert fix["current_record"] == fix_id
    assert fix["current_guidance"] == f"This record resolves {bug_id}."


def test_project_search_adds_current_guidance_for_resolved_records_and_fixes(tmp_path: Path, monkeypatch) -> None:
    # Given: a resolved bug and a later change using the existing fixes relation
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-resolved-bug.md",
        ["type: bug", "date: 2026-08-04", "title: Resolved current-token bug", "status: resolved"],
        "## Summary\ncurrent-token bug was fixed after diagnosis.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-fix-change.md",
        ["type: change", "date: 2026-08-05", "title: Fix current-token bug", "status: implemented", "fixes: bug-001"],
        "## Summary\ncurrent-token is fixed by the current change.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search finds both the resolved lifecycle evidence and the fixing change
    rows = search_project("current-token bug")

    # Then: the resolved record points to its fixing successor, and the fixer identifies itself as current
    bug = next(item for item in rows if item["record_id"] == "bug-001")
    fix = next(item for item in rows if item["record_id"] == "change-002")
    assert bug["successor_record"] == "change-002"
    assert bug["current_record"] == "change-002"
    assert bug["current_guidance"] == "Prefer successor change-002 for current guidance."
    assert fix["current_record"] == "change-002"
    assert fix["current_guidance"] == "This record resolves bug-001."


def test_project_search_chases_superseded_fixer_to_active_replacement(tmp_path: Path, monkeypatch) -> None:
    # Given: a resolved bug was fixed by a change that is itself superseded by an active replacement
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-chain-bug.md",
        ["type: bug", "date: 2026-08-04", "title: Resolved chain-token bug", "status: resolved"],
        "## Summary\nchain-token bug was resolved by a stale fix.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-stale-fix.md",
        [
            "type: change",
            "date: 2026-08-05",
            "title: Stale chain-token fix",
            "status: implemented",
            "fixes: bug-001",
            "superseded_by: change-003",
        ],
        "## Summary\nchain-token fix was replaced.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-06-003-active-fix.md",
        ["type: change", "date: 2026-08-06", "title: Active chain-token fix", "status: implemented"],
        "## Summary\nchain-token is fixed by the active replacement.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search presents the resolved bug and stale fixing change
    rows = search_project("chain-token")

    # Then: both historical records point to the active replacement, not the stale fixer
    bug = next(item for item in rows if item["record_id"] == "bug-001")
    stale_fix = next(item for item in rows if item["record_id"] == "change-002")
    assert bug["successor_record"] == "change-003"
    assert bug["current_record"] == "change-003"
    assert stale_fix["successor_record"] == "change-003"
    assert stale_fix["current_record"] == "change-003"


def test_project_search_omits_current_guidance_for_missing_superseded_target(tmp_path: Path, monkeypatch) -> None:
    # Given: a historical record points at a missing successor id
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-missing-target.md",
        [
            "type: decision",
            "date: 2026-08-04",
            "title: Missing miss-token successor",
            "status: decided",
            "superseded_by: decision-099",
        ],
        "## Summary\nmiss-token points to a missing successor.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search returns the stale historical record
    rows = search_project("miss-token")

    # Then: missing targets are not promoted as current guidance
    row = next(item for item in rows if item["record_id"] == "decision-001")
    assert "successor_record" not in row
    assert "current_record" not in row
    assert "current_guidance" not in row


def test_project_search_never_promotes_evidence_fixer_as_current(tmp_path: Path, monkeypatch) -> None:
    # Given: the only fixing record is auto-trail evidence
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-evidence-bug.md",
        ["type: bug", "date: 2026-08-04", "title: Resolved evidence-token bug", "status: resolved"],
        "## Summary\nevidence-token bug was resolved.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-auto-fix.md",
        ["type: change", "date: 2026-08-05", "title: Auto evidence-token fix", "status: implemented", "fixes: bug-001"],
        "## Change Content\nAuto-generated from workspace changes detected at session stop. evidence-token",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search sees both the resolved bug and auto-trail fixer evidence
    rows = search_project("evidence-token")

    # Then: the evidence fixer remains searchable but is not promoted as current guidance
    bug = next(item for item in rows if item["record_id"] == "bug-001")
    auto_fix = next(item for item in rows if item["record_id"] == "change-002")
    assert auto_fix["authority"] == "evidence"
    assert "successor_record" not in bug
    assert "current_record" not in bug
    assert "current_guidance" not in auto_fix


def test_project_search_omits_current_guidance_for_successor_cycle(tmp_path: Path, monkeypatch) -> None:
    # Given: two stale decisions point at each other as successors
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-cycle-a.md",
        ["type: decision", "date: 2026-08-04", "title: Cycle cycle-token A", "status: decided", "superseded_by: decision-002"],
        "## Summary\ncycle-token A points to B.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-002-cycle-b.md",
        ["type: decision", "date: 2026-08-05", "title: Cycle cycle-token B", "status: decided", "superseded_by: decision-001"],
        "## Summary\ncycle-token B points to A.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search returns both historical records
    rows = search_project("cycle-token")

    # Then: cycles are guarded and no stale record is promoted as current
    assert {row["record_id"] for row in rows} == {"decision-001", "decision-002"}
    assert all("current_record" not in row for row in rows)
    assert all("successor_record" not in row for row in rows)


def test_high_signal_recall_stays_silent_for_keyword_only_matches(tmp_path: Path, monkeypatch) -> None:
    # Given: a current authoritative record that only matches by distributed keyword overlap
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-keyword-only.md",
        ["type: requirement", "date: 2026-08-04", "title: Workspace recall behavior", "status: accepted"],
        "## Summary\nNatural prompts should retrieve concise context without exact phrase matching.",
    )
    monkeypatch.chdir(project_root)

    # When: the hot-path hook helper and the explicit compact search see the same prompt
    hints, reason = high_signal_recall_hints("retrieve workspace context for behavior", limit=3)
    compact_rows = compact_project_search("retrieve workspace context for behavior", limit=3)

    # Then: compact search still surfaces the keyword hit, but the hook abstains with a reason
    assert [row["record_id"] for row in compact_rows] == ["requirement-001"]
    assert hints == []
    assert reason == "matched rows were keyword-only and below the high-signal floor"


def test_high_signal_recall_injects_relation_and_record_id_matches(tmp_path: Path, monkeypatch) -> None:
    # Given: a record reachable by an explicit relation match
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-relation-hit.md",
        ["type: change", "date: 2026-08-04", "title: Signal change", "status: implemented", "implements: requirement-002"],
        "## Summary\nHigh-signal relation match should inject.",
    )
    monkeypatch.chdir(project_root)

    # When: the prompt references the related record id (relation match) and the record id itself
    relation_hints, relation_reason = high_signal_recall_hints("what implements requirement-002 here", limit=3)
    id_hints, id_reason = high_signal_recall_hints("change-001", limit=3)

    # Then: both strong signals inject with no abstention
    assert [row["record_id"] for row in relation_hints] == ["change-001"]
    assert relation_reason == ""
    assert [row["record_id"] for row in id_hints] == ["change-001"]
    assert id_reason == ""


def test_high_signal_recall_reports_no_candidate_reason(tmp_path: Path, monkeypatch) -> None:
    # Given: a project whose records do not match the prompt at all
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-unrelated.md",
        ["type: change", "date: 2026-08-04", "title: Unrelated topic", "status: implemented"],
        "## Summary\nCompletely unrelated content.",
    )
    monkeypatch.chdir(project_root)

    # When: the prompt shares no meaningful terms with any record
    hints, reason = high_signal_recall_hints("quantum teleportation latency budget", limit=3)

    # Then: the hook abstains and the reason is bounded and non-empty for debug logging
    assert hints == []
    assert reason != ""


def test_compact_search_ranks_specific_match_above_newer_generic_match(tmp_path: Path, monkeypatch) -> None:
    # Given: an older record matched specifically by topic, and a newer record matched only
    # by generic keyword overlap — both authoritative and current.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-01-001-specific.md",
        [
            "type: decision",
            "date: 2026-08-01",
            "title: Older policy",
            "status: decided",
            "topics: [rankspecificity, retrieval]",
        ],
        "## Summary\nThe rankspecificity retrieval policy decision.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-09-002-generic.md",
        ["type: change", "date: 2026-08-09", "title: Newer rankspecificity retrieval note", "status: implemented"],
        "## Summary\nA newer record that only overlaps by generic keyword in title and body.",
    )
    monkeypatch.chdir(project_root)

    # When: a query matches the old record by topic and the new record by keyword
    rows = compact_project_search("rankspecificity retrieval", limit=3)

    # Then: the specific (topic) match ranks first despite being older (E5)
    assert rows[0]["record_id"] == "decision-001"
    assert rows[0]["match"] == "topic"
