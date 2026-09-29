"""Current empty evidence stores and protected-file mutation checks."""

import unittest

from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.real_roots import require_real_roots
from tests.helpers.snapshots import snapshot_files, assert_unchanged
from tests.integration.test_real_engine_evidence import manifest_and_registry, engine_pairs
from tests.integration.test_real_vault import load_index, frontmatter


def registered_data(roots):
    entities = load_index(roots)
    datasets = []
    windows = []
    for entity_id, row in entities.items():
        if row["type"] != "data":
            continue
        fields = frontmatter((roots.vault / row["file"]).read_text(encoding="utf-8-sig"))
        if fields.get("data_kind") == "dataset":
            datasets.append(entity_id)
        elif fields.get("data_kind") == "window":
            windows.append(entity_id)
    return sorted(datasets), sorted(windows)


def protected_paths(roots):
    manifest, registry = manifest_and_registry(roots)
    paths = [roots.vault / "_INDEX/entities.json", roots.vault / "_INDEX/relations.json",
             roots.vault / "_INDEX/source-hashes.json", roots.vault / "06_SOURCE/References/registry.json"]
    paths.extend(mirror for _, mirror, _ in engine_pairs(roots, manifest))
    paths.extend(engine for _, _, engine in engine_pairs(roots, manifest))
    paths.extend(roots.vault / row["local_path"] for row in registry["references"])
    if roots.engine:
        paths.extend(roots.engine / row["repository_relative_path"] for row in registry["references"])
    paths.append(roots.vault / "08_DATA/Raw")
    paths.append(roots.vault / "07_VALIDATION/Fixtures")
    return paths


class RealDataAndReadOnlyTests(unittest.TestCase):
    def test_current_stores_are_empty_by_design_and_missing_entities_are_explicit(self):
        roots = require_real_roots(self)
        datasets, windows = registered_data(roots)
        self.assertEqual((datasets, windows), ([], []))
        for relative in ("08_DATA/Raw", "07_VALIDATION/Fixtures"):
            self.assertEqual([], [path for path in (roots.vault / relative).rglob("*") if path.is_file()])
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            for call in (lambda: reader.get_dataset("data.missing_dataset"),
                         lambda: reader.get_window("data.missing_window", include_rows=True)):
                with self.assertRaises(ValueError) as caught:
                    call()
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "ENTITY_NOT_FOUND")
            full = reader.verify_package("full-data")
            self.assertTrue(full["ok"], full["errors"])
            self.assertEqual(full["data_status"], "EMPTY_BY_DESIGN")
            self.assertEqual(full["verified_datasets"], 0)
            self.assertEqual(full["verified_windows"], 0)

    def test_public_operations_and_both_verifiers_do_not_mutate_protected_files(self):
        roots = require_real_roots(self, engine_required=True)
        manifest, registry = manifest_and_registry(roots)
        entities = load_index(roots)
        datasets, windows = registered_data(roots)
        self.assertEqual((datasets, windows), ([], []))
        self.assertTrue(manifest["files"] and registry["references"])
        selected_note = roots.vault / entities["algorithm.order.a"]["file"]
        paths = protected_paths(roots) + [selected_note]
        before = snapshot_files(paths)
        try:
            with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
                self.assertEqual(reader.get_entity("algorithm.order.a")["id"], "algorithm.order.a")
                self.assertIsInstance(reader.search("order", limit=1), list)
                self.assertEqual(reader.relations("algorithm.order.a")["entity_id"], "algorithm.order.a")
                source = next(row["mirror"] for row in manifest["files"] if row["mirror"].startswith("06_SOURCE/Code/") and row["bytes"] > 0)
                self.assertEqual(reader.read_evidence(source, 1, 1)["path"], source)
                reference_id = registry["references"][0]["id"]
                self.assertEqual(reader.read_algorithm_reference_evidence(reference_id, 1, 1)["reference_id"], reference_id)
                for call in (lambda: reader.get_dataset("data.missing_dataset"),
                             lambda: reader.get_window("data.missing_window", include_rows=True)):
                    with self.assertRaises(ValueError):
                        call()
                for mode in ("knowledge", "full-data"):
                    result = reader.verify_package(mode)
                    self.assertEqual(result["mode"], mode)
                    self.assertEqual(result["errors"], [], result["errors"])
        finally:
            after = snapshot_files(paths)
            assert_unchanged(before, after)
