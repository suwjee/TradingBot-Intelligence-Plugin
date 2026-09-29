"""Pinned Engine mirrors and registered external references."""

import hashlib
import json
import unittest

from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.real_roots import require_real_roots


def manifest_and_registry(roots):
    manifest = json.loads((roots.vault / "_INDEX/source-hashes.json").read_text(encoding="utf-8-sig"))
    registry = json.loads((roots.vault / "06_SOURCE/References/registry.json").read_text(encoding="utf-8-sig"))
    return manifest, registry


def engine_pairs(roots, manifest):
    pairs = []
    prefix = "06_SOURCE/Code/"
    for row in manifest["files"]:
        mirror = row.get("mirror", row.get("source"))
        if not mirror or not mirror.startswith(prefix + "engine/"):
            continue
        relative_engine = mirror.removeprefix(prefix)
        pairs.append((row, roots.vault / mirror, roots.engine / relative_engine))
    return pairs


class RealEngineEvidenceTests(unittest.TestCase):
    def test_all_manifest_engine_mirrors_match_configured_checkout(self):
        roots = require_real_roots(self, engine_required=True)
        manifest, _ = manifest_and_registry(roots)
        pairs = engine_pairs(roots, manifest)
        self.assertTrue(pairs, "Manifest has no captured Engine files")
        for row, mirror, engine in pairs:
            with self.subTest(mirror=row["mirror"]):
                self.assertTrue(mirror.is_file() and engine.is_file())
                self.assertEqual(mirror.read_bytes(), engine.read_bytes())
                data = engine.read_bytes()
                self.assertEqual(len(data), row["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_registered_external_references_have_identity_and_bounded_evidence(self):
        roots = require_real_roots(self, engine_required=True)
        _, registry = manifest_and_registry(roots)
        references = registry["references"]
        self.assertEqual(len(references), 2)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            for row in references:
                with self.subTest(reference=row["id"]):
                    path = (roots.engine / row["repository_relative_path"]).resolve()
                    self.assertTrue(path.is_relative_to(roots.engine) and path.is_file())
                    data = path.read_bytes()
                    self.assertEqual(len(data), row["bytes"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
                    evidence = reader.read_algorithm_reference_evidence(row["id"], 1, 2)
                    self.assertEqual(evidence["reference_id"], row["id"])
                    self.assertEqual(evidence["sha256"], row["sha256"])
                    self.assertGreaterEqual(len(evidence["lines"]), 1)
                    self.assertLessEqual(len(evidence["lines"]), 2)
