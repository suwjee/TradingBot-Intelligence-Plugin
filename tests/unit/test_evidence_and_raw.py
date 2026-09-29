"""Public evidence and RAW retrieval against synthetic Vault metadata."""

import tempfile
import unittest
import hashlib
import json
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class EvidenceAndRawTests(unittest.TestCase):
    SOURCE = "06_SOURCE/Code/sample.py"
    RAW = "08_DATA/Raw/sample.json"

    def make_vault(self, root, *, include_raw=True, reference=None, reference_content=None):
        raw = [{"time": epoch, "value": epoch} for epoch in (10, 20, 30, 40)]
        raw_bytes = json.dumps(raw).encode("utf-8")
        entities = [
            EntitySpec("source.sample", "06_SOURCE/source-sample.md", "source", "active",
                       "canonical", "Sample source", "Source note.", {"source_path": self.SOURCE}),
            EntitySpec("data.sample", "08_DATA/dataset.md", "data", "active", "canonical",
                       "Sample dataset", "Dataset note.", {"data_kind": "dataset",
                       "raw_path": self.RAW, "raw_bytes": len(raw_bytes),
                       "raw_sha256": hashlib.sha256(raw_bytes).hexdigest()}),
            EntitySpec("data.window", "08_DATA/window.md", "data", "active", "canonical",
                       "Sample window", "Window note.", {"data_kind": "window",
                       "raw_path": self.RAW, "first_epoch": 10, "last_epoch": 40}),
        ]
        build_fake_vault(root, entities, source_files={self.SOURCE: b"alpha\nbeta\ngamma\n"},
                         raw_files={self.RAW: raw_bytes} if include_raw else {},
                         references=[reference] if reference else [],
                         reference_files={reference["local_path"]: reference_content}
                         if reference and reference_content is not None else {})

    def test_pinned_source_excerpt_uses_inclusive_line_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                result = reader.read_evidence("06_SOURCE/Code/sample.py", 2, 2)
            self.assertEqual(result["lines"], [
                {"line": 2, "text": "beta"}, {"line": 3, "text": "gamma"}])

    def test_source_id_resolves_pinned_path_and_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                result = reader.read_evidence("source.sample", 1, 1)
            self.assertEqual(result["path"], self.SOURCE)
            self.assertEqual(result["sha256"], hashlib.sha256(b"alpha\nbeta\ngamma\n").hexdigest())

    def test_source_rejects_invalid_line_ranges_and_changed_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                for start, count in ((0, 1), (1, 0), (1, 121), (4, 1)):
                    with self.subTest(start=start, count=count), self.assertRaises(ValueError):
                        reader.read_evidence(self.SOURCE, start, count)
                (root / self.SOURCE).write_text("changed\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Evidence hash") as raised:
                    reader.read_evidence(self.SOURCE)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "SOURCE_HASH_MISMATCH")

    def test_reference_uses_registry_filename_and_pinned_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, engine = base / "vault", base / "engine"
            relative = "engine/algorithms/sample-reference.md"
            target = engine / relative
            target.parent.mkdir(parents=True)
            content = b"first\nsecond\nthird\n"
            target.write_bytes(content)
            reference = {"id": "reference.sample", "repository_relative_path": relative,
                         "local_path": "06_SOURCE/Code/" + relative,
                         "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                         "version": "sample"}
            self.make_vault(root, reference=reference, reference_content=content)
            with plugin_reader(root, engine_root=engine) as reader:
                result = reader.read_algorithm_reference_evidence("reference.sample", 2, 2)
                self.assertEqual([row["text"] for row in result["lines"]], ["second", "third"])
                self.assertEqual(result["version"], "sample")
                with self.assertRaises(ValueError):
                    reader.read_algorithm_reference_evidence("reference.missing")
                target.write_bytes(b"tampered\n")
                with self.assertRaisesRegex(ValueError, "identity"):
                    reader.read_algorithm_reference_evidence("reference.sample")

    def test_dataset_and_inclusive_raw_window_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                dataset = reader.get_dataset("data.sample")
                self.assertTrue(dataset["raw_present"])
                self.assertEqual(dataset["raw_bytes"], len((root / self.RAW).read_bytes()))
                metadata = reader.get_window("data.window")
                self.assertTrue(metadata["data_available"])
                self.assertNotIn("rows", metadata)
                selected = reader.get_window("data.window", include_rows=True,
                                             start_epoch=20, end_epoch=30)
                self.assertEqual([row["time"] for row in selected["rows"]], [20, 30])
                self.assertEqual(selected["requested_range"], [20, 30])
                exact = reader.get_window("data.window", include_rows=True,
                                          start_epoch=10, end_epoch=10)
                self.assertEqual([row["time"] for row in exact["rows"]], [10])
                upper = reader.get_window("data.window", include_rows=True,
                                          start_epoch=40, end_epoch=40)
                self.assertEqual([row["time"] for row in upper["rows"]], [40])
                empty = reader.get_window("data.window", include_rows=True,
                                          start_epoch=21, end_epoch=29)
                self.assertEqual(empty["rows"], [])

    def test_raw_cap_truncation_and_invalid_ranges(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                limited = reader.get_window("data.window", include_rows=True, limit=2)
                self.assertEqual([row["time"] for row in limited["rows"]], [10, 20])
                self.assertTrue(limited["truncated"])
                for options in ({"start_epoch": 40, "end_epoch": 20},
                                {"start_epoch": 9, "end_epoch": 20},
                                {"start_epoch": True}, {"end_epoch": 41}):
                    with self.subTest(options=options), self.assertRaisesRegex(ValueError, "time range"):
                        reader.get_window("data.window", include_rows=True, **options)
                with self.assertRaises(ValueError) as raised:
                    reader.get_window("data.window", include_rows=True,
                                      start_epoch=40, end_epoch=20)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "INVALID_TIME_RANGE")
                with self.assertRaises(ValueError):
                    reader.get_window("data.window", start_epoch=20)
                for limit in (0, 1001, True):
                    with self.subTest(limit=limit), self.assertRaises(ValueError):
                        reader.get_window("data.window", include_rows=True, limit=limit)

    def test_missing_raw_degrades_only_data_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root, include_raw=False)
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("source.sample")["id"], "source.sample")
                self.assertEqual(reader.read_evidence("source.sample")["path"], self.SOURCE)
                self.assertFalse(reader.get_dataset("data.sample")["raw_present"])
                result = reader.get_window("data.window", include_rows=True)
                self.assertEqual(result["reason"], "vault_raw_unavailable")
                self.assertEqual(result["rows"], [])

    def test_streamed_raw_rejects_duplicate_keys_at_every_depth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            invalid_rows = (
                b'[{"time":10,"time":20}]',
                b'[{"time":10,"details":{"value":1,"value":2}}]',
            )
            with plugin_reader(root) as reader:
                for content in invalid_rows:
                    with self.subTest(content=content):
                        (root / self.RAW).write_bytes(content)
                        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                            reader.get_window("data.window", include_rows=True)
