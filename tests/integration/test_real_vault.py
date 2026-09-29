"""Live Vault retrieval and graph contracts."""

import json
import hashlib
import re
import unittest

from tests.helpers.real_roots import require_real_roots
from tests.helpers.plugin_runtime import plugin_reader


def load_index(roots):
    path = roots.vault / "_INDEX/entities.json"
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON object key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_pairs)["entities"]


def frontmatter(content):
    header = content.split("\n---\n", 1)[0][4:]
    return {key: json.loads(value.strip()) for key, value in
            (line.split(":", 1) for line in header.splitlines() if line.strip())}


class RealVaultTests(unittest.TestCase):
    def test_required_vault_root_is_checked_before_live_reads(self):
        roots = require_real_roots(self)
        self.assertTrue(roots.vault.is_dir())

    def test_current_order_metadata_and_default_retrieval(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            for entity_id in ("algorithm.order.a", "algorithm.order.b"):
                self.assertIn(entity_id, entities)
                result = reader.get_entity(entity_id)
                metadata = frontmatter(result["content"])
                self.assertEqual(metadata["status"], "active")
                self.assertEqual(metadata["authority"], "executable")
                self.assertIsNone(result["warning"])
                self.assertIn(entity_id, [hit["id"] for hit in reader.search(entity_id, limit=25)])
                self.assertEqual({key: value for key, value in entities[entity_id].items()
                                  if key not in {"file", "content_sha256", "content_bytes"}}, metadata)
                note_bytes = (roots.vault / entities[entity_id]["file"]).read_bytes()
                self.assertEqual(hashlib.sha256(note_bytes).hexdigest(), result["content_sha256"])
                self.assertEqual(len(note_bytes), result["content_bytes"])
            self.assertNotIn("algorithm.order.c", entities)

    def test_orderaudit_is_first_class_and_pinned_source_is_readable(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        self.assertIn("algorithm.orderaudit", entities)
        manifest = json.loads((roots.vault / "_INDEX/source-hashes.json").read_text(encoding="utf-8-sig"))
        candidates = [row.get("mirror", row.get("source", row.get("path")))
                      for row in manifest["files"] + manifest.get("algorithm_references", [])
                      + manifest.get("supporting_files", [])]
        matching = [path for path in candidates if path and path.startswith("06_SOURCE/Code/")
                    and "order_audit" in (roots.vault / path).read_text(encoding="utf-8-sig").lower()]
        self.assertTrue(matching, "No pinned source contains order_audit")
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            audit = reader.get_entity("algorithm.orderaudit")
            self.assertEqual(audit["status"], "active")
            self.assertIsNone(audit["warning"])
            self.assertIn("algorithm.orderaudit", [row["id"] for row in reader.search("algorithm.orderaudit", limit=25)])
            self.assertEqual(reader.read_evidence(matching[0], 1, 1)["path"], matching[0])

    def test_type3_metadata_relations_and_evidence_linkage(self):
        roots = require_real_roots(self)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            result = reader.get_entity("behavior.s.blue.type3")
            metadata = frontmatter(result["content"])
            for key in ("status", "authority", "title"):
                self.assertEqual(result[key], metadata[key])
            self.assertEqual(metadata["id"], result["id"])
            self.assertTrue(metadata.get("implemented_by"))
            self.assertIn("algorithm.s.type3", metadata["related_entities"])
            self.assertTrue(metadata.get("source_reference"))
            graph = reader.relations(result["id"], include_quarantined=True)
            outgoing = {(edge["type"], edge["to"]) for edge in graph["outgoing"]}
            for field in ("related_entities", "implemented_by"):
                for target in metadata.get(field, []):
                    self.assertIn(("relates_to" if field == "related_entities" else field, target), outgoing)
                    self.assertEqual(reader.get_entity(target)["id"], target)
            for anchor in metadata["source_reference"]:
                match = re.fullmatch(r"([^#]+)(?:#L([1-9][0-9]*))?", anchor)
                self.assertIsNotNone(match, anchor)
                self.assertEqual(reader.read_evidence(match[1], int(match[2] or 1), 1)["path"], match[1])

    def test_index_graph_and_source_anchors_are_consistent(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        edges = json.loads((roots.vault / "_INDEX/relations.json").read_text(encoding="utf-8-sig"))["relations"]
        triplets = [(edge["from"], edge["type"], edge["to"]) for edge in edges]
        self.assertEqual(len(triplets), len(set(triplets)))
        for source, _, target in triplets:
            self.assertIn(source, entities)
            self.assertIn(target, entities)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            for entity_id, row in entities.items():
                relative = row["file"]
                path = (roots.vault / relative).resolve()
                self.assertTrue(path.is_relative_to(roots.vault) and path.is_file(), entity_id)
                metadata = frontmatter(reader.get_entity(entity_id)["content"])
                self.assertEqual({key: value for key, value in row.items()
                                  if key not in {"file", "content_sha256", "content_bytes"}}, metadata)
                note_bytes = path.read_bytes()
                self.assertEqual(hashlib.sha256(note_bytes).hexdigest(), row["content_sha256"])
                self.assertEqual(len(note_bytes), row["content_bytes"])
                if row["type"] == "source":
                    for anchor in metadata.get("source_refs", []) + metadata.get("source_reference", []):
                        match = re.fullmatch(r"([^#]+)(?:#L([1-9][0-9]*))?", anchor)
                        self.assertIsNotNone(match, anchor)
                        source_path = (roots.vault / match[1]).resolve()
                        self.assertTrue(source_path.is_relative_to(roots.vault) and source_path.is_file())
                        if match[2]:
                            self.assertLessEqual(int(match[2]), len(source_path.read_text(encoding="utf-8-sig").splitlines()))
            verified = reader.verify_package("knowledge")
            self.assertEqual(verified["errors"], [], verified["errors"])
            self.assertIsInstance(verified["known_pending"], list)
