# Task 3 fix round 3 report

## Independent genericity control

Added `test_verify_package_rejects_tampered_generic_indexed_frontmatter` with a neutral synthetic `system.sample` entity. Its `validation_tier: sampled` metadata appears in both the note frontmatter and raw `_INDEX/entities.json`. The untampered `verify_package("knowledge")` baseline returns `ok=true` with no errors. The test then changes only the note field to `validation_tier: complete`, leaves the index untouched, and requires `ok=false` with an error identifying the exact note path or a stale/integrity/mismatch condition tied to the entity or field. This control is independent of Order naming and requires general indexed-field validation.

The existing Order detector retains the same untampered-baseline and note-only-tamper sequence. Neither detector is skipped or marked expected failure.

## Fresh focused command

`python -B -m unittest tests.unit.test_evidence_and_raw tests.unit.test_verifier tests.contract.test_integrity_contract tests.security.test_untrusted_paths tests.security.test_protocol_safety -v`

- Exit code: **1**
- Tests: **25 total; 22 passed, 2 failed, 1 skipped**
- Failure 1: `test_verify_package_rejects_tampered_generic_indexed_frontmatter` — current source returns `ok=true` after the neutral indexed metadata field changes in the note.
- Failure 2: `test_verify_package_rejects_tampered_order_contract_frontmatter` — current source returns `ok=true` after the indexed Order contract field changes in the note.
- Classification: both failures expose the same generalized **PLUGIN_BUG**: `verify_package("knowledge")` does not reject a note/index mismatch for arbitrary indexed frontmatter fields. An Order-A-only rejection would leave the neutral control failing.
- Skip: `test_symlink_source_escape_is_rejected_when_available` because Windows denied symlink creation with `WinError 1314`.

## Mutation and Git boundary

Both integrity tests snapshot the entire temporary synthetic Vault immediately after their note-only tamper and assert identical file identities after verification. Each identity includes relative path, byte count, and SHA-256. The synthetic Vaults are automatically cleaned temporary directories. Only `tests/contract/test_integrity_contract.py` and this report under `tests/.sdd/` were edited in this round. No Plugin runtime, real Vault, Production, dependency, configuration, or cache file was edited. No Git command, commit, stage, push, worktree, reset, clean, or stash action was performed.
