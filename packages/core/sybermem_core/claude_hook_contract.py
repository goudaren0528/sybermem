"""Shared Claude Code hook deployment and host compatibility contract."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

MIN_EXEC_VERSION = (2, 1, 139)  # Claude Code release introducing exec command + args.
VERSION_TIMEOUT_SECONDS = 3
VERSION_OUTPUT_LIMIT = 8192
HOST_TIMEOUT_SECONDS = 30
CHILD_TIMEOUT_SECONDS = 20
CLEANUP_MARGIN_SECONDS = 5
HOOK_IDS = ("user_prompt", "session_start_context", "record_change_on_stop", "recall_outcome_on_stop")
LAUNCHER_PATH = Path.home() / ".claude" / "sybermem" / "launch_hook.py"


def probe_claude_version(
    executable: str = "claude",
    runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
) -> tuple[int, ...] | None:
    """Return only an unambiguous stable integer version from a bounded probe."""
    try:
        if runner is None:
            # Redirect to disk so even a malicious --version cannot fill process memory.
            with tempfile.TemporaryFile() as output_file:
                result = subprocess.run([executable, "--version"], timeout=VERSION_TIMEOUT_SECONDS,
                                        stdout=output_file, stderr=subprocess.DEVNULL, check=False)
                output_file.seek(0)
                output = output_file.read(VERSION_OUTPUT_LIMIT + 1)
        else:
            result = runner([executable, "--version"], timeout=VERSION_TIMEOUT_SECONDS,
                            capture_output=True, check=False)
            output = result.stdout
        if result.returncode != 0 or not isinstance(output, bytes) or len(output) > VERSION_OUTPUT_LIMIT:
            return None
        match = re.fullmatch(rb"(?:Claude Code\s+)?v?(\d+)\.(\d+)\.(\d+)(?:\s+\(Claude Code\))?\s*", output)
        return tuple(int(part) for part in match.groups()) if match else None
    except (OSError, subprocess.SubprocessError):
        return None


def supports_exec(version: tuple[int, ...] | None) -> bool:
    return version is not None and len(version) == 3 and version >= MIN_EXEC_VERSION


def safe_child_timeout(host_timeout: int = HOST_TIMEOUT_SECONDS) -> int:
    if isinstance(host_timeout, bool) or not isinstance(host_timeout, int) or host_timeout <= CLEANUP_MARGIN_SECONDS + 1:
        raise ValueError("unsafe Claude hook timeout budget")
    return min(CHILD_TIMEOUT_SECONDS, host_timeout - CLEANUP_MARGIN_SECONDS)


def executable_python() -> Path:
    # Only the interpreter of this process may be normalized.  Unix Python
    # installations routinely expose it through /usr/local/bin/python -> python3;
    # managed settings must record the real executable, not that link.
    try:
        path = Path(sys.executable).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("Python executable unavailable") from exc
    if not path.is_absolute() or not path.is_file():
        raise ValueError("Python executable unavailable")
    return path
