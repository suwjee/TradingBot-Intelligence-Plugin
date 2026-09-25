"""Exercise committed-only sync against an isolated Git repository."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from sync_sources import sync
from install_hook import install


class SyncSourcesTests(unittest.TestCase):
    def test_note_write_failure_rolls_back_source_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            vault = base / "vault"
            project.mkdir()
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"def rule():\n    return 2\n")
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Sync Test"), ("user.email", "sync@example.invalid")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "new rule"], check=True)
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            original = b"def rule():\n    return 1\n"
            snapshot.write_bytes(original)
            index = vault / "_INDEX"
            index.mkdir()
            manifest = {"files": [{"source": relative, "mirror": relative,
                                    "sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original)}],
                        "algorithm_references": [], "supporting_files": []}
            manifest_file = index / "source-hashes.json"
            original_manifest = json.dumps(manifest)
            manifest_file.write_text(original_manifest, encoding="utf-8")
            note = vault / "06_SOURCE/Modules/rule.md"
            note.parent.mkdir(parents=True)
            note.write_text('---\nsource_path: "' + relative + '"\nsha256: "old"\n---\n',
                            encoding="utf-8")
            builder = vault / "_SCHEMA/build_indexes.py"
            builder.parent.mkdir()
            builder.write_text("print('OK')\n", encoding="utf-8")
            with patch("sync_sources.write_note", side_effect=OSError("simulated note failure")):
                with self.assertRaisesRegex(OSError, "simulated note failure"):
                    sync(project, vault)
            self.assertEqual(snapshot.read_bytes(), original)
            self.assertEqual(manifest_file.read_text(encoding="utf-8"), original_manifest)

    def test_failed_index_build_rolls_back_source_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            vault = base / "vault"
            project.mkdir()
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"def rule():\n    return 2\n")
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Sync Test"), ("user.email", "sync@example.invalid")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "new rule"], check=True)
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            original = b"def rule():\n    return 1\n"
            snapshot.write_bytes(original)
            index = vault / "_INDEX"
            index.mkdir()
            manifest = {"files": [{"source": relative, "mirror": relative,
                                    "sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original)}],
                        "algorithm_references": [], "supporting_files": []}
            manifest_file = index / "source-hashes.json"
            original_manifest = json.dumps(manifest)
            manifest_file.write_text(original_manifest, encoding="utf-8")
            schema = vault / "_SCHEMA"
            schema.mkdir()
            (schema / "build_indexes.py").write_text(
                "from pathlib import Path\n"
                "(Path(__file__).resolve().parents[1] / '_INDEX/entities.json').write_text('partial')\n"
                "raise SystemExit(3)\n", encoding="utf-8")
            result = sync(project, vault)
            self.assertEqual(result["index_check"], "failed")
            self.assertEqual(result["rolled_back_source_paths"], [relative])
            self.assertEqual(snapshot.read_bytes(), original)
            self.assertEqual(manifest_file.read_text(encoding="utf-8"), original_manifest)
            self.assertFalse((index / "entities.json").exists())

    def test_clean_crlf_worktree_keeps_exact_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            vault = base / "vault"
            project.mkdir()
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            working = b"def rule():\r\n    return 2\r\n"
            source.write_bytes(working)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Sync Test"), ("user.email", "sync@example.invalid"),
                               ("core.autocrlf", "true")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "CRLF source"], check=True)
            committed = subprocess.run(["git", "-C", str(project), "show", "HEAD:engine/pipeline/rule.py"],
                                       capture_output=True, check=True).stdout
            self.assertNotEqual(committed, working)
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            snapshot.write_bytes(working)
            index = vault / "_INDEX"
            index.mkdir()
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [{"source": relative, "mirror": relative,
                           "sha256": hashlib.sha256(working).hexdigest(), "bytes": len(working)}],
                "algorithm_references": [], "supporting_files": []
            }), encoding="utf-8")
            status = sync(project, vault, check=True)
            self.assertEqual(status["changed_source_paths"], [])
            self.assertEqual(status["dirty_worktree_paths"], [])

    def test_excluded_order_route_cannot_reenter_vault_after_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            vault = base / "vault"
            project.mkdir()
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            source.write_text("# Order_B must be rewritten\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Sync Test"), ("user.email", "sync@example.invalid")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "excluded route"], check=True)
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            retained = b"def order_a():\n    return 1\n"
            snapshot.write_bytes(retained)
            index = vault / "_INDEX"
            index.mkdir()
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [{"source": relative, "mirror": relative,
                           "sha256": hashlib.sha256(retained).hexdigest(), "bytes": len(retained)}],
                "algorithm_references": [], "supporting_files": []
            }), encoding="utf-8")
            schema = vault / "_SCHEMA"
            schema.mkdir()
            (schema / "build_indexes.py").write_text("print('OK')\n", encoding="utf-8")
            result = sync(project, vault)
            self.assertEqual(snapshot.read_bytes(), retained)
            self.assertEqual(result["changed_source_paths"], [])
            self.assertEqual(result["blocked_excluded_routes"], [relative])
            self.assertEqual(result["review_state"], "needs_review")

    def test_post_commit_hook_captures_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "with spaces"
            project = base / "project"
            vault = base / "vault"
            project.mkdir(parents=True)
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            committed = b"def rule():\n    return 3\n"
            source.write_bytes(committed)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Hook Test"), ("user.email", "hook@example.invalid")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            old = b"def rule():\n    return 1\n"
            snapshot.write_bytes(old)
            index = vault / "_INDEX"
            index.mkdir()
            manifest = {"files": [{"source": relative, "mirror": relative,
                                    "sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old)}],
                        "algorithm_references": [], "supporting_files": []}
            (index / "source-hashes.json").write_text(json.dumps(manifest), encoding="utf-8")
            schema = vault / "_SCHEMA"
            schema.mkdir()
            (schema / "build_indexes.py").write_text("print('OK')\n", encoding="utf-8")
            hook = install(project, vault)
            self.assertTrue(hook.is_file())
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "capture"], check=True)
            self.assertEqual(snapshot.read_bytes(), committed)
            self.assertEqual(json.loads((index / "sync-status.json").read_text())["index_check"], "passed")

    def test_does_not_replace_dirty_working_source_with_old_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            vault = base / "vault"
            project.mkdir()
            source = project / "engine/pipeline/rule.py"
            source.parent.mkdir(parents=True)
            committed = b"def rule():\n    return 2\n"
            old = b"def rule():\n    return 1\n"
            source.write_bytes(committed)
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            for key, value in (("user.name", "Sync Test"), ("user.email", "sync@example.invalid")):
                subprocess.run(["git", "-C", str(project), "config", key, value], check=True)
            subprocess.run(["git", "-C", str(project), "add", "engine/pipeline/rule.py"], check=True)
            subprocess.run(["git", "-C", str(project), "commit", "-qm", "capture"], check=True)
            source.write_bytes(b"def rule():\n    return 999\n")
            relative = "06_SOURCE/Code/engine/pipeline/rule.py"
            snapshot = vault / relative
            snapshot.parent.mkdir(parents=True)
            snapshot.write_bytes(old)
            index = vault / "_INDEX"
            index.mkdir()
            manifest = {"files": [{"source": relative, "mirror": relative,
                                    "sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old)}],
                        "algorithm_references": [], "supporting_files": []}
            (index / "source-hashes.json").write_text(json.dumps(manifest), encoding="utf-8")
            schema = vault / "_SCHEMA"
            schema.mkdir()
            (schema / "build_indexes.py").write_text("print('OK')\n", encoding="utf-8")
            result = sync(project, vault)
            self.assertEqual(snapshot.read_bytes(), old)
            self.assertEqual(result["review_state"], "needs_review")
            self.assertEqual(result["index_check"], "passed")
            self.assertEqual(result["dirty_worktree_paths"], [relative])
            self.assertEqual(json.loads((index / "source-hashes.json").read_text())["files"][0]["sha256"],
                             hashlib.sha256(old).hexdigest())


if __name__ == "__main__":
    unittest.main()
