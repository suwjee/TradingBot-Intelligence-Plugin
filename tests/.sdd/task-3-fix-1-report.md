# Task 3 fix round 1 report

## Review corrections

1. Added a `pending-manual-review` case with an absent source fixture. Knowledge verification returns `ok=false` and `fixture_source_missing:case.sample` in `errors`; the pending hash category does not suppress the missing-source error. Existing pending hash tests still assert heading and line validation.
2. Added a controlled outside-canary test for direct and ID-based source evidence, dataset metadata, RAW windows, and registered references. Each route returns `PATH_OUTSIDE_ALLOWED_ROOT`. A test-local boundary watches `Path.stat`, `Path.open`, `Path.read_bytes`, and `Path.read_text` for the three controlled outside files and records zero accesses. Before/after byte-count and SHA-256 snapshots of those canaries are identical.
3. Restricted symlink skipping to Windows capability/privilege errors WinError 1314 or 50. Other `OSError` instances propagate as failures.
4. In the missing Engine/reference case, `get_entity("system.authority-model")` succeeds before the registered reference call returns `REFERENCE_NOT_FOUND`.
5. The Order integrity assertion now requires an error explicitly naming a stale `valid_for_regression_baseline` indexed field. Added an exact upper RAW boundary request of `40–40`, which returns only epoch 40.

## Fresh commands

- `python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v` — exit code **1**; **24 tests**, **22 passed**, **1 failed**, **1 skipped**.
- `python -B -m unittest tests.contract.test_retrieval_contract.RetrievalContractTests.test_runtime_and_new_tests_have_no_machine_specific_paths -v` — exit code **0**; **1 passed**.

## Non-PASS outcomes

- `test_verify_package_rejects_tampered_order_contract_frontmatter`: **PLUGIN_BUG, still active**. The synthetic `algorithm.order.a` note changes only `valid_for_regression_baseline` after index creation. Current `verify_package("knowledge")` returns `ok=true`; the test requires `ok=false` and a stale-field integrity error. The test was not skipped, marked expected failure, or weakened, and Plugin code was not changed.
- `test_symlink_source_escape_is_rejected_when_available`: **SKIPPED** because symlink creation returned Windows privilege error `WinError 1314`. The skip is limited to recognized capability/privilege errors; traversal and canary path cases passed.

## Mutation and scope

The new canary test snapshots controlled outside files before and after public reader calls and confirms identical byte counts and SHA-256 digests. The missing-fixture verifier test snapshots its entire synthetic Vault after fixture removal and confirms verification does not mutate it. Synthetic files live inside automatically cleaned temporary directories. Only Task 3 test files and this report under `tests/` were edited. Plugin runtime, real Vault, Production, dependency, configuration, and cache files were not edited. No Git commands, commits, stage, push, worktree, reset, clean, or stash operations were performed.
