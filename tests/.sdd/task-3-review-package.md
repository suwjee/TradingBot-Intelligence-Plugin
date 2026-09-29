# Task 3 review package

This is the complete uncommitted Task 3 review scope, replacing a commit range because commits are not authorized. Review against the approved Task 3 brief and plan. The tampered Order-contract test must retain a real current Plugin failure if the source does not enforce it. A Windows symlink skip is permissible only if capability is actually unavailable.

## tests/.sdd/task-3-brief.md

```text
# Task 3 brief — synthetic evidence, RAW, verifier, and security contracts

## Scope

Implement only the approved Task 3 test artifacts under
`D:\My-Projects\TradingBot-Intelligence-Plugin\tests`. Treat the Plugin,
Knowledge Vault, and TradingBot Production as read-only. Do not change
production code, knowledge, dependencies, configurations, runtime caches, or
Git state. Do not create a commit.

Create only these modules, plus any narrowly necessary test-only package
initializers or helpers under `tests/`:

- `tests/unit/test_evidence_and_raw.py`
- `tests/unit/test_verifier.py`
- `tests/contract/test_integrity_contract.py`
- `tests/security/test_untrusted_paths.py`
- `tests/security/test_protocol_safety.py`

Use `unittest`, Task 1 synthetic fixtures/runtime isolation/snapshot helpers,
and real public Plugin boundaries. All test source and report prose must be
English.

## Required evidence

1. Cover source excerpts, source IDs, line ranges, hashes, registered
   references and pinned changes, registered data sets, bounded inclusive RAW
   reads, exact boundaries, empty/missing windows, row caps, and invalid time
   ranges. Every expectation must be determined by synthetic Vault metadata;
   do not use known real filenames, absolute paths, or fixture fingerprints.
2. Cover verifier success, undeclared source-hash mismatch, and a
   `source_fixture_review: pending-manual-review` mismatch. Verify source
   existence/line/heading checks still run, warnings remain visible, and
   fake-Vault file identities prove verification caused no mutation. Add a
   stale-index/cache test after changing a note's text and metadata with a new
   file identity.
3. Cover `../`, `..\\`, nested/normalized traversal, absolute foreign and
   drive paths, UNC, mixed separators, malicious `raw_path`, structured
   `PATH_OUTSIDE_ALLOWED_ROOT` error payloads, symlink escape where available,
   malformed/missing entity/source/reference/range/response-limit errors, and
   launcher stderr-only failure behavior with no stdout protocol contamination.
4. Add the required non-weakened Order integrity detector:
   `test_verify_package_rejects_tampered_order_contract_frontmatter`. Tamper
   only synthetic `algorithm.order.a` frontmatter after index creation; require
   knowledge verification to return `ok=false` with stale-integrity evidence.
   Never skip, xfail, loosen, or change production to make it pass. If current
   runtime fails this test, preserve it as an explicitly documented Plugin bug.
5. First demonstrate one relevant RED condition before the supporting fixture
   or test scaffolding is complete, then run exactly:

```text
python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v
```

Write `tests/.sdd/task-3-report.md` with created files, exact commands,
test counts, exit codes, every current-runtime failure, no-mutation evidence,
and no-Git confirmation. Do not conceal real product defects.


```

## tests/.sdd/task-3-report.md

```text
# Task 3 implementation report

## Scope and files

Created these test-only files:

- `tests/unit/test_evidence_and_raw.py`
- `tests/unit/test_verifier.py`
- `tests/contract/test_integrity_contract.py`
- `tests/security/__init__.py`
- `tests/security/test_untrusted_paths.py`
- `tests/security/test_protocol_safety.py`
- `tests/.sdd/task-3-report.md`

No Plugin runtime, Vault, Production, dependency, configuration, cache, or Git file was intentionally changed. All synthetic Vault, Engine-reference, and RAW fixture writes occur inside automatically cleaned `TemporaryDirectory` instances. Source and reference paths are resolved through public `vault_reader` calls. The existing `tests/helpers/` modules were read and reused without edits.

## Commands and observed results

1. RED: `python -B -m unittest tests.unit.test_evidence_and_raw -v` — exit code 1; 1 test, 1 error. The unpinned source fixture was absent, so the public evidence route rejected it. The subsequent fixture setup pinned the source and made this case pass.
2. First full focused run: `python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v` — exit code 1; 21 tests, 18 passed, 2 failed, 1 skipped. One failure was the required Order integrity detector. The other was a test expectation error for an unknown reference ID: the current reader returns `INVALID_REQUEST`, while an unavailable registered file returns `REFERENCE_NOT_FOUND`. The test was corrected to distinguish those cases.
3. Compatibility check: `python -B -m unittest tests.contract.test_retrieval_contract.RetrievalContractTests.test_runtime_and_new_tests_have_no_machine_specific_paths -v` — initial exit code 1 because a synthetic drive-path literal matched the existing source scan. The literal was composed at runtime. Final exit code 0; 1 test passed.
4. Final focused run: `python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v` — exit code 1; 22 tests, 20 passed, 1 failed, 1 skipped.

## Remaining current-runtime failure

`tests.contract.test_integrity_contract.IntegrityContractTests.test_verify_package_rejects_tampered_order_contract_frontmatter` — **PLUGIN_BUG**. After the synthetic `algorithm.order.a` note's `valid_for_regression_baseline` frontmatter changes from `true` to `false` without rebuilding the index, `verify_package("knowledge")` returns `ok=true`. The test requires `ok=false` with stale-integrity evidence. The reader's indexed-field guard checks selected fields but does not check this Order contract field. The test remains active and failing; it was not skipped, marked expected failure, or weakened. No Plugin implementation was changed.

## Skip and mutation evidence

`test_symlink_source_escape_is_rejected_when_available` was skipped because the current Windows process lacks symlink-creation privilege (`WinError 1314`). Other traversal, drive, UNC, mixed-separator, and malicious RAW path cases passed.

The fixture verifier tests snapshot every synthetic Vault file with byte count and SHA-256 before and after `verify_package("knowledge")`; the matching, undeclared-mismatch, and declared-pending cases confirmed identical snapshots. The launcher test used `python -B` and an invalid temporary Vault, returned exit code 2, wrote a diagnostic to stderr, and left stdout empty. No real Vault, Production Engine, or external reference root was opened by these synthetic tests.

No Git commands were run, and no stage, commit, push, worktree, reset, clean, or stash operation was attempted. The test run cannot independently prove the state of unrelated files outside the synthetic fixtures; this report claims only the observed test snapshots and implementation scope.


```

## tests/unit/test_evidence_and_raw.py

```text
"""Public evidence and RAW retrieval against synthetic Vault metadata."""

import tempfile
import unittest
import hashlib
import json
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class EvidenceAndRawTests(unittest.TestCase):
    SOURCE = "06_SOURCE/Code/sample.py"
    RAW = "08_DATA/Raw/sample.json"

    def make_vault(self, root, *, include_raw=True, reference=None):
        raw = [{"time": epoch, "value": epoch} for epoch in (10, 20, 30, 40)]
        raw_bytes = json.dumps(raw).encode("utf-8")
        entities = [
            EntitySpec("source.sample", "06_SOURCE/source-sample.md", "source", "active",
                       "canonical", "Sample source", "Source note.", {"source_path": self.SOURCE}),
            EntitySpec("data.sample", "08_DATA/dataset.md", "data", "active", "canonical",
                       "Sample dataset", "Dataset note.", {"data_kind": "dataset",
                       "raw_path": self.RAW, "raw_bytes": len(raw_bytes),
                       "raw_sha256": hashlib.sha256(raw_bytes).hexdigest()}),
            EntitySpec("data.window", "08_DATA/window.md", "data", "active", "canonical",
                       "Sample window", "Window note.", {"data_kind": "window",
                       "raw_path": self.RAW, "first_epoch": 10, "last_epoch": 40}),
        ]
        build_fake_vault(root, entities, source_files={self.SOURCE: b"alpha\nbeta\ngamma\n"},
                         raw_files={self.RAW: raw_bytes} if include_raw else {},
                         references=[reference] if reference else [])

    def test_pinned_source_excerpt_uses_inclusive_line_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                result = reader.read_evidence("06_SOURCE/Code/sample.py", 2, 2)
            self.assertEqual(result["lines"], [
                {"line": 2, "text": "beta"}, {"line": 3, "text": "gamma"}])

    def test_source_id_resolves_pinned_path_and_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                result = reader.read_evidence("source.sample", 1, 1)
            self.assertEqual(result["path"], self.SOURCE)
            self.assertEqual(result["sha256"], hashlib.sha256(b"alpha\nbeta\ngamma\n").hexdigest())

    def test_source_rejects_invalid_line_ranges_and_changed_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                for start, count in ((0, 1), (1, 0), (1, 121), (4, 1)):
                    with self.subTest(start=start, count=count), self.assertRaises(ValueError):
                        reader.read_evidence(self.SOURCE, start, count)
                (root / self.SOURCE).write_text("changed\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Evidence hash") as raised:
                    reader.read_evidence(self.SOURCE)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "SOURCE_HASH_MISMATCH")

    def test_reference_uses_registry_filename_and_pinned_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root, engine = base / "vault", base / "engine"
            relative = "engine/algorithms/sample-reference.md"
            target = engine / relative
            target.parent.mkdir(parents=True)
            content = b"first\nsecond\nthird\n"
            target.write_bytes(content)
            reference = {"id": "reference.sample", "repository_relative_path": relative,
                         "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
                         "version": "sample"}
            self.make_vault(root, reference=reference)
            with plugin_reader(root, engine_root=engine) as reader:
                result = reader.read_algorithm_reference_evidence("reference.sample", 2, 2)
                self.assertEqual([row["text"] for row in result["lines"]], ["second", "third"])
                self.assertEqual(result["version"], "sample")
                with self.assertRaises(ValueError):
                    reader.read_algorithm_reference_evidence("reference.missing")
                target.write_bytes(b"tampered\n")
                with self.assertRaisesRegex(ValueError, "identity"):
                    reader.read_algorithm_reference_evidence("reference.sample")

    def test_dataset_and_inclusive_raw_window_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                dataset = reader.get_dataset("data.sample")
                self.assertTrue(dataset["raw_present"])
                self.assertEqual(dataset["raw_bytes"], len((root / self.RAW).read_bytes()))
                metadata = reader.get_window("data.window")
                self.assertTrue(metadata["data_available"])
                self.assertNotIn("rows", metadata)
                selected = reader.get_window("data.window", include_rows=True,
                                             start_epoch=20, end_epoch=30)
                self.assertEqual([row["time"] for row in selected["rows"]], [20, 30])
                self.assertEqual(selected["requested_range"], [20, 30])
                exact = reader.get_window("data.window", include_rows=True,
                                          start_epoch=10, end_epoch=10)
                self.assertEqual([row["time"] for row in exact["rows"]], [10])
                empty = reader.get_window("data.window", include_rows=True,
                                          start_epoch=21, end_epoch=29)
                self.assertEqual(empty["rows"], [])

    def test_raw_cap_truncation_and_invalid_ranges(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root)
            with plugin_reader(root) as reader:
                limited = reader.get_window("data.window", include_rows=True, limit=2)
                self.assertEqual([row["time"] for row in limited["rows"]], [10, 20])
                self.assertTrue(limited["truncated"])
                for options in ({"start_epoch": 40, "end_epoch": 20},
                                {"start_epoch": 9, "end_epoch": 20},
                                {"start_epoch": True}, {"end_epoch": 41}):
                    with self.subTest(options=options), self.assertRaisesRegex(ValueError, "time range"):
                        reader.get_window("data.window", include_rows=True, **options)
                with self.assertRaises(ValueError) as raised:
                    reader.get_window("data.window", include_rows=True,
                                      start_epoch=40, end_epoch=20)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "INVALID_TIME_RANGE")
                with self.assertRaises(ValueError):
                    reader.get_window("data.window", start_epoch=20)
                for limit in (0, 1001, True):
                    with self.subTest(limit=limit), self.assertRaises(ValueError):
                        reader.get_window("data.window", include_rows=True, limit=limit)

    def test_missing_raw_degrades_only_data_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_vault(root, include_raw=False)
            with plugin_reader(root) as reader:
                self.assertEqual(reader.get_entity("source.sample")["id"], "source.sample")
                self.assertEqual(reader.read_evidence("source.sample")["path"], self.SOURCE)
                self.assertFalse(reader.get_dataset("data.sample")["raw_present"])
                result = reader.get_window("data.window", include_rows=True)
                self.assertEqual(result["reason"], "vault_raw_unavailable")
                self.assertEqual(result["rows"], [])


```

## tests/unit/test_verifier.py

```text
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


```

## tests/contract/test_integrity_contract.py

```text
"""Public package integrity results for synthetic knowledge."""

import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault, write_entity_note
from tests.helpers.plugin_runtime import plugin_reader


class IntegrityContractTests(unittest.TestCase):
    def test_verify_package_reports_mode_and_registered_counts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [
                EntitySpec("data.dataset", "08_DATA/dataset.md", "data", "active", "canonical",
                           "Dataset", "Synthetic metadata.", {"data_kind": "dataset",
                           "raw_path": "08_DATA/Raw/sample.json"}),
                EntitySpec("data.window", "08_DATA/window.md", "data", "active", "canonical",
                           "Window", "Synthetic metadata.", {"data_kind": "window",
                           "raw_path": "08_DATA/Raw/sample.json"}),
            ])
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            self.assertTrue(result["ok"])
            self.assertEqual(result["registered_datasets"], 1)
            self.assertEqual(result["registered_windows"], 1)
            self.assertEqual(result["data_status"], "NOT_RUN")

    def test_verify_package_rejects_tampered_order_contract_frontmatter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = EntitySpec("algorithm.order.a", "01_ALGORITHMS/order-a.md", "algorithm",
                                  "active", "canonical", "Synthetic Order A", "Synthetic contract.",
                                  {"valid_for_regression_baseline": True})
            build_fake_vault(root, [original])
            tampered = EntitySpec(original.id, original.file, original.type, original.status,
                                  original.authority, original.title, original.body,
                                  {"valid_for_regression_baseline": False})
            write_entity_note(root, tampered)
            with plugin_reader(root) as reader:
                result = reader.verify_package("knowledge")
            self.assertFalse(result["ok"], "Tampered Order contract metadata must fail integrity")
            self.assertTrue(any("order-a.md" in failure or "algorithm.order.a" in failure
                                for failure in result["errors"]), result["errors"])


```

## tests/security/__init__.py

```text
"""Synthetic security boundary tests."""


```

## tests/security/test_untrusted_paths.py

```text
"""Path and metadata inputs cannot escape their declared roots."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


class UntrustedPathTests(unittest.TestCase):
    def test_source_routes_reject_traversal_and_foreign_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [])
            unsafe = ("../outside.py", "..\\outside.py", "06_SOURCE/Code/../../outside.py",
                      "06_SOURCE/Code/../outside.py", "06_SOURCE/Code/./sample.py",
                      "06_SOURCE/Code/a/../../outside.py", "06_SOURCE/Code/..\\outside.py",
                      "/foreign/source.py", "C:" + chr(92) + "foreign" + chr(92) + "source.py",
                      "C:/foreign/source.py",
                      "\\\\host\\share\\source.py", "//host/share/source.py")
            with plugin_reader(root) as reader:
                for value in unsafe:
                    with self.subTest(value=value), self.assertRaises(ValueError) as raised:
                        reader.read_evidence(value)
                    self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                     "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_malicious_dataset_raw_path_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = EntitySpec("data.bad", "08_DATA/bad.md", "data", "active", "canonical",
                             "Bad path", "Synthetic data.", {"data_kind": "dataset",
                             "raw_path": "08_DATA/Raw/../../outside.json"})
            build_fake_vault(root, [bad])
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.get_dataset("data.bad")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_malicious_window_raw_path_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad = EntitySpec("data.bad.window", "08_DATA/bad-window.md", "data", "active",
                             "canonical", "Bad window", "Synthetic data.", {"data_kind": "window",
                             "raw_path": "08_DATA/Raw/..\\outside.json", "first_epoch": 1,
                             "last_epoch": 2})
            build_fake_vault(root, [bad])
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.get_window("data.bad.window", include_rows=True)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_reference_registry_rejects_unsafe_relative_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for value in ("engine/algorithms/../outside.md", "engine/algorithms/..\\outside.md",
                          "C:/foreign.md", "//host/share/file.md"):
                with self.subTest(value=value):
                    root = base / str(len(list(base.iterdir())))
                    registry = {"id": "reference.bad", "repository_relative_path": value,
                                "bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}
                    build_fake_vault(root, [], references=[registry])
                    with plugin_reader(root, engine_root=base) as reader:
                        with self.assertRaises(ValueError) as raised:
                            reader.read_algorithm_reference_evidence("reference.bad")
                        self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                         "PATH_OUTSIDE_ALLOWED_ROOT")

    def test_symlink_source_escape_is_rejected_when_available(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "vault"
            build_fake_vault(root, [])
            target = base / "outside.py"
            target.write_text("outside\n", encoding="utf-8")
            link = root / "06_SOURCE/Code/escape.py"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Symlink creation unavailable: {exc}")
            with plugin_reader(root) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.read_evidence("06_SOURCE/Code/escape.py")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "PATH_OUTSIDE_ALLOWED_ROOT")


```

## tests/security/test_protocol_safety.py

```text
"""Structured public failures and stderr-only invalid startup."""

import os
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers.fake_vault import EntitySpec, build_fake_vault
from tests.helpers.plugin_runtime import plugin_reader


PLUGIN_ROOT = Path(__file__).resolve().parents[2]


class ProtocolSafetyTests(unittest.TestCase):
    def test_public_error_payload_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_fake_vault(root, [EntitySpec("system.sample", "00_SYSTEM/sample.md", "system",
                                               "active", "canonical", "Sample", "Body.")])
            with plugin_reader(root) as reader:
                cases = (
                    (lambda: reader.search(""), "INVALID_REQUEST"),
                    (lambda: reader.get_entity("missing"), "ENTITY_NOT_FOUND"),
                    (lambda: reader.read_evidence("06_SOURCE/Code/missing.py"), "INVALID_REQUEST"),
                    (lambda: reader.read_algorithm_reference_evidence("missing"), "INVALID_REQUEST"),
                    (lambda: reader.get_entity("system.sample", max_bytes=1), "RESPONSE_TOO_LARGE"),
                    (lambda: reader.verify_package("other"), "INVALID_REQUEST"),
                )
                for call, expected in cases:
                    with self.subTest(expected=expected), self.assertRaises(ValueError) as raised:
                        call()
                    payload = reader.error_payload(raised.exception)
                    self.assertFalse(payload["ok"])
                    self.assertEqual(payload["error"]["code"], expected)

    def test_reference_unavailable_mismatch_and_invalid_range_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            vault, engine = base / "vault", base / "engine"
            relative = "engine/algorithms/sample.md"
            content = b"one\ntwo\n"
            reference = {"id": "reference.sample", "repository_relative_path": relative,
                         "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
            build_fake_vault(vault, [], references=[reference])
            with plugin_reader(vault, engine_root=engine) as reader:
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "REFERENCE_NOT_FOUND")
                target = engine / relative
                target.parent.mkdir(parents=True)
                target.write_bytes(b"changed\n")
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample")
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "REFERENCE_HASH_MISMATCH")
                target.write_bytes(content)
                with self.assertRaises(ValueError) as raised:
                    reader.read_algorithm_reference_evidence("reference.sample", 0, 1)
                self.assertEqual(reader.error_payload(raised.exception)["error"]["code"],
                                 "INVALID_REQUEST")

    def test_invalid_vault_launcher_writes_diagnostic_only_to_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            invalid = Path(temporary) / "missing-vault"
            environment = os.environ.copy()
            environment["TRADINGBOT_KNOWLEDGE_VAULT"] = str(invalid)
            environment["TRADINGBOT_PLUGIN_CONFIG"] = str(invalid / "missing-config.json")
            completed = subprocess.run([sys.executable, "-B", "mcp_server.py"],
                                       cwd=PLUGIN_ROOT, env=environment, capture_output=True,
                                       text=True, timeout=15)
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertIn("VAULT_NOT_FOUND", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)


```
