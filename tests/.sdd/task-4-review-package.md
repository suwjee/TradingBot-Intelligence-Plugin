# Task 4 review package

This is the complete uncommitted Task 4 review scope. Review against the approved brief and Task 4 plan. Treat the recorded Engine count discrepancy as a current observation needing honest test behavior, not permission to hardcode an old count.

## tests/.sdd/task-4-brief.md

```text
# Task 4 brief — read-only real-Vault integration

## Scope and immutable boundary

Implement the approved Task 4 integration tests only under
`D:\My-Projects\TradingBot-Intelligence-Plugin\tests`. The Plugin runtime,
TradingBot Knowledge Vault, Engine, external references, Production checkout,
dependencies, configuration, caches, and Git state are read-only. Do not run
Graphify. Do not use Git or create commits.

Create:

- `tests/helpers/real_roots.py`
- `tests/integration/__init__.py`
- `tests/integration/test_real_vault.py`
- `tests/integration/test_real_engine_evidence.py`
- `tests/integration/test_real_data_and_read_only.py`

All test code and report prose must be English. Tests must not hard-code host
paths, derived module filenames, reference filenames, data IDs, raw filenames,
line numbers, entities beyond the mandatory stable-ID claims, or hash values.
Derive all variable objects from active registry, manifest, frontmatter, and
public reader results.

## Required behavior

1. `require_real_roots(testcase)` must read only the designated environment
   variables, verify paths, and raise `SkipTest` with exactly one actionable
   missing-resource reason when unavailable. Use it in real integration tests.
2. Check current canonical Order A authority/status/validity from returned
   frontmatter; default-versus-explicit Order B/C retrieval; absent active
   OrderAudit with discoverable `order_audit` source evidence; and Type-3 S
   entity/current metadata/relations/source-algorithm linkage without asserting
   a trading formation.
3. Parse the raw entity index using `object_pairs_hook` before ordinary JSON
   decoding to reject duplicate object keys. Check relation triplet uniqueness,
   endpoints, indexed note paths, and every source anchor's file and one-based
   range. `verify_package('knowledge')` must have no errors; record
   `known_pending` as an observed status rather than inferring PASS/FAIL.
4. From active Vault records, derive captured Engine paths (currently nine),
   mirror mapping, and two registry external references. Verify every selected
   Engine/reference pair through byte and SHA-256 identity plus bounded
   Bullish/Bearish reference-evidence calls.
5. Derive a registered dataset and window. Check metadata-only versus bounded
   inclusive RAW read and cap behavior. Snapshot selected Vault files, every
   derived Engine module, and both references before/after all public reader
   operations and both verification modes; assert no mutation.

First run a meaningful RED condition appropriate for a test-suite task, then
run exactly:

```text
python -B -m unittest discover -s tests/integration -t . -v
```

Write `tests/.sdd/task-4-report.md` with real-root availability, commands,
exact counts/exit codes, bounded no-mutation identity evidence, current facts
versus assumptions, all skips, failures, and a no-Git confirmation. Never
massage failing real-world evidence.


```

## tests/.sdd/task-4-report.md

```text
# Task 4 read-only integration report

## Outcome

The Task 4 integration layer contains nine `unittest` tests in three integration
modules, plus one real-root helper and the package initializer. The live run
completed with **9 PASS, 0 FAIL, 0 SKIP** and exit code **0**. No Plugin runtime,
Vault, Engine, external reference, Production, configuration, dependency, cache,
or Git state was changed by this task.

## Commands and exact results

| Purpose | Command | Exit | PASS | FAIL | SKIP |
| --- | --- | ---: | ---: | ---: | ---: |
| RED precondition | `python -B -m unittest tests.integration.test_real_vault -v` | 1 | 0 | 1 import error | 0 |
| Exact Task 4 command, inherited environment | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 0 | 0 | 9 |
| Live integration, process-local root variables | `python -B -m unittest discover -s tests/integration -t . -v` | 0 | 9 | 0 | 0 |

The RED import error was `ModuleNotFoundError: No module named
'tests.helpers.real_roots'`; that helper did not yet exist. The exact command
skipped all nine tests because `TRADINGBOT_KNOWLEDGE_VAULT` was unset. The live
run set `TRADINGBOT_KNOWLEDGE_VAULT` and `TRADINGBOT_ENGINE_ROOT` only in the
test process's shell; it took 4.951 seconds. Both configured roots were present.
No required resource was missing in the live run.

## Current facts and bounded identity evidence

- The active manifest produced **12** captured Engine file pairs, not the
  plan's recorded nine. Every pair passed byte, length, and SHA-256 equality.
  The count comes from the active manifest; the tests do not encode filenames.
- The active registry produced **2** external references. Both passed byte,
  length, and SHA-256 checks and bounded public evidence reads.
- `algorithm.order.a` returned canonical, normative, valid metadata. Explicit
  `algorithm.order.b` and `.c` retrieval retained non-canonical warnings while
  default search excluded them. `algorithm.orderaudit` was absent from the active
  entity index, and a pinned source containing `order_audit` remained readable.
  `behavior.s.blue.type3` returned indexed metadata, graph links, and pinned
  source anchors. These are retrieval facts, not trading-rule validation.
- The selected registered data IDs were `data.dataset_062df750` and
  `data.window_0291455b`. Metadata-only window retrieval omitted rows; bounded
  reads honored both exact endpoint epochs and the row cap.
- The protected snapshot covered **35 distinct files** and **58,114,599 bytes**:
  selected Vault indexes/notes/RAW, every derived Vault Engine mirror, every
  corresponding configured Engine file, and both external references. The
  sorted path/size/SHA-256 identity aggregate was
  `4986b5de2b15a2cf5efa2505b95d3b5b7760cabe4f936be70bce21a65c34ff88`.
  The test asserted identical before/after identities around public search,
  knowledge, relations, source, reference, dataset, window, `knowledge`
  verification, and `full-data` verification. Both verification modes returned
  empty `errors`; each returned `known_pending` count **0** in this observed run.

## Scope and limits

The first exact command is a valid skip result, not a live PASS. The live PASS
depends on process-local root configuration and the current contents of those
roots; a later checkout should rerun it. The snapshot proves no mutation of
the selected 35 files during the operation sequence, not of every file under
all roots. No Graphify command, Git command, stage, commit, or push was run.


```

## tests/helpers/real_roots.py

```text
"""Explicit, read-only roots for real integration tests."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import unittest


@dataclass(frozen=True)
class RealRoots:
    vault: Path
    engine: Path


def require_real_roots(testcase: unittest.TestCase) -> RealRoots:
    """Require both configured roots, reporting the first actionable absence."""
    requirements = (
        ("TRADINGBOT_KNOWLEDGE_VAULT", ("_INDEX/entities.json", "_INDEX/relations.json",
                                           "_INDEX/source-hashes.json", "06_SOURCE/References/registry.json")),
        ("TRADINGBOT_ENGINE_ROOT", ("engine",)),
    )
    resolved = []
    for name, required in requirements:
        configured = os.environ.get(name)
        if not configured:
            raise unittest.SkipTest(f"Set {name} to the real checkout root")
        root = Path(configured).expanduser().resolve()
        if not root.is_dir():
            raise unittest.SkipTest(f"{name} is not an existing directory: {root}")
        for relative in required:
            if not (root / relative).exists():
                raise unittest.SkipTest(f"{name} is missing required resource: {relative}")
        resolved.append(root)
    return RealRoots(*resolved)


```

## tests/integration/__init__.py

```text
"""Read-only integration checks against configured real roots."""


```

## tests/integration/test_real_vault.py

```text
"""Live Vault retrieval and graph contracts."""

import json
from pathlib import Path
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
    def test_required_roots_are_checked_before_live_reads(self):
        roots = require_real_roots(self)
        self.assertTrue(roots.vault.is_dir())
        self.assertTrue(roots.engine.is_dir())

    def test_current_order_metadata_and_diagnostic_retrieval(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            order_a = reader.get_entity("algorithm.order.a")
            fields = frontmatter(order_a["content"])
            for key in ("status", "authority", "valid_for_reasoning",
                        "valid_for_validation", "valid_for_regression_baseline"):
                self.assertEqual(order_a.get(key, fields.get(key)), fields[key])
            self.assertEqual(fields["status"], "canonical")
            self.assertEqual(fields["authority"], "normative")
            for key in ("valid_for_reasoning", "valid_for_validation", "valid_for_regression_baseline"):
                self.assertIs(fields[key], True, key)
            for entity_id in ("algorithm.order.b", "algorithm.order.c"):
                self.assertIn(entity_id, entities)
                result = reader.get_entity(entity_id)
                metadata = frontmatter(result["content"])
                self.assertEqual(result["status"], metadata["status"])
                self.assertEqual(result["authority"], metadata["authority"])
                self.assertFalse(metadata["valid_for_reasoning"])
                self.assertTrue(result["warning"])
                self.assertNotIn(entity_id, [hit["id"] for hit in reader.search(entity_id, limit=25)])
                self.assertIn(entity_id, [hit["id"] for hit in
                                     reader.search(entity_id, limit=25, include_quarantined=True)])

    def test_orderaudit_is_not_active_but_pinned_source_is_readable(self):
        roots = require_real_roots(self)
        entities = load_index(roots)
        self.assertNotIn("algorithm.orderaudit", entities)
        manifest = json.loads((roots.vault / "_INDEX/source-hashes.json").read_text(encoding="utf-8-sig"))
        candidates = [row.get("mirror", row.get("source", row.get("path")))
                      for row in manifest["files"] + manifest.get("algorithm_references", [])
                      + manifest.get("supporting_files", [])]
        matching = [path for path in candidates if path and path.startswith("06_SOURCE/Code/")
                    and "order_audit" in (roots.vault / path).read_text(encoding="utf-8-sig").lower()]
        self.assertTrue(matching, "No pinned source contains order_audit")
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            self.assertEqual(reader.read_evidence(matching[0], 1, 1)["path"], matching[0])

    def test_type3_metadata_relations_and_evidence_linkage(self):
        roots = require_real_roots(self)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            result = reader.get_entity("behavior.s.blue.type3")
            metadata = frontmatter(result["content"])
            for key in ("status", "authority", "title"):
                self.assertEqual(result[key], metadata[key])
            graph = reader.relations(result["id"], include_quarantined=True)
            outgoing = {(edge["type"], edge["to"]) for edge in graph["outgoing"]}
            for field in ("calculated_by", "implemented_by"):
                for target in metadata.get(field, []):
                    self.assertIn((field, target), outgoing)
                    self.assertEqual(reader.get_entity(target)["id"], target)
            self.assertTrue(metadata.get("source_refs"))
            for anchor in metadata["source_refs"]:
                match = re.fullmatch(r"([^#]+)#L([1-9][0-9]*)", anchor)
                self.assertIsNotNone(match, anchor)
                self.assertEqual(reader.read_evidence(match[1], int(match[2]), 1)["path"], match[1])

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
                if row["type"] == "source":
                    for anchor in metadata.get("source_refs", []) + metadata.get("source_reference", []):
                        match = re.fullmatch(r"([^#]+)#L([1-9][0-9]*)", anchor)
                        self.assertIsNotNone(match, anchor)
                        source_path = (roots.vault / match[1]).resolve()
                        self.assertTrue(source_path.is_relative_to(roots.vault) and source_path.is_file())
                        self.assertLessEqual(int(match[2]), len(source_path.read_text(encoding="utf-8-sig").splitlines()))
            verified = reader.verify_package("knowledge")
            self.assertEqual(verified["errors"], [], verified["errors"])
            self.assertIsInstance(verified["known_pending"], list)


```

## tests/integration/test_real_engine_evidence.py

```text
"""Pinned Engine mirrors and registered external references."""

import hashlib
import json
import unittest

from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.real_roots import require_real_roots


def manifest_and_registry(roots):
    manifest = json.loads((roots.vault / "_INDEX/source-hashes.json").read_text(encoding="utf-8-sig"))
    registry = json.loads((roots.vault / "06_SOURCE/References/registry.json").read_text(encoding="utf-8-sig"))
    return manifest, registry


def engine_pairs(roots, manifest):
    pairs = []
    prefix = "06_SOURCE/Code/"
    for row in manifest["files"]:
        mirror = row.get("mirror", row.get("source"))
        if not mirror or not mirror.startswith(prefix + "engine/"):
            continue
        relative_engine = mirror.removeprefix(prefix)
        pairs.append((row, roots.vault / mirror, roots.engine / relative_engine))
    return pairs


class RealEngineEvidenceTests(unittest.TestCase):
    def test_all_manifest_engine_mirrors_match_configured_checkout(self):
        roots = require_real_roots(self)
        manifest, _ = manifest_and_registry(roots)
        pairs = engine_pairs(roots, manifest)
        self.assertTrue(pairs, "Manifest has no captured Engine files")
        for row, mirror, engine in pairs:
            with self.subTest(mirror=row["mirror"]):
                self.assertTrue(mirror.is_file() and engine.is_file())
                self.assertEqual(mirror.read_bytes(), engine.read_bytes())
                data = engine.read_bytes()
                self.assertEqual(len(data), row["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_registered_external_references_have_identity_and_bounded_evidence(self):
        roots = require_real_roots(self)
        _, registry = manifest_and_registry(roots)
        references = registry["references"]
        self.assertEqual(len(references), 2)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            for row in references:
                with self.subTest(reference=row["id"]):
                    path = (roots.engine / row["repository_relative_path"]).resolve()
                    self.assertTrue(path.is_relative_to(roots.engine) and path.is_file())
                    data = path.read_bytes()
                    self.assertEqual(len(data), row["bytes"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])
                    evidence = reader.read_algorithm_reference_evidence(row["id"], 1, 2)
                    self.assertEqual(evidence["reference_id"], row["id"])
                    self.assertEqual(evidence["sha256"], row["sha256"])
                    self.assertGreaterEqual(len(evidence["lines"]), 1)
                    self.assertLessEqual(len(evidence["lines"]), 2)


```

## tests/integration/test_real_data_and_read_only.py

```text
"""Registered RAW behavior and protected-file mutation checks."""

import json
import unittest

from tests.helpers.plugin_runtime import plugin_reader
from tests.helpers.real_roots import require_real_roots
from tests.helpers.snapshots import snapshot_files, assert_unchanged
from tests.integration.test_real_engine_evidence import manifest_and_registry, engine_pairs
from tests.integration.test_real_vault import load_index, frontmatter


def registered_data(roots):
    entities = load_index(roots)
    datasets = []
    windows = []
    for entity_id, row in entities.items():
        if row["type"] != "data":
            continue
        fields = frontmatter((roots.vault / row["file"]).read_text(encoding="utf-8-sig"))
        if fields.get("data_kind") == "dataset":
            datasets.append(entity_id)
        elif fields.get("data_kind") == "window":
            windows.append(entity_id)
    return sorted(datasets), sorted(windows)


def protected_paths(roots):
    manifest, registry = manifest_and_registry(roots)
    paths = [roots.vault / "_INDEX/entities.json", roots.vault / "_INDEX/relations.json",
             roots.vault / "_INDEX/source-hashes.json", roots.vault / "06_SOURCE/References/registry.json"]
    paths.extend(mirror for _, mirror, _ in engine_pairs(roots, manifest))
    paths.extend(engine for _, _, engine in engine_pairs(roots, manifest))
    paths.extend(roots.engine / row["repository_relative_path"] for row in registry["references"])
    return paths


class RealDataAndReadOnlyTests(unittest.TestCase):
    def test_registered_dataset_and_window_respect_metadata_bounds_and_cap(self):
        roots = require_real_roots(self)
        datasets, windows = registered_data(roots)
        self.assertTrue(datasets and windows)
        with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
            dataset = reader.get_dataset(datasets[0])
            self.assertEqual(dataset["metadata"]["data_kind"], "dataset")
            window_id = next((entity_id for entity_id in windows
                              if reader.get_window(entity_id)["data_available"]), None)
            if window_id is None:
                raise unittest.SkipTest("Registered RAW windows are unavailable in the configured Vault")
            metadata = reader.get_window(window_id)
            self.assertNotIn("rows", metadata)
            first = metadata["metadata"]["first_epoch"]
            last = metadata["metadata"]["last_epoch"]
            bounded = reader.get_window(window_id, include_rows=True, start_epoch=first,
                                        end_epoch=last, limit=1)
            self.assertEqual(bounded["requested_range"], [first, last])
            self.assertLessEqual(len(bounded["rows"]), 1)
            self.assertTrue(all(first <= row["time"] <= last for row in bounded["rows"]))
            self.assertEqual(bounded["truncated"], len(bounded["rows"]) == 1
                             and metadata["metadata"]["row_count"] > 1)
            for epoch in (first, last):
                exact = reader.get_window(window_id, include_rows=True,
                                          start_epoch=epoch, end_epoch=epoch, limit=1000)
                self.assertEqual([row["time"] for row in exact["rows"]], [epoch])
            with self.assertRaises(ValueError):
                reader.get_window(window_id, include_rows=True, limit=1001)

    def test_public_operations_and_both_verifiers_do_not_mutate_protected_files(self):
        roots = require_real_roots(self)
        manifest, registry = manifest_and_registry(roots)
        entities = load_index(roots)
        datasets, windows = registered_data(roots)
        self.assertTrue(datasets and windows and manifest["files"] and registry["references"])
        selected_note = roots.vault / entities["algorithm.order.a"]["file"]
        data_notes = [roots.vault / entities[entity_id]["file"] for entity_id in
                      (datasets[0], windows[0])]
        raw_paths = [roots.vault / frontmatter(path.read_text(encoding="utf-8-sig"))["raw_path"]
                     for path in data_notes]
        paths = protected_paths(roots) + [selected_note] + data_notes + raw_paths
        before = snapshot_files(paths)
        try:
            with plugin_reader(roots.vault, engine_root=roots.engine) as reader:
                self.assertEqual(reader.get_entity("algorithm.order.a")["id"], "algorithm.order.a")
                self.assertIsInstance(reader.search("order", limit=1), list)
                self.assertEqual(reader.relations("algorithm.order.a")["entity_id"], "algorithm.order.a")
                source = next(row["mirror"] for row in manifest["files"] if row["mirror"].startswith("06_SOURCE/Code/"))
                self.assertEqual(reader.read_evidence(source, 1, 1)["path"], source)
                reference_id = registry["references"][0]["id"]
                self.assertEqual(reader.read_algorithm_reference_evidence(reference_id, 1, 1)["reference_id"], reference_id)
                self.assertEqual(reader.get_dataset(datasets[0])["id"], datasets[0])
                self.assertEqual(reader.get_window(windows[0])["id"], windows[0])
                reader.get_window(windows[0], include_rows=True, limit=1)
                for mode in ("knowledge", "full-data"):
                    result = reader.verify_package(mode)
                    self.assertEqual(result["mode"], mode)
                    self.assertEqual(result["errors"], [], result["errors"])
        finally:
            after = snapshot_files(paths)
            assert_unchanged(before, after)


```
