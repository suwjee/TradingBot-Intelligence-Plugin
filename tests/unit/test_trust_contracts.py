"""Retrieval must reject malformed registries and derived relationship drift."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader
from tests.unit import test_local_reference_contract


class TrustContractTests(unittest.TestCase):
    def test_malformed_registry_row_has_stable_invalid_vault_error(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            row = {"id": "malformed", "repository_relative_path": "engine/algorithms/Broken.md",
                   "bytes": 0, "sha256": "0" * 64}
            build_fake_vault(root, [], references=[row])
            with plugin_reader(root) as reader:
                with self.assertRaises(reader.VaultError) as caught:
                    reader.read_algorithm_reference_evidence("malformed")
                self.assertEqual(caught.exception.code, "INVALID_VAULT")
                self.assertFalse(reader.verify_package("knowledge")["ok"])

    def test_relationship_retrieval_rejects_edge_added_only_to_index(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            entities = [EntitySpec(f"system.{name}", f"00_SYSTEM/{name}.md", "system", "active",
                                   "canonical", name, "Synthetic node.") for name in ("a", "b")]
            build_fake_vault(root, entities)
            path = root / "_INDEX/relations.json"
            path.write_text(json.dumps({"relations": [{"from": "system.a", "to": "system.b",
                                                      "type": "produces"}]}), encoding="utf-8")
            with plugin_reader(root) as reader:
                with self.assertRaisesRegex(ValueError, "Stale relation index"):
                    reader.relations("system.a")

    def test_reference_read_checks_manifest_pin_as_well_as_registry(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = test_local_reference_contract.LocalReferenceContractTests()
            row = fixture.make_vault(root)
            path = root / "_INDEX/source-hashes.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["algorithm_references"][0]["sha256"] = "0" * 64
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with plugin_reader(root) as reader:
                with self.assertRaisesRegex(ValueError, "identity"):
                    reader.read_algorithm_reference_evidence(row["id"])
