# Task 3 fix round 2 report

## Detector correction

`test_verify_package_rejects_tampered_order_contract_frontmatter` now adds `valid_for_regression_baseline: true` to the synthetic `algorithm.order.a` entry in raw `_INDEX/entities.json` after fake Vault creation. The matching note and indexed field form a baseline that `verify_package("knowledge")` must accept; the test observes `ok=true` and no errors before tampering. It then changes only the note frontmatter value to `false`, leaving the generated index unchanged, and requires `ok=false` with a public integrity error identifying the exact indexed note path or a stale/integrity/mismatch marker tied to the entity or field. This baseline gate prevents indiscriminate rejection of Order A notes from satisfying the detector.

## Fresh focused command

`python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v`

- Exit code: **1**
- Tests: **24 total; 22 passed, 1 failed, 1 skipped**
- Failure: `test_verify_package_rejects_tampered_order_contract_frontmatter` remains an active **PLUGIN_BUG**. Current source returns `ok=true` after the indexed Order contract field changes in the note. The test is neither skipped nor marked expected failure.
- Skip: `test_symlink_source_escape_is_rejected_when_available` because Windows denied symlink creation with `WinError 1314`; the skip applies only to recognized capability/privilege errors.

Only `tests/contract/test_integrity_contract.py` and this report under `tests/.sdd/` were edited in this round. The index and note writes performed by the test are confined to an automatically cleaned synthetic temporary Vault. No Plugin runtime, real Vault, Production, dependency, configuration, or cache file was edited. No Git commands or commit, stage, push, worktree, reset, clean, or stash actions were performed.
