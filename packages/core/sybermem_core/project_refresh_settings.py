from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]

MANAGED_MARKERS = {
    "UserPromptSubmit": (
        "user_prompt.py",
        "detect_record_intent.py",
        "task_recall.py",
    ),
    "SessionStart": ("session_start_context.py", "launch_session_start_context.py"),
    "Stop": ("record_change_on_stop.py", "launch_record_change_on_stop.py"),
}


def merge_settings_file(root: Path, template_text: str) -> bool:
    path = root / ".claude" / "settings.json"
    _guard_settings_path(root, path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        template = _operational_template(_load_object(template_text))
        _write_json(path, template)
        return True

    current = _load_object(path.read_text(encoding="utf-8"))
    template = _operational_template(_load_object(template_text))
    merged = _merge_settings(current, template)
    if merged == current:
        return False
    _write_json(path, merged)
    return True


def _load_object(text: str) -> JsonObject:
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError(".claude/settings.json must contain a JSON object")
    return loaded


def _operational_template(template: JsonObject) -> JsonObject:
    adjusted = dict(template)
    hooks = adjusted.get("hooks")
    if isinstance(hooks, dict):
        adjusted_hooks = dict(hooks)
        _rewrite_event_command(
            adjusted_hooks,
            "SessionStart",
            "session_start_context.py",
            "launch_session_start_context.py",
        )
        _rewrite_event_command(
            adjusted_hooks,
            "Stop",
            "record_change_on_stop.py",
            "launch_record_change_on_stop.py",
        )
        adjusted["hooks"] = adjusted_hooks
    return adjusted


def _rewrite_event_command(hooks: JsonObject, event: str, relative_marker: str, launcher_name: str) -> None:
    groups = hooks.get(event)
    if not isinstance(groups, list):
        return
    launcher = (Path.home() / ".claude" / "sybermem" / launcher_name).as_posix()
    hooks[event] = [_rewrite_group_command(group, relative_marker, f'python "{launcher}"') for group in groups]


def _rewrite_group_command(group: JsonValue, marker: str, command: str) -> JsonValue:
    if not isinstance(group, dict):
        return group
    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return group
    rewritten = dict(group)
    rewritten["hooks"] = [_rewrite_hook_command(hook, marker, command) for hook in hooks]
    return rewritten


def _rewrite_hook_command(hook: JsonValue, marker: str, command: str) -> JsonValue:
    if not isinstance(hook, dict):
        return hook
    existing = hook.get("command")
    if not isinstance(existing, str) or marker not in existing:
        return hook
    rewritten = dict(hook)
    rewritten["command"] = command
    return rewritten


def _merge_settings(current: JsonObject, template: JsonObject) -> JsonObject:
    merged = dict(current)
    _merge_env(merged, template)
    _merge_hooks(merged, template)
    return merged


def _merge_env(merged: JsonObject, template: JsonObject) -> None:
    template_env = template.get("env")
    if not isinstance(template_env, dict):
        return
    current_env = merged.get("env")
    if not isinstance(current_env, dict):
        current_env = {}
    env = dict(current_env)
    record_mode = template_env.get("SYBERMEM_RECORD_MODE")
    if isinstance(record_mode, str):
        env["SYBERMEM_RECORD_MODE"] = record_mode
    merged["env"] = env


def _merge_hooks(merged: JsonObject, template: JsonObject) -> None:
    template_hooks = template.get("hooks")
    if not isinstance(template_hooks, dict):
        return
    current_hooks = merged.get("hooks")
    if not isinstance(current_hooks, dict):
        current_hooks = {}
    hooks = dict(current_hooks)
    for event in ("SessionStart", "Stop", "UserPromptSubmit"):
        template_groups = template_hooks.get(event)
        if isinstance(template_groups, list):
            hooks[event] = _merge_event_groups(hooks.get(event), template_groups, event)
    merged["hooks"] = hooks


def _merge_event_groups(current_value: JsonValue, template_groups: list[JsonValue], event: str) -> list[JsonValue]:
    current_groups = current_value if isinstance(current_value, list) else []
    custom_groups = [group for group in current_groups if not _is_managed_group(group, event)]
    return [*custom_groups, *template_groups]


def _is_managed_group(group: JsonValue, event: str) -> bool:
    markers = MANAGED_MARKERS[event]
    return any(marker in command for command in _group_commands(group) for marker in markers)


def _group_commands(group: JsonValue) -> list[str]:
    if not isinstance(group, dict):
        return []
    hooks = group.get("hooks")
    if not isinstance(hooks, list):
        return []
    commands: list[str] = []
    for hook in hooks:
        if isinstance(hook, dict):
            command = hook.get("command")
            if isinstance(command, str):
                commands.append(command)
    return commands


def _guard_settings_path(root: Path, path: Path) -> None:
    current = root
    for part in Path(".claude/settings.json").parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"managed path parent is a symlink: {current}")
    if path.exists() and path.is_symlink():
        raise ValueError(f"managed path is a symlink: {path}")


def _write_json(path: Path, payload: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        tmp_path = Path(handle.name)
    os.replace(tmp_path, path)
