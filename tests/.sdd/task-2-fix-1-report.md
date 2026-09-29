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
