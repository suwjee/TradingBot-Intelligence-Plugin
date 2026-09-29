"""Maintenance transactions against controlled temporary source captures."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from maintenance import sync_sources
from tests.helpers.fake_vault import build_fake_vault
from tests.helpers.snapshots import assert_unchanged, snapshot_files


class SourceSyncTests(unittest.TestCase):
    def make_capture(self, base, *, failing_builder=False):
        project, vault = base / "project", base / "vault"
        relative = "engine/algorithms/Synthetic.md"
        local = "06_SOURCE/Code/" + relative
        old = b"**Document Version:** `synthetic-1`\n**Target Direction:** `Bullish`\nOld text.\n"
        new = b"**Document Version:** `synthetic-2`\n**Target Direction:** `Bullish`\nNew text.\nNew detail.\n"
        source = project / relative
        source.parent.mkdir(parents=True)
        source.write_bytes(new)
        reference = {"id": "reference.synthetic", "local_path": local,
                     "repository_relative_path": relative, "version": "synthetic-1",
                     "direction": "Bullish", "bytes": len(old),
                     "sha256": hashlib.sha256(old).hexdigest()}
        build_fake_vault(vault, [], references=[reference], reference_files={local: old})
        manifest_path = vault / "_INDEX/source-hashes.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["algorithm_references"][0].update({"line_count": 3, "version": "synthetic-1"})
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        generated = vault / "_GENERATED"
        generated.mkdir()
        for name in ("source-structure.json", "knowledge-model.json"):
            (generated / name).write_text('{"previous":true}\n', encoding="utf-8")
        builder = vault / "_SCHEMA/build_indexes.py"
        builder.write_text(
            "from pathlib import Path\n"
            "root = Path(__file__).resolve().parents[1]\n"
            "for name in ('source-structure.json', 'knowledge-model.json'):\n"
            "    (root / '_GENERATED' / name).write_text('{\"rebuilt\":true}\\n', encoding='utf-8')\n"
            f"raise SystemExit({1 if failing_builder else 0})\n", encoding="utf-8")
        return project, vault, local, new

    @staticmethod
    def tracked_git(project, *args):
        """Keep Git read-only while modeling clean, tracked source paths."""
        if args == ("rev-parse", "HEAD"):
            return b"ffffffffffffffffffffffffffffffffffffffff\n"
        if args[:1] == ("status",):
            return b""
        if args[:1] == ("show",) and (project / args[1].removeprefix("HEAD:")).is_file():
            return (project / args[1].removeprefix("HEAD:")).read_bytes()
        raise AssertionError(f"Unexpected read-only Git request: {args}")

    def invoke(self, project, vault, *, check=False):
        with patch.object(sync_sources, "git", side_effect=self.tracked_git):
            with redirect_stdout(io.StringIO()):
                return sync_sources.sync(project, vault, check)

    def test_check_mode_reports_reference_change_without_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, local, _ = self.make_capture(Path(temporary))
            before = snapshot_files([project, vault])
            result = self.invoke(project, vault, check=True)
            self.assertEqual(result["changed_source_paths"], [local])
            self.assertEqual(result["changed_reference_paths"], ["engine/algorithms/Synthetic.md"])
            self.assertEqual(result["review_state"], "needs_review")
            assert_unchanged(before, snapshot_files([project, vault]))

    def test_reference_only_capture_updates_local_bytes_and_all_identity_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, local, new = self.make_capture(Path(temporary))
            source_before = snapshot_files([project])
            result = self.invoke(project, vault)
            self.assertEqual(result["index_check"], "passed")
            self.assertEqual((vault / local).read_bytes(), new)
            registry = json.loads((vault / "06_SOURCE/References/registry.json").read_text(encoding="utf-8"))
            row = registry["references"][0]
            self.assertEqual(row["sha256"], hashlib.sha256(new).hexdigest())
            self.assertEqual(row["bytes"], len(new))
            self.assertEqual(row["version"], "synthetic-2")
            manifest = json.loads((vault / "_INDEX/source-hashes.json").read_text(encoding="utf-8"))
            pin = manifest["algorithm_references"][0]
            self.assertEqual(pin["sha256"], row["sha256"])
            self.assertEqual(pin["bytes"], len(new))
            self.assertEqual(pin["line_count"], 4)
            self.assertEqual(pin["version"], "synthetic-2")
            registry_pin = next(item for item in manifest["supporting_files"]
                                if item["path"] == "06_SOURCE/References/registry.json")
            registry_bytes = (vault / registry_pin["path"]).read_bytes()
            self.assertEqual(registry_pin["sha256"], hashlib.sha256(registry_bytes).hexdigest())
            assert_unchanged(source_before, snapshot_files([project]))

    def test_failed_builder_rolls_back_generated_files_and_source_capture(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, vault, _, _ = self.make_capture(Path(temporary), failing_builder=True)
            before = snapshot_files([project, vault])
            result = self.invoke(project, vault)
            self.assertEqual(result["index_check"], "failed")
            self.assertEqual(result["review_state"], "needs_review")
            after = snapshot_files([project, vault])
            after = {key: value for key, value in after.items() if not key.endswith("/_INDEX/sync-status.json")}
            assert_unchanged(before, after)
