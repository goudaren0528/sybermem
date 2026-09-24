"""Release-chain tests with temporary files and mocked subprocesses only."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("sybermem_release", Path(__file__).with_name("release.py"))
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)

BUILDS = [
    ["bun", "scripts/build-opencode-plugin.mjs", *flags]
    for flags in ((), ("--v1",), ("--tui",), ("--package",), ("--package", "--tui"))
]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "VERSION").write_text("0.6.0\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## Unreleased\n\n- entry\n\n## 0.6.0 - earlier\n", encoding="utf-8")
        for name, value in (("ROOT", root), ("VERSION_FILE", root / "VERSION"),
                            ("CHANGELOG_FILE", root / "CHANGELOG.md")):
            override = patch.object(release, name, value)
            override.start()
            self.addCleanup(override.stop)

    def test_dry_run_shows_all_five_builds_and_guard_without_mutating(self):
        before = [release.VERSION_FILE.read_bytes(), release.CHANGELOG_FILE.read_bytes()]
        with patch.object(sys, "argv", ["release.py", "0.7.0", "--dry-run"]), \
             patch.object(release.subprocess, "run", side_effect=AssertionError("must not run")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(release.main(), 0)
        text = output.getvalue()
        for cmd in BUILDS:
            self.assertIn("would run: " + " ".join(cmd) + "\n", text)
        self.assertIn("would run: " + sys.executable + " scripts/check-plugin-package.py", text)
        self.assertEqual(before, [release.VERSION_FILE.read_bytes(), release.CHANGELOG_FILE.read_bytes()])

    def test_real_chain_builds_all_targets_before_mandatory_guard(self):
        commands = []

        def fake_run(cmd, **kwargs):
            self.assertEqual(kwargs["cwd"], release.ROOT)
            commands.append(cmd)
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with patch.object(sys, "argv", ["release.py", "0.7.0"]), \
             patch.object(release.subprocess, "run", side_effect=fake_run), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(release.main(), 0)
        self.assertEqual(commands, [[sys.executable, "scripts/sync-version.py"], *BUILDS,
                                    [sys.executable, "scripts/check-plugin-package.py"]])
        self.assertEqual(release.VERSION_FILE.read_text(encoding="utf-8"), "0.7.0\n")
        self.assertIn("## 0.7.0 - ", release.CHANGELOG_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
