from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HEALTH_TEMPLATES = (
    Path("packages/claude-skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py"),
    Path("skills/sybermem-init-project/project-files/.sybermem/hooks/check_project_health.py"),
)


def test_health_templates_do_not_expose_removed_team_contract() -> None:
    for relative_path in HEALTH_TEMPLATES:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        for forbidden in ("team_info", "team_path_accessible", '"team":'):
            assert forbidden not in text
    assert (ROOT / HEALTH_TEMPLATES[0]).read_bytes() == (ROOT / HEALTH_TEMPLATES[1]).read_bytes()
