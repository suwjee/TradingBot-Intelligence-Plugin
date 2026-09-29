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
