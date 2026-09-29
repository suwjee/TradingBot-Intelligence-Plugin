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
