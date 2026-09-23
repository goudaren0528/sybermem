"""Isolated-home distribution tests; never touches the user's OpenCode install."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("opencode_install", Path(__file__).with_name("opencode-install.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class OpenCodeInstallTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root, self.home = self.base / "checkout", self.base / "home"
        source = self.root / "packages/opencode-plugin"
        (source / "dist-v2").mkdir(parents=True)
        (source / "sybermem-v1.ts").write_text("// V1\n")
        (source / "dist-v2/package.json").write_bytes(Path(__file__).with_name("opencode-v2-package.json").read_bytes())
        for name in ("server.js", "tui.js"):
            (source / "dist-v2" / name).write_text("// " + name)
        self.config = self.home / ".config/opencode/opencode.jsonc"
        self.config.parent.mkdir(parents=True)
        self.config.write_text('{\n  // keep my comment\n  "theme": "dark",\n  "plugin": ["example"],\n}\n')

    def test_unknown_is_noop(self):
        before = self.config.read_bytes()
        with patch.object(module, "_version", return_value=None):
            self.assertEqual(module.install(self.root, self.home), "skipped")
        self.assertEqual(before, self.config.read_bytes())

    def test_v2_idempotent_migration_and_uninstall(self):
        legacy = self.home / ".config/opencode/plugins/sybermem.ts"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("/** SyberMem OpenCode Plugin (generated bundle) */")
        module.install(self.root, self.home, "2")
        self.assertFalse(legacy.exists())
        self.assertTrue((self.home / ".config/opencode/sybermem-v2/tui.js").exists())
        first = self.config.read_bytes()
        self.assertIn(b"keep my comment", first)
        parsed = json.loads(module._strip_trailing_commas(module._mask_jsonc(first.decode())))
        self.assertNotIn("plugin", parsed)
        self.assertEqual(parsed["plugins"], ["example", str(self.config.parent / "sybermem-v2")])
        module.install(self.root, self.home, "2")
        self.assertEqual(first, self.config.read_bytes())
        module.uninstall(self.home)
        self.assertIn('"example"', self.config.read_text())
        self.assertNotIn("sybermem-v2", self.config.read_text())

    def test_v1_switch_to_v2_and_back(self):
        module.install(self.root, self.home, "1")
        module.install(self.root, self.home, "2")
        module.install(self.root, self.home, "1")
        self.assertTrue((self.home / ".config/opencode/plugins/sybermem.ts").is_file())
        self.assertNotIn("sybermem-v2", self.config.read_text())

    def test_reject_tampered_file_and_symlink(self):
        module.install(self.root, self.home, "2")
        server = self.home / ".config/opencode/sybermem-v2/server.js"
        server.write_text("user edit")
        with self.assertRaisesRegex(RuntimeError, "modified"):
            module.uninstall(self.home)
        self.assertEqual(server.read_text(), "user edit")
        server.unlink()
        try: server.symlink_to(self.config)
        except (OSError, NotImplementedError): return
        with self.assertRaisesRegex(RuntimeError, "linked"):
            module.install(self.root, self.home, "2")

    def test_rollback_on_write_failure(self):
        before = self.config.read_bytes()
        real_write = module._write
        def fail_config(path, data):
            if path == self.config: raise OSError("injected")
            return real_write(path, data)
        with patch.object(module, "_write", side_effect=fail_config):
            with self.assertRaises(OSError): module.install(self.root, self.home, "2")
        self.assertEqual(before, self.config.read_bytes())
        self.assertFalse((self.home / ".config/opencode/sybermem-v2/server.js").exists())

    def test_switch_rollback_restores_deleted_legacy_and_config(self):
        module.install(self.root, self.home, "1")
        legacy = self.config.parent / "plugins/sybermem.ts"
        before_legacy, before_config = legacy.read_bytes(), self.config.read_bytes()
        real_write = module._write
        def fail_config(path, data):
            if path == self.config: raise OSError("injected after legacy deletion")
            return real_write(path, data)
        with patch.object(module, "_write", side_effect=fail_config):
            with self.assertRaisesRegex(OSError, "injected"):
                module.install(self.root, self.home, "2")
        self.assertEqual(legacy.read_bytes(), before_legacy)
        self.assertEqual(self.config.read_bytes(), before_config)
        self.assertFalse((self.config.parent / "sybermem-v2/server.js").exists())
        module.install(self.root, self.home, "2")
        self.assertFalse(legacy.exists())
        self.assertEqual(len(json.loads(module._strip_trailing_commas(module._mask_jsonc(self.config.read_text())))["plugins"]), 2)

    def test_file_uri_and_actual_array_comments_survive_upgrades_and_uninstall(self):
        uri = "file:///other/plugin"
        self.config.write_text('{\n  "theme": "dark",\n  "plugin": [\n    "file:///other/plugin", // user plugin\n    "example", /* another plugin */\n  ],\n}\n')
        module.install(self.root, self.home, "2")
        module.install(self.root, self.home, "2")
        text = self.config.read_text()
        self.assertIn("// user plugin", text)
        self.assertIn("/* another plugin */", text)
        parsed = json.loads(module._strip_trailing_commas(module._mask_jsonc(text)))
        self.assertEqual(parsed["plugins"].count(uri), 1)
        self.assertNotIn("plugin", parsed)
        module.uninstall(self.home)
        parsed = json.loads(module._strip_trailing_commas(module._mask_jsonc(self.config.read_text())))
        self.assertIn(uri, parsed["plugins"])
        self.assertNotIn(str(self.config.parent / "sybermem-v2"), parsed["plugins"])

    def test_v2_existing_plugins_merges_v1_third_party_without_double_load(self):
        self.config.write_text('{"plugin": ["file:///other/plugin"], "plugins": ["another"]}')
        module.install(self.root, self.home, "2")
        parsed = json.loads(self.config.read_text())
        self.assertNotIn("plugin", parsed)
        self.assertEqual(parsed["plugins"], ["another", "file:///other/plugin", str(self.config.parent / "sybermem-v2")])

    def test_array_edits_all_positions_and_comments(self):
        cases = [
            ('{"plugins":["old","keep"]}', {"old"}, "new", ["keep", "new"]),
            ('{"plugins":["keep","old","end"]}', {"old"}, "new", ["keep", "end", "new"]),
            ('{"plugins":["keep","old"]}', {"old"}, "new", ["keep", "new"]),
            ('{"plugins":["keep","old","old"]}', {"old"}, None, ["keep"]),
            ('{"plugins":["old","old","keep"]}', {"old"}, "new", ["keep", "new"]),
            ('{"plugins":["old","old"]}', {"old"}, None, []),
            ('{"plugins":[]}', {"old"}, "new", ["new"]),
            ('{"plugins":["keep", "old",]}', {"old"}, "new", ["keep", "new"]),
            ('{"plugins":["file:///other/plugin", /* comment */ "old",]}', {"old"}, "new", ["file:///other/plugin", "new"]),
            ('{"plugin":["file:///other/plugin","old"],"plugins":["keep", "old",]}', {"old"}, "new", ["keep", "file:///other/plugin", "new"]),
        ]
        for text, remove, add, expected in cases:
            with self.subTest(text=text):
                result = module._config(text, remove, add)
                parsed = json.loads(module._strip_trailing_commas(module._mask_jsonc(result)))
                self.assertEqual(parsed["plugins"], expected)
                self.assertNotIn("plugin", parsed)
                if "/* comment */" in text: self.assertIn("/* comment */", result)

    def test_install_legacy_last_and_uninstall_duplicate_managed_entries(self):
        module.install(self.root, self.home, "1")
        legacy = str(self.config.parent / "plugins/sybermem.ts")
        self.config.write_text(json.dumps({"theme": "dark", "plugin": ["file:///other/plugin", legacy]}))
        module.install(self.root, self.home, "2")
        parsed = json.loads(module._strip_trailing_commas(module._mask_jsonc(self.config.read_text())))
        entry = str(self.config.parent / "sybermem-v2")
        self.assertEqual(parsed["plugins"], ["file:///other/plugin", entry])
        self.config.write_text(json.dumps({"plugins": [entry, "file:///other/plugin", entry]}))
        module.uninstall(self.home)
        self.assertEqual(json.loads(self.config.read_text())["plugins"], ["file:///other/plugin"])

    def test_bad_generated_config_does_not_touch_install_or_uninstall_files(self):
        before = self.config.read_bytes()
        with patch.object(module, "_config", return_value='{"plugins": ["broken",]} garbage'):
            with self.assertRaises(ValueError): module.install(self.root, self.home, "2")
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.config.parent / "sybermem-v2/server.js").exists())
        module.install(self.root, self.home, "2")
        before = self.config.read_bytes()
        server = self.config.parent / "sybermem-v2/server.js"
        with patch.object(module, "_config", return_value='{"plugins": nope}'):
            with self.assertRaises(ValueError): module.uninstall(self.home)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertTrue(server.exists())

    def test_existing_unrelated_directory_and_config_survive(self):
        package = self.home / ".config/opencode/sybermem-v2"
        package.mkdir()
        (package / "notes.txt").write_text("owned by user")
        module.install(self.root, self.home, "2")
        module.uninstall(self.home)
        self.assertEqual((package / "notes.txt").read_text(), "owned by user")

    def test_reject_ambiguous_or_invalid_config_without_writes(self):
        (self.config.parent / "opencode.json").write_text("{}")
        with self.assertRaisesRegex(RuntimeError, "multiple"):
            module.install(self.root, self.home, "2")
        (self.config.parent / "opencode.json").unlink()
        self.config.write_text('{"plugin": {"not": "an array"}}')
        with self.assertRaisesRegex(ValueError, "array"):
            module.install(self.root, self.home, "2")
        self.assertFalse((self.config.parent / "sybermem-v2/server.js").exists())

    def test_uninstall_rejects_linked_ancestor(self):
        module.install(self.root, self.home, "2")
        linked = self.base / "linked"
        try: linked.symlink_to(self.home, target_is_directory=True)
        except (OSError, NotImplementedError): return
        with self.assertRaisesRegex(RuntimeError, "linked"):
            module.uninstall(linked)
        self.assertTrue((self.home / ".config/opencode/sybermem-v2/server.js").exists())

    def test_host_version_detection_refuses_unsupported_major(self):
        from unittest.mock import Mock
        with patch.object(module.subprocess, "run", return_value=Mock(stdout="opencode 3.0.0", stderr="")):
            self.assertIsNone(module._version(None))
        with patch.object(module.subprocess, "run", return_value=Mock(stdout="2.0.15", stderr="")):
            self.assertEqual(module._version(None), "2")


if __name__ == "__main__":
    unittest.main()
