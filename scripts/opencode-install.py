"""Transactional, user-scoped OpenCode plugin deployment (no host restart)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from uuid import uuid4


def _safe(path: Path) -> None:
    import stat
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise RuntimeError(f"refusing linked managed path: {part}")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _version(override: str | None) -> str | None:
    if override:
        if override not in {"1", "2"}:
            raise ValueError("--opencode-major must be 1 or 2")
        return override
    try:
        result = subprocess.run(["opencode", "--version"], capture_output=True, text=True, timeout=8, check=True)
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"(?<![\d.])(\d+)\.\d+\.\d+(?!\d)", result.stdout + result.stderr)
    if match and match.group(1) not in {"1", "2"}: return None
    return match.group(1) if match else None


def _mask_jsonc(text: str) -> str:
    """Replace comments with spaces while retaining string literals and offsets."""
    out = list(text)
    i = 0
    while i < len(text):
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == "\\": i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else: i += 1
            continue
        if text[i:i+2] in {"//", "/*"}:
            start, kind = i, text[i:i+2]
            end = text.find("\n", i) if kind == "//" else text.find("*/", i + 2)
            if end < 0 and kind == "/*": raise ValueError("unterminated JSONC comment")
            end = len(text) if end < 0 else end + (2 if kind == "/*" else 0)
            for j in range(start, end):
                if out[j] not in "\r\n": out[j] = " "
            i = end
        else: i += 1
    return "".join(out)


def _strip_trailing_commas(text: str) -> str:
    chars = list(text)
    i = 0
    while i < len(chars):
        if chars[i] == '"':
            _, i = json.JSONDecoder().raw_decode(text, i)
            continue
        if chars[i] == ",":
            j = i + 1
            while j < len(chars) and chars[j].isspace(): j += 1
            if j < len(chars) and chars[j] in "}]": chars[i] = " "
        i += 1
    return "".join(chars)


def _validated_config(text: str) -> dict:
    try:
        value = json.loads(_strip_trailing_commas(_mask_jsonc(text)))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("OpenCode JSONC config is invalid") from exc
    if not isinstance(value, dict): raise ValueError("OpenCode config must be an object")
    return value


def _array_comments(text: str, mask: str, start: int, end: int) -> list[str]:
    """Collect only real comments, never comment markers within JSON strings."""
    comments = []
    i = start + 1
    while i < end - 1:
        if text[i:i + 2] in {"//", "/*"} and mask[i:i + 2] == "  ":
            line = text[i:i + 2] == "//"
            finish = text.find("\n", i) if line else text.find("*/", i + 2)
            if finish < 0: finish = end - 1
            elif not line: finish += 2
            comments.append(text[i:finish])
            i = finish
        else: i += 1
    return comments


def _config(text: str, remove: set[str], add: str | None) -> str:
    mask = _mask_jsonc(text)
    # Edit only the two top-level plugin keys; masked comments retain their offsets.
    decoder = json.JSONDecoder()
    try:
        value = json.loads(_strip_trailing_commas(mask))
    except json.JSONDecodeError as exc:
        raise ValueError("OpenCode JSONC config is invalid") from exc
    if not isinstance(value, dict): raise ValueError("OpenCode config must be an object")
    depth = 0
    hits: dict[str, tuple[int, int, int, int, list[str]]] = {}
    i = 0
    while i < len(mask):
        char = mask[i]
        if char == '"':
            key, end = decoder.raw_decode(mask, i)
            after = end
            while after < len(mask) and mask[after].isspace(): after += 1
            if depth == 1 and key in {"plugin", "plugins"} and after < len(mask) and mask[after] == ":":
                start = after + 1
                while start < len(mask) and mask[start].isspace(): start += 1
                if start >= len(mask) or mask[start] != "[": raise ValueError("OpenCode plugins field must be an array")
                level, cursor = 0, start
                while cursor < len(mask):
                    if mask[cursor] == '"':
                        _, cursor = decoder.raw_decode(mask, cursor)
                        continue
                    if mask[cursor] == "[": level += 1
                    if mask[cursor] == "]":
                        level -= 1
                        if level == 0: break
                    cursor += 1
                if level: raise ValueError("unterminated plugins array")
                raw = _strip_trailing_commas(mask[start:cursor + 1])
                items = json.loads(raw)
                if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
                    raise ValueError("OpenCode plugins entries must be strings")
                if key in hits: raise ValueError("duplicate plugins config keys")
                hits[key] = (i, end, start, cursor + 1, items)
                i = cursor + 1
                continue
            i = end
            continue
        if char in "{[": depth += 1
        if char in "}]": depth -= 1
        i += 1
    edits: list[tuple[int, int, str]] = []
    legacy = hits.get("plugin")
    current = hits.get("plugins")
    if legacy and not current:
        edits.append((legacy[0], legacy[1], '"plugins"'))
        current = legacy
    elif legacy:
        # Remove the old key, not its third-party entries: merge those into plugins.
        left, right = legacy[0], legacy[3]
        cursor = right
        while cursor < len(mask) and mask[cursor].isspace(): cursor += 1
        if cursor < len(mask) and mask[cursor] == ",": right = cursor + 1
        else:
            cursor = left - 1
            while cursor >= 0 and mask[cursor].isspace(): cursor -= 1
            if cursor >= 0 and mask[cursor] == ",": left = cursor
        edits.append((left, right, ""))
    if current:
        _, _, start, end, items = current
        merged = [item for item in items if item not in remove]
        if legacy and legacy != current:
            merged.extend(item for item in legacy[4] if item not in remove and item not in merged)
        if add and add not in merged: merged.append(add)
        if merged != items or legacy and legacy != current and _array_comments(text, mask, legacy[2], legacy[3]):
            # Rebuild this array atomically: deleting adjacent tokens and inserting
            # at a nearby offset must never produce overlapping edits.
            comments = _array_comments(text, mask, start, end)
            if legacy and legacy != current:
                comments += _array_comments(text, mask, legacy[2], legacy[3])
            body = "\n".join(comments) + ("\n" if comments else "")
            body += ", ".join(json.dumps(item, ensure_ascii=False) for item in merged)
            edits.append((start, end, "[" + body + "]"))
        for begin, finish, replacement in sorted(edits, reverse=True):
            text = text[:begin] + replacement + text[finish:]
        return text
    if not add: return text
    closing = mask.rfind("}")
    if closing < 0: raise ValueError("missing closing config brace")
    prefix = mask[:closing].rstrip()
    comma = "" if prefix.endswith("{") or prefix.endswith(",") else ","
    return text[:closing] + comma + '\n  "plugins": ' + json.dumps([add]) + '\n' + text[closing:]


def _write(path: Path, data: bytes) -> None:
    _safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _paths(home: Path) -> tuple[Path, Path, Path, Path]:
    base = home / ".config" / "opencode"
    return base, base / "plugins" / "sybermem.ts", base / "sybermem-v2", base / "sybermem-install.json"


def _selected_config(base: Path) -> Path:
    candidates = [base / "opencode.jsonc", base / "opencode.json"]
    existing = [path for path in candidates if path.exists()]
    if len(existing) > 1: raise RuntimeError("multiple OpenCode config files: select one manually")
    return existing[0] if existing else candidates[1]


def install(root: Path, home: Path, override: str | None = None) -> str:
    major = _version(override)
    if major is None:
        print("  [OpenCode] install: skipped (unknown host major; pass --opencode-major 1|2); load: unverified; function: unverified")
        return "skipped"
    base, legacy, package, state_path = _paths(home)
    _safe(base)
    source = root / "packages" / "opencode-plugin"
    files = {"1": [source / "sybermem-v1.ts"], "2": [source / "dist-v2" / name for name in ("package.json", "server.js", "tui.js")]}
    if not all(p.is_file() and p.stat().st_size for p in files[major]):
        raise RuntimeError(f"missing OpenCode V{major} distribution; build bundles before installing")
    for p in files[major]: _safe(p)
    if major == "2":
        expected = json.loads(files[major][0].read_text(encoding="utf-8"))
        if expected.get("exports", {}).get("./tui") != "./tui.js" or expected.get("exports", {}).get("./server") != "./server.js":
            raise RuntimeError("V2 package exports incomplete")
    config = _selected_config(base)
    targets = [legacy, package / "package.json", package / "server.js", package / "tui.js", state_path, config]
    for path in targets: _safe(path)
    for path in (legacy, state_path, config, *(package / name for name in ("package.json", "server.js", "tui.js"))):
        if path.exists() and not path.is_file(): raise RuntimeError(f"OpenCode target is not a regular file: {path}")
    if package.exists() and not package.is_dir(): raise RuntimeError("V2 target is not a directory")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    if state and (state.get("schema") != 1 or state.get("major") not in {"1", "2"}): raise RuntimeError("unknown managed OpenCode state")
    managed = state.get("hashes", {})
    if not isinstance(managed, dict) or not set(managed).issubset({"plugins/sybermem.ts", "sybermem-v2/package.json", "sybermem-v2/server.js", "sybermem-v2/tui.js"}):
        raise RuntimeError("invalid managed OpenCode paths")
    if state and (state["major"] == "2" and set(managed) != {"sybermem-v2/package.json", "sybermem-v2/server.js", "sybermem-v2/tui.js"} or state["major"] == "1" and set(managed) != {"plugins/sybermem.ts"}):
        raise RuntimeError("incomplete managed OpenCode state")
    for path in (legacy, *[package / name for name in ("package.json", "server.js", "tui.js")]):
        if path.exists() and path.is_file():
            digest = _digest(path.read_bytes())
            if str(path.relative_to(base)).replace("\\", "/") in managed:
                if managed[str(path.relative_to(base)).replace("\\", "/")] != digest: raise RuntimeError(f"managed OpenCode file modified: {path}")
            elif path == legacy and "SyberMem OpenCode Plugin (generated bundle)" in path.read_text(encoding="utf-8", errors="replace")[:400]:
                pass  # Legacy generated SyberMem bundle, migrated out of the scan directory.
            else: raise RuntimeError(f"unmanaged OpenCode target already exists: {path}")
    original = {path: path.read_bytes() if path.is_file() else None for path in targets}
    for path, content in original.items():
        if content is not None and _digest(path.read_bytes()) != _digest(content):
            raise RuntimeError(f"OpenCode backup hash mismatch: {path}")
    old_bytes = original[config]
    old = old_bytes.decode("utf-8-sig") if old_bytes is not None else "{}\n"
    bom = b"\xef\xbb\xbf" if old_bytes is not None and old_bytes.startswith(b"\xef\xbb\xbf") else b""
    v2_entry = str(package.absolute())
    # Only remove known managed entries and the old scanned legacy path.
    remove = {v2_entry, v2_entry.replace("\\", "/")} if state.get("major") == "2" and major == "1" else set()
    if state.get("major") == "1" or legacy.is_file() and "SyberMem OpenCode Plugin (generated bundle)" in legacy.read_text(encoding="utf-8", errors="replace")[:400]:
        remove.update({str(legacy.absolute()), str(legacy.absolute()).replace("\\", "/")})
    if major == "2" and not state:
        parsed = json.loads(_strip_trailing_commas(_mask_jsonc(old)))
        if not isinstance(parsed, dict): raise ValueError("OpenCode config must be an object")
        entries = [entry for key in ("plugin", "plugins") for entry in (parsed.get(key) if isinstance(parsed.get(key), list) else [])]
        if v2_entry in entries or v2_entry.replace("\\", "/") in entries:
            raise RuntimeError("unmanaged OpenCode V2 plugin config entry already exists")
    next_text = _config(old, remove, v2_entry if major == "2" else None) if (major == "2" or state.get("major") == "2") else old
    _validated_config(next_text)
    if major == "1" and not state and config.exists():
        mask = _mask_jsonc(old)
        try:
            value = json.loads(_strip_trailing_commas(mask))
        except json.JSONDecodeError as exc:
            raise ValueError("OpenCode JSONC config is invalid") from exc
        if not isinstance(value, dict): raise ValueError("OpenCode config must be an object")
    hashes: dict[str, str] = {}
    written: dict[Path, bytes] = {}
    try:
        if major == "2":
            for src in files[major]:
                dst = package / src.name
                data = src.read_bytes()
                if original[dst] != data:
                    _write(dst, data)
                    written[dst] = data
                hashes[str(dst.relative_to(base)).replace("\\", "/")] = _digest(data)
            if legacy.exists(): legacy.unlink()
        else:
            data = files[major][0].read_bytes()
            if original[legacy] != data:
                _write(legacy, data)
                written[legacy] = data
            hashes["plugins/sybermem.ts"] = _digest(data)
            for name in ("package.json", "server.js", "tui.js"):
                path = package / name
                if path.exists(): path.unlink()
        if next_text != old:
            updated_config = bom + next_text.encode("utf-8")
            _write(config, updated_config)
            written[config] = updated_config
        next_state = json.dumps({"schema": 1, "major": major, "hashes": hashes}, indent=2).encode() + b"\n"
        if original[state_path] != next_state:
            _write(state_path, next_state)
            written[state_path] = next_state
    except Exception:
        failures = []
        for path in reversed(targets):
            try:
                _safe(path)
                if original[path] is None:
                    if path.is_file():
                        if path not in written or path.read_bytes() != written[path]:
                            raise RuntimeError(f"concurrent change during rollback: {path}")
                        path.unlink()
                elif not path.exists(): _write(path, original[path])
                elif path.read_bytes() != original[path]:
                    # Do not overwrite a concurrently changed managed file.
                    if path in written and path.read_bytes() == written[path]: _write(path, original[path])
                    else: raise RuntimeError(f"concurrent change during rollback: {path}")
            except Exception as rollback_error:
                failures.append(f"{path}: {rollback_error}")
        if failures:
            raise RuntimeError("OpenCode rollback incomplete; manual recovery required: " + "; ".join(failures))
        raise
    print(f"  [OpenCode] install: V{major} deployed; load: unverified (restart/reload manually); function: unverified")
    return major


def uninstall(home: Path) -> None:
    base, legacy, package, state_path = _paths(home)
    _safe(base)
    _safe(state_path)
    _safe(legacy)
    _safe(package)
    if not state_path.exists():
        # Legacy manifest users may still have the original generated bundle.
        _safe(legacy)
        if legacy.is_file() and "SyberMem OpenCode Plugin (generated bundle)" in legacy.read_text(encoding="utf-8", errors="replace")[:400]:
            legacy.unlink()
        return
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("schema") != 1 or state.get("major") not in {"1", "2"}: raise RuntimeError("unknown managed OpenCode state")
    allowed = {"plugins/sybermem.ts", "sybermem-v2/package.json", "sybermem-v2/server.js", "sybermem-v2/tui.js"}
    hashes = state.get("hashes", {})
    if not isinstance(hashes, dict) or not set(hashes).issubset(allowed): raise RuntimeError("invalid managed OpenCode paths")
    if state["major"] == "2" and set(hashes) != {"sybermem-v2/package.json", "sybermem-v2/server.js", "sybermem-v2/tui.js"} or state["major"] == "1" and set(hashes) != {"plugins/sybermem.ts"}:
        raise RuntimeError("incomplete managed OpenCode state")
    targets = [base / item for item in hashes]
    for path in targets:
        _safe(path)
        if path.exists() and _digest(path.read_bytes()) != hashes[str(path.relative_to(base)).replace("\\", "/")]:
            raise RuntimeError(f"managed OpenCode file modified: {path}")
    config = _selected_config(base)
    _safe(config)
    old_config = config.read_bytes() if config.exists() else None
    existing = {path: path.read_bytes() if path.exists() else None for path in targets}
    try:
        if config.exists():
            raw = config.read_bytes()
            old = raw.decode("utf-8-sig")
            entry = str(package.absolute())
            new = _config(old, {entry, entry.replace("\\", "/")}, None)
            _validated_config(new)
            if new != old: _write(config, (b"\xef\xbb\xbf" if raw.startswith(b"\xef\xbb\xbf") else b"") + new.encode("utf-8"))
        for path in targets:
            if path.exists(): path.unlink()
        if package.exists():
            try: package.rmdir()
            except OSError: pass  # Preserve unrelated user files.
        state_path.unlink()
    except Exception:
        for path, content in existing.items():
            if content is not None and not path.exists(): _write(path, content)
        if old_config is not None and (not config.exists() or config.read_bytes() != old_config): _write(config, old_config)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--opencode-major", choices=("1", "2"), default=os.environ.get("SYBERMEM_OPENCODE_MAJOR"))
    args = parser.parse_args()
    if args.action == "install":
        if not args.root: parser.error("install requires --root")
        install(args.root, args.home, args.opencode_major)
    else: uninstall(args.home)
    return 0


if __name__ == "__main__":
    sys.exit(main())
