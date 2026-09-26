"""Portable reader checks; run with Python's built-in unittest."""
from __future__ import annotations

import re
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

import vault_reader as reader
import vault_cli


VAULT_ROOT = reader.ROOT
FIXTURE_SOURCE = Path("07_VALIDATION/Fixtures/Sources/TradingBot_Fixtures_Regression_Anchors.md")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copied_vault_without_raw() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    target = Path(temporary.name) / "vault"

    def ignore(directory: str, names: list[str]) -> set[str]:
        relative = Path(directory).resolve().relative_to(VAULT_ROOT)
        blocked = {".git", "_GENERATED", "__pycache__"}
        if relative.parts[:2] == ("08_DATA", "Raw"):
            blocked.update(name for name in names if name.endswith(".json"))
        return blocked.intersection(names)

    shutil.copytree(VAULT_ROOT, target, ignore=ignore)
    return temporary, target


def copied_vault() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temporary = tempfile.TemporaryDirectory()
    target = Path(temporary.name) / "vault"

    def ignore(directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".git", "_GENERATED", "__pycache__"}}

    shutil.copytree(VAULT_ROOT, target, ignore=ignore)
    return temporary, target


def fixture_notes(root: Path) -> list[Path]:
    return sorted(
        path
        for path in (root / "07_VALIDATION/Fixtures").rglob("*.md")
        if "source_fixture_sha256:" in path.read_text(encoding="utf-8-sig")
    )


def fixture_hashes(notes: list[Path]) -> dict[Path, str]:
    return {
        path: next(
            line.split(": ", 1)[1]
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.startswith("source_fixture_sha256:")
        )
        for path in notes
    }


def mark_pending_manual_review(notes: list[Path]) -> None:
    for path in notes:
        content = path.read_text(encoding="utf-8-sig")
        path.write_text(
            content.replace(
                "source_fixture_sha256:",
                "source_fixture_review: \"pending-manual-review\"\nsource_fixture_sha256:",
                1,
            ),
            encoding="utf-8",
        )


def replace_frontmatter_value(path: Path, field: str, value: str) -> None:
    content = path.read_text(encoding="utf-8-sig")
    updated, count = re.subn(
        rf"(?m)^{re.escape(field)}: .+$",
        f"{field}: {value}",
        content,
        count=1,
    )
    if count != 1:
        raise AssertionError(f"Missing frontmatter field: {field}")
    path.write_text(updated, encoding="utf-8")


def mutate_fixture_source_and_manifest(root: Path) -> None:
    source = root / FIXTURE_SOURCE
    source.write_text(
        source.read_text(encoding="utf-8-sig")
        + "\n<!-- isolated fixture-source mutation for verification -->\n",
        encoding="utf-8",
    )
    manifest_path = root / "_INDEX/source-hashes.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    evidence = next(
        row
        for row in manifest["supporting_files"]
        if row["path"] == FIXTURE_SOURCE.as_posix()
    )
    evidence["sha256"] = sha256(source)
    evidence["bytes"] = source.stat().st_size
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


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

    def test_unregistered_physical_raw_is_reported_as_an_error(self) -> None:
        temporary, root = copied_vault()
        self.addCleanup(temporary.cleanup)
        raw = root / "08_DATA/Raw/XAUUSD/extra.json"
        raw.write_text("[]\n", encoding="utf-8")
        sidecar = root / "08_DATA/Raw/XAUUSD/extra.json.meta.json"
        sidecar.write_text("{}\n", encoding="utf-8")

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package()

        expected_raw = "unregistered_raw_file:08_DATA/Raw/XAUUSD/extra.json"
        expected_sidecar = "unregistered_raw_sidecar:08_DATA/Raw/XAUUSD/extra.json.meta.json"
        self.assertFalse(result["ok"])
        self.assertIn(expected_raw, result["errors"])
        self.assertIn(expected_sidecar, result["errors"])
        self.assertEqual(result["failures"], result["errors"])

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

    def test_order_c_is_hidden_by_default_and_available_explicitly(self) -> None:
        self.assertNotIn("algorithm.order.c", [row["id"] for row in reader.search("Order_C", 25)])
        explicit = reader.search("Order_C", 25, include_quarantined=True)
        self.assertIn("algorithm.order.c", [row["id"] for row in explicit])
        note = reader.get_entity("algorithm.order.c")
        self.assertEqual(note["status"], "pending-fix")
        self.assertFalse(note["valid_for_reasoning"])
        self.assertIn("Known-invalid", note["warning"])

    def test_undeclared_fixture_source_hash_mismatch_is_an_error(self) -> None:
        temporary, root = copied_vault_without_raw()
        self.addCleanup(temporary.cleanup)
        mutate_fixture_source_and_manifest(root)

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package(mode="knowledge")

        self.assertFalse(result["ok"])
        self.assertTrue(result["errors"])
        self.assertEqual(result["failures"], result["errors"])
        self.assertTrue(any(item.startswith("fixture_source_sha_mismatch:") for item in result["errors"]))

    def test_declared_fixture_source_hash_mismatch_is_known_pending_without_sha_rewrite(self) -> None:
        temporary, root = copied_vault_without_raw()
        self.addCleanup(temporary.cleanup)
        notes = fixture_notes(root)
        original_hashes = fixture_hashes(notes)
        self.assertEqual(22, len(notes))
        mark_pending_manual_review(notes)
        mutate_fixture_source_and_manifest(root)

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package(mode="knowledge")

        self.assertTrue(result["ok"])
        self.assertEqual([], result["errors"])
        self.assertTrue(result["warnings"])
        self.assertEqual(22, len(result["known_pending"]))
        self.assertFalse(result["verified_pins_ok"])
        self.assertEqual(original_hashes, fixture_hashes(notes))

    def test_declared_fixture_source_hash_mismatch_keeps_line_check_strict(self) -> None:
        temporary, root = copied_vault_without_raw()
        self.addCleanup(temporary.cleanup)
        notes = fixture_notes(root)
        mark_pending_manual_review(notes)
        note = notes[0]
        fixture_id = re.search(r'(?m)^id: "([^"]+)"$', note.read_text(encoding="utf-8-sig")).group(1)
        replace_frontmatter_value(note, "source_fixture_line", "999999")
        mutate_fixture_source_and_manifest(root)

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package(mode="knowledge")

        self.assertFalse(result["ok"])
        self.assertTrue(result["known_pending"])
        self.assertIn(f"fixture_source_line_out_of_range:{fixture_id}", result["errors"])

    def test_declared_fixture_source_hash_mismatch_keeps_heading_check_strict(self) -> None:
        temporary, root = copied_vault_without_raw()
        self.addCleanup(temporary.cleanup)
        notes = fixture_notes(root)
        mark_pending_manual_review(notes)
        note = notes[0]
        fixture_id = re.search(r'(?m)^id: "([^"]+)"$', note.read_text(encoding="utf-8-sig")).group(1)
        replace_frontmatter_value(note, "source_fixture_line", "1")
        mutate_fixture_source_and_manifest(root)

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package(mode="knowledge")

        self.assertFalse(result["ok"])
        self.assertTrue(result["known_pending"])
        self.assertIn(f"fixture_source_heading_mismatch:{fixture_id}", result["errors"])

    def test_order_contract_metadata_tampering_is_rejected(self) -> None:
        contracts = (
            (
                "algorithm.order.a",
                "04_ALGORITHMS/Order/Order-A.md",
                (
                    ("valid_for_validation", "false"),
                    ("valid_for_regression_baseline", "false"),
                ),
            ),
            (
                "algorithm.order.b",
                "04_ALGORITHMS/Order/Order-B.md",
                (
                    ("valid_for_validation", "true"),
                    ("valid_for_regression_baseline", "true"),
                    ("rewrite_required", "false"),
                ),
            ),
            (
                "algorithm.order.c",
                "04_ALGORITHMS/Order/Order-C.md",
                (
                    ("valid_for_validation", "true"),
                    ("valid_for_regression_baseline", "true"),
                    ("rewrite_required", "false"),
                ),
            ),
        )
        for entity_id, relative, changes in contracts:
            with self.subTest(entity_id=entity_id):
                temporary, root = copied_vault_without_raw()
                self.addCleanup(temporary.cleanup)
                note = root / relative
                for field, value in changes:
                    replace_frontmatter_value(note, field, value)

                with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
                    with self.assertRaisesRegex(ValueError, "Order contract metadata mismatch"):
                        reader.get_entity(entity_id)
                    result = reader.verify_package(mode="knowledge")

                self.assertFalse(result["ok"])
                self.assertIn(relative, result["errors"])

    def test_machine_owned_generated_markdown_is_excluded_from_verification(self) -> None:
        temporary, root = copied_vault_without_raw()
        self.addCleanup(temporary.cleanup)
        generated = root / "_GENERATED/Fixture-Catalog-Full.md"
        generated.parent.mkdir()
        generated.write_text("machine-owned generated artifact\n", encoding="utf-8")

        with patch.object(reader, "ROOT", root), patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": ""}):
            result = reader.verify_package(mode="knowledge")

        self.assertTrue(result["ok"], result["failures"])
        self.assertNotIn("_GENERATED/Fixture-Catalog-Full.md", result["failures"])

    def test_current_external_hpzr6_evidence_verifies_in_both_directions(self) -> None:
        engine_root = Path(r"D:\My-Projects\TradingBot")
        with patch.dict(os.environ, {"TRADINGBOT_ENGINE_ROOT": str(engine_root)}):
            result = reader.verify_package(mode="knowledge")
            bullish = reader.read_algorithm_reference_evidence("bullish_hpzr6", 409, 3)
            bearish = reader.read_algorithm_reference_evidence("bearish_hpzr6", 409, 3)

        self.assertEqual({"verified"}, set(result["external_references"].values()))
        self.assertIn("Type-3 S", bullish["lines"][0]["text"])
        self.assertIn("Type-3 S", bearish["lines"][0]["text"])

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
            if not path.is_file() or any(part in {".git", ".obsidian", "_GENERATED"} for part in path.parts):
                continue
            if path.suffix not in {".md", ".py", ".js", ".json"} or "08_DATA/Raw" in path.as_posix() and not path.name.endswith(".meta.json"):
                continue
            content = path.read_text(encoding="utf-8-sig")
            self.assertIsNone(pattern.search(content), str(path))


if __name__ == "__main__":
    unittest.main()
