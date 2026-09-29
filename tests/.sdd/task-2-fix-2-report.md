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
