"""Reject generic trusted-JSON and whole-frontmatter integrity drift."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault, write_entity_note
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class CompleteMetadataIntegrityTests(unittest.TestCase):
    def sample(self, **fields):
        return EntitySpec("system.sample", "00_SYSTEM/Sample.md", "system", "active",
                          "canonical", "Sample", "Synthetic metadata only.", fields)

    def test_added_removed_nested_and_type_changed_note_metadata_is_rejected(self):
        changes = ({"valid_for_reasoning": 1, "evidence_basis": ["captured"]},
                   {"valid_for_reasoning": True},
                   {"valid_for_reasoning": True, "evidence_basis": ["changed"]},
                   {"valid_for_reasoning": True, "evidence_basis": ["captured"], "version": "new"})
        for fields in changes:
            with self.subTest(fields=fields), TemporaryDirectory() as temporary:
                root = Path(temporary)
                build_fake_vault(root, [self.sample(valid_for_reasoning=True, evidence_basis=["captured"])])
                with plugin_reader(root) as reader:
                    self.assertTrue(reader.verify_package("knowledge")["ok"])
                    write_entity_note(root, self.sample(**fields))
                    before = snapshot_files([root])
                    with self.assertRaises(ValueError) as caught:
                        reader.get_entity("system.sample")
                    self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "INDEX_STALE")
                    self.assertFalse(reader.verify_package("knowledge")["ok"])
                    assert_unchanged(before, snapshot_files([root]))

    def test_index_only_extra_and_removed_fields_are_rejected(self):
        for operation in ("add", "remove"):
            with self.subTest(operation=operation), TemporaryDirectory() as temporary:
                root = Path(temporary)
                build_fake_vault(root, [self.sample(evidence_basis=["captured"])])
                with plugin_reader(root) as reader:
                    index_path = root / "_INDEX/entities.json"
                    index = json.loads(index_path.read_text(encoding="utf-8"))
                    row = index["entities"]["system.sample"]
                    if operation == "add":
                        row["version"] = "fabricated"
                    else:
                        del row["evidence_basis"]
                    index_path.write_text(json.dumps(index), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        reader.get_entity("system.sample")
                    self.assertFalse(reader.verify_package("knowledge")["ok"])

    def test_matching_index_and_note_cannot_bypass_schema_field_types(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [self.sample(valid_for_reasoning=1)])
            with plugin_reader(root) as reader:
                with self.assertRaises(reader.VaultError) as caught:
                    reader.get_entity("system.sample")
                self.assertEqual(caught.exception.code, "INVALID_VAULT")
                self.assertFalse(reader.verify_package("knowledge")["ok"])

    def test_nested_duplicate_keys_are_rejected_in_all_trusted_json(self):
        paths = ("_INDEX/entities.json", "_INDEX/relations.json", "_INDEX/source-hashes.json",
                 "06_SOURCE/References/registry.json", "_SCHEMA/note.schema.json")
        for relative in paths:
            with self.subTest(relative=relative), TemporaryDirectory() as temporary:
                root = Path(temporary)
                build_fake_vault(root, [self.sample()])
                with plugin_reader(root) as reader:
                    path = root / relative
                    text = path.read_text(encoding="utf-8")
                    path.write_text(text[:-2] + ',"nested":{"key":1,"key":2}}\n', encoding="utf-8")
                    with self.assertRaises(reader.VaultError) as caught:
                        reader.locate_vault()
                    self.assertEqual(caught.exception.code, "INVALID_VAULT")

    def test_non_json_numeric_constants_are_rejected_in_trusted_json(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), TemporaryDirectory() as temporary:
                root = Path(temporary)
                build_fake_vault(root, [self.sample()])
                with plugin_reader(root) as reader:
                    path = root / "_INDEX/entities.json"
                    text = path.read_text(encoding="utf-8")
                    path.write_text(text[:-2] + ',"invalid":' + token + '}\n', encoding="utf-8")
                    with self.assertRaises(reader.VaultError) as caught:
                        reader.locate_vault()
                    self.assertEqual(caught.exception.code, "INVALID_VAULT")

