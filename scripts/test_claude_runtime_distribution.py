"""Side-effect-free distribution checks using only temporary homes and dummy hooks."""
import importlib.util
import contextlib
import io
import json
import os
import re
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unittest.mock


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
IDS = {
    "launch_record_change_on_stop.py": "record_change_on_stop",
    "launch_session_start_context.py": "session_start_context",
    "launch_user_prompt.py": "user_prompt",
    "launch_recall_outcome_on_stop.py": "recall_outcome_on_stop",
}


def load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace("-", "_"), SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClaudeRuntimeDistribution(unittest.TestCase):
    def test_cli_invalid_private_source_does_not_leak_traceback_or_path(self):
        sentinel = "PRIVATE_DUMMY_SENTINEL"
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            checkout = base / "private-dummy-checkout"
            scripts = checkout / "scripts"
            scripts.mkdir(parents=True)
            for name in ("global-hook-launcher.py", "managed-install.json", "safe-managed-remove.py", "opencode-install.py"):
                shutil.copy2(SCRIPTS / name, scripts / name)
            (scripts / "safe-managed-remove.py").write_text(f"{sentinel}=(\n", encoding="utf-8")
            home = base / "isolated-home"
            result = subprocess.run([sys.executable, str(SCRIPTS / "claude-runtime-deploy.py"),
                                     "--root", str(checkout), "--home", str(home)],
                                    capture_output=True, text=True,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("deployment failed verification", result.stderr)
            for private in (sentinel, str(base), "Traceback", "SyntaxError"):
                self.assertNotIn(private, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_deployment_verifies_final_bytes_without_running_hooks(self):
        deployer = load("claude-runtime-deploy.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            with unittest.mock.patch.object(deployer, "verify_deployment", wraps=deployer.verify_deployment) as checked:
                deployer.deploy(ROOT, home)
                checked.assert_called_once()
            runtime = home / ".claude" / "sybermem"
            (runtime / "launch_hook.py").write_text("raise RuntimeError('do not execute')\n")
            with self.assertRaisesRegex(RuntimeError, "runtime byte mismatch"):
                deployer.verify_deployment(ROOT, home)
            (runtime / "launch_hook.py").unlink()
            with self.assertRaises(RuntimeError):
                deployer.verify_deployment(ROOT, home)

    def test_linked_runtime_rejected_as_batch_without_overwriting_outside(self):
        deployer = load("claude-runtime-deploy.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            outside = Path(folder) / "outside"
            (home / ".claude").mkdir(parents=True)
            outside.mkdir()
            sentinel = outside / "launch_hook.py"
            sentinel.write_bytes(b"USER FILE")
            junction = home / ".claude" / "sybermem"
            if os.name == "nt":
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True)
                if result.returncode:
                    self.skipTest("Windows junction creation unavailable")
            else:
                junction.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "unsafe linked path"):
                deployer.deploy(ROOT, home)
            self.assertEqual(sentinel.read_bytes(), b"USER FILE")
            self.assertEqual({item.name for item in outside.iterdir()}, {"launch_hook.py"})

    def test_linked_late_shim_rejects_before_any_runtime_write(self):
        deployer = load("claude-runtime-deploy.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            runtime = home / ".claude" / "sybermem"
            runtime.mkdir(parents=True)
            outside = Path(folder) / "outside.py"
            outside.write_bytes(b"USER FILE")
            try:
                (runtime / "launch_recall_outcome_on_stop.py").symlink_to(outside)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"target symlink permission unavailable: {exc}")
            with self.assertRaisesRegex(RuntimeError, "unsafe linked path"):
                deployer.deploy(ROOT, home)
            self.assertEqual(outside.read_bytes(), b"USER FILE")
            self.assertFalse((runtime / "launch_hook.py").exists())
            self.assertFalse((runtime / "managed-install.json").exists())

    def test_manifest_install_and_uninstall_preserve_third_party(self):
        deployer = load("claude-runtime-deploy.py")
        remover = load("safe-managed-remove.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            deployer.deploy(ROOT, home)
            runtime = home / ".claude" / "sybermem"
            manifest = json.loads((runtime / "managed-install.json").read_text(encoding="utf-8"))
            for name in ("launch_hook.py", *IDS):
                self.assertIn(name, manifest["runtime_files"])
                self.assertTrue((runtime / name).is_file(), name)
            (runtime / "third_party.py").write_text("untouched")
            with unittest.mock.patch.object(remover, "_remove_fixed_plugin"):
                remover.uninstall(home, runtime / "managed-install.json")
            self.assertEqual((runtime / "third_party.py").read_text(), "untouched")
            for name in ("launch_hook.py", *IDS):
                self.assertFalse((runtime / name).exists())

    def test_legacy_shims_fail_open_with_dummy_missing_target(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            git = home / "sample"; git.mkdir()
            subprocess.run(["git", "init", "-q", str(git)], check=True, capture_output=True)
            (git / ".sybermem" / "hooks").mkdir(parents=True)
            (git / ".sybermem" / "project.yaml").write_text("name: dummy\n")
            runtime = home / "runtime"; runtime.mkdir()
            (runtime / "launch_hook.py").write_bytes((SCRIPTS / "global-hook-launcher.py").read_bytes())
            for name, hook in IDS.items():
                (runtime / name).write_text(
                    "import sys\nfrom launch_hook import main\n"
                    f"sys.argv = [sys.argv[0], {hook!r}]\nraise SystemExit(main())\n")
                result = subprocess.run([sys.executable, str(runtime / name)], cwd=git,
                                        input=b"{}", capture_output=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(git)})
                self.assertEqual((result.returncode, result.stdout), (0, b""), name)

    def test_installed_shims_execute_dummy(self):
        deployer = load("claude-runtime-deploy.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            scripts = home / ".claude" / "sybermem"
            deployer.deploy(ROOT, home)
            project = home / "project"
            subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
            hooks = project / ".sybermem" / "hooks"
            hooks.mkdir(parents=True)
            (hooks / "user_prompt.py").write_text("print('dummy context')\n")
            result = subprocess.run([sys.executable, str(scripts / "launch_user_prompt.py")], cwd=project,
                                    input=b"{}", capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn(b"decision", result.stdout)

    def test_remote_payload_references_unified_source(self):
        for name in ("install-remote.sh", "install-remote.ps1", "install-remote.py"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            if name.endswith(".py"):
                self.assertIn("install_from_checkout", text)
            else:
                self.assertIn("claude-runtime-deploy.py", text)

    def test_shims_forward_arguments_to_stub_without_runtime(self):
        deployer = load("claude-runtime-deploy.py")
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            runtime = home / ".claude" / "sybermem"
            deployer.deploy(ROOT, home)
            stub = "import json,sys\ndef main():\n print(json.dumps(sys.argv[1:]))\n return 0\n"
            (runtime / "launch_hook.py").write_text(stub, encoding="utf-8")
            for script in ("install.sh", "update.sh", "install-remote.sh", "install.ps1", "update.ps1", "install-remote.ps1"):
                self.assertIn("claude-runtime-deploy.py", (SCRIPTS / script).read_text(encoding="utf-8"))
            for name, hook_id in IDS.items():
                entry = runtime / name
                entry.write_text((SCRIPTS / ("global-stop-hook-launcher.py" if hook_id == "record_change_on_stop" else "global-session-start-launcher.py")).read_text(encoding="utf-8") if hook_id in ("record_change_on_stop", "session_start_context") else (runtime / name).read_text(encoding="utf-8"))
                for args in (("--timeout-seconds", "1"), ("--invalid",)):
                    result = subprocess.run([sys.executable, str(entry), *args], capture_output=True, text=True)
                    self.assertEqual(json.loads(result.stdout), [hook_id, *args])

    def test_python_probe_wiring_rejects_broken_alias(self):
        for name in ("install.sh", "update.sh", "install-remote.sh"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            for fragment in ('for candidate in python python3;', 'sys.executable', '"$executable" -c', 'CLAUDE_PYTHON', 'not verified'):
                self.assertIn(fragment, text, name)
        for name in ("install.ps1", "update.ps1", "install-remote.ps1"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            for fragment in ('@("python", "python3")', '$LASTEXITCODE -ne 0', 'sys.executable', '.exe', '& $exe -c', '$ClaudePython', 'not verified'):
                self.assertIn(fragment, text, name)

    def test_all_entrypoints_explain_project_refresh_is_pending(self):
        for name in ("install.sh", "update.sh", "install-remote.sh", "install.ps1", "update.ps1", "install-remote.ps1", "_install_common.py"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertIn("sybermem project refresh", text, name)
            self.assertIn("未迁移" if name in ("install.sh", "update.sh") else "NOT migrated", text, name)

    def test_python_install_reports_deployment_but_not_project_migration(self):
        common = load("_install_common.py")
        import unittest.mock
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()) as output:
            with unittest.mock.patch.object(common.Path, "home", return_value=Path(folder)), \
                 unittest.mock.patch.object(common, "_sync_skills"), \
                 unittest.mock.patch.object(common, "_install_codex_hooks"), \
                 unittest.mock.patch.object(common, "_install_runtime"), \
                 unittest.mock.patch.object(common.subprocess, "run"):
                common.install_from_checkout(ROOT)
            self.assertIn("Global hook runtime deployed", output.getvalue())
            self.assertIn("project settings NOT migrated", output.getvalue())
            self.assertIn("sybermem project refresh", output.getvalue())
            self.assertIn("Host acceptance remains unverified", output.getvalue())

    @unittest.skipUnless(os.name == "nt" and shutil.which("powershell"), "PowerShell probe requires Windows")
    def test_powershell_probe_skips_broken_python_cmd_and_accepts_python3(self):
        with tempfile.TemporaryDirectory(prefix="探测 path with spaces ") as folder:
            directory = Path(folder)
            (directory / "python.cmd").write_text("@echo off\r\nexit /b 2\r\n", encoding="ascii")
            (directory / "python3.cmd").write_text(f'@echo off\r\n"{sys.executable}" %*\r\n', encoding="ascii")
            env = {**os.environ, "PATH": str(directory) + os.pathsep + os.environ["PATH"],
                   "PYTHONDONTWRITEBYTECODE": "1"}
            for name in ("install.ps1", "update.ps1", "install-remote.ps1"):
                text = (SCRIPTS / name).read_text(encoding="utf-8")
                start = text.index("$ClaudePython = $null")
                end = text.index("\n", text.index('if (-not $ClaudePython) { throw "No working real Python executable', start))
                runner = directory / "probe.ps1"
                runner.write_text(text[start:end] + "\nWrite-Output $ClaudePython\n", encoding="utf-8-sig")
                result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(runner)],
                                        capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 0, (name, result.stderr))
                self.assertEqual(Path(result.stdout.strip()), Path(sys.executable).resolve())
                (directory / "python3.cmd").write_text("@echo off\r\nexit /b 2\r\n", encoding="ascii")
                failed = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(runner)],
                                        capture_output=True, text=True, env=env)
                self.assertNotEqual(failed.returncode, 0, name)
                self.assertIn("not verified", failed.stderr)
                (directory / "python3.cmd").write_text(f'@echo off\r\n"{sys.executable}" %*\r\n', encoding="ascii")


if __name__ == "__main__":
    unittest.main()
