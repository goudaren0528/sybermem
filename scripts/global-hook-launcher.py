"""Fail-open Claude managed-hook entry point. Installed as launch_hook.py.

Usage: absolute-python absolute-launch_hook.py HOOK_ID --timeout-seconds N
"""

import json
import os
from pathlib import Path
import stat
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

    class _BASIC_LIMIT(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64), ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD), ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

    class _EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _BASIC_LIMIT), ("IoInfo", _IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    kernel.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel.ResumeThread.argtypes = (wintypes.HANDLE,)
    kernel.ResumeThread.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)

    class _THREAD_ENTRY(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                    ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG), ("dwFlags", wintypes.DWORD)]

    kernel.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Thread32First.argtypes = (wintypes.HANDLE, ctypes.POINTER(_THREAD_ENTRY))
    kernel.Thread32Next.argtypes = (wintypes.HANDLE, ctypes.POINTER(_THREAD_ENTRY))
    kernel.OpenThread.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenThread.restype = wintypes.HANDLE


def _resume(proc):
    snapshot = kernel.CreateToolhelp32Snapshot(0x4, 0)  # TH32CS_SNAPTHREAD
    if snapshot == ctypes.c_void_p(-1).value:
        raise OSError("thread snapshot failed")
    try:
        entry = _THREAD_ENTRY()
        entry.dwSize = ctypes.sizeof(entry)
        found = False
        current = kernel.Thread32First(snapshot, ctypes.byref(entry))
        while current:
            if entry.th32OwnerProcessID == proc.pid:
                thread = kernel.OpenThread(0x0002, False, entry.th32ThreadID)
                if not thread:
                    raise OSError("thread unavailable")
                try:
                    if kernel.ResumeThread(thread) == 0xFFFFFFFF:
                        raise OSError("resume failed")
                    found = True
                finally:
                    kernel.CloseHandle(thread)
            current = kernel.Thread32Next(snapshot, ctypes.byref(entry))
        if not found:
            raise OSError("thread not found")
    finally:
        kernel.CloseHandle(snapshot)


def _job(proc):
    """Assign a suspended process before its first instruction; fail closed."""
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise OSError("job unavailable")
    try:
        limits = _EXTENDED_LIMIT()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise OSError("job configuration failed")
        if not kernel.AssignProcessToJobObject(job, wintypes.HANDLE(proc._handle)):
            raise OSError("job assignment failed")
        return job
    except BaseException:
        kernel.CloseHandle(job)
        raise


HOOKS = {
    "user_prompt": "user_prompt.py",
    "session_start_context": "session_start_context.py",
    "record_change_on_stop": "record_change_on_stop.py",
    "recall_outcome_on_stop": "recall_outcome_on_stop.py",
}
EVENTS = {"user_prompt": "UserPromptSubmit", "session_start_context": "SessionStart"}
MAX_INPUT = 1024 * 1024
MAX_OUTPUT = 1024 * 1024
MAX_LOG = 64 * 1024
DEFAULT_TIMEOUT = 20.0  # host default 30s; reserve 5s for cleanup


def _safe(path):
    """Reject symlinks and Windows junctions/reparse points at every component."""
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except OSError:
            continue  # the final log file may not exist yet
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            return False
    return True


def _within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _git_root(directory):
    """Find the nearest real Git worktree boundary without crossing a nested repo."""
    current = directory.resolve(strict=True)
    for candidate in (current, *current.parents):
        marker = candidate / ".git"
        if not _safe(marker):
            return None
        if marker.is_dir() or marker.is_file():  # .git files identify worktrees
            return candidate
    return None


def _root():
    # An environment root is not authority over the current worktree. In particular,
    # CLAUDE_PROJECT_DIR often names the original tree when cwd is a worktree.
    cwd = Path.cwd().resolve(strict=True)
    root = _git_root(cwd)
    if root is None or not _within(cwd, root) or not _safe(cwd):
        return None
    # Never follow a symlink through the managed runtime path (including .sybermem).
    managed = root / ".sybermem"
    if not _safe(managed) or not managed.is_dir():
        return None
    return root


def _target(root, hook):
    directory = root / ".sybermem" / "hooks"
    target = directory / HOOKS[hook]
    if not _safe(target) or not target.is_file():
        return None
    if not _within(target.resolve(strict=True), root):
        return None
    return target


def _allowed(raw, hook):
    if not raw:
        return True
    try:
        text = raw.decode("utf-8")
        if hook in EVENTS:
            packet = json.loads(text)
            if not isinstance(packet, dict) or set(packet) != {"hookSpecificOutput"}:
                return False
            specific = packet["hookSpecificOutput"]
            return (isinstance(specific, dict)
                    and set(specific) == {"hookEventName", "additionalContext"}
                    and specific["hookEventName"] == EVENTS[hook]
                    and isinstance(specific["additionalContext"], str))
        if hook == "recall_outcome_on_stop":
            return False  # this hook never writes stdout
        # record_change_on_stop emits one existing plain-text reminder line.
        # Never interpret arbitrary JSON/control text as a reminder.
        line = text.rstrip("\r\n")
        fixed = ("You marked this work as worth recording earlier. If this round is complete, run /sybermem-record now.",
                 "SyberMem note: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point.")
        prefixes = ("Recommended next step: /sybermem-record — ",
                    "SyberMem note: this change looks important enough for a manual /sybermem-record so the reason and impact are preserved more clearly.")
        if not line or "\n" in line or "\r" in line or len(line) > 4096:
            return False
        recommendation = line.startswith("Recommended next step: /sybermem-") and " — " in line
        if line not in fixed and not any(line.startswith(prefix) for prefix in prefixes) and not recommendation:
            return False
        # Braces delimit host JSON objects, but brackets, quotes, backslashes
        # and other punctuation can occur in the business-authored reason.
        # They are text here, not a JSON packet or a second output line.
        if any(ch in line for ch in '{}') or not all(ord(ch) >= 32 for ch in line):
            return False
        # The free-form reason/classification may contain user text. Reject host
        # control names, even when disguised as ordinary reminder prose.
        remainder = line.removeprefix("Recommended next step: ").casefold()
        return not any(token in remainder for token in ("decision:", "continue:", "stopreason:", "suppressoutput:"))
    except (UnicodeError, ValueError, TypeError):
        return False


def _log(root, hook, reason, exit_code, duration):
    if root is None:
        return
    try:
        path = root / ".sybermem" / "hook-errors.jsonl"
        if not _safe(path):
            return
        row = {"ts": datetime.now(timezone.utc).isoformat(), "hook": hook,
               "reason": reason, "exit": exit_code, "duration": round(duration, 3)}
        data = (json.dumps(row, separators=(",", ":")) + "\n").encode("utf-8")
        # OS advisory exclusive lock, non-blocking. Keep size check and append
        # inside the same critical section; reject links via O_NOFOLLOW where available.
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags, 0o600)
        try:
            if not _safe(path):
                return
            if os.name == "nt":
                import msvcrt
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                size = os.fstat(fd).st_size
                if size + len(data) <= MAX_LOG:
                    os.lseek(fd, 0, os.SEEK_END)
                    os.write(fd, data)
            finally:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    except OSError:
        pass


def _kill_tree(proc, job=None):
    if os.name == "nt":
        if job:
            kernel.TerminateJobObject(job, 1)
            kernel.CloseHandle(job)
        if proc.poll() is None:
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _run(root, target, data, deadline):
    flags = 0x00000004 if os.name == "nt" else 0  # CREATE_SUSPENDED
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_CEILING_DIRECTORIES", "GIT_PREFIX"):
        env.pop(key, None)
    env["CLAUDE_PROJECT_DIR"] = str(root)
    # Real Stop hooks use print(), not the byte buffer. Pin only the child's
    # stdio encoding so inherited console/locale settings cannot corrupt UTF-8.
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen([sys.executable, str(target)], cwd=root, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=flags, start_new_session=os.name != "nt")
    job = None
    try:
        if os.name == "nt":
            job = _job(proc)
            _resume(proc)
    except BaseException:
        _kill_tree(proc, job)
        raise
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    too_large = threading.Event()

    def drain(name, pipe):
        try:
            while True:
                block = pipe.read(8192)
                if not block:
                    break
                chunks[name].extend(block)
                if len(chunks[name]) > MAX_OUTPUT:
                    too_large.set()
                    break
        except OSError:
            too_large.set()
        finally:
            pipe.close()

    def feed():
        try:
            proc.stdin.write(data)
            proc.stdin.close()
        except OSError:
            pass

    readers = [threading.Thread(target=drain, args=(name, getattr(proc, name)), daemon=True)
               for name in ("stdout", "stderr")]
    for thread in readers:
        thread.start()
    threading.Thread(target=feed, daemon=True).start()
    try:
        while time.monotonic() < deadline:
            if too_large.is_set():
                return "oversize", proc.returncode, b""
            if proc.poll() is not None and all(not thread.is_alive() for thread in readers):
                if proc.returncode != 0:
                    return "exit", proc.returncode, b""
                return "ok", 0, bytes(chunks["stdout"])
            time.sleep(0.01)
        return "timeout", proc.poll(), b""
    finally:
        # Kill the *group* even if its parent exited and descendants inherited pipes.
        _kill_tree(proc, job)
        for thread in readers:
            thread.join(timeout=0.25)


def _input(deadline):
    result = []
    done = threading.Event()

    def read_input():
        try:
            # Raw fd reads do not hold BufferedReader's interpreter-shutdown lock.
            # Wait for EOF, not merely the first short read; bound total bytes.
            data = bytearray()
            while len(data) <= MAX_INPUT:
                block = os.read(sys.stdin.fileno(), min(8192, MAX_INPUT + 1 - len(data)))
                if not block:
                    break
                data.extend(block)
            result.append(bytes(data))
        except OSError:
            pass
        finally:
            done.set()

    threading.Thread(target=read_input, daemon=True).start()
    if not done.wait(max(0, deadline - time.monotonic())):
        return None
    return result[0] if result else None


def main():
    start = time.monotonic()
    root = None
    hook = "unknown"
    exit_code = None
    reason = "error"
    try:
        if len(sys.argv) not in (2, 4) or sys.argv[1] not in HOOKS:
            return 0
        hook = sys.argv[1]
        budget = DEFAULT_TIMEOUT
        if len(sys.argv) == 4:
            if sys.argv[2] != "--timeout-seconds":
                return 0
            budget = float(sys.argv[3])
        # Five seconds are reserved for cleanup; under-sized budgets do no work.
        if not 0 < budget <= 20 or budget < 1:
            return 0
        deadline = start + budget
        root = _root()
        if root is None:
            return 0
        target = _target(root, hook)
        if target is None:
            reason = "missing_target"
            return 0
        data = _input(deadline)
        if data is None:
            reason = "input_timeout"
            return 0
        if len(data) > MAX_INPUT:
            reason = "input_oversize"
            return 0
        if time.monotonic() >= deadline:
            reason = "timeout"
            return 0
        reason, exit_code, output = _run(root, target, data, deadline)
        if reason == "ok" and not _allowed(output, hook):
            reason = "invalid_output"
        if reason == "ok":
            sys.stdout.buffer.write(output)
            return 0
    except Exception:
        reason = "error"
    finally:
        if root is not None and reason != "ok":
            _log(root, hook, reason, exit_code, time.monotonic() - start)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
