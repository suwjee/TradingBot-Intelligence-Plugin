"""Portable reader checks; run with Python's built-in unittest."""
from __future__ import annotations

import re
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import vault_reader as reader
import vault_cli


class VaultReaderTests(unittest.TestCase):
    def test_cli_verify_exits_nonzero_for_incomplete_inventory(self) -> None:
        output = StringIO()
        with patch("sys.argv", ["vault_cli.py", "verify"]), \
                patch.object(vault_cli.reader, "verify_package", return_value={"ok": False}), \
                redirect_stdout(output):
            code = vault_cli.main()
        self.assertEqual(code, 1)

    def test_stale_index_cannot_mislabel_a_note(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            note = root / "04_ALGORITHMS/Order/Order-A.md"
            note.parent.mkdir(parents=True)
            note.write_text('---\nid: "algorithm.order.a"\ntype: "algorithm"\nstatus: "pending"\n'
                            'authority: "non-canonical"\ntitle: "Order_A"\n---\n\n# Order_A\n',
                            encoding="utf-8")
            (index / "entities.json").write_text(json.dumps({"entities": {"algorithm.order.a": {
                "file": "04_ALGORITHMS/Order/Order-A.md", "type": "algorithm",
                "status": "active", "authority": "empirical", "title": "Order_A"}}}), encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "Stale entity index"):
                    reader.get_entity("algorithm.order.a")
                with self.assertRaisesRegex(ValueError, "Stale entity index"):
                    reader.search("Order_A")

    def test_verify_reports_broken_relation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            note = root / "00_SYSTEM/AUTHORITY_MODEL.md"
            note.parent.mkdir(parents=True)
            note.write_text('---\nid: "system.authority"\ntype: "system"\nstatus: "canonical"\n'
                            'authority: "normative"\ntitle: "Authority"\n---\n\n# Authority\n',
                            encoding="utf-8")
            (index / "entities.json").write_text(json.dumps({"entities": {"system.authority": {
                "file": "00_SYSTEM/AUTHORITY_MODEL.md", "type": "system",
                "status": "canonical", "authority": "normative", "title": "Authority"}}}), encoding="utf-8")
            (index / "relations.json").write_text(json.dumps({"relations": [
                {"from": "system.authority", "type": "relates_to", "to": "missing.entity"}]}), encoding="utf-8")
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [], "algorithm_references": [], "supporting_files": []}), encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                result = reader.verify_package()
            self.assertFalse(result["ok"])
            self.assertIn("_INDEX/relations.json", result["failures"])

    def test_verify_rejects_missing_reference_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            note = root / "02_MARKET_MODEL/Crossing.md"
            note.parent.mkdir(parents=True)
            note.write_text('---\nid: "market.crossing"\ntype: "market"\nstatus: "canonical"\n'
                            'authority: "normative"\ntitle: "Crossing"\n---\n\n# Crossing\n',
                            encoding="utf-8")
            (index / "entities.json").write_text(json.dumps({"entities": {"market.crossing": {
                "file": "02_MARKET_MODEL/Crossing.md", "type": "market",
                "status": "canonical", "authority": "normative", "title": "Crossing"}}}), encoding="utf-8")
            (index / "relations.json").write_text(json.dumps({"relations": []}), encoding="utf-8")
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [], "algorithm_references": [], "supporting_files": []}), encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                result = reader.verify_package()
            self.assertFalse(result["ok"])
            self.assertIn("reference_registry_invalid", result["failures"])

    def test_verify_rejects_unpinned_source_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            (index / "entities.json").write_text(json.dumps({"entities": {}}), encoding="utf-8")
            (index / "relations.json").write_text(json.dumps({"relations": []}), encoding="utf-8")
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [], "algorithm_references": [], "supporting_files": []}), encoding="utf-8")
            unpinned = root / "06_SOURCE/Code/engine/pipeline/unpinned.py"
            unpinned.parent.mkdir(parents=True)
            unpinned.write_text("pass\n", encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                result = reader.verify_package()
            self.assertFalse(result["ok"])
            self.assertIn("06_SOURCE/Code/engine/pipeline/unpinned.py", result["failures"])

    def test_verify_reports_unregistered_physical_raw(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            (index / "entities.json").write_text(json.dumps({"entities": {}}), encoding="utf-8")
            (index / "relations.json").write_text(json.dumps({"relations": []}), encoding="utf-8")
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [], "algorithm_references": [], "supporting_files": []}), encoding="utf-8")
            raw = root / "08_DATA/Raw/XAUUSD/extra.json"
            raw.parent.mkdir(parents=True)
            raw.write_text("[]\n", encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                result = reader.verify_package()
            self.assertIn("incomplete_engine_source_coverage", result["failures"])
            self.assertFalse(result["inventory_complete"])
            self.assertFalse(result["ok"])
            self.assertEqual(result["unregistered_raw_files"], ["08_DATA/Raw/XAUUSD/extra.json"])

    def test_verify_reports_corrupt_registered_raw_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "_INDEX"
            index.mkdir()
            raw_path = "08_DATA/Raw/XAUUSD/broken.json"
            raw = root / raw_path
            raw.parent.mkdir(parents=True)
            raw.write_text("{broken", encoding="utf-8")
            entities = {}
            for entity_id, kind, filename in (
                ("data.dataset_00000000", "dataset", "Dataset.md"),
                ("data.window_00000000", "window", "Window.md"),
            ):
                relative = f"08_DATA/Datasets/{filename}"
                note = root / relative
                note.parent.mkdir(parents=True, exist_ok=True)
                metadata = {"id": entity_id, "type": "data", "status": "active",
                            "authority": "empirical", "title": filename,
                            "data_kind": kind, "raw_path": raw_path,
                            "raw_bytes": raw.stat().st_size, "raw_sha256": "0" * 64,
                            "first_epoch": 1, "last_epoch": 2, "row_count": 1}
                note.write_text("---\n" + "".join(
                    f"{key}: {json.dumps(value)}\n" for key, value in metadata.items()
                ) + "---\n\n# RAW\n", encoding="utf-8")
                entities[entity_id] = {"file": relative, "type": "data",
                                       "status": "active", "authority": "empirical",
                                       "title": filename}
            (index / "entities.json").write_text(json.dumps({"entities": entities}), encoding="utf-8")
            (index / "relations.json").write_text(json.dumps({"relations": []}), encoding="utf-8")
            (index / "source-hashes.json").write_text(json.dumps({
                "files": [], "algorithm_references": [], "supporting_files": []}), encoding="utf-8")
            with patch.object(reader, "ROOT", root):
                result = reader.verify_package()
            self.assertFalse(result["verified_pins_ok"])
            self.assertIn(raw_path, result["failures"])
            self.assertIn("data.window_00000000", result["failures"])

    def test_rule_retrieval_and_relations(self) -> None:
        self.assertIn("algorithm.order.a", [row["id"] for row in reader.search("Order_A", 20)])
        note = reader.get_entity("algorithm.order.a")
        self.assertEqual(note["authority"], "normative")
        self.assertIn("Order_A", note["content"])
        self.assertTrue(reader.relations("algorithm.order.a")["outgoing"])
        self.assertEqual(reader.get_entity("algorithm.stopall")["authority"], "non-canonical")

    def test_known_invalid_order_routes_are_explicitly_quarantined(self) -> None:
        self.assertNotIn("algorithm.order.b", [row["id"] for row in reader.search("Order_B", 25)])
        explicit = reader.search("Order_B", 25, include_quarantined=True)
        self.assertIn("algorithm.order.b", [row["id"] for row in explicit])
        note = reader.get_entity("algorithm.order.b")
        self.assertEqual(note["status"], "pending-fix")
        self.assertFalse(note["valid_for_reasoning"])
        self.assertIn("Known-invalid", note["warning"])
        self.assertEqual(reader.search("OrderAudit"), [])
        with self.assertRaises(ValueError):
            reader.get_entity("algorithm.orderaudit")
        self.assertEqual(reader.relations("algorithm.order.b")["outgoing"], [])
        self.assertTrue(reader.relations("algorithm.order.b", include_quarantined=True)["outgoing"])

    def test_optional_reference_requires_exact_hash(self) -> None:
        from unittest.mock import patch
        import tempfile
        import hashlib
        from pathlib import Path
        with patch.dict("os.environ", {"TRADINGBOT_ENGINE_ROOT": ""}):
            with self.assertRaisesRegex(ValueError, "TRADINGBOT_ENGINE_ROOT"):
                reader.read_algorithm_reference_evidence("bullish_hpzr6", 29, 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "engine/algorithms/ref.md"
            path.parent.mkdir(parents=True)
            payload = b"accepted Order_A\ncurrent Order_B\n"
            path.write_bytes(payload)
            registry = {"references": [{"id": "test_ref", "repository_relative_path": "engine/algorithms/ref.md",
                                        "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                                        "version": "test", "authority_scope": "diagnostic",
                                        "known_invalid_sections": ["Order_B"], "inactive_sections": []}]}
            with patch.dict("os.environ", {"TRADINGBOT_ENGINE_ROOT": temporary}):
                with patch.object(reader, "_reference_registry", return_value=registry):
                    evidence = reader.read_algorithm_reference_evidence("test_ref", 1, 1)
                    self.assertIn("Order_A", evidence["lines"][0]["text"])
                    path.write_bytes(b"changed\n")
                    with self.assertRaisesRegex(ValueError, "identity differs"):
                        reader.read_algorithm_reference_evidence("test_ref", 1, 1)

    def test_reference_registry_and_mixed_source_are_labeled(self) -> None:
        registry = reader._reference_registry()
        self.assertEqual({row["id"] for row in registry["references"]},
                         {"bullish_hpzr6", "bearish_hpzr6"})
        evidence = reader.read_evidence("06_SOURCE/Code/engine/pipeline/e_zone_detector.py", 499, 1)
        self.assertEqual(evidence["authority"], "executable")
        self.assertIn("known-invalid", evidence["warning"])

    def test_evidence_is_local_and_hash_pinned(self) -> None:
        evidence = reader.read_evidence("06_SOURCE/Code/engine/pipeline/reaction_engine.py", 2250, 9)
        self.assertEqual(evidence["start_line"], 2250)
        self.assertTrue(any("analysis.extreme" in row["text"] for row in evidence["lines"]))
        with self.assertRaises(ValueError):
            reader.read_evidence("06_SOURCE/Code/../../_INDEX/entities.json")
        with self.assertRaises(ValueError):
            reader.read_evidence("C:" + "/TradingBot/engine/pipeline/reaction_engine.py")

    def test_every_registered_raw_is_inside_vault(self) -> None:
        ids = [ident for ident in reader._entities()
               if re.fullmatch(r"data\.dataset_[0-9a-f]{8}", ident)]
        self.assertEqual(len(ids), 7)
        for ident in ids:
            record = reader.get_dataset(ident)
            relative = record["metadata"]["raw_path"]
            self.assertTrue(relative.startswith("08_DATA/Raw/"))
            self.assertTrue((reader.ROOT / relative).is_file())
            self.assertTrue(record["raw_present"])

    def test_captured_evidence_hashes(self) -> None:
        result = reader.verify_package()
        self.assertTrue(result["verified_pins_ok"], result["failures"])
        self.assertEqual(result["ok"], result["inventory_complete"])
        self.assertEqual(result["verified_datasets"], 7)
        self.assertEqual(result["verified_windows"], 3)

    def test_knowledge_mode_does_not_require_raw_bytes(self) -> None:
        original_is_file = Path.is_file
        original_read_bytes = Path.read_bytes

        def unavailable_raw(path: Path) -> bool:
            if "08_DATA/Raw/" in path.as_posix() and path.suffix == ".json":
                return False
            return original_is_file(path)

        def reject_raw_read(path: Path) -> bytes:
            if "08_DATA/Raw/" in path.as_posix() and path.suffix == ".json":
                raise AssertionError("RAW bytes were read in knowledge mode")
            return original_read_bytes(path)

        with patch.object(Path, "is_file", unavailable_raw), \
                patch.object(Path, "read_bytes", reject_raw_read), \
                patch.object(reader, "get_dataset", side_effect=AssertionError("RAW dataset read")), \
                patch.object(reader, "get_window", side_effect=AssertionError("RAW window read")):
            result = reader.verify_package(mode="knowledge")
        self.assertTrue(result["ok"], result["failures"])
        self.assertEqual(result["data_status"], "NOT_RUN")
        self.assertIsNone(result["inventory_complete"])
        self.assertEqual(result["registered_datasets"], 7)
        self.assertEqual(result["registered_windows"], 3)

    def test_retained_window_is_not_a_physical_dataset(self) -> None:
        window = reader.get_entity("data.window_0291455b")
        self.assertIn("1788824908", window["content"])
        metadata = reader.get_window("data.window_0291455b")["metadata"]
        self.assertEqual(metadata["row_count"], 161376)
        with self.assertRaises(ValueError):
            reader.get_dataset("data.window_0291455b")

    def test_no_machine_specific_paths_in_package_text(self) -> None:
        pattern = re.compile(r"[A-Za-z]:[\\/](?!/)|/" + "Users/|/" + "home/|" + r"\\\\" + "vmware", re.I)
        for path in reader.ROOT.rglob("*"):
            if not path.is_file() or any(part in {".git", ".obsidian"} for part in path.parts):
                continue
            if path.suffix not in {".md", ".py", ".js", ".json"} or "08_DATA/Raw" in path.as_posix() and not path.name.endswith(".meta.json"):
                continue
            content = path.read_text(encoding="utf-8-sig")
            self.assertIsNone(pattern.search(content), str(path))


if __name__ == "__main__":
    unittest.main()
