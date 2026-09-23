"""Surgical and fail-safe migration of Claude Code project settings."""

from __future__ import annotations

import json
import os
import re
import shlex
import stat
import tempfile
from pathlib import Path

from . import claude_hook_contract as contract

JsonObject = dict[str, object]

_SCRIPTS = {
    "user_prompt.py": "user_prompt",
    "detect_record_intent.py": "user_prompt",
    "task_recall.py": "user_prompt",
    "launch_user_prompt.py": "user_prompt",
    "session_start_context.py": "session_start_context",
    "launch_session_start_context.py": "session_start_context",
    "record_change_on_stop.py": "record_change_on_stop",
    "launch_record_change_on_stop.py": "record_change_on_stop",
    "recall_outcome_on_stop.py": "recall_outcome_on_stop",
    "launch_recall_outcome_on_stop.py": "recall_outcome_on_stop",
}
_EVENT = {"UserPromptSubmit": ("user_prompt",), "SessionStart": ("session_start_context",),
          "Stop": ("record_change_on_stop", "recall_outcome_on_stop")}


def _identity(hook: object, event: str) -> str | None:
    if not isinstance(hook, dict):
        return None
    command = hook.get("command")
    if not isinstance(command, str):
        return None
    if hook.get("type") == "exec":
        args = hook.get("args")
        if not isinstance(args, list) or len(args) != 4 or not all(isinstance(a, str) for a in args):
            return None
        if Path(args[0]).name != "launch_hook.py" or args[2] != "--timeout-seconds":
            return None
        if Path(args[0]).parent.as_posix().replace("\\", "/").lower() != contract.LAUNCHER_PATH.parent.as_posix().lower():
            return None
        return args[1] if args[1] in _EVENT[event] else None
    if hook.get("type") not in ("command", "sybermem-template"):
        return None
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return None
    if len(tokens) != 2 or not re.fullmatch(r"(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?", Path(tokens[0]).name, re.I):
        return None
    path = tokens[1].replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    identity = _SCRIPTS.get(name)
    if identity not in _EVENT[event]:
        return None
    if name.startswith("launch_"):
        # Only claim the established global SyberMem launcher directory.
        return identity if Path(path).parent.as_posix().lower() == contract.LAUNCHER_PATH.parent.as_posix().lower() else None
    return identity if path == f".sybermem/hooks/{name}" else None


def _strip_placeholders(settings: JsonObject) -> JsonObject:
    """Placeholders are install-only instructions; none may be active hooks."""
    result = dict(settings)
    events = settings.get("hooks")
    if not isinstance(events, dict):
        return result
    result_events = dict(events)
    for event, groups in events.items():
        if not isinstance(groups, list):
            continue
        filtered = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                filtered.append(group)
                continue
            entries = [hook for hook in group["hooks"]
                       if not (isinstance(hook, dict) and hook.get("type") == "sybermem-template")]
            if entries:
                filtered.append({**group, "hooks": entries})
        result_events[event] = filtered
    result["hooks"] = result_events
    return result


def _all_managed(settings: JsonObject) -> bool:
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return False
    return any(_identity(hook, event) for event in _EVENT
               for group in (hooks.get(event) if isinstance(hooks.get(event), list) else [])
               if isinstance(group, dict) and isinstance(group.get("hooks"), list)
               for hook in group["hooks"])


def _merge(current: JsonObject, template: JsonObject, enabled: bool, python: Path | None = None,
           launcher: Path | None = None) -> JsonObject:
    result = dict(current)
    if enabled and isinstance(template.get("env"), dict):
        env = dict(current.get("env", {})) if isinstance(current.get("env"), dict) else {}
        for key, value in template["env"].items():
            env.setdefault(key, value)
        result["env"] = env
    hooks = dict(current.get("hooks", {})) if isinstance(current.get("hooks"), dict) else {}
    template_hooks = template.get("hooks", {})
    if not isinstance(template_hooks, dict):
        template_hooks = {}
    for event, ids in _EVENT.items():
        existing = hooks.get(event, [])
        groups = existing if isinstance(existing, list) else []
        defaults = template_hooks.get(event, [])
        defaults = defaults if isinstance(defaults, list) else []
        result_groups: list[object] = []
        found: set[tuple[str, str]] = set()
        existing_identities: set[str] = set()
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                result_groups.append(group)
                continue
            output = []
            matcher = json.dumps(group.get("matcher"), sort_keys=True)
            for hook in group["hooks"]:
                identity = _identity(hook, event)
                if not identity:
                    output.append(hook)
                else:
                    existing_identities.add(identity)
                    if enabled and (identity, matcher) not in found:
                        output.append(_enabled_hook(hook, identity, python, launcher))
                        found.add((identity, matcher))
            if output:
                result_groups.append({**group, "hooks": output})
        if enabled:
            for group in defaults:
                if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                    continue
                matcher = json.dumps(group.get("matcher"), sort_keys=True)
                for hook in group["hooks"]:
                    identity = _identity(hook, event)
                    # A template matcher is only a default for identities absent
                    # altogether; never broaden an existing user matcher scope.
                    if identity and identity not in existing_identities and (identity, matcher) not in found:
                        result_groups.append({**group, "hooks": [_enabled_hook(hook, identity, python, launcher)]})
                        found.add((identity, matcher))
        if result_groups != existing:
            hooks[event] = result_groups
    if hooks != current.get("hooks"):
        result["hooks"] = hooks
    return result


def _enabled_hook(hook: dict, identity: str, python: Path | None, launcher: Path | None) -> dict:
    assert python is not None and launcher is not None
    host = hook.get("timeout", contract.HOST_TIMEOUT_SECONDS)
    child = contract.safe_child_timeout(host)
    return {**hook, "type": "exec", "command": str(python),
            "args": [str(launcher), identity, "--timeout-seconds", str(child)], "timeout": host}


def _guard(path: Path) -> None:
    # Inspect lexical ancestors rather than resolving: a junction/reparse point
    # must not redirect settings (or its backup) outside the project.
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("unsafe Claude settings path")
        try:
            attributes = component.lstat().st_file_attributes
        except FileNotFoundError:
            continue
        except AttributeError:
            continue  # Non-Windows stat results have no reparse attributes.
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError("unsafe Claude settings path")


def _atomic(path: Path, content: bytes) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def migrate_settings_file(root: Path, template_text: str, *, version: tuple[int, ...] | None = None,
                          python: Path | None = None, launcher: Path | None = None,
                          dry_run: bool = False) -> str:
    """Return enabled, disabled_requires_upgrade, fresh, or error_unsafe_state."""
    path = root / ".claude" / "settings.json"
    backup = path.with_name(path.name + ".sybermem.bak")
    original: bytes | None = None
    replaced = False
    current: JsonObject = {}
    disabled_failure = False
    try:
        _guard(path)
        _guard(backup)
        template = json.loads(template_text.lstrip("\ufeff"))
        if not isinstance(template, dict):
            raise ValueError("invalid template")
        current = json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}
        if not isinstance(current, dict):
            raise ValueError("invalid settings")
        version = contract.probe_claude_version() if version is None else version
        compatible = contract.supports_exec(version)
        if compatible:
            try:
                python = python or contract.executable_python()
                launcher = launcher or contract.LAUNCHER_PATH
                if not python.is_absolute() or not python.is_file() or not launcher.is_absolute() or not launcher.is_file():
                    raise ValueError("managed launcher or interpreter missing")
            except (OSError, ValueError):
                compatible = False
                disabled_failure = True
        if not compatible and not _all_managed(current):
            # Even placeholder-only cleanup must use the same backup, atomic
            # replacement and post-write verification as a normal migration.
            merged = _strip_placeholders(current)
            unsafe_budget = False
        else:
            unsafe_budget = False
            try:
                merged = _strip_placeholders(_merge(current, template, compatible, python, launcher))
            except ValueError:
                # Disable only identifiable managed hooks rather than retaining dangerous entries.
                merged = _strip_placeholders(_merge(current, template, False))
                unsafe_budget = True
        if merged == current:
            return "error_unsafe_state" if unsafe_budget or disabled_failure else ("fresh" if compatible else "disabled_requires_upgrade")
        if dry_run:
            return "error_unsafe_state" if unsafe_budget or disabled_failure else ("enabled" if compatible else "disabled_requires_upgrade")
        path.parent.mkdir(parents=True, exist_ok=True)
        _guard(path)
        _guard(backup)
        original = path.read_bytes() if path.exists() else None
        if original is not None:
            _guard(path)
            _guard(backup)
            _atomic(backup, original)
        payload = (json.dumps(merged, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _guard(path)
        _guard(backup)
        _atomic(path, payload)
        replaced = True
        if json.loads(path.read_text(encoding="utf-8")) != merged:
            raise ValueError("settings verification failed")
        return "error_unsafe_state" if unsafe_budget or disabled_failure else ("enabled" if compatible else "disabled_requires_upgrade")
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        if replaced:
            try:
                _guard(path)
                _guard(backup)
                # Restore only when the previous state contains no managed hooks;
                # otherwise disable identifiable managed entries, never revive relative commands.
                safe = _strip_placeholders(current if not _all_managed(current) else _merge(current, {}, False))
                _atomic(path, (json.dumps(safe, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            except (OSError, ValueError, TypeError):
                pass
        return "error_unsafe_state"


def merge_settings_file(root: Path, template_text: str) -> bool:
    return migrate_settings_file(root, template_text) == "enabled"
