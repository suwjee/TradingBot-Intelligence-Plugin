# Task 2: Synthetic discovery, entities, authority, search, and relations

## Binding constraints

- Edit only under `D:\My-Projects\TradingBot-Intelligence-Plugin\tests\`.
- Do not modify Plugin runtime source, Knowledge Vault, Production Engine, dependencies, user configuration, Git state, or package artifacts.
- Use `unittest` and existing Task 1 helpers only; do not add dependencies.
- Use `apply_patch` for edits; do not dispatch subagents.
- Do not commit, stage, push, create a branch/worktree, clean, or delete files.
- This is a test-suite task. Capture the planned pre-module `ImportError` as RED evidence; do not create artificial product failures or change production code.

## Existing interfaces

Read and use:

- `tests/helpers/fake_vault.py`: `EntitySpec`, `build_fake_vault()`
- `tests/helpers/plugin_runtime.py`: `plugin_reader()`
- `tests/helpers/snapshots.py`

## Files

- Create: `tests/unit/test_config_and_discovery.py`
- Create: `tests/unit/test_entities_and_authority.py`
- Create: `tests/unit/test_search_and_relations.py`
- Create: `tests/contract/__init__.py`
- Create: `tests/contract/test_retrieval_contract.py`

## Required coverage

1. Discovery/configuration: explicit valid Vault, missing root, random directory,
   missing index/schema, malformed registry/index, config-file override,
   explicit environment precedence, relative paths, spaces, Unicode paths,
   missing optional Engine, optional RAW behavior, and unknown registry schema
   version. Assert `VaultError.code`, not message fragments alone.

2. Entity identity/authority: stable ID still resolves after a note move and
   regenerated index; missing entity maps to structured `ENTITY_NOT_FOUND`;
   default search excludes arbitrary metadata-quarantined entity; a canonical
   entity named `Order_B_Test_Name` is not quarantined by name. Add malformed
   frontmatter, duplicate frontmatter key, duplicate stable ID, missing required
   metadata, unsupported entity type, unknown optional metadata, and
   changed-note/unchanged-index cases. Record current generic-future-type source
   behavior rather than inventing a schema restriction.

3. Search/relations: exact/partial title, stable ID, Unicode/Persian content,
   multiple matches, type/authority/status filters, explicit diagnostic
   inclusion, empty query, no result, limit/offset, repeatable tie ordering;
   incoming/outgoing/both, depth 1/multi-depth, three-node cycle, missing target,
   quarantined target filtering, max depth, deterministic traversal. Include
   UTF-8 filenames and Persian note content. Use `ThreadPoolExecutor` only for
   independent reader calls; assert result isolation and determinism without a
   timing threshold.

4. Retrieval public contract: assert only fields emitted by current source:
   entity `id`, index fields, `warning`, `sync_review_state`, `content`; search
   `total_matches`, `truncated`, `next_offset`. Do not invent `snippet` or
   `reasoning_eligibility` fields.

5. Machine-specific path scan: scan non-documentation Plugin runtime Python and
   new test Python files for drive/home literals. Documentation templates are
   excluded. Build forbidden test needles dynamically, for example with
   `"D" + ":" + chr(92)`, rather than embedding the prohibited literal in the
   test that scans itself. Explain that local exception in a comment.

## Required RED/GREEN evidence

1. Before creating the Task 2 modules, run:

   `python -B -m unittest tests.unit.test_config_and_discovery -v`

   Capture the expected module import failure as the plan's RED state.
2. Implement the modules and run:

   `python -B -m unittest tests.unit.test_config_and_discovery tests.unit.test_entities_and_authority tests.unit.test_search_and_relations tests.contract.test_retrieval_contract -v`

   All current-runtime contract tests must pass. If a test exposes a real source
   discrepancy, preserve it and report `DONE_WITH_CONCERNS` rather than weakening
   it.

## Report

Append a detailed report with RED/GREEN command/output evidence, changed files,
self-review, and any source discrepancies to:

`D:\My-Projects\TradingBot-Intelligence-Plugin\tests\.sdd\task-2-report.md`

Return only: status, no commits created, one-line test summary, concerns, and
the report path.
