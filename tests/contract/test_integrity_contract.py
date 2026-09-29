"""Public package integrity results for synthetic knowledge."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault, write_entity_note
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class IntegrityContractTests(unittest.TestCase):
    def test_verify_package_reports_mode_and_registered_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [
                EntitySpec("data.dataset", "08_DATA/dataset.md", "data", "active", "canonical",
                           "Dataset", "Synthetic metadata.", {"data_kind": "dataset",
                           "raw_path": "08_DATA/Raw/sample.json"}),
                EntitySpec("data.window", "08_DATA/window.md", "data", "active", "canonical",
                           "Window", "Synthetic metadata.", {"data_kind": "window",
                           "raw_path": "08_DATA/Raw/sample.json"}),
            ])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            self.assertTrue(result["ok"])
            self.assertEqual(result["registered_datasets"], 1)
            self.assertEqual(result["registered_windows"], 1)
            self.assertEqual(result["data_status"], "NOT_RUN")

    def test_verify_package_rejects_tampered_order_contract_frontmatter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = EntitySpec("algorithm.order.a", "01_ALGORITHMS/order-a.md", "algorithm",
                                  "active", "canonical", "Synthetic Order A", "Synthetic contract.",
                                  {"valid_for_regression_baseline": True})
            build_fake_vault(root, [original])
            index_path = root / "_INDEX/entities.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["entities"][original.id]["valid_for_regression_baseline"] = True
            index_path.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n",
                                  encoding="utf-8")
            with plugin_reader(root) as reader:
                baseline = reader.verify_package("knowledge")
                self.assertTrue(baseline["ok"], baseline["errors"])
                self.assertEqual(baseline["errors"], [])
                tampered = EntitySpec(original.id, original.file, original.type, original.status,
                                      original.authority, original.title, original.body,
                                      {"valid_for_regression_baseline": False})
                write_entity_note(root, tampered)
                before_verify = snapshot_files([root])
                result = reader.verify_package("knowledge")
                assert_unchanged(before_verify, snapshot_files([root]))
            self.assertFalse(result["ok"], "Tampered Order contract metadata must fail integrity")
            self.assertTrue(
                any(error == original.file or
                    (any(marker in error.lower() for marker in ("stale", "integrity", "mismatch"))
                     and (original.id in error or "valid_for_regression_baseline" in error))
                    for error in result["errors"]),
                "Errors must identify the stale indexed Order contract note or field: "
                + repr(result["errors"]),
            )

    def test_verify_package_rejects_tampered_generic_indexed_frontmatter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = EntitySpec("system.sample", "00_SYSTEM/sample.md", "system", "active",
                                  "canonical", "Synthetic system", "Synthetic guidance.",
                                  {"validation_tier": "sampled"})
            build_fake_vault(root, [original])
            index_path = root / "_INDEX/entities.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["entities"][original.id]["validation_tier"] = "sampled"
            index_path.write_text(json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n",
                                  encoding="utf-8")
            with plugin_reader(root) as reader:
                baseline = reader.verify_package("knowledge")
                self.assertTrue(baseline["ok"], baseline["errors"])
                self.assertEqual(baseline["errors"], [])
                tampered = EntitySpec(original.id, original.file, original.type, original.status,
                                      original.authority, original.title, original.body,
                                      {"validation_tier": "complete"})
                write_entity_note(root, tampered)
                before_verify = snapshot_files([root])
                result = reader.verify_package("knowledge")
                assert_unchanged(before_verify, snapshot_files([root]))
            self.assertFalse(result["ok"], "Changed indexed metadata must fail integrity")
            self.assertTrue(
                any(error == original.file or
                    (any(marker in error.lower() for marker in ("stale", "integrity", "mismatch"))
                     and (original.id in error or "validation_tier" in error))
                    for error in result["errors"]),
                "Errors must identify the stale indexed neutral note or field: "
                + repr(result["errors"]),
            )
