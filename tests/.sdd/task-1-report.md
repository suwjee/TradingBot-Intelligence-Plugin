# Task 1 report: test foundation and synthetic Vault builder

Status: PASS for Task 1 foundation. No commits, staging, branches, worktrees,
dependency changes, Plugin runtime changes, Vault reads, or Production reads.

## Scope and files created

- `tests/__init__.py` and `tests/helpers/__init__.py`: importable test packages.
- `tests/helpers/fake_vault.py`: `EntitySpec`, `FakeVault`, `build_fake_vault`,
  `write_entity_note`, and `write_raw`. The builder writes a synthetic indexed
  authority note, user-supplied notes, deterministic entity and relation
  indexes, the schema marker, a reference registry, and SHA-256 manifest pins.
- `tests/helpers/plugin_runtime.py`: `plugin_reader` isolates import-time reader
  discovery with process-local environment and cached-module restoration.
- `tests/helpers/snapshots.py`: `FileIdentity`, `snapshot_files`, and
  `assert_unchanged` compare explicit file or directory byte identities.
- `tests/helpers/mcp_client.py`: `MCPTranscript` and a lazy-imported real stdio
  `run_mcp_session` client for later transport tests.
- `tests/unit/test_helpers.py`: five synthetic foundation tests.
- `tests/README.md`: suite architecture, prerequisites, environment, category
  and full-discovery commands, optional skip policy, and verification modes.

## Required RED evidence

Command, from `D:\My-Projects\TradingBot-Intelligence-Plugin`:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `1`. This was run after creating the first test and before creating
any helper implementation. Its failure was the expected missing module:

```text
test_helpers (unittest.loader._FailedTest.test_helpers) ... ERROR
ImportError: Failed to import test module: test_helpers
ModuleNotFoundError: No module named 'tests.helpers.fake_vault'
Ran 1 test in 0.000s
FAILED (errors=1)
```

## GREEN evidence

Command, from the same directory after helper and README implementation:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `0`. Exact final output:

```text
test_entity_index_is_deterministic_across_input_order (tests.unit.test_helpers.FoundationTests.test_entity_index_is_deterministic_across_input_order) ... ok
test_one_entity_vault_is_read_by_fresh_plugin_reader (tests.unit.test_helpers.FoundationTests.test_one_entity_vault_is_read_by_fresh_plugin_reader) ... ok
test_plugin_reader_restores_environment_and_module_cache (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_environment_and_module_cache) ... ok
test_reference_registry_and_source_pins_match_bytes (tests.unit.test_helpers.FoundationTests.test_reference_registry_and_source_pins_match_bytes) ... ok
test_snapshot_detects_changed_file (tests.unit.test_helpers.FoundationTests.test_snapshot_detects_changed_file) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.104s

OK
```

The pin test also calls the unmodified Plugin reader's
`verify_package("knowledge")` against temporary synthetic content and observes
`ok=True`.

## Self-review and limits

- All writes are test source under `tests/` or temporary synthetic Vault files
  created by test execution. No real Vault or Engine material is imported or
  copied by the helpers.
- Entity index serialization is sorted by stable ID; source and RAW pin order
  is sorted by path. Synthetic path writes reject traversal and drive syntax.
- `plugin_reader` restores the three environment variables and four relevant
  Plugin module cache entries even when a call raises. Because it temporarily
  changes process globals, callers should not overlap its contexts in threads.
- `run_mcp_session` was implemented from the Plugin's stdio client contract but
  not exercised by Task 1. The actual MCP transport remains for Task 5.
- Other planned category modules do not exist yet. A full-suite success claim
  would be premature; this result covers only the Task 1 foundation tests.

## Fix round 1: relation index and exception cleanup

The review found that supplied relations were written only to
`_INDEX/relations.json`. The reader reconstructs expected relations from note
frontmatter, so that fixture failed knowledge verification. The builder now
adds supplied edges to the corresponding note relation fields and derives the
index from the final note fields. It validates indexed endpoints and supported
relation types. Existing list values are copied before appending, so caller
frontmatter is not mutated.

Two tests were added: a two-entity `depends_on` fixture that requires
`verify_package("knowledge")` to succeed and a body exception inside
`plugin_reader()` that requires environment and module-cache restoration.

RED command, from the Plugin repository root:

```powershell
python -B -m unittest tests.unit.test_helpers -v
```

Exit code: `1`. The new exception test passed; the relation test exposed the
reported failure:

```text
test_plugin_reader_restores_state_after_body_exception ... ok
test_relation_argument_produces_verifiable_note_and_index ... FAIL
AssertionError: False is not true : ['_INDEX/relations.json']
Ran 7 tests in 0.262s
FAILED (failures=1)
```

GREEN command: the same focused command after the builder change. Exit code:
`0`. Exact final output:

```text
test_entity_index_is_deterministic_across_input_order (tests.unit.test_helpers.FoundationTests.test_entity_index_is_deterministic_across_input_order) ... ok
test_one_entity_vault_is_read_by_fresh_plugin_reader (tests.unit.test_helpers.FoundationTests.test_one_entity_vault_is_read_by_fresh_plugin_reader) ... ok
test_plugin_reader_restores_environment_and_module_cache (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_environment_and_module_cache) ... ok
test_plugin_reader_restores_state_after_body_exception (tests.unit.test_helpers.FoundationTests.test_plugin_reader_restores_state_after_body_exception) ... ok
test_reference_registry_and_source_pins_match_bytes (tests.unit.test_helpers.FoundationTests.test_reference_registry_and_source_pins_match_bytes) ... ok
test_relation_argument_produces_verifiable_note_and_index (tests.unit.test_helpers.FoundationTests.test_relation_argument_produces_verifiable_note_and_index) ... ok
test_snapshot_detects_changed_file (tests.unit.test_helpers.FoundationTests.test_snapshot_detects_changed_file) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.175s

OK
```

Files changed in this round: `tests/helpers/fake_vault.py`,
`tests/unit/test_helpers.py`, and this report. No production source was changed.
