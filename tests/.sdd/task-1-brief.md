# Task 1: Test foundation and synthetic Vault builder

## Binding constraints

- Work only under `D:\My-Projects\TradingBot-Intelligence-Plugin\tests\`.
- Do not modify Plugin runtime source, Knowledge Vault, Production Engine, dependencies, user configuration, Git state, or existing package artifacts.
- Use standard-library `unittest`; do not add dependencies.
- Use `apply_patch` for file edits. Do not dispatch subagents.
- Do not commit, stage, push, create a branch/worktree, clean, or delete files.

## Files

- Create: `tests/__init__.py`
- Create: `tests/helpers/__init__.py`
- Create: `tests/helpers/fake_vault.py`
- Create: `tests/helpers/plugin_runtime.py`
- Create: `tests/helpers/snapshots.py`
- Create: `tests/helpers/mcp_client.py`
- Create: `tests/unit/test_helpers.py`
- Create: `tests/README.md`

## Interfaces to produce

Create `FakeVault`, `EntitySpec`, `build_fake_vault()`, `write_entity_note()`,
`write_raw()`, `plugin_reader()`, `snapshot_files()`, `assert_unchanged()`, and
`run_mcp_session()` for later tasks.

`EntitySpec` must be a dataclass containing stable ID, relative note path, type,
status, authority, title, body, and optional frontmatter.

Implement:

```python
build_fake_vault(
    root: Path,
    entities: Sequence[EntitySpec],
    *,
    relations: Sequence[dict[str, str]] = (),
    source_files: Mapping[str, bytes] = {},
    references: Sequence[dict] = (),
    raw_files: Mapping[str, bytes] = {},
) -> FakeVault
```

It must produce Plugin-required indexes, schema marker, authority note,
reference registry, pinned source manifest, and notes using synthetic content
only.

Implement:

```python
plugin_reader(vault_root: Path, *, engine_root: Path | None = None) -> Iterator[ModuleType]
snapshot_files(paths: Iterable[Path]) -> dict[str, FileIdentity]
assert_unchanged(before: Mapping[str, FileIdentity], after: Mapping[str, FileIdentity]) -> None
run_mcp_session(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    calls: Mapping[str, dict],
) -> MCPTranscript
```

`plugin_reader()` must set only process-local environment variables, purge cached
Plugin modules from `sys.modules`, import a fresh reader, and restore environment
and module state on exit. `FileIdentity` must contain relative path, byte count,
and SHA-256.

## Required steps and evidence

1. Add `tests/__init__.py`, `tests/helpers/__init__.py`, and an initial
   `tests/unit/test_helpers.py` test that imports the future helpers, builds a
   temporary one-entity synthetic Vault, reloads `vault_reader`, and expects
   `get_entity("system.sample")` to return that stable ID.
2. Run `python -B -m unittest tests.unit.test_helpers -v` before helper
   implementation. Capture the expected RED failure caused by the absent helper
   modules.
3. Implement the helpers above without importing or copying a real Vault or
   Engine.
4. Add helper tests for deterministic entity-index creation, manifest pin
   validity, environment restoration, and changed-file detection.
5. Run `python -B -m unittest tests.unit.test_helpers -v`; it must PASS.
6. Write `tests/README.md` in English. Include test architecture,
   prerequisites, environment variables, all seven category commands, full
   discovery, optional-resource skip policy, and the difference between
   knowledge-only and full-data verification.

## Report

Write your detailed report with RED/GREEN evidence, exact commands/outputs,
files changed, and self-review to:

`D:\My-Projects\TradingBot-Intelligence-Plugin\tests\.sdd\task-1-report.md`

Return only: status, no commits created, one-line test summary, concerns, and
the report path.
