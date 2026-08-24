from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_core.norms import CONSTITUTION_MAX, active_norms, constitution, scoped_norms


def write_project(root: Path) -> None:
    sybermem = root / ".sybermem"
    (sybermem / "norms").mkdir(parents=True)
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text("{}\n", encoding="utf-8")
    (sybermem / "INDEX.md").write_text("# SyberMem Index\n", encoding="utf-8")
    (sybermem / "project.yaml").write_text("project_id: project-1\nslug: demo\n", encoding="utf-8")


def write_norm(root: Path, name: str, record_id: str, scope: str, statement: str, *, status: str = "active", superseded_by: str = "") -> None:
    fm = [
        "type: norm",
        f"record_id: {record_id}",
        "date: 2026-08-20",
        f"title: {statement}",
        "authority: authoritative",
        f"status: {status}",
        f"scope: {scope}",
        f"key_conclusion: {statement}",
    ]
    if superseded_by:
        fm.append(f"superseded_by: {superseded_by}")
    text = "\n".join(["---", *fm, "---", "", "## Norm Statement", f"{statement}"]) + "\n"
    (root / ".sybermem" / "norms" / name).write_text(text, encoding="utf-8")


def test_constitution_returns_only_active_global_norms(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "g1.md", "norm-001", "global", "Use pnpm in this repo")
    write_norm(root, "g2.md", "norm-002", "global", "PRs must be small and focused")
    write_norm(root, "s1.md", "norm-003", "topic:auth", "Sessions expire in 30m")  # scoped, not in constitution
    write_norm(root, "sup.md", "norm-004", "global", "Old rule", status="active", superseded_by="norm-001")  # superseded -> excluded

    con = constitution(root)
    ids = [n["record_id"] for n in con]
    assert "norm-001" in ids and "norm-002" in ids
    assert "norm-003" not in ids  # scoped
    assert "norm-004" not in ids  # superseded


def test_constitution_is_bounded_and_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    for i in range(CONSTITUTION_MAX + 3):
        write_norm(root, f"g{i}.md", f"norm-{i:03d}", "global", f"Global rule {i}")

    con = constitution(root)
    assert len(con) == CONSTITUTION_MAX
    # deterministic: sorted by record_id
    ids = [n["record_id"] for n in con]
    assert ids == sorted(ids)


def test_scoped_norms_match_by_scope_tag(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "auth.md", "norm-010", "topic:auth", "Sessions expire in 30 minutes")
    write_norm(root, "pay.md", "norm-011", "topic:payment", "Webhooks must be idempotent")
    write_norm(root, "glob.md", "norm-012", "global", "Use pnpm")

    got = scoped_norms(root, "working on the auth session flow")
    ids = [n["record_id"] for n in got]
    assert ids == ["norm-010"]  # only the auth-scoped norm; global excluded from scoped lane


def test_scoped_norms_match_by_statement_overlap_when_no_scope_tag(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "n.md", "norm-020", "topic:webhooks", "Payment webhooks must be idempotent")

    # context shares two distinct statement terms (payment, webhooks) -> matches
    got = scoped_norms(root, "adding a new payment webhooks handler")
    assert [n["record_id"] for n in got] == ["norm-020"]

    # unrelated context -> silent
    assert scoped_norms(root, "update the readme title") == []


def test_active_norms_excludes_superseded_and_archived(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    write_project(root)
    write_norm(root, "a.md", "norm-030", "global", "Active rule")
    write_norm(root, "s.md", "norm-031", "global", "Superseded rule", superseded_by="norm-030")

    ids = [n["record_id"] for n in active_norms(root)]
    assert ids == ["norm-030"]
