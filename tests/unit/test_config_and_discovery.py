"""Synthetic Vault discovery and configuration contracts."""

import json
import os
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def sample():
    return EntitySpec("system.sample", "00_SYSTEM/Sample.md", "system", "active",
                      "canonical", "Sample", "Synthetic content.")


class DiscoveryTests(unittest.TestCase):
    def assert_import_code(self, root, code):
        with TemporaryDirectory() as directory:
            valid = Path(directory) / "valid"
            build_fake_vault(valid, [sample()])
            with plugin_reader(valid) as reader:
                with patch.dict(os.environ, {"TRADINGBOT_KNOWLEDGE_VAULT": str(root)}, clear=False):
                    with self.assertRaises(reader.VaultError) as caught:
                        reader.locate_vault()
                    self.assertEqual(caught.exception.code, code)

    def test_explicit_valid_vault_and_unicode_space_path(self):
        with TemporaryDirectory(prefix="Vault فضای آزمایش ") as directory:
            root = Path(directory) / "Knowledge Vault"
            build_fake_vault(root, [sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.ROOT, root.resolve())
                self.assertEqual(reader.get_entity("system.sample")["id"], "system.sample")

    def test_missing_root_and_random_directory_have_distinct_codes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assert_import_code(root / "missing", "VAULT_NOT_FOUND")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_required_index_and_schema_are_required(self):
        for relative in ("_INDEX/entities.json", "_SCHEMA/note.schema.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).unlink()
                self.assert_import_code(root, "INVALID_VAULT")

    def test_malformed_registry_and_index_are_invalid_vaults(self):
        for relative in ("06_SOURCE/References/registry.json", "_INDEX/entities.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).write_text("{invalid", encoding="utf-8")
                self.assert_import_code(root, "INVALID_VAULT")

    def test_unknown_registry_schema_version_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            registry = root / "06_SOURCE/References/registry.json"
            registry.write_text(json.dumps({"schema_version": 999, "references": []}), encoding="utf-8")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_config_file_override_and_explicit_environment_precedence(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            configured = build_fake_vault(base / "configured", [sample()]).root
            explicit = build_fake_vault(base / "explicit", [sample()]).root
            config = base / "vault config.json"
            config.write_text(json.dumps({"vault_root": str(configured)}), encoding="utf-8")
            with plugin_reader(explicit) as reader:
                with patch.dict(os.environ, {"TRADINGBOT_PLUGIN_CONFIG": str(config)}, clear=False):
                    with patch.dict(os.environ, {"TRADINGBOT_KNOWLEDGE_VAULT": ""}, clear=False):
                        self.assertEqual(reader.locate_vault(), configured.resolve())
                    self.assertEqual(reader.locate_vault(), explicit.resolve())

    def test_relative_explicit_path_resolves(self):
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            relative = Path(root.name)
            with plugin_reader(relative) as reader:
                self.assertEqual(reader.ROOT, root.resolve())

    def test_optional_engine_and_raw_are_not_discovery_dependencies(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            content = b"synthetic reference\n"
            reference_id = "algorithm.synthetic"
            local = "06_SOURCE/Code/engine/algorithms/Synthetic.md"
            build_fake_vault(root, [sample()], references=[{
                "id": reference_id,
                "local_path": local,
                "repository_relative_path": "engine/algorithms/Synthetic.md",
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }], reference_files={local: content})
            with plugin_reader(root) as reader:
                unconfigured = reader.verify_package("knowledge")
                self.assertTrue(unconfigured["ok"])
                self.assertEqual(unconfigured["local_references"][reference_id], "verified")
                self.assertEqual(unconfigured["external_references"][reference_id], "optional_not_configured")
            with plugin_reader(root, engine_root=Path(directory) / "absent-engine") as reader:
                missing = reader.verify_package("knowledge")
                self.assertFalse(missing["ok"])
                self.assertEqual(missing["external_references"][reference_id], "unavailable")
                self.assertIn(f"reference_unavailable:{reference_id}", missing["errors"])

    def test_missing_pinned_raw_is_optional_only_in_knowledge_mode(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()], raw_files={"08_DATA/Raw/synthetic.json": b"[]\n"})
            (root / "08_DATA/Raw/synthetic.json").unlink()
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])
                full = reader.verify_package("full-data")
                self.assertFalse(full["ok"])
                self.assertIn("08_DATA/Raw/synthetic.json", full["errors"])


if __name__ == "__main__":
    unittest.main()
