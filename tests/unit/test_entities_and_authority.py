"""Entity identity and metadata authority contracts."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def entity(entity_id="concept.sample", file="01_CONCEPT/Sample.md", **changes):
    values = dict(id=entity_id, file=file, type="concept", status="active",
                  authority="canonical", title="Sample", body="Synthetic searchable body.")
    values.update(changes)
    return EntitySpec(**values)


class EntityAuthorityTests(unittest.TestCase):
    def test_stable_id_survives_note_move_and_regenerated_index(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [entity()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("concept.sample")["file"], "01_CONCEPT/Sample.md")
            build_fake_vault(root, [entity(file="01_CONCEPT/Moved.md")])
            with plugin_reader(root) as reader:
                result = reader.get_entity("concept.sample")
                self.assertEqual(result["file"], "01_CONCEPT/Moved.md")
                self.assertEqual(result["id"], "concept.sample")

    def test_missing_entity_has_structured_code(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [entity()])
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as caught:
                    reader.get_entity("concept.missing")
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "ENTITY_NOT_FOUND")

    def test_metadata_quarantine_and_name_independence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [
                entity("concept.quarantined", "01_CONCEPT/Quarantined.md", authority="non-canonical"),
                entity("concept.order-name", "01_CONCEPT/Order_B_Test_Name.md", title="Order_B_Test_Name"),
            ])
            with plugin_reader(root) as reader:
                ids = [row["id"] for row in reader.search("synthetic")]
                self.assertIn("concept.order-name", ids)
                self.assertNotIn("concept.quarantined", ids)
                included = {row["id"]: row for row in reader.search("synthetic", include_quarantined=True)}
                self.assertIsNotNone(included["concept.quarantined"]["warning"])
                self.assertIsNone(included["concept.order-name"]["warning"])

    def test_malformed_and_duplicate_frontmatter_fail_read(self):
        for content in ("No frontmatter\n", "---\nid: \"concept.sample\"\nid: \"concept.sample\"\n---\nBody\n"):
            with self.subTest(content=content[:20]), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [entity()])
                (root / "01_CONCEPT/Sample.md").write_text(content, encoding="utf-8")
                with plugin_reader(root) as reader:
                    with self.assertRaises(ValueError):
                        reader.get_entity("concept.sample")
                    self.assertFalse(reader.verify_package("knowledge")["ok"])

    def test_duplicate_stable_id_is_rejected_by_builder(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "unique IDs"):
                build_fake_vault(Path(directory), [entity(), entity(file="01_CONCEPT/Other.md")])

    def test_duplicate_stable_id_in_raw_index_requires_reader_rejection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [entity()])
            index_path = root / "_INDEX/entities.json"
            with plugin_reader(root) as reader:
                original = json.loads(index_path.read_text(encoding="utf-8"))["entities"]
                row = json.dumps(original["concept.sample"], ensure_ascii=False)
                duplicate = ('{"entities":{"concept.sample":' + row +
                             ',"concept.sample":' + row + '}}')
                index_path.write_text(duplicate, encoding="utf-8")
                with self.assertRaises(reader.VaultError) as caught:
                    reader.locate_vault()
                self.assertEqual(caught.exception.code, "INVALID_VAULT")

    def test_missing_required_metadata_and_stale_changed_note(self):
        for replacement in (None, '"Changed"'):
            with self.subTest(replacement=replacement), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [entity()])
                note = root / "01_CONCEPT/Sample.md"
                original = note.read_text(encoding="utf-8")
                changed = (original.replace('title: "Sample"\n', "") if replacement is None else
                           original.replace('title: "Sample"', f"title: {replacement}"))
                note.write_text(changed, encoding="utf-8")
                with plugin_reader(root) as reader:
                    with self.assertRaises(ValueError) as caught:
                        reader.get_entity("concept.sample")
                    self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "INDEX_STALE")

    def test_unknown_optional_metadata_is_preserved_in_content(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [entity(frontmatter={"future_optional": "kept"})])
            with plugin_reader(root) as reader:
                self.assertIn('future_optional: "kept"', reader.get_entity("concept.sample")["content"])

    def test_generic_future_type_current_source_behavior(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [entity(type="future-type")])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("concept.sample")["type"], "future-type")
                self.assertTrue(reader.verify_package("knowledge")["ok"])


if __name__ == "__main__":
    unittest.main()
