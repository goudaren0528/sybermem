"""Exercise build guards in synthetic repositories without changing user installs."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("sybermem.ts", ()),
    ("sybermem-v1.ts", ("--v1",)),
    ("sybermem-tui.ts", ("--tui",)),
    ("dist-v2/server.js", ("--package",)),
    ("dist-v2/tui.js", ("--package", "--tui")),
)
BUN = shutil.which("bun")


@unittest.skipUnless(BUN, "Bun is required for build regression tests")
class OpenCodeBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sybermem-build-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        for name in ("build-opencode-plugin.mjs", "opencode-v2-package.json", "check-plugin-package.py"):
            shutil.copyfile(ROOT / "scripts" / name, self.root / "scripts" / name)
        shutil.copyfile(ROOT / ".bun-version", self.root / ".bun-version")
        self.plugin = self.root / "packages" / "opencode-plugin"
        shutil.copytree(ROOT / "packages" / "opencode-plugin" / "src", self.plugin / "src")
        for name, flags in TARGETS:
            self.assert_build_ok(flags)

    def build(self, flags=(), check=False):
        return subprocess.run(
            [BUN, "scripts/build-opencode-plugin.mjs", *flags, *(["--check"] if check else [])],
            cwd=self.root, capture_output=True, text=True,
        )

    def assert_build_ok(self, flags=(), check=False):
        result = self.build(flags, check)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_bundles_and_manifest_accept_crlf_without_writes(self):
        paths = [self.plugin / name for name, _ in TARGETS]
        paths += [self.plugin / "dist-v2/package.json"]
        for path in paths:
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        before = {path: path.read_bytes() for path in paths}
        for name, flags in TARGETS:
            with self.subTest(bundle=name):
                self.assert_build_ok(flags, check=True)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})

    def test_each_bundle_rejects_content_drift_and_missing_output(self):
        for name, flags in TARGETS:
            with self.subTest(bundle=name):
                path = self.plugin / name
                original = path.read_bytes()
                path.write_bytes(original + b"// synthetic content drift\n")
                result = self.build(flags, check=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("is stale", result.stderr)
                self.assertEqual(path.read_bytes(), original + b"// synthetic content drift\n")
                path.unlink()
                result = self.build(flags, check=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(path.exists())
                path.write_bytes(original)

    def test_version_mismatch_blocks_check_and_write(self):
        path = self.plugin / "sybermem.ts"
        original = path.read_bytes()
        (self.root / ".bun-version").write_text("0.0.0\n", encoding="utf-8")
        for check in (False, True):
            with self.subTest(check=check):
                result = self.build(check=check)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("require Bun 0.0.0 from .bun-version", result.stderr)
                self.assertEqual(path.read_bytes(), original)

    def test_manifest_content_drift_and_missing_output_are_rejected(self):
        manifest = self.plugin / "dist-v2/package.json"
        manifest.write_text('{}\n', encoding="utf-8")
        for flags in (("--package",), ("--package", "--tui")):
            self.assertNotEqual(self.build(flags, check=True).returncode, 0)
        manifest.unlink()
        self.assertNotEqual(self.build(("--package",), check=True).returncode, 0)
        self.assertFalse(manifest.exists())

    def test_package_checker_detects_compatibility_tui_drift(self):
        checker = runpy.run_path(str(self.root / "scripts/check-plugin-package.py"))
        guard = checker["check_opencode_plugin_source_bundle"]
        guard(self.root)
        path = self.plugin / "sybermem-tui.ts"
        path.write_bytes(path.read_bytes() + b"// synthetic drift\n")
        with contextlib.redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit):
                guard(self.root)
        self.assertIn("sybermem-tui.ts is stale", error.getvalue())

    def test_package_tui_regeneration_command_targets_same_output(self):
        path = self.plugin / "dist-v2/tui.js"
        self.assertIn(
            "Regenerate with: bun scripts/build-opencode-plugin.mjs --package --tui",
            path.read_text(encoding="utf-8"),
        )
        path.write_text("stale", encoding="utf-8")
        result = self.build(("--package", "--tui"), check=True)
        self.assertIn("build-opencode-plugin.mjs --package --tui", result.stderr)


if __name__ == "__main__":
    unittest.main()
