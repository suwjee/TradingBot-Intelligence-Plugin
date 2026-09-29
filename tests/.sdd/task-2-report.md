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
