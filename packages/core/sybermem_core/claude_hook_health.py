"""Read-only acceptance check for the four owned Claude Code project hooks."""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import claude_hook_contract as contract
from .project_refresh_settings import _EVENT, _identity, _guard


TARGETS = {
    "user_prompt": "user_prompt.py",
    "session_start_context": "session_start_context.py",
    "record_change_on_stop": "record_change_on_stop.py",
    "recall_outcome_on_stop": "recall_outcome_on_stop.py",
}


def check_managed_claude_hooks(root: Path, *, version: tuple[int, ...] | None = None) -> dict:
    """Inspect settings and prerequisites only; do not import or execute project scripts."""
    errors: list[str] = []
    settings_path = root / ".claude" / "settings.json"
    # Check lexical components before any read/is_file: resolve() would hide links.
    try:
        _guard(settings_path)
        _guard(contract.LAUNCHER_PATH)
    except (OSError, ValueError):
        return {"status": "error", "errors": ["unsafe managed settings or launcher path"]}
    version = contract.probe_claude_version() if version is None else version
    if not contract.supports_exec(version):
        errors.append("Claude Code version unknown or too old for exec hooks")
    launcher = contract.LAUNCHER_PATH
    if not launcher.is_absolute() or not launcher.is_file():
        errors.append("managed launcher missing")
    try:
        python = contract.executable_python()
    except (OSError, ValueError):
        python = None
        errors.append("real Python executable unavailable")
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
        if not isinstance(settings, dict) or not isinstance(settings.get("hooks"), dict):
            raise ValueError("invalid settings")
    except (OSError, ValueError):
        return {"status": "error", "errors": [*errors, "Claude settings missing or invalid"]}
    seen: set[str] = set()
    for event, identities in _EVENT.items():
        groups = settings["hooks"].get(event, [])
        for group in groups if isinstance(groups, list) else []:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            for hook in group["hooks"]:
                identity = _identity(hook, event)
                if identity is None:
                    continue  # Unowned third-party hook is never executed or assessed.
                seen.add(identity)
                label = f"{event}/{identity}"
                if hook.get("type") != "exec":
                    errors.append(f"{label}: relative or legacy managed entry")
                    continue
                command = Path(hook["command"])
                args = hook["args"]
                try:
                    _guard(command)
                    command_safe = True
                except (OSError, ValueError):
                    command_safe = False
                if not command_safe or not command.is_absolute() or not command.is_file() or not os.access(command, os.X_OK) or command != python:
                    errors.append(f"{label}: Python executable missing or not current")
                try:
                    _guard(Path(args[0]))
                    launcher_safe = True
                except (OSError, ValueError):
                    launcher_safe = False
                if not launcher_safe or Path(args[0]) != launcher or not Path(args[0]).is_absolute() or not Path(args[0]).is_file():
                    errors.append(f"{label}: managed launcher missing or incorrect")
                target = root / ".sybermem" / "hooks" / TARGETS[identity]
                try:
                    _guard(target)
                    target_safe = True
                except (OSError, ValueError):
                    target_safe = False
                if not target_safe or not target.is_file() or not os.access(target, os.R_OK):
                    errors.append(f"{label}: target hook missing or unreadable")
                try:
                    host = hook["timeout"]
                    child = int(args[3])
                    if isinstance(host, bool) or not isinstance(host, int) or child != contract.safe_child_timeout(host):
                        raise ValueError("unsafe budget")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{label}: unsafe timeout budget")
    for event, identities in _EVENT.items():
        for identity in identities:
            if identity not in seen:
                errors.append(f"{event}/{identity}: managed hook missing")
    return {"status": "error" if errors else "fresh", "errors": errors}
