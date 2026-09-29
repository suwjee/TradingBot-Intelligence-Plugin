"""Local references are default evidence; external copies are optional checks."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class LocalReferenceContractTests(unittest.TestCase):
    CONTENT = b"# Synthetic current reference\nSecond evidence line\n"
    LOCAL = "06_SOURCE/Code/engine/algorithms/Synthetic_Current.md"
    EXTERNAL = "engine/algorithms/Synthetic_Current.md"

    def make_vault(self, root):
        row = {"id": "synthetic_current", "version": "synthetic", "direction": "Bullish",
               "name": "Synthetic_Current.md", "local_path": self.LOCAL,
               "repository_relative_path": self.EXTERNAL, "bytes": len(self.CONTENT),
               "sha256": hashlib.sha256(self.CONTENT).hexdigest()}
        build_fake_vault(root, [], references=[row], reference_files={self.LOCAL: self.CONTENT})
        return row

    def test_local_reference_reads_without_configured_engine(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            row = self.make_vault(root)
            with plugin_reader(root) as reader:
                result = reader.read_algorithm_reference_evidence(row["id"], 1, 2)
                self.assertEqual(result["sha256"], row["sha256"])
                self.assertEqual([item["text"] for item in result["lines"]], self.CONTENT.decode().splitlines())
                self.assertTrue(reader.verify_package("full-data")["ok"])

    def test_tampered_local_reference_cannot_fall_back_to_matching_external_copy(self):
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, engine = base / "vault", base / "engine"
            row = self.make_vault(root)
            external = engine / self.EXTERNAL
            external.parent.mkdir(parents=True)
            external.write_bytes(self.CONTENT)
            (root / self.LOCAL).write_bytes(b"tampered local\n")
            with plugin_reader(root, engine_root=engine) as reader:
                with self.assertRaises(ValueError) as caught:
                    reader.read_algorithm_reference_evidence(row["id"])
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "REFERENCE_HASH_MISMATCH")
                self.assertFalse(reader.verify_package("full-data")["ok"])

    def test_configured_external_mismatch_is_rejected_despite_valid_local_copy(self):
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, engine = base / "vault", base / "engine"
            row = self.make_vault(root)
            external = engine / self.EXTERNAL
            external.parent.mkdir(parents=True)
            external.write_bytes(b"stale external\n")
            with plugin_reader(root, engine_root=engine) as reader:
                with self.assertRaises(ValueError) as caught:
                    reader.read_algorithm_reference_evidence(row["id"])
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "REFERENCE_HASH_MISMATCH")
                self.assertFalse(reader.verify_package("knowledge")["ok"])

