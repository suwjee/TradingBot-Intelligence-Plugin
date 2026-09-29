# Task 2 fix round 2 review package

Review the single round-2 correction against the round-1 reviewer finding. This is uncommitted because commits are unauthorized. Confirm the duplicate-key test remains a real current-product detector and will pass after a correct product implementation.

## tests/.sdd/task-2-fix-1-review-package.md

```text
# Task 2 fix round 1 review package

This is the complete uncommitted review scope. It is a file-scoped substitute for a commit range because commits are not authorized. Review against the approved Task 2 brief and implementation plan. The duplicate-ID detector is intentionally allowed to fail only if actual current reader behavior does not reject duplicate raw JSON keys; do not accept a weakened assertion.

## tests/.sdd/task-2-brief.md

```text
# Task 2: Synthetic discovery, entities, authority, search, and relations

## Binding constraints

- Edit only under `D:\My-Projects\TradingBot-Intelligence-Plugin\tests\`.
- Do not modify Plugin runtime source, Knowledge Vault, Production Engine, dependencies, user configuration, Git state, or package artifacts.
- Use `unittest` and existing Task 1 helpers only; do not add dependencies.
- Use `apply_patch` for edits; do not dispatch subagents.
- Do not commit, stage, push, create a branch/worktree, clean, or delete files.
- This is a test-suite task. Capture the planned pre-module `ImportError` as RED evidence; do not create artificial product failures or change production code.

## Existing interfaces

Read and use:

- `tests/helpers/fake_vault.py`: `EntitySpec`, `build_fake_vault()`
- `tests/helpers/plugin_runtime.py`: `plugin_reader()`
- `tests/helpers/snapshots.py`

## Files

- Create: `tests/unit/test_config_and_discovery.py`
- Create: `tests/unit/test_entities_and_authority.py`
- Create: `tests/unit/test_search_and_relations.py`
- Create: `tests/contract/__init__.py`
- Create: `tests/contract/test_retrieval_contract.py`

## Required coverage

1. Discovery/configuration: explicit valid Vault, missing root, random directory,
   missing index/schema, malformed registry/index, config-file override,
   explicit environment precedence, relative paths, spaces, Unicode paths,
   missing optional Engine, optional RAW behavior, and unknown registry schema
   version. Assert `VaultError.code`, not message fragments alone.

2. Entity identity/authority: stable ID still resolves after a note move and
   regenerated index; missing entity maps to structured `ENTITY_NOT_FOUND`;
   default search excludes arbitrary metadata-quarantined entity; a canonical
   entity named `Order_B_Test_Name` is not quarantined by name. Add malformed
   frontmatter, duplicate frontmatter key, duplicate stable ID, missing required
   metadata, unsupported entity type, unknown optional metadata, and
   changed-note/unchanged-index cases. Record current generic-future-type source
   behavior rather than inventing a schema restriction.

3. Search/relations: exact/partial title, stable ID, Unicode/Persian content,
   multiple matches, type/authority/status filters, explicit diagnostic
   inclusion, empty query, no result, limit/offset, repeatable tie ordering;
   incoming/outgoing/both, depth 1/multi-depth, three-node cycle, missing target,
   quarantined target filtering, max depth, deterministic traversal. Include
   UTF-8 filenames and Persian note content. Use `ThreadPoolExecutor` only for
   independent reader calls; assert result isolation and determinism without a
   timing threshold.

4. Retrieval public contract: assert only fields emitted by current source:
   entity `id`, index fields, `warning`, `sync_review_state`, `content`; search
   `total_matches`, `truncated`, `next_offset`. Do not invent `snippet` or
   `reasoning_eligibility` fields.

5. Machine-specific path scan: scan non-documentation Plugin runtime Python and
   new test Python files for drive/home literals. Documentation templates are
   excluded. Build forbidden test needles dynamically, for example with
   `"D" + ":" + chr(92)`, rather than embedding the prohibited literal in the
   test that scans itself. Explain that local exception in a comment.

## Required RED/GREEN evidence

1. Before creating the Task 2 modules, run:

   `python -B -m unittest tests.unit.test_config_and_discovery -v`

   Capture the expected module import failure as the plan's RED state.
2. Implement the modules and run:

   `python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v`

   All current-runtime contract tests must pass. If a test exposes a real source
   discrepancy, preserve it and report `DONE_WITH_CONCERNS` rather than weakening
   it.

## Report

Append a detailed report with RED/GREEN command/output evidence, changed files,
self-review, and any source discrepancies to:

`D:\My-Projects\TradingBot-Intelligence-Plugin\tests\.sdd\task-2-report.md`

Return only: status, no commits created, one-line test summary, concerns, and
the report path.


```

## tests/.sdd/task-2-report.md

```text
# Task 2 report: synthetic retrieval tests

## Status

DONE_WITH_CONCERNS. Test-only implementation completed. No commits, staging, branch, worktree, cleanup, package, runtime-source, Vault, Engine, dependency, or user-configuration changes were made.

## RED evidence

Before creating the Task 2 modules, ran:

```text
python -B -m unittest tests.unit.test_config_and_discovery -v
test_config_and_discovery (unittest.loader._FailedTest.test_config_and_discovery) ... ERROR
ModuleNotFoundError: No module named 'tests.unit.test_config_and_discovery'
Ran 1 test in 0.000s
FAILED (errors=1)
```

This was the planned missing-module RED state, not a product failure.

## GREEN evidence

After creating and tightening the tests, ran:

```text
python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v
Ran 25 tests in 0.804s
OK
exit code: 0
```

The final run covers explicit and configured Vault discovery, structured discovery errors, relative/Unicode/space paths, optional Engine and RAW behavior, registry version, stable identity, metadata quarantine, malformed and stale notes, search filters and pagination, Unicode content, relation traversal and cycles, concurrent reader-call isolation, public retrieval fields, and machine-specific path scanning.

## Changed files

- `tests/unit/test_config_and_discovery.py` — 9 discovery/configuration tests.
- `tests/unit/test_entities_and_authority.py` — 8 entity/authority tests.
- `tests/unit/test_search_and_relations.py` — 6 search/relation tests.
- `tests/contract/__init__.py` — contract package marker.
- `tests/contract/test_retrieval_contract.py` — 2 public-contract/portability tests.
- `tests/.sdd/task-2-report.md` — this report.

## Self-review and source behavior

- The path scanner builds its forbidden drive/home needles at runtime. This local exception is necessary because the scanner reads its own Python source. Documentation templates are outside its scan set.
- The reader currently accepts an indexed generic future entity type. The test records that behavior; it does not invent an enum restriction. Whether future types should be rejected is a schema/policy decision outside this test-only task.
- Duplicate stable IDs are rejected by the synthetic Vault builder before writing an ambiguous index. This test does not claim that the runtime can detect duplicate JSON object keys after JSON parsing.
- Missing and changed required note metadata produce `INDEX_STALE` through the current reader. A missing entity is a `ValueError` mapped to `ENTITY_NOT_FOUND` by `error_payload`; it is not raised as `VaultError`.
- The tests are synthetic and bounded to the current reader implementation. They do not validate real Vault semantic content or Production Engine behavior.


```

## tests/.sdd/task-2-review.md

```text
# Task 2 review package — uncommitted additions

## Review basis

- Plan task: `tests/TEST_SUITE_IMPLEMENTATION_PLAN.md`, Task 2.
- Baseline Git commit: `808435cdf5c8cfa9fcb0ab97678b1d36cfd9c516`.
- No commit is authorized. The files below are all Task 2 additions relative to Task 1's reviewed state; their full contents are the review diff.

## Implementer report

# Task 2 report: synthetic retrieval tests

## Status

DONE_WITH_CONCERNS. Test-only implementation completed. No commits, staging, branch, worktree, cleanup, package, runtime-source, Vault, Engine, dependency, or user-configuration changes were made.

## RED evidence

Before creating the Task 2 modules, ran:

```text
python -B -m unittest tests.unit.test_config_and_discovery -v
test_config_and_discovery (unittest.loader._FailedTest.test_config_and_discovery) ... ERROR
ModuleNotFoundError: No module named 'tests.unit.test_config_and_discovery'
Ran 1 test in 0.000s
FAILED (errors=1)
```

This was the planned missing-module RED state, not a product failure.

## GREEN evidence

After creating and tightening the tests, ran:

```text
python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v
Ran 25 tests in 0.804s
OK
exit code: 0
```

The final run covers explicit and configured Vault discovery, structured discovery errors, relative/Unicode/space paths, optional Engine and RAW behavior, registry version, stable identity, metadata quarantine, malformed and stale notes, search filters and pagination, Unicode content, relation traversal and cycles, concurrent reader-call isolation, public retrieval fields, and machine-specific path scanning.

## Changed files

- `tests/unit/test_config_and_discovery.py` — 9 discovery/configuration tests.
- `tests/unit/test_entities_and_authority.py` — 8 entity/authority tests.
- `tests/unit/test_search_and_relations.py` — 6 search/relation tests.
- `tests/contract/__init__.py` — contract package marker.
- `tests/contract/test_retrieval_contract.py` — 2 public-contract/portability tests.
- `tests/.sdd/task-2-report.md` — this report.

## Self-review and source behavior

- The path scanner builds its forbidden drive/home needles at runtime. This local exception is necessary because the scanner reads its own Python source. Documentation templates are outside its scan set.
- The reader currently accepts an indexed generic future entity type. The test records that behavior; it does not invent an enum restriction. Whether future types should be rejected is a schema/policy decision outside this test-only task.
- Duplicate stable IDs are rejected by the synthetic Vault builder before writing an ambiguous index. This test does not claim that the runtime can detect duplicate JSON object keys after JSON parsing.
- Missing and changed required note metadata produce `INDEX_STALE` through the current reader. A missing entity is a `ValueError` mapped to `ENTITY_NOT_FOUND` by `error_payload`; it is not raised as `VaultError`.
- The tests are synthetic and bounded to the current reader implementation. They do not validate real Vault semantic content or Production Engine behavior.


## Changed files

## tests/unit/test_config_and_discovery.py

```
"""Synthetic Vault discovery and configuration contracts."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def sample():
    return EntitySpec("system.sample", "00_SYSTEM/Sample.md", "system", "active",
                      "canonical", "Sample", "Synthetic content.")


class DiscoveryTests(unittest.TestCase):
    def assert_import_code(self, root, code):
        with self.assertRaises(Exception) as caught:
            with plugin_reader(root):
                pass
        self.assertEqual(getattr(caught.exception, "code", None), code)

    def test_explicit_valid_vault_and_unicode_space_path(self):
        with TemporaryDirectory(prefix="Vault فضای آزمایش ") as directory:
            root = Path(directory) / "Knowledge Vault"
            build_fake_vault(root, [sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.ROOT, root.resolve())
                self.assertEqual(reader.get_entity("system.sample")["id"], "system.sample")

    def test_missing_root_and_random_directory_have_distinct_codes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assert_import_code(root / "missing", "VAULT_NOT_FOUND")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_required_index_and_schema_are_required(self):
        for relative in ("_INDEX/entities.json", "_SCHEMA/note.schema.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).unlink()
                self.assert_import_code(root, "INVALID_VAULT")

    def test_malformed_registry_and_index_are_invalid_vaults(self):
        for relative in ("06_SOURCE/References/registry.json", "_INDEX/entities.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).write_text("{invalid", encoding="utf-8")
                self.assert_import_code(root, "INVALID_VAULT")

    def test_unknown_registry_schema_version_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            registry = root / "06_SOURCE/References/registry.json"
            registry.write_text(json.dumps({"schema_version": 999, "references": []}), encoding="utf-8")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_config_file_override_and_explicit_environment_precedence(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            configured = build_fake_vault(base / "configured", [sample()]).root
            explicit = build_fake_vault(base / "explicit", [sample()]).root
            config = base / "vault config.json"
            config.write_text(json.dumps({"vault_root": str(configured)}), encoding="utf-8")
            with plugin_reader(explicit) as reader:
                with patch.dict(os.environ, {"TRADINGBOT_PLUGIN_CONFIG": str(config)}, clear=False):
                    with patch.dict(os.environ, {"TRADINGBOT_KNOWLEDGE_VAULT": ""}, clear=False):
                        self.assertEqual(reader.locate_vault(), configured.resolve())
                    self.assertEqual(reader.locate_vault(), explicit.resolve())

    def test_relative_explicit_path_resolves(self):
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            relative = Path(root.name)
            with plugin_reader(relative) as reader:
                self.assertEqual(reader.ROOT, root.resolve())

    def test_optional_engine_and_raw_are_not_discovery_dependencies(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            build_fake_vault(root, [sample()])
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])
                self.assertTrue(reader.verify_package("full-data")["ok"])

    def test_missing_pinned_raw_is_optional_only_in_knowledge_mode(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()], raw_files={"08_DATA/Raw/synthetic.json": b"[]\n"})
            (root / "08_DATA/Raw/synthetic.json").unlink()
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])
                full = reader.verify_package("full-data")
                self.assertFalse(full["ok"])
                self.assertIn("08_DATA/Raw/synthetic.json", full["errors"])


if __name__ == "__main__":
    unittest.main()

```

## tests/unit/test_entities_and_authority.py

```
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

```

## tests/unit/test_search_and_relations.py

```
"""Synthetic search and relation traversal contracts."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def item(entity_id, title, body="Synthetic text", *, status="active", authority="canonical", type="concept"):
    return EntitySpec(entity_id, f"01_CONCEPT/{title}.md", type, status, authority, title, body)


class SearchRelationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        build_fake_vault(self.root, [
            item("concept.alpha", "Alpha", "Persian کندل and shared term"),
            item("concept.beta", "Beta", "shared term"),
            item("concept.gamma", "Gamma", "shared term"),
            item("concept.hidden", "Hidden", "shared term", status="pending", authority="non-canonical"),
            item("data.utf8", "یادداشت", "محتوای فارسی کندل", type="data"),
        ], relations=[
            {"from": "concept.alpha", "type": "depends_on", "to": "concept.beta"},
            {"from": "concept.beta", "type": "supports", "to": "concept.gamma"},
            {"from": "concept.gamma", "type": "relates_to", "to": "concept.alpha"},
            {"from": "concept.alpha", "type": "affects", "to": "concept.hidden"},
        ])

    def test_exact_partial_id_and_persian_content_search(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(reader.search("Alpha")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("Alph")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("concept.beta")[0]["id"], "concept.beta")
            self.assertEqual({row["id"] for row in reader.search("کندل")},
                             {"concept.alpha", "data.utf8"})
            self.assertEqual(reader.search("یادداشت")[0]["file"], "01_CONCEPT/یادداشت.md")

    def test_multiple_matches_filters_and_explicit_diagnostic_inclusion(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(len(reader.search("shared")), 3)
            self.assertEqual([r["id"] for r in reader.search("shared", entity_type="data")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", authority="non-canonical")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", status="pending")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", include_pending=True, status="pending")],
                             ["concept.hidden"])
            self.assertEqual([r["id"] for r in reader.search("shared", include_noncanonical=True,
                                                             authority="non-canonical")], ["concept.hidden"])

    def test_empty_no_result_pagination_and_tie_order(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError):
                reader.search(" ")
            self.assertEqual(reader.search("absentvalue"), [])
            pages = [reader.search("shared", limit=1, offset=n) for n in range(3)]
            self.assertEqual([page[0]["id"] for page in pages],
                             ["concept.alpha", "concept.beta", "concept.gamma"])
            self.assertTrue(pages[0][0]["truncated"])
            self.assertEqual(pages[0][0]["next_offset"], 1)
            self.assertEqual(pages[2][0]["next_offset"], None)
            self.assertEqual(reader.search("shared", offset=99), [])

    def test_direction_depth_cycle_and_deterministic_traversal(self):
        with plugin_reader(self.root) as reader:
            outgoing = reader.relations("concept.alpha", direction="outgoing", max_depth=1)
            self.assertEqual([r["entity_id"] for r in outgoing["traversal"]], ["concept.beta"])
            incoming = reader.relations("concept.alpha", direction="incoming", max_depth=1)
            self.assertEqual([r["entity_id"] for r in incoming["traversal"]], ["concept.gamma"])
            both = reader.relations("concept.alpha", direction="both", max_depth=2)
            self.assertEqual([r["entity_id"] for r in both["traversal"]],
                             ["concept.beta", "concept.gamma"])
            deep = reader.relations("concept.alpha", direction="outgoing", max_depth=5)
            self.assertEqual([r["entity_id"] for r in deep["traversal"]],
                             ["concept.beta", "concept.gamma"])
            self.assertEqual(deep, reader.relations("concept.alpha", direction="outgoing", max_depth=5))

    def test_missing_target_quarantine_and_max_depth(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError) as caught:
                reader.relations("concept.missing")
            self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "ENTITY_NOT_FOUND")
            self.assertNotIn("concept.hidden", [e["to"] for e in reader.relations("concept.alpha")["outgoing"]])
            self.assertIn("concept.hidden", [e["to"] for e in reader.relations(
                "concept.alpha", include_quarantined=True)["outgoing"]])
            for depth in (0, 6):
                with self.assertRaises(ValueError):
                    reader.relations("concept.alpha", max_depth=depth)

    def test_independent_concurrent_reads_are_isolated_and_repeatable(self):
        with plugin_reader(self.root) as reader:
            def call(index):
                if index % 2:
                    return reader.relations("concept.alpha", direction="outgoing", max_depth=3)
                return reader.search("shared", limit=2)

            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(call, range(20)))
            self.assertTrue(all(result == results[0] for result in results[::2]))
            self.assertTrue(all(result == results[1] for result in results[1::2]))
            results[0][0]["id"] = "mutated"
            self.assertEqual(results[2][0]["id"], "concept.alpha")


if __name__ == "__main__":
    unittest.main()

```

## tests/contract/__init__.py

```
"""Public retrieval contract tests."""

```

## tests/contract/test_retrieval_contract.py

```
"""Current public retrieval fields and portable runtime path contract."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class RetrievalContractTests(unittest.TestCase):
    def test_entity_and_search_emit_current_source_fields_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [EntitySpec("concept.sample", "01_CONCEPT/Sample.md", "concept",
                                               "active", "canonical", "Sample", "Synthetic word")])
            with plugin_reader(root) as reader:
                entity = reader.get_entity("concept.sample")
                expected = {"id", "file", "type", "status", "authority", "title",
                            "warning", "sync_review_state", "content"}
                self.assertEqual(set(entity), expected)
                hit = reader.search("sample")[0]
                self.assertEqual(set(hit), (expected - {"content"}) |
                                 {"excerpt", "total_matches", "truncated", "next_offset"})
                self.assertEqual(hit["total_matches"], 1)
                self.assertFalse(hit["truncated"])
                self.assertIsNone(hit["next_offset"])
                self.assertNotIn("snippet", hit)
                self.assertNotIn("reasoning_eligibility", entity)

    def test_runtime_and_new_tests_have_no_machine_specific_paths(self):
        plugin = Path(__file__).resolve().parents[2]
        runtime = [plugin / name for name in ("vault_reader.py", "vault_cli.py", "mcp_server.py", "runtime_doctor.py")]
        runtime.extend((plugin / "maintenance").glob("*.py"))
        tests = list((plugin / "tests" / "unit").glob("test_*.py"))
        tests.extend((plugin / "tests" / "contract").glob("test_*.py"))
        # Construct forbidden literals at runtime so this self-scanning test does not contain them.
        drive = "D" + ":" + chr(92)
        home = "C" + ":" + chr(92) + "Users" + chr(92)
        for path in [*runtime, *tests]:
            with self.subTest(path=path.relative_to(plugin)):
                content = path.read_text(encoding="utf-8")
                self.assertNotIn(drive, content)
                self.assertNotIn(home, content)


if __name__ == "__main__":
    unittest.main()

```



```

## tests/.sdd/task-2-fix-1-report.md

```text
# Task 2 fix round 1 report

## Status and scope

DONE_WITH_CONCERNS. Changes are confined to four Task 2 Python test modules and this report under `tests/`. No Plugin runtime, Vault, Production, dependency, user configuration, or Git action was taken. No commits were created.

## Review findings addressed

1. The portability test now constructs five forbidden path patterns dynamically: three specified drive roots and two Unix-style home roots. It scans all root runtime Python, `maintenance/**/*.py`, `scripts/**/*.py`, and `tests/**/*.py`, including `tests/contract/__init__.py`. The patterns do not appear literally in the self-scanning source.
2. A reader-level test writes duplicate `concept.sample` object keys into raw `_INDEX/entities.json` and requires `locate_vault()` to raise `VaultError(code="INVALID_VAULT")`. The assertion remains failing because the current reader accepts the index. The existing FakeVault builder duplicate-ID test remains intact.
3. Discovery failures now assert `reader.VaultError` and its exact `code` at the reader boundary.
4. The optional Engine test registers an actual pinned reference to a missing `engine/algorithms/missing.py` path. With Engine unconfigured, knowledge verification succeeds and reports `optional_not_configured`; with an absent Engine root configured, verification fails and reports `unavailable` plus `reference_unavailable:algorithm.synthetic`.
5. The synthetic search corpus now includes the same matching term in `concept` and `data` entities, and tests positive type filters for both.
6. Concurrent calls now exercise public `get_knowledge`, `search_knowledge`, and `trace_relations` in one `ThreadPoolExecutor`, checking repeatability and independent result objects without a timing threshold.

## Focused test evidence

Command:

```text
python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v
```

Final output summary:

```text
Ran 26 tests in 1.743s
FAILED (failures=1)
exit code: 1
```

The sole failure is `test_duplicate_stable_id_in_raw_index_requires_reader_rejection`: `AssertionError: VaultError not raised` at `tests/unit/test_entities_and_authority.py:83`. The other 25 tests passed, including the expanded portability scan and public concurrent retrieval test.

## Source-behavior evidence and self-review

`vault_reader.locate_vault()` reads `_INDEX/entities.json` with standard `json.loads`, checks that `entities` is a dictionary, and returns the root. Standard JSON object parsing retains one value for repeated keys, so this path has no duplicate-key rejection before the dictionary check. The raw test keeps both repeated keys in the file and calls `locate_vault()` after the mutation. Its required `INVALID_VAULT` assertion is a deliberate detector for this Plugin defect; changing the test to accept overwrite would hide it.

The FakeVault builder rejects duplicate IDs before serialization, but that protects only test-generated indexes. The new test checks the reader's trust boundary. No production fix is included because this round is explicitly tests-only.


```

## tests/unit/test_config_and_discovery.py

```text
"""Synthetic Vault discovery and configuration contracts."""

import json
import os
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def sample():
    return EntitySpec("system.sample", "00_SYSTEM/Sample.md", "system", "active",
                      "canonical", "Sample", "Synthetic content.")


class DiscoveryTests(unittest.TestCase):
    def assert_import_code(self, root, code):
        with TemporaryDirectory() as directory:
            valid = Path(directory) / "valid"
            build_fake_vault(valid, [sample()])
            with plugin_reader(valid) as reader:
                with patch.dict(os.environ, {"TRADINGBOT_KNOWLEDGE_VAULT": str(root)}, clear=False):
                    with self.assertRaises(reader.VaultError) as caught:
                        reader.locate_vault()
                    self.assertEqual(caught.exception.code, code)

    def test_explicit_valid_vault_and_unicode_space_path(self):
        with TemporaryDirectory(prefix="Vault فضای آزمایش ") as directory:
            root = Path(directory) / "Knowledge Vault"
            build_fake_vault(root, [sample()])
            with plugin_reader(root) as reader:
                self.assertEqual(reader.ROOT, root.resolve())
                self.assertEqual(reader.get_entity("system.sample")["id"], "system.sample")

    def test_missing_root_and_random_directory_have_distinct_codes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self.assert_import_code(root / "missing", "VAULT_NOT_FOUND")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_required_index_and_schema_are_required(self):
        for relative in ("_INDEX/entities.json", "_SCHEMA/note.schema.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).unlink()
                self.assert_import_code(root, "INVALID_VAULT")

    def test_malformed_registry_and_index_are_invalid_vaults(self):
        for relative in ("06_SOURCE/References/registry.json", "_INDEX/entities.json"):
            with self.subTest(relative=relative), TemporaryDirectory() as directory:
                root = Path(directory)
                build_fake_vault(root, [sample()])
                (root / relative).write_text("{invalid", encoding="utf-8")
                self.assert_import_code(root, "INVALID_VAULT")

    def test_unknown_registry_schema_version_is_rejected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            registry = root / "06_SOURCE/References/registry.json"
            registry.write_text(json.dumps({"schema_version": 999, "references": []}), encoding="utf-8")
            self.assert_import_code(root, "INVALID_VAULT")

    def test_config_file_override_and_explicit_environment_precedence(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            configured = build_fake_vault(base / "configured", [sample()]).root
            explicit = build_fake_vault(base / "explicit", [sample()]).root
            config = base / "vault config.json"
            config.write_text(json.dumps({"vault_root": str(configured)}), encoding="utf-8")
            with plugin_reader(explicit) as reader:
                with patch.dict(os.environ, {"TRADINGBOT_PLUGIN_CONFIG": str(config)}, clear=False):
                    with patch.dict(os.environ, {"TRADINGBOT_KNOWLEDGE_VAULT": ""}, clear=False):
                        self.assertEqual(reader.locate_vault(), configured.resolve())
                    self.assertEqual(reader.locate_vault(), explicit.resolve())

    def test_relative_explicit_path_resolves(self):
        with TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()])
            relative = Path(root.name)
            with plugin_reader(relative) as reader:
                self.assertEqual(reader.ROOT, root.resolve())

    def test_optional_engine_and_raw_are_not_discovery_dependencies(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "vault"
            content = b"synthetic reference\n"
            reference_id = "algorithm.synthetic"
            build_fake_vault(root, [sample()], references=[{
                "id": reference_id,
                "repository_relative_path": "engine/algorithms/missing.py",
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }])
            with plugin_reader(root) as reader:
                unconfigured = reader.verify_package("knowledge")
                self.assertTrue(unconfigured["ok"])
                self.assertEqual(unconfigured["external_references"][reference_id], "optional_not_configured")
            with plugin_reader(root, engine_root=Path(directory) / "absent-engine") as reader:
                missing = reader.verify_package("knowledge")
                self.assertFalse(missing["ok"])
                self.assertEqual(missing["external_references"][reference_id], "unavailable")
                self.assertIn(f"reference_unavailable:{reference_id}", missing["errors"])

    def test_missing_pinned_raw_is_optional_only_in_knowledge_mode(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [sample()], raw_files={"08_DATA/Raw/synthetic.json": b"[]\n"})
            (root / "08_DATA/Raw/synthetic.json").unlink()
            with plugin_reader(root) as reader:
                self.assertTrue(reader.verify_package("knowledge")["ok"])
                full = reader.verify_package("full-data")
                self.assertFalse(full["ok"])
                self.assertIn("08_DATA/Raw/synthetic.json", full["errors"])


if __name__ == "__main__":
    unittest.main()


```

## tests/unit/test_entities_and_authority.py

```text
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
            original = json.loads(index_path.read_text(encoding="utf-8"))["entities"]
            row = json.dumps(original["concept.sample"], ensure_ascii=False)
            duplicate = ('{"entities":{"concept.sample":' + row +
                         ',"concept.sample":' + row + '}}')
            index_path.write_text(duplicate, encoding="utf-8")
            with plugin_reader(root) as reader:
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


```

## tests/unit/test_search_and_relations.py

```text
"""Synthetic search and relation traversal contracts."""

from concurrent.futures import ThreadPoolExecutor
import importlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


def item(entity_id, title, body="Synthetic text", *, status="active", authority="canonical", type="concept"):
    return EntitySpec(entity_id, f"01_CONCEPT/{title}.md", type, status, authority, title, body)


class SearchRelationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        build_fake_vault(self.root, [
            item("concept.alpha", "Alpha", "Persian کندل and shared term"),
            item("concept.beta", "Beta", "shared term"),
            item("concept.gamma", "Gamma", "shared term"),
            item("concept.hidden", "Hidden", "shared term", status="pending", authority="non-canonical"),
            item("data.utf8", "یادداشت", "محتوای فارسی کندل and shared term", type="data"),
        ], relations=[
            {"from": "concept.alpha", "type": "depends_on", "to": "concept.beta"},
            {"from": "concept.beta", "type": "supports", "to": "concept.gamma"},
            {"from": "concept.gamma", "type": "relates_to", "to": "concept.alpha"},
            {"from": "concept.alpha", "type": "affects", "to": "concept.hidden"},
        ])

    def test_exact_partial_id_and_persian_content_search(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(reader.search("Alpha")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("Alph")[0]["id"], "concept.alpha")
            self.assertEqual(reader.search("concept.beta")[0]["id"], "concept.beta")
            self.assertEqual({row["id"] for row in reader.search("کندل")},
                             {"concept.alpha", "data.utf8"})
            self.assertEqual(reader.search("یادداشت")[0]["file"], "01_CONCEPT/یادداشت.md")

    def test_multiple_matches_filters_and_explicit_diagnostic_inclusion(self):
        with plugin_reader(self.root) as reader:
            self.assertEqual(len(reader.search("shared")), 4)
            self.assertEqual([r["id"] for r in reader.search("shared", entity_type="data")], ["data.utf8"])
            self.assertEqual([r["id"] for r in reader.search("shared", entity_type="concept")],
                             ["concept.alpha", "concept.beta", "concept.gamma"])
            self.assertEqual([r["id"] for r in reader.search("shared", authority="non-canonical")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", status="pending")], [])
            self.assertEqual([r["id"] for r in reader.search("shared", include_pending=True, status="pending")],
                             ["concept.hidden"])
            self.assertEqual([r["id"] for r in reader.search("shared", include_noncanonical=True,
                                                             authority="non-canonical")], ["concept.hidden"])

    def test_empty_no_result_pagination_and_tie_order(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError):
                reader.search(" ")
            self.assertEqual(reader.search("absentvalue"), [])
            pages = [reader.search("shared", limit=1, offset=n) for n in range(4)]
            self.assertEqual([page[0]["id"] for page in pages],
                             ["concept.alpha", "concept.beta", "concept.gamma", "data.utf8"])
            self.assertTrue(pages[0][0]["truncated"])
            self.assertEqual(pages[0][0]["next_offset"], 1)
            self.assertEqual(pages[3][0]["next_offset"], None)
            self.assertEqual(reader.search("shared", offset=99), [])

    def test_direction_depth_cycle_and_deterministic_traversal(self):
        with plugin_reader(self.root) as reader:
            outgoing = reader.relations("concept.alpha", direction="outgoing", max_depth=1)
            self.assertEqual([r["entity_id"] for r in outgoing["traversal"]], ["concept.beta"])
            incoming = reader.relations("concept.alpha", direction="incoming", max_depth=1)
            self.assertEqual([r["entity_id"] for r in incoming["traversal"]], ["concept.gamma"])
            both = reader.relations("concept.alpha", direction="both", max_depth=2)
            self.assertEqual([r["entity_id"] for r in both["traversal"]],
                             ["concept.beta", "concept.gamma"])
            deep = reader.relations("concept.alpha", direction="outgoing", max_depth=5)
            self.assertEqual([r["entity_id"] for r in deep["traversal"]],
                             ["concept.beta", "concept.gamma"])
            self.assertEqual(deep, reader.relations("concept.alpha", direction="outgoing", max_depth=5))

    def test_missing_target_quarantine_and_max_depth(self):
        with plugin_reader(self.root) as reader:
            with self.assertRaises(ValueError) as caught:
                reader.relations("concept.missing")
            self.assertEqual(reader.error_payload(caught.exception)["error"]["code"], "ENTITY_NOT_FOUND")
            self.assertNotIn("concept.hidden", [e["to"] for e in reader.relations("concept.alpha")["outgoing"]])
            self.assertIn("concept.hidden", [e["to"] for e in reader.relations(
                "concept.alpha", include_quarantined=True)["outgoing"]])
            for depth in (0, 6):
                with self.assertRaises(ValueError):
                    reader.relations("concept.alpha", max_depth=depth)

    def test_independent_concurrent_reads_are_isolated_and_repeatable(self):
        with plugin_reader(self.root) as reader:
            api = importlib.import_module("mcp_server")
            def call(index):
                if index % 3 == 2:
                    return api.trace_relations("concept.alpha", direction="outgoing", max_depth=3)
                if index % 3 == 1:
                    return api.get_knowledge("concept.alpha")
                return api.search_knowledge("shared", limit=2)

            with ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(call, range(21)))
            for kind in range(3):
                self.assertTrue(all(result == results[kind] for result in results[kind::3]))
            results[0][0]["id"] = "mutated"
            self.assertEqual(results[3][0]["id"], "concept.alpha")
            results[1]["id"] = "mutated"
            self.assertEqual(results[4]["id"], "concept.alpha")


if __name__ == "__main__":
    unittest.main()


```

## tests/contract/test_retrieval_contract.py

```text
"""Current public retrieval fields and portable runtime path contract."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class RetrievalContractTests(unittest.TestCase):
    def test_entity_and_search_emit_current_source_fields_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            build_fake_vault(root, [EntitySpec("concept.sample", "01_CONCEPT/Sample.md", "concept",
                                               "active", "canonical", "Sample", "Synthetic word")])
            with plugin_reader(root) as reader:
                entity = reader.get_entity("concept.sample")
                expected = {"id", "file", "type", "status", "authority", "title",
                            "warning", "sync_review_state", "content"}
                self.assertEqual(set(entity), expected)
                hit = reader.search("sample")[0]
                self.assertEqual(set(hit), (expected - {"content"}) |
                                 {"excerpt", "total_matches", "truncated", "next_offset"})
                self.assertEqual(hit["total_matches"], 1)
                self.assertFalse(hit["truncated"])
                self.assertIsNone(hit["next_offset"])
                self.assertNotIn("snippet", hit)
                self.assertNotIn("reasoning_eligibility", entity)

    def test_runtime_and_new_tests_have_no_machine_specific_paths(self):
        plugin = Path(__file__).resolve().parents[2]
        runtime = list(plugin.glob("*.py"))
        runtime.extend((plugin / "maintenance").rglob("*.py"))
        runtime.extend((plugin / "scripts").rglob("*.py"))
        tests = list((plugin / "tests").rglob("*.py"))
        # Compose all forbidden needles at runtime because this test scans itself.
        drive_suffix = ":" + chr(92)
        forbidden = tuple(letter + drive_suffix for letter in ("D", "C", "X"))
        forbidden += ("/" + "home" + "/", "/" + "Users" + "/")
        for path in sorted({*runtime, *tests}):
            with self.subTest(path=path.relative_to(plugin)):
                content = path.read_text(encoding="utf-8")
                for needle in forbidden:
                    self.assertNotIn(needle, content)


if __name__ == "__main__":
    unittest.main()


```


```

## tests/.sdd/task-2-fix-2-report.md

```text
# Task 2 fix round 2 report

## Change

Updated only `tests/unit/test_entities_and_authority.py` and this report. The duplicate raw JSON-key detector now enters `plugin_reader(root)` while the synthetic Vault index is valid. Inside that loaded-reader context, it writes the duplicate `concept.sample` keys and calls `reader.locate_vault()` within `assertRaises(reader.VaultError)`, then requires `code == "INVALID_VAULT"`. This arrangement keeps a future correct reader import from failing before the explicit assertion is reached.

No Plugin runtime, Vault, Production, dependency, user configuration, or Git changes were made. No commits were created.

## Focused result

Command:

```text
python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v
```

Result:

```text
Ran 26 tests in 2.064s
FAILED (failures=1)
exit code: 1
```

Expected deliberate failure: `test_duplicate_stable_id_in_raw_index_requires_reader_rejection` at `tests/unit/test_entities_and_authority.py:83` reports `AssertionError: VaultError not raised`. The other 25 tests passed. Current `vault_reader.locate_vault()` parses the raw index with `json.loads`, which silently retains one duplicate object-key value, then accepts the resulting dictionary. The required reader-level duplicate-ID rejection remains unmet; the test was not weakened.


```

## tests/unit/test_entities_and_authority.py

```text
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


```
