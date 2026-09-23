"""Isolated subprocess contract tests; no real memory hook runs."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


LAUNCHER = Path(__file__).with_name("global-hook-launcher.py").resolve()
HOOKS = ("user_prompt", "session_start_context", "record_change_on_stop", "recall_outcome_on_stop")


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sybermem 中文 space ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "current tree"
        self.root.mkdir()
        (self.root / ".git").mkdir()
        self.hooks = self.root / ".sybermem" / "hooks"
        self.hooks.mkdir(parents=True)

    def dummy(self, hook="user_prompt", body="print('')"):
        (self.hooks / (hook + ".py")).write_text(body, encoding="utf-8")

    def invoke(self, hook="user_prompt", cwd=None, envroot=None, data=b"{}", timeout="2", env_overrides=None):
        env = dict(os.environ)
        env.pop("CLAUDE_PROJECT_DIR", None)
        if envroot is not None:
            env["CLAUDE_PROJECT_DIR"] = str(envroot)
        for key, value in (env_overrides or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return subprocess.run([sys.executable, str(LAUNCHER), hook, "--timeout-seconds", timeout],
                              cwd=cwd or self.root, env=env, input=data, capture_output=True, timeout=9)

    def test_unicode_stop_print_with_non_utf8_parent(self):
        # The actual hook prints an em dash; cp1252 encodes it as 0x97 and
        # cp936 as A1AA, neither of which is valid UTF-8 for this output.
        reminder = "Recommended next step: /sybermem-record — 记忆. Classification: change."
        self.dummy("record_change_on_stop", f"print({reminder!r})")
        for parent_encoding in ("cp1252", "cp936", None):
            with self.subTest(parent_encoding=parent_encoding):
                result = self.invoke("record_change_on_stop", env_overrides={
                    "PYTHONIOENCODING": parent_encoding, "PYTHONUTF8": "0",
                })
                self.assertEqual((result.returncode, result.stderr), (0, b""))
                self.assertEqual(result.stdout.decode("utf-8").strip(), reminder)

    def test_unicode_prompt_and_session_print_with_non_utf8_parent(self):
        for hook, event in (("user_prompt", "UserPromptSubmit"),
                            ("session_start_context", "SessionStart")):
            context = "中文记忆 — ⭐"
            self.dummy(hook, "import json; print(json.dumps({" +
                       f"'hookSpecificOutput': {{'hookEventName': {event!r}, 'additionalContext': {context!r}}}" +
                       "}, ensure_ascii=False))")
            for parent_encoding in ("cp1252", "cp936", None):
                with self.subTest(hook=hook, parent_encoding=parent_encoding):
                    result = self.invoke(hook, env_overrides={
                        "PYTHONIOENCODING": parent_encoding, "PYTHONUTF8": "0",
                    })
                    self.assertEqual((result.returncode, result.stderr), (0, b""))
                    self.assertEqual(json.loads(result.stdout.decode("utf-8")), {
                        "hookSpecificOutput": {"hookEventName": event, "additionalContext": context},
                    })

    def test_root_subdir_unicode_space_and_python3_only(self):
        packet = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "记忆 ⭐"}}
        expected = (json.dumps(packet, ensure_ascii=False) + "\n").encode()
        self.dummy(body=f"import sys; sys.stdout.buffer.write({expected!r})")
        sub = self.root / "backend"
        sub.mkdir()
        for cwd in (self.root, sub):
            result = self.invoke(cwd=cwd)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, expected, b""))

    def test_session_and_stop_formats(self):
        packet = '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"startup"}}\n'
        self.dummy("session_start_context", f"import sys; sys.stdout.buffer.write({packet.encode()!r})")
        self.assertEqual(self.invoke("session_start_context").stdout, packet.encode())
        reminder = "Recommended next step: /sybermem-record — worthwhile. Classification: change.\n"
        self.dummy("record_change_on_stop", f"import sys; sys.stdout.buffer.write({reminder.encode()!r})")
        self.assertIn(b"Recommended next step", self.invoke("record_change_on_stop").stdout)
        self.dummy("record_change_on_stop", "print('SyberMem note: recent records around this area may now be enough for a /sybermem-digest if this phase has reached a stable stopping point.')")
        self.assertIn(b"SyberMem note", self.invoke("record_change_on_stop").stdout)
        self.dummy("recall_outcome_on_stop", "pass")
        self.assertEqual(self.invoke("recall_outcome_on_stop").stdout, b"")

    def test_missing_target_exit_and_block_controls(self):
        self.assertEqual(self.invoke().stdout, b"")
        cases = ["print('partial'); raise SystemExit(2)",
                 "raise RuntimeError('private')",
                 "print('{\"decision\":\"block\"}')",
                 "print('{\"continue\":false}')",
                 "print('{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":\"ok\"},\"suppressOutput\":true}')"]
        for code in cases:
            with self.subTest(code=code):
                self.dummy(body=code)
                result = self.invoke()
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_timeout_oversize_stderr_and_small_budget(self):
        self.dummy(body="import time; time.sleep(10)")
        self.assertEqual(self.invoke(timeout="1").stdout, b"")
        self.assertEqual(self.invoke(timeout="0.1").stdout, b"")
        self.dummy(body="import sys; sys.stderr.write('private' * 200000); print('ok')")
        self.assertEqual(self.invoke().stdout, b"")
        self.dummy(body="print('x' * 1100000)")
        self.assertEqual(self.invoke().stdout, b"")
        self.dummy(body="print('ok')")
        self.assertEqual(self.invoke(data=b"x" * (1024 * 1024 + 1)).stdout, b"")

    def test_unknown_hook_does_not_run_script_and_log_is_redacted(self):
        marker = self.root / "called"
        self.dummy(body=f"from pathlib import Path; Path({str(marker)!r}).write_text('called')")
        self.assertEqual(self.invoke(hook="../../user_prompt").returncode, 0)
        self.assertFalse(marker.exists())
        self.dummy(body="import sys; sys.stderr.write('private'); raise SystemExit(2)")
        self.assertEqual(self.invoke(data=b"secret-prompt").stdout, b"")
        rows = (self.root / ".sybermem" / "hook-errors.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(set(json.loads(rows[0])), {"ts", "hook", "reason", "exit", "duration"})
        self.assertNotIn("private", rows[0])
        self.assertNotIn("secret-prompt", rows[0])

    def test_timeout_cleans_descendants(self):
        marker = self.root / "leak"
        body = ("import subprocess,sys,time\n"
                f"subprocess.Popen([sys.executable, '-c', {('import time; from pathlib import Path; time.sleep(3); Path('+repr(str(marker))+').write_text(\'leak\')')!r}])\n"
                "time.sleep(10)\n")
        self.dummy(body=body)
        self.assertEqual(self.invoke(timeout="1").stdout, b"")
        # The child would write its marker after three seconds if tree cleanup failed.
        time.sleep(3.2)
        self.assertFalse(marker.exists())

    def test_parent_exits_but_descendant_keeps_pipe(self):
        marker = self.root / "orphan"
        descendant = f"import time; from pathlib import Path; time.sleep(3); Path({str(marker)!r}).write_text('escaped')"
        self.dummy(body=f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{descendant!r}])")
        result = self.invoke(timeout="1")
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        time.sleep(3.2)
        self.assertFalse(marker.exists())

    def test_successful_parent_descendant_is_still_cleaned(self):
        marker = self.root / "success-descendant"
        descendant = f"import time; from pathlib import Path; time.sleep(2); Path({str(marker)!r}).write_text('escaped')"
        packet = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "valid"}}
        body = f"import subprocess,sys; subprocess.Popen([sys.executable,'-c',{descendant!r}], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); print({json.dumps(packet)!r})"
        self.dummy(body=body)
        self.assertIn(b"valid", self.invoke().stdout)
        time.sleep(2.2)
        self.assertFalse(marker.exists())

    def test_concurrent_log_near_limit(self):
        log = self.root / ".sybermem" / "hook-errors.jsonl"
        log.write_bytes(b" " * (64 * 1024 - 400))
        launch = [sys.executable, str(LAUNCHER), "user_prompt", "--timeout-seconds", "2"]
        processes = [subprocess.Popen(launch, cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for _ in range(8)]
        for proc in processes:
            out, err = proc.communicate(b"{}", timeout=5)
            self.assertEqual((proc.returncode, out, err), (0, b"", b""))
        self.assertLessEqual(log.stat().st_size, 64 * 1024)

    def test_stdin_without_eof_respects_budget(self):
        marker = self.root / "read-input"
        self.dummy(body=f"from pathlib import Path; Path({str(marker)!r}).write_text('bad')")
        proc = subprocess.Popen([sys.executable, str(LAUNCHER), "user_prompt", "--timeout-seconds", "1"],
                                cwd=self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            proc.stdin.write(b"not EOF")
            proc.stdin.flush()
            out, err = proc.stdout.read(), proc.stderr.read()
            self.assertEqual((proc.wait(timeout=1), out, err), (0, b"", b""))
            self.assertFalse(marker.exists())
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.stderr.close()
            if proc.poll() is None:
                proc.kill()

    def test_child_environment_is_worktree_scoped(self):
        self.dummy("record_change_on_stop", "import os; print('Recommended next step: ' + os.environ.get('CLAUDE_PROJECT_DIR', '<missing>'))")
        env = dict(os.environ, GIT_DIR="bad", GIT_WORK_TREE="bad", GIT_COMMON_DIR="bad")
        env["CLAUDE_PROJECT_DIR"] = "original-tree"
        self.dummy("user_prompt", "import json, os; print(json.dumps({'hookSpecificOutput': {'hookEventName':'UserPromptSubmit', 'additionalContext': str((os.environ.get('CLAUDE_PROJECT_DIR'), [os.environ.get(k) for k in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR')]))}}))")
        result = subprocess.run([sys.executable, str(LAUNCHER), "user_prompt", "--timeout-seconds", "2"],
                                cwd=self.root, input=b"{}", env=env, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"], str((str(self.root), [None] * 3)))

    def test_stop_rejects_control_payloads(self):
        for hook in ("record_change_on_stop", "recall_outcome_on_stop"):
            for message in ('{"de\\u0063ision":"block"}', 'Recommended next step: {"continue":false}',
                             'Recommended next step: /sybermem-record — ok.\\n{"decision":"block"}'):
                with self.subTest(hook=hook, message=message):
                    self.dummy(hook, f"print({message!r})")
                    self.assertEqual(self.invoke(hook).stdout, b"")

    def test_stop_print_preserves_punctuation_without_passing_controls(self):
        reason = 'Fix [parser] handling "quoted" C:\\work\\parser\\config.py'
        reminder = f"Recommended next step: /sybermem-record — {reason} Classification: change."
        self.dummy("record_change_on_stop", f"print({reminder!r})")
        result = self.invoke("record_change_on_stop")
        self.assertEqual((result.returncode, result.stderr), (0, b""))
        self.assertIn(result.stdout, ((reminder + "\n").encode("utf-8"),
                                      (reminder + "\r\n").encode("utf-8")))

        for payload in (reminder + '\n{"decision":"block"}',
                        reminder + ' {"continue":false}',
                        reminder + ' decision: block',
                        reminder + '\x00'):
            with self.subTest(payload=payload):
                self.dummy("record_change_on_stop", f"print({payload!r})")
                self.assertEqual(self.invoke("record_change_on_stop").stdout, b"")

    @unittest.skipUnless(os.name == "nt", "Windows junction only")
    def test_junction_blocks_execution_and_external_logging(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (outside / "hooks").mkdir()
        (outside / "hooks" / "user_prompt.py").write_text("print('outside')", encoding="utf-8")
        import shutil
        shutil.rmtree(self.root / ".sybermem")
        subprocess.run(["cmd", "/c", "mklink", "/J", str(self.root / ".sybermem"), str(outside)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        self.assertEqual(self.invoke().stdout, b"")
        self.assertFalse((outside / "hook-errors.jsonl").exists())
        (self.root / ".sybermem").rmdir()

    def test_nested_repository_worktree_env_and_no_project(self):
        self.dummy(body="print('outer')")
        nested = self.root / "nested"
        nested.mkdir()
        (nested / ".git").mkdir()
        self.assertEqual(self.invoke(cwd=nested).stdout, b"")
        other = Path(self.temp.name) / "worktree"
        other.mkdir()
        (other / ".git").write_text("gitdir: /not/accessed", encoding="utf-8")
        hooks = other / ".sybermem" / "hooks"
        hooks.mkdir(parents=True)
        reminder = "Recommended next step: /sybermem-record — worktree. Classification: change.\n"
        (hooks / "record_change_on_stop.py").write_text(f"import sys; sys.stdout.buffer.write({reminder.encode()!r})", encoding="utf-8")
        self.assertIn(b"worktree", self.invoke("record_change_on_stop", cwd=other, envroot=self.root).stdout)
        self.assertEqual(self.invoke("record_change_on_stop", cwd=self.root, envroot=other).stdout, b"")
        nowhere = Path(self.temp.name) / "nowhere"
        nowhere.mkdir()
        self.assertEqual(self.invoke(cwd=nowhere, envroot=self.root).stdout, b"")
        self.assertFalse((nowhere / ".sybermem").exists())

    def test_readonly_log_and_target_symlink(self):
        self.dummy(body="raise SystemExit(2)")
        log = self.root / ".sybermem" / "hook-errors.jsonl"
        log.mkdir()  # deterministic log write failure even with elevated privileges
        self.assertEqual((self.invoke().returncode, self.invoke().stdout), (0, b""))
        outside = Path(self.temp.name) / "outside.py"
        outside.write_text("print('outside')", encoding="utf-8")
        (self.hooks / "user_prompt.py").unlink()
        try:
            (self.hooks / "user_prompt.py").symlink_to(outside)
        except (OSError, NotImplementedError):
            return
        self.assertEqual(self.invoke().stdout, b"")


if __name__ == "__main__":
    unittest.main()
