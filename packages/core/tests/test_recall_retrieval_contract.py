from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.search import HIGH_SIGNAL_SCORE_FLOOR, compact_project_search, high_signal_recall_hints, search_project


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


def test_project_search_scores_key_conclusion_as_first_class_signal(tmp_path: Path, monkeypatch) -> None:
    # Given: one record only names the decisive phrase in key_conclusion, while a newer
    # record has a weaker body-only overlap with the same query.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "decisions",
        "2026-08-04-001-key-conclusion.md",
        [
            "type: decision",
            "date: 2026-08-04",
            "title: Recall ranking",
            "status: decided",
            "key_conclusion: Prefer keydetail-token anchors for recall ranking.",
        ],
        "## Summary\nRanking policy without the exact decisive phrase.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-body-only.md",
        ["type: change", "date: 2026-08-05", "title: Generic ranking followup", "status: implemented"],
        "## Summary\nA body-only keydetail-token mention should not outrank the conclusion.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search asks about the key conclusion phrase.
    rows = search_project("keydetail-token ranking")

    # Then: key_conclusion contributes to score and remains explainable.
    assert rows[0]["record_id"] == "decision-001"
    assert "key_conclusion" in rows[0]["matched_fields_detail"]
    assert rows[0]["score_breakdown"]["key_conclusion"] > 0


def test_related_files_path_boost_breaks_recall_ties_without_penalizing_anchorless_records(tmp_path: Path, monkeypatch) -> None:
    # Given: two current records tie on ordinary text, but only one declares the queried path.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "changes",
        "2026-08-04-001-path-hit.md",
        [
            "type: change",
            "date: 2026-08-04",
            "title: Recall scoring",
            "status: implemented",
            "related_files:",
            "  - packages/core/sybermem_core/search_query.py",
        ],
        "## Summary\npathboost-token keeps recall scoring explainable.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-anchorless.md",
        ["type: change", "date: 2026-08-05", "title: Recall scoring", "status: implemented"],
        "## Summary\npathboost-token search_query.py keeps recall scoring explainable.",
    )
    monkeypatch.chdir(project_root)

    # When: the query includes a concrete file path.
    rows = search_project("pathboost-token packages/core/sybermem_core/search_query.py")

    # Then: the anchored row wins, while the anchorless row is still retrievable.
    assert [row["record_id"] for row in rows[:2]] == ["change-001", "change-002"]
    assert "related_files" in rows[0]["matched_fields_detail"]
    assert rows[0]["score_breakdown"]["related_files"] > 0


def test_key_conclusion_and_path_keyword_hits_do_not_bypass_high_signal_gate(tmp_path: Path, monkeypatch) -> None:
    # Given: a weak keyword-only match comes from the new Phase 1 scoring facets.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-weak-facets.md",
        [
            "type: requirement",
            "date: 2026-08-04",
            "title: Weak facet record",
            "status: accepted",
            "key_conclusion: weakfacet-token should stay diagnostic.",
            "related_files:",
            "  - packages/core/weakfacet.py",
        ],
        "## Summary\nNo extra strong signal here.",
    )
    monkeypatch.chdir(project_root)

    # When: automatic prompt-time recall evaluates the facet-only hit.
    compact_rows = compact_project_search("weakfacet-token packages/core/weakfacet.py", limit=3)
    hints, reason = high_signal_recall_hints("weakfacet-token packages/core/weakfacet.py", limit=3)

    # Then: compact diagnostics can show it, but the high-signal hook still abstains.
    assert [row["record_id"] for row in compact_rows] == ["requirement-001"]
    assert compact_rows[0]["match"] == "keyword"
    assert hints == []
    assert reason == "matched rows were keyword-only and below the high-signal floor"


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


def test_high_signal_recall_keeps_digest_preference_behind_keyword_gate(tmp_path: Path, monkeypatch) -> None:
    # Given: digest matches are eligible for compact ordering, but only through weak keyword overlap.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "digests",
        "2026-08-01-001-current-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-01", "number: 001", "title: Current digest", "status: completed"],
        "## Core Conclusions\n- digestgate-token summarizes the current covered phase.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-09-002-archived-digest.md",
        [
            "type: digest",
            "kind: phase",
            "date: 2026-08-09",
            "number: 002",
            "title: Archived digest",
            "status: completed",
            "lifecycle: archived",
        ],
        "## Core Conclusions\n- digestgate-token summarizes archived phase history.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-10-003-current-decision.md",
        ["type: decision", "date: 2026-08-10", "title: Current digestgate decision", "status: active"],
        "## Summary\ndigestgate-token keeps compact recall in the current lane.",
    )
    monkeypatch.chdir(project_root)

    # When: compact search ranks digest candidates, while the hot-path gate evaluates them.
    compact_rows = compact_project_search("digestgate-token", limit=3)
    hints, reason = high_signal_recall_hints("digestgate-token", limit=3)

    # Then: current digest preference affects ordering, but keyword-only matches still do not auto-inject.
    assert [row["record_id"] for row in compact_rows] == ["decision-003", "digest-001", "digest-002"]
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


def test_high_signal_recall_caps_current_relation_expansion_per_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: one exact seed linked to evidence, historical, and two current records
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-prompt-expansion.md",
        ["type: requirement", "date: 2026-08-04", "title: Prompt expansion gate", "status: accepted"],
        "## Summary\nThe exact requirement is a high-signal prompt seed.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-evidence.md",
        ["type: change", "date: 2026-08-05", "title: Evidence link", "status: implemented", "authority: evidence", "implements: requirement-001"],
        "## Summary\nEvidence-only context must not enter prompt recall.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-06-003-historical.md",
        ["type: change", "date: 2026-08-06", "title: Historical link", "status: resolved", "implements: requirement-001"],
        "## Summary\nHistorical context must not enter prompt recall.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-07-004-current-older.md",
        ["type: change", "date: 2026-08-07", "title: Current older link", "status: implemented", "implements: requirement-001"],
        "## Summary\nA current authoritative expansion candidate.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-08-005-current-newer.md",
        ["type: change", "date: 2026-08-08", "title: Current newer link", "status: implemented", "implements: requirement-001"],
        "## Summary\nThe newest current authoritative expansion candidate.",
    )
    monkeypatch.chdir(project_root)

    # When: prompt-time recall names the exact requirement seed
    hints, reason = high_signal_recall_hints("requirement-001", limit=5)

    # Then: the seed carries only one current non-evidence expansion
    assert HIGH_SIGNAL_SCORE_FLOOR == 12.0
    assert [row["record_id"] for row in hints] == ["requirement-001", "change-005"]
    assert hints[1]["expanded_from"] == "requirement-001"
    assert hints[1]["authority"] == "authoritative"
    assert hints[1]["freshness"] == "current"
    assert reason == ""


def test_high_signal_recall_caps_relation_expansion_globally(tmp_path: Path, monkeypatch) -> None:
    # Given: three exact high-signal seeds each linked to one current authoritative record
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    for number in range(1, 4):
        write_record(
            project_root,
            "requirements",
            f"2026-08-0{number}-{number:03d}-seed.md",
            ["type: requirement", f"date: 2026-08-0{number}", f"title: Seed {number}", "status: accepted"],
            f"## Summary\nHigh-signal seed {number}.",
        )
        write_record(
            project_root,
            "changes",
            f"2026-08-1{number}-{number:03d}-linked.md",
            ["type: change", f"date: 2026-08-1{number}", f"title: Linked {number}", "status: implemented", f"implements: requirement-{number:03d}"],
            f"## Summary\nCurrent linked context {number}.",
        )
    monkeypatch.chdir(project_root)

    # When: one prompt names all three exact record-id seeds
    hints, reason = high_signal_recall_hints("requirement-001 requirement-002 requirement-003", limit=6)

    # Then: all seeds remain injectable but prompt-time expansion stops at two rows total
    expanded = [row for row in hints if row.get("match") == "relation-expanded"]
    assert len(expanded) == 2
    assert len({row["expanded_from"] for row in expanded}) == 2
    assert reason == ""


def test_relation_expansion_adds_implementing_change_after_explicit_requirement_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: a requirement and a change that implements it without sharing query text
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-relation-expansion.md",
        ["type: requirement", "date: 2026-08-04", "title: Typed relation expansion", "status: accepted"],
        "## Summary\nExplicit requirement seeds should bring their implementation context.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-implementation.md",
        [
            "type: change",
            "date: 2026-08-05",
            "title: Guarded graph traversal",
            "status: implemented",
            "implements: requirement-001",
        ],
        "## Summary\nOne-hop traversal now returns bounded linked context.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search names the requirement record id
    rows = search_project("requirement-001")

    # Then: the direct seed stays first and its implementing change follows with bounded provenance
    assert [row["record_id"] for row in rows[:2]] == ["requirement-001", "change-002"]
    expanded = rows[1]
    assert expanded["expanded_from"] == "requirement-001"
    assert expanded["expansion_relation"] == "implements"
    assert expanded["match"] == "relation-expanded"
    assert expanded["match_reason"] == "relation-expanded"


def test_relation_expansion_adds_fixing_change_after_explicit_bug_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: a bug and a fixing change whose only link to the query is fixes metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "bugs",
        "2026-08-04-001-expansion-bug.md",
        ["type: bug", "date: 2026-08-04", "title: Missing linked fix", "status: resolved"],
        "## Summary\nThe direct bug record should remain the retrieval seed.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-fix.md",
        [
            "type: change",
            "date: 2026-08-05",
            "title: Restore linked context",
            "status: implemented",
            "fixes: bug-001",
        ],
        "## Summary\nThe current change resolves the linked retrieval defect.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search names the bug record id
    rows = search_project("bug-001")

    # Then: the fixing change is expanded from the direct bug seed
    assert [row["record_id"] for row in rows[:2]] == ["bug-001", "change-002"]
    assert rows[1]["expanded_from"] == "bug-001"
    assert rows[1]["expansion_relation"] == "fixes"


def test_relation_expansion_dedupes_linked_row_already_present_as_direct_match(tmp_path: Path, monkeypatch) -> None:
    # Given: an exact seed whose implementing change also matches through relation metadata
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-dedupe-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Dedupe relation expansion", "status: accepted"],
        "## Summary\nThe explicit requirement is the direct retrieval seed.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-dedupe-target.md",
        ["type: change", "date: 2026-08-05", "title: Dedupe linked target", "status: implemented", "implements: requirement-001"],
        "## Summary\nThe linked row is also named explicitly by record id.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search expands the exact requirement seed
    rows = search_project("requirement-001 change-002")

    # Then: each explicitly matched record id occurs once and neither is reclassified as expanded
    record_ids = [row["record_id"] for row in rows]
    assert set(record_ids) == {"requirement-001", "change-002"}
    assert len(record_ids) == len(set(record_ids))
    assert all(row["match"] == "record-id" for row in rows)
    assert all("expanded_from" not in row for row in rows)


def test_high_signal_relation_expansion_prefers_current_authoritative_successor(tmp_path: Path, monkeypatch) -> None:
    # Given: one seed linked to evidence, a superseded record, and its active successor
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-authority-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Authority expansion seed", "status: accepted"],
        "## Summary\nPrompt recall should expand only to current authoritative context.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-09-002-evidence.md",
        ["type: change", "date: 2026-08-09", "title: Evidence expansion", "status: implemented", "authority: evidence", "implements: requirement-001"],
        "## Summary\nEvidence-only relation context.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-08-003-superseded.md",
        [
            "type: decision",
            "date: 2026-08-08",
            "title: Superseded expansion",
            "status: superseded",
            "superseded_by: decision-004",
            "related: requirement-001",
        ],
        "## Summary\nStale relation context should not enter prompt recall.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-07-004-current.md",
        ["type: decision", "date: 2026-08-07", "title: Current expansion", "status: decided", "related: requirement-001"],
        "## Summary\nCurrent authoritative relation context.",
    )
    monkeypatch.chdir(project_root)

    # When: prompt-time recall expands the exact requirement seed
    hints, reason = high_signal_recall_hints("requirement-001", limit=5)

    # Then: only the active authoritative successor is eligible for expansion
    assert [row["record_id"] for row in hints] == ["requirement-001", "decision-004"]
    assert hints[1]["authority"] == "authoritative"
    assert hints[1]["lifecycle"] == "active"
    assert hints[1]["freshness"] == "current"
    assert reason == ""


def test_relation_expansion_cycle_stays_one_hop(tmp_path: Path, monkeypatch) -> None:
    # Given: a three-record relation cycle rooted at an explicit requirement seed
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-cycle-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Cycle seed", "status: accepted", "related: decision-002"],
        "## Summary\nThe explicit seed starts a cyclic relation graph.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-002-cycle-middle.md",
        ["type: decision", "date: 2026-08-05", "title: Cycle middle", "status: decided", "related: change-003"],
        "## Summary\nThe first hop links onward but must not become a traversal seed.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-06-003-cycle-tail.md",
        ["type: change", "date: 2026-08-06", "title: Cycle tail", "status: implemented", "related: requirement-001"],
        "## Summary\nThe cycle closes back to the original seed.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search expands the requirement record id
    rows = search_project("requirement-001")

    # Then: expansion is bounded to direct neighbors without duplicate recursion
    assert [row["record_id"] for row in rows] == ["requirement-001", "change-003", "decision-002"]
    assert len({row["record_id"] for row in rows}) == 3
    assert all(row.get("expanded_from") == "requirement-001" for row in rows[1:])


def test_relation_expansion_orders_all_direct_matches_before_expanded_rows(tmp_path: Path, monkeypatch) -> None:
    # Given: two direct relation matches and one linked row that does not match the query itself
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-ordering-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Ordering seed", "status: accepted", "related: decision-002"],
        "## Summary\norder-token identifies the first direct relation seed.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-05-002-ordering-seed.md",
        ["type: decision", "date: 2026-08-05", "title: Ordering peer", "status: decided", "related: requirement-001"],
        "## Summary\nThe peer is also named explicitly by record id.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-06-003-ordering-expansion.md",
        ["type: change", "date: 2026-08-06", "title: Ordering expansion", "status: implemented", "implements: requirement-001"],
        "## Summary\nLinked context without the direct query term.",
    )
    monkeypatch.chdir(project_root)

    # When: search matches both seeds strongly enough to permit relation expansion
    rows = search_project("requirement-001 decision-002")

    # Then: every direct match is ordered before the relation-expanded row
    matches = [row["match"] for row in rows]
    first_expansion = matches.index("relation-expanded")
    assert {row["record_id"] for row in rows[:first_expansion]} == {"requirement-001", "decision-002"}
    assert all(match != "relation-expanded" for match in matches[:first_expansion])
    assert all(match == "relation-expanded" for match in matches[first_expansion:])


def test_relation_expansion_stays_off_for_weak_keyword_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: a requirement matched only by body keywords and a change implementing it
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-keyword-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Conservative retrieval", "status: accepted"],
        "## Summary\nweakexpand-token appears only as ordinary body context.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-keyword-implementation.md",
        ["type: change", "date: 2026-08-05", "title: Unrelated implementation title", "status: implemented", "implements: requirement-001"],
        "## Summary\nLinked implementation content does not repeat the weak query.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search reaches the requirement only through a weak keyword match
    rows = search_project("weakexpand-token")
    hints, reason = high_signal_recall_hints("weakexpand-token")

    # Then: the direct weak result remains visible without relation-expanded rows
    assert [row["record_id"] for row in rows] == ["requirement-001"]
    assert rows[0]["match"] == "keyword"
    assert all("expanded_from" not in row for row in rows)
    assert hints == []
    assert reason == "matched rows were keyword-only and below the high-signal floor"


def test_relation_expansion_stays_off_for_weak_topic_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: a requirement matched by topic and a change implementing it
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-topic-seed.md",
        [
            "type: requirement",
            "date: 2026-08-04",
            "title: Topic-gated retrieval",
            "status: accepted",
            "topics: [topicexpand, guardrail]",
        ],
        "## Summary\nTopic overlap remains a weak expansion seed.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-topic-implementation.md",
        ["type: change", "date: 2026-08-05", "title: Linked implementation", "status: implemented", "implements: requirement-001"],
        "## Summary\nThe implementation does not contain the topic query.",
    )
    monkeypatch.chdir(project_root)

    # When: explicit search reaches the requirement through topic overlap only
    rows = search_project("topicexpand guardrail")
    hints, reason = high_signal_recall_hints("topicexpand guardrail")

    # Then: topic matches do not trigger relation expansion
    assert [row["record_id"] for row in rows] == ["requirement-001"]
    assert rows[0]["match"] == "topic"
    assert all("expanded_from" not in row for row in rows)
    assert hints == []
    assert reason == "matches did not cross compact recall reliability threshold"


def test_relation_expansion_stays_off_for_semantic_only_seed(tmp_path: Path, monkeypatch) -> None:
    # Given: semantic recall can reach a requirement, which has an implementing change
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "requirements",
        "2026-08-04-001-semantic-seed.md",
        ["type: requirement", "date: 2026-08-04", "title: Authentication authorization boundary", "status: accepted"],
        "## Summary\nAuthentication and authorization must share a typed boundary.",
    )
    write_record(
        project_root,
        "changes",
        "2026-08-05-002-semantic-implementation.md",
        ["type: change", "date: 2026-08-05", "title: Identity boundary implementation", "status: implemented", "implements: requirement-001"],
        "## Summary\nThe linked change avoids the inflected semantic query terms.",
    )
    monkeypatch.setenv("SYBERMEM_SEMANTIC_RECALL", "1")
    monkeypatch.chdir(project_root)

    # When: an inflected query reaches the requirement through semantic supplement only
    rows = search_project("authenticating and authorizing")
    hints, reason = high_signal_recall_hints("authenticating and authorizing")

    # Then: semantic-only results do not trigger relation expansion
    semantic_rows = [row for row in rows if row.get("match") == "semantic"]
    assert [row["record_id"] for row in semantic_rows] == ["requirement-001"]
    assert all("expanded_from" not in row for row in rows)
    assert hints == []
    assert reason == "matched rows were keyword-only and below the high-signal floor"


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


def test_compact_search_prefers_current_digest_over_newer_archived_digest_with_same_tier(tmp_path: Path, monkeypatch) -> None:
    # Given: two digest matches share the same authority and keyword specificity, but only
    # one digest is still current coverage rather than archived history, and a current
    # authoritative row keeps compact recall eligible.
    project_root = tmp_path / "project"
    project_root.mkdir()
    write_project(project_root)
    write_record(
        project_root,
        "digests",
        "2026-08-01-001-current-digest.md",
        ["type: digest", "kind: phase", "date: 2026-08-01", "number: 001", "title: Current digest", "status: completed"],
        "## Core Conclusions\n- digestpref-token summarizes the current covered phase.",
    )
    write_record(
        project_root,
        "digests",
        "2026-08-09-002-archived-digest.md",
        [
            "type: digest",
            "kind: phase",
            "date: 2026-08-09",
            "number: 002",
            "title: Archived digest",
            "status: completed",
            "lifecycle: archived",
        ],
        "## Core Conclusions\n- digestpref-token summarizes archived phase history.",
    )
    write_record(
        project_root,
        "decisions",
        "2026-08-10-003-current-decision.md",
        ["type: decision", "date: 2026-08-10", "title: Current digestpref decision", "status: active"],
        "## Summary\ndigestpref-token keeps compact recall in the current lane.",
    )
    monkeypatch.chdir(project_root)

    # When: compact recall ranks same-tier digest matches
    rows = compact_project_search("digestpref-token", limit=3)

    # Then: the current digest outranks newer archived digest history within the summarized tier
    assert [row["record_id"] for row in rows] == ["decision-003", "digest-001", "digest-002"]
    assert rows[1]["lifecycle"] == "resolved"
    assert rows[2]["lifecycle"] == "archived"
