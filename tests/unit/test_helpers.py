"""Contracts for the test-only foundation."""

from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import os
import sys
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class FoundationTests(unittest.TestCase):
    def sample(self):
        return EntitySpec(id="system.sample", file="00_SYSTEM/Sample.md", type="system",
                          status="active", authority="canonical", title="Sample",
                          body="Synthetic sample.")

    def test_one_entity_vault_is_read_by_fresh_plugin_reader(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("system.sample")["id"], "system.sample")

    def test_entity_index_is_deterministic_across_input_order(self):
        other = EntitySpec(id="system.alpha", file="00_SYSTEM/Alpha.md", type="system",
                           status="active", authority="canonical", title="Alpha", body="Synthetic alpha.")
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            build_fake_vault(Path(first), [self.sample(), other])
            build_fake_vault(Path(second), [other, self.sample()])
            left = (Path(first) / "_INDEX/entities.json").read_bytes()
            right = (Path(second) / "_INDEX/entities.json").read_bytes()
            self.assertEqual(left, right)
            self.assertEqual(list(json.loads(left)["entities"]),
                             ["system.alpha", "system.authority-model", "system.sample"])

    def test_reference_registry_and_source_pins_match_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            built = build_fake_vault(root, [self.sample()],
                                     source_files={"06_SOURCE/Code/sample.py": b"x = 1\n"})
            pins = built.manifest["files"] + built.manifest["supporting_files"]
            for pin in pins:
                relative = pin.get("mirror", pin.get("path"))
                data = (root / relative).read_bytes()
                self.assertEqual(pin["bytes"], len(data))
                self.assertEqual(pin["sha256"], hashlib.sha256(data).hexdigest())
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])

    def test_relation_argument_produces_verifiable_note_and_index(self):
        other = EntitySpec(id="system.other", file="00_SYSTEM/Other.md", type="system",
                           status="active", authority="canonical", title="Other", body="Synthetic other.")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample(), other], relations=[
                {"from": "system.sample", "type": "depends_on", "to": "system.other"}])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
                self.assertTrue(result["ok"], result["errors"])
                fields, _ = reader._frontmatter(reader.get_entity("system.sample")["content"])
                self.assertEqual(fields["depends_on"], ["system.other"])

    def test_plugin_reader_restores_environment_and_module_cache(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            keys = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
                    "TRADINGBOT_PLUGIN_CONFIG")
            before = {key: os.environ.get(key) for key in keys}
            prior_reader = sys.modules.get("vault_reader")
            with plugin_reader(root) as reader:
                self.assertEqual(reader.ROOT, root.resolve())
                self.assertEqual(os.environ["TRADINGBOT_KNOWLEDGE_VAULT"], str(root.resolve()))
                self.assertNotIn("TRADINGBOT_ENGINE_ROOT", os.environ)
            self.assertEqual({key: os.environ.get(key) for key in keys}, before)
            self.assertIs(sys.modules.get("vault_reader"), prior_reader)

    def test_plugin_reader_restores_state_after_body_exception(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [self.sample()])
            keys = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
                    "TRADINGBOT_PLUGIN_CONFIG")
            before = {key: os.environ.get(key) for key in keys}
            prior_reader = sys.modules.get("vault_reader")
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                with plugin_reader(root) as reader:
                    self.assertEqual(reader.ROOT, root.resolve())
                    raise RuntimeError("synthetic failure")
            self.assertEqual({key: os.environ.get(key) for key in keys}, before)
            self.assertIs(sys.modules.get("vault_reader"), prior_reader)

    def test_snapshot_detects_changed_file(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(b"one")
            before = snapshot_files([path])
            path.write_bytes(b"two")
            after = snapshot_files([path])
            with self.assertRaisesRegex(AssertionError, "sample.txt"):
                assert_unchanged(before, after)
