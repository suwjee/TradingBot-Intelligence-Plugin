"""Knowledge verifier and indexed-note freshness contracts."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault, write_entity_note
from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class VerifierTests(unittest.TestCase):
    FIXTURE = "07_VALIDATION/Fixtures/Sources/source.md"

    def make_case(self, root, *, review=None, mismatch=False, heading="### Sample case", line=1):
        content = (heading + "\nEvidence.\n").encode("utf-8")
        fields = {"source_fixture": self.FIXTURE,
                  "source_fixture_sha256": hashlib.sha256(content if not mismatch else b"other").hexdigest(),
                  "source_fixture_line": line}
        if review:
            fields["source_fixture_review"] = review
        spec = EntitySpec("case.sample", "07_VALIDATION/sample.md", "case", "active",
                          "canonical", "Sample case", "Case body.", fields)
        build_fake_vault(root, [spec])
        fixture = root / self.FIXTURE
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_bytes(content)
        return fixture

    def test_matching_fixture_hash_passes_without_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_case(root)
            before = snapshot_files([root])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            assert_unchanged(before, snapshot_files([root]))
            self.assertTrue(result["ok"])
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["data_status"], "NOT_RUN")

    def test_undeclared_fixture_hash_mismatch_is_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_case(root, mismatch=True)
            before = snapshot_files([root])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            assert_unchanged(before, snapshot_files([root]))
            self.assertFalse(result["ok"])
            self.assertIn("fixture_source_sha_mismatch:case.sample", result["errors"])

    def test_declared_pending_mismatch_remains_visible_and_checks_line_heading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_case(root, review="pending-manual-review", mismatch=True,
                           heading="### Wrong heading", line=1)
            before = snapshot_files([root])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            assert_unchanged(before, snapshot_files([root]))
            issue = "fixture_source_sha_mismatch:case.sample"
            self.assertIn(issue, result["known_pending"])
            self.assertTrue(any(issue in warning for warning in result["warnings"]))
            self.assertIn("fixture_source_heading_mismatch:case.sample", result["errors"])
            self.assertFalse(result["ok"])

    def test_pending_hash_does_not_hide_invalid_source_line(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_case(root, review="pending-manual-review", mismatch=True, line=99)
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            self.assertIn("fixture_source_line_out_of_range:case.sample", result["errors"])
            self.assertIn("fixture_source_sha_mismatch:case.sample", result["known_pending"])

    def test_pending_review_does_not_hide_missing_fixture_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = self.make_case(root, review="pending-manual-review", mismatch=True)
            fixture.unlink()
            before = snapshot_files([root])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            assert_unchanged(before, snapshot_files([root]))
            self.assertFalse(result["ok"])
            self.assertIn("fixture_source_missing:case.sample", result["errors"])
            self.assertNotIn("fixture_source_sha_mismatch:case.sample", result["known_pending"])

    def test_changed_note_with_new_identity_rejects_stale_index_and_cache(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = EntitySpec("system.sample", "00_SYSTEM/sample.md", "system", "active",
                                  "canonical", "Sample", "Initial body.")
            build_fake_vault(root, [original])
            with plugin_reader(root) as reader:
                self.assertIn("Initial body.", reader.get_entity("system.sample")["content"])
                changed = EntitySpec("system.sample", original.file, "system", "pending",
                                     "non-canonical", "Changed", "A longer replacement body.")
                write_entity_note(root, changed)
                with self.assertRaisesRegex(ValueError, "Stale entity index"):
                    reader.get_entity("system.sample")
