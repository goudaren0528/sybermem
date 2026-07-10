from __future__ import annotations

from pathlib import Path
import json


def remove_sybermem_protocol_block(text: str) -> str:
    start = "<!-- SYBERMEM_SESSION_PROTOCOL:START -->"
    end = "<!-- SYBERMEM_SESSION_PROTOCOL:END -->"
    if start not in text or end not in text:
        return text
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    pieces = []
    if before:
        pieces.append(before)
    if after:
        pieces.append(after)
    return "\n\n".join(pieces).rstrip() + "\n"


def deactivate_project_sybermem(root: Path) -> dict[str, object]:
    changed = []

    # 1) Preserve .sybermem/ untouched
    sybermem_dir = root / ".sybermem"
    if not sybermem_dir.is_dir():
        raise ValueError(f"No .sybermem directory found at {root}")

    # 2) Remove SyberMem hook/env entries from .claude/settings.json (non-destructive)
    settings_path = root / ".claude" / "settings.json"
    if settings_path.is_file():
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        env = dict(data.get("env", {}))
        env.pop("SYBERMEM_RECORD_MODE", None)
        if env:
            data["env"] = env
        elif "env" in data:
            data.pop("env")

        hooks = dict(data.get("hooks", {}))
        for key in ["SessionStart", "Stop", "UserPromptSubmit"]:
            hooks.pop(key, None)
        if hooks:
            data["hooks"] = hooks
        elif "hooks" in data:
            data.pop("hooks")

        settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        changed.append(str(settings_path).replace('\\', '/'))

    # 3) Remove protocol block from CLAUDE.md / AGENTS.md (non-destructive)
    for name in ["CLAUDE.md", "AGENTS.md"]:
        p = root / name
        if p.is_file():
            original = p.read_text(encoding="utf-8")
            updated = remove_sybermem_protocol_block(original)
            if updated != original:
                p.write_text(updated, encoding="utf-8")
                changed.append(str(p).replace('\\', '/'))

    return {
        "status": "project_deactivated",
        "root": str(root).replace('\\', '/'),
        "history_preserved": True,
        "changed_files": changed,
    }