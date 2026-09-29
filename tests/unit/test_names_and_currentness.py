"""Public name lookup, currentness and status contracts on temporary software Vaults."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import hashlib
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


SOURCE = "06_SOURCE/Code/engine/pipeline/sample.py"
SOURCE_BYTES = b'"""Synthetic software provenance only."""\nVALUE = 1\n'


def sample(ident="concept.sample", *, name="Sample", aliases=(), status="active",
           authority="canonical", **metadata):
    return EntitySpec(ident, "01_CONCEPT/" + ident + ".md", "concept", status,
                      authority, "Display " + ident, "Independent software-test body.",
                      {"name": name, "aliases": list(aliases), **metadata})


class NameLookupTests(unittest.TestCase):
    def test_canonical_name_and_alias_preserve_id_metadata_and_content(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample(name="Signal", aliases=["Trigger"] )])
            with plugin_reader(root) as reader:
                expected = reader.get_entity("concept.sample")
                for query in ("Signal", "signal", " TRIGGER "):
                    with self.subTest(query=query):
                        self.assertEqual(reader.get_entity(query), expected)

    def test_alias_search_does_not_require_alias_in_title_or_body(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample(aliases=["UnmentionedAlias"])])
            with plugin_reader(root) as reader:
                self.assertEqual([row["id"] for row in reader.search("UnmentionedAlias")],
                                 ["concept.sample"])

    def test_single_letter_name_search_is_exact_and_does_not_flood_body_matches(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample("concept.a", name="A"),
                                    sample("concept.beta", name="Beta")])
            with plugin_reader(root) as reader:
                self.assertEqual([row["id"] for row in reader.search("A")], ["concept.a"])
                self.assertEqual(reader.search("Z"), [])

    def test_relations_accept_the_same_alias_and_return_canonical_identity(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample(aliases=["Signal"]), sample("concept.other", name="Other")],
                             relations=[{"from": "concept.sample", "to": "concept.other", "type": "depends_on"}])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.relations("Signal"), reader.relations("concept.sample"))

    def test_colliding_aliases_are_rejected_instead_of_selecting_an_arbitrary_owner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample("concept.left", name="Left", aliases=["Shared"]),
                                   sample("concept.right", name="Right", aliases=["SHARED"])])
            with plugin_reader(root) as reader:
                self.assertFalse(reader.verify_package("knowledge")["ok"])
                with self.assertRaises((ValueError, reader.VaultError)):
                    reader.search("Shared")

    def test_alias_cannot_shadow_another_stable_id(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample("concept.left", name="Left", aliases=["concept.right"]),
                                   sample("concept.right", name="Right")])
            with plugin_reader(root) as reader:
                self.assertFalse(reader.verify_package("knowledge")["ok"])

    def test_historical_and_known_invalid_names_remain_diagnostic(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample("concept.old", name="Old Signal", aliases=["OldAlias"], status="historical"),
                                   sample("concept.invalid", name="Invalid Signal", implementation_validity="known-invalid")])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.search("OldAlias"), [])
                self.assertEqual(reader.search("Invalid Signal"), [])
                self.assertIsNotNone(reader.get_entity("OldAlias")["warning"])
                self.assertEqual(reader.search("OldAlias", include_quarantined=True)[0]["status"], "historical")

    def test_conflicting_reference_metadata_warns_without_rewriting_executable_authority(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample(reference_agreement="conflict", authority="executable")])
            with plugin_reader(root) as reader:
                result = reader.get_entity("concept.sample")
                self.assertEqual(result["authority"], "executable")
                self.assertIsNotNone(result["warning"])


class RetrievalCurrentnessTests(unittest.TestCase):
    def test_engine_pin_mapping_cannot_disable_external_verification(self):
        for mapping in ("../outside.py", "apps/masked.py", "engine/other.py"):
            with self.subTest(mapping=mapping), TemporaryDirectory() as directory:
                base=Path(directory)
                root,engine=base / "vault",base / "engine"
                build_fake_vault(root,[sample(source_reference=[SOURCE])],source_files={SOURCE:SOURCE_BYTES})
                manifest_path=root / "_INDEX/source-hashes.json"
                manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["files"][0]["repository_relative_path"]=mapping
                manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
                with plugin_reader(root,engine_root=engine) as reader:
                    for operation in (lambda:reader.get_entity("concept.sample"),lambda:reader.read_evidence(SOURCE,1,1)):
                        with self.assertRaises((ValueError,reader.VaultError)) as caught:
                            operation()
                        self.assertEqual(reader.error_payload(caught.exception)["error"]["code"],"PATH_OUTSIDE_ALLOWED_ROOT")

    def test_runtime_enforces_the_declared_current_inventory_and_metadata(self):
        for defect in ("authority", "missing", "extra"):
            with self.subTest(defect=defect), TemporaryDirectory() as directory:
                root=Path(directory)
                build_fake_vault(root,[sample()])
                manifest_path=root / "_INDEX/source-hashes.json"
                manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
                declared={"concept.sample":{"status":"active","authority":"canonical"}}
                if defect=="authority":
                    declared["concept.sample"]["authority"]="executable"
                elif defect=="missing":
                    declared["concept.other"]={"status":"active"}
                else:
                    declared={}
                manifest["current_contract"]={"closed_entity_inventory":True,"entities":declared}
                manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
                with plugin_reader(root) as reader:
                    for operation in (lambda:reader.get_entity("concept.sample"),lambda:reader.search("Sample"),
                                      lambda:reader.relations("concept.sample"),lambda:reader.verify_package("knowledge")):
                        with self.assertRaises((ValueError,reader.VaultError)) as caught:
                            operation()
                        self.assertEqual(reader.error_payload(caught.exception)["error"]["code"],"INVALID_VAULT")

    def test_reference_excerpt_keeps_documented_scope_and_conflict_metadata(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            path="06_SOURCE/Code/engine/algorithms/reference.md"
            content=b"A documented claim.\n"
            reference={"id":"reference.sample","local_path":path,
                       "repository_relative_path":"engine/algorithms/reference.md",
                       "bytes":len(content),"sha256":hashlib.sha256(content).hexdigest(),
                       "authority_scope":"Preserved documented intent with disclosed narrative conflict",
                       "narrative_review_status":"reviewed-with-disclosed-scope-discrepancies",
                       "semantic_review_entity":"source.consistency","reference_conflicts":["TEST-SCOPE"]}
            build_fake_vault(root,[sample()],references=[reference],
                             reference_files={path:content})
            with plugin_reader(root) as reader:
                result=reader.read_evidence(path,1,1)
                self.assertEqual(result["authority"],"documented")
                self.assertEqual(result["reference_id"],"reference.sample")
                self.assertEqual(result["reference_conflicts"],["TEST-SCOPE"])
                self.assertEqual(result["semantic_review_entity"],"source.consistency")
                self.assertIsNotNone(result["warning"])

    def test_source_excerpt_checks_external_currentness_by_id_and_path(self):
        for query in ("source.sample", SOURCE):
            with self.subTest(query=query), TemporaryDirectory() as directory:
                base=Path(directory)
                root, engine=base / "vault", base / "engine"
                source=EntitySpec("source.sample", "06_SOURCE/sample.md", "source", "active", "executable",
                                  "Sample source", "Synthetic software evidence owner.", {"source_path": SOURCE})
                build_fake_vault(root,[source],source_files={SOURCE: SOURCE_BYTES})
                external=engine / "engine/pipeline/sample.py"
                external.parent.mkdir(parents=True)
                external.write_bytes(SOURCE_BYTES)
                with plugin_reader(root,engine_root=engine) as reader:
                    self.assertEqual(reader.read_evidence(query,1,1)["path"],SOURCE)
                    external.write_bytes(SOURCE_BYTES.replace(b"VALUE = 1",b"VALUE = 2"))
                    with self.assertRaises((ValueError,reader.VaultError)) as caught:
                        reader.read_evidence(query,1,1)
                    self.assertEqual(reader.error_payload(caught.exception)["error"]["code"],"SOURCE_HASH_MISMATCH")

    def test_declared_note_identity_contract_cannot_be_bypassed_by_removing_pins(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            manifest_path = root / "_INDEX/source-hashes.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["current_contract"] = {"require_note_identity": True}
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            index_path = root / "_INDEX/entities.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["entities"]["concept.sample"].pop("content_sha256")
            index["entities"]["concept.sample"].pop("content_bytes")
            index_path.write_text(json.dumps(index), encoding="utf-8")
            with plugin_reader(root) as reader:
                with self.assertRaises((ValueError, reader.VaultError)) as caught:
                    reader.get_entity("concept.sample")
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "INDEX_STALE")

    def test_relation_neighbor_evidence_is_checked_before_returning_its_authority(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample(related_entities=["concept.neighbor"]),
                                   sample("concept.neighbor", name="Neighbor", source_reference=[SOURCE])],
                             source_files={SOURCE: SOURCE_BYTES})
            (root / SOURCE).write_bytes(SOURCE_BYTES.replace(b"VALUE = 1", b"VALUE = 2"))
            with plugin_reader(root) as reader:
                with self.assertRaises((ValueError, reader.VaultError)) as caught:
                    reader.relations("concept.sample")
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "SOURCE_HASH_MISMATCH")

    def test_source_tampering_blocks_knowledge_retrieval_and_search(self):
        for operation in ("entity", "search", "relations"):
            with self.subTest(operation=operation), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample(source_reference=[SOURCE])], source_files={SOURCE: SOURCE_BYTES})
                with plugin_reader(root) as reader:
                    self.assertEqual(reader.get_entity("concept.sample")["id"], "concept.sample")
                    (root / SOURCE).write_bytes(SOURCE_BYTES.replace(b"VALUE = 1", b"VALUE = 2"))
                    call = {"entity": lambda: reader.get_entity("concept.sample"),
                            "search": lambda: reader.search("Sample"),
                            "relations": lambda: reader.relations("concept.sample")}[operation]
                    with self.assertRaises((ValueError, reader.VaultError)) as caught:
                        call()
                    self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "SOURCE_HASH_MISMATCH")

    def test_changed_note_body_cannot_keep_an_old_current_index(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("concept.sample")["id"], "concept.sample")
                path = root / "01_CONCEPT/concept.sample.md"
                path.write_text(path.read_text(encoding="utf-8").replace("Independent software-test body.",
                                                                        "Changed software-test body."), encoding="utf-8")
                with self.assertRaises((ValueError, reader.VaultError)) as caught:
                    reader.get_entity("concept.sample")
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "INDEX_STALE")

    def test_matching_external_source_is_verified_and_changed_source_is_rejected(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root, engine = base / "vault", base / "engine"
            build_fake_vault(root, [sample(source_reference=[SOURCE])], source_files={SOURCE: SOURCE_BYTES})
            external = engine / "engine/pipeline/sample.py"
            external.parent.mkdir(parents=True)
            external.write_bytes(SOURCE_BYTES)
            with plugin_reader(root, engine_root=engine) as reader:
                self.assertEqual(reader.get_entity("concept.sample")["id"], "concept.sample")
                external.write_bytes(SOURCE_BYTES.replace(b"VALUE = 1", b"VALUE = 2"))
                with self.assertRaises((ValueError, reader.VaultError)) as caught:
                    reader.get_entity("concept.sample")
                self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "SOURCE_HASH_MISMATCH")


if __name__ == "__main__":
    unittest.main()
