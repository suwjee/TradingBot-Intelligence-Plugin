# TradingBot Intelligence Plugin operational report

Evidence date: 2026-09-27 UTC. This is a dated validation snapshot, not trading-rule authority. The editable plugin is `X:\TradingBot-Intelligence-Plugin`; the standalone Vault and Production checkout were read-only during this work. After validation, the user requested removal of source test files and development plans. The test results below describe the pre-cleanup source state. The installed runtime package never included those files.

## Executive Summary

**Verdict: `PLUGIN_OPERATIONAL_WITH_KNOWN_PENDING_KNOWLEDGE`.** Version `0.3.6` is installed as a 24-file local Codex package. The installed copy's `doctor` returned `ready=true`, `integrity.ok=true`, both external references verified, and all eight MCP tools invoked through the package's actual `mcp.json` command. Current Vault metadata still marks two Order routes pending and known-invalid; this is a knowledge state, not a plugin failure.

## Architecture Before

The editable root was installed directly. Its installed cache copied `.git`, bytecode, tests, maintenance tools, and development plans. Reader code encoded named Order quarantine, an OrderAudit name exclusion, named source/reference assumptions, and a fixture ID pattern. One integration test contained a machine-specific drive path. Package prose duplicated a large, aging knowledge catalog.

## Architecture After

`vault_reader.py` reads current Vault indexes, note metadata, retained evidence, reference registry, and registered RAW. `mcp_server.py` and `vault_cli.py` are thin read-only adapters. A bounded metadata cache avoids reparsing unchanged notes while preserving drift checks. `scripts/build_package.py` builds an explicit 24-file runtime/documentation package under ignored `.plugin-package/`; the local marketplace installs from that path. A per-user file stores Vault and optional Python paths outside the installed cache. `runtime_doctor.py` verifies integrity, references, MCP dependency, handshake, and calls.

## Vault-Driven Compliance

Entity status, authority, validity, relation edges, data kind, source paths, fixture review state, and reference identities come from the Vault. No production trading rule or named Order status is embedded in runtime branching. Incomplete or incompatible Vault structure fails discovery. Source excerpts are executable evidence, and external references remain external evidence even when hashes match.

## Files Modified

`.agents/plugins/marketplace.json`, `.gitignore`, `plugin.json`, `vault_reader.py`, `vault_cli.py`, `mcp_server.py`, `scripts/configure_vault.py`, `scripts/launch_mcp.py`, `maintenance/__init__.py`, `skills/tradingbot-knowledge/SKILL.md`, `README.md`, `TECHNICAL_ARCHITECTURE.md`, `Context-Recipes.md`, `Tool-Catalog.md`, `Plugin-Contract.md`, `MCP-Contract.md`, `Operational-Runbook.md`, and `Version-Pinning.md`.

## Files Created

`runtime_doctor.py`, `scripts/build_package.py`, `scripts/smoke_mcp.py`, `Quick-Start.md`, `config/README.md`, `config/codex.ps1`, `config/mimo.mimocode.jsonc`, `config/generic-stdio.json`, and this dated report.

## Files Removed

`maintenance/dedupe_raw.py`: a one-time, hardcoded dataset migration helper outside runtime behavior. After validation, `test_vault_reader.py`, `maintenance/test_sync_sources.py`, four new `test_*.py` files, the development plan, and two historical development plans/specifications were removed at the user's request. Ignored `.pyc` cache files remain physically present because automatic command review blocked their deletion; they are absent from Git status and the installable package.

## Configuration

`TRADINGBOT_KNOWLEDGE_VAULT` overrides the per-user Vault path, then a sibling Vault is the final fallback. `TRADINGBOT_PLUGIN_PYTHON` overrides an optional saved interpreter; the launcher validates MCP availability before use. `TRADINGBOT_ENGINE_ROOT` enables optional external reference evidence. The per-user configuration currently points to the verified local Vault and Python runtime. See `Quick-Start.md`, `Operational-Runbook.md`, and `config/`.

## Search/Retrieval Results

Search, full note retrieval, and bounded directional relation traversal passed. Search supports type, authority, status, and diagnostic filters. Pages have at most 25 results; hits report `total_matches`, `truncated`, and `next_offset`. Complete notes have a configurable byte cap and return `RESPONSE_TOO_LARGE` instead of partial content. Changed note files invalidate cached text.

## Authority Filtering Results

Current Vault metadata, rather than entity names, excludes non-canonical, unresolved, or invalid-for-reasoning entries from default search and relations. Explicit lookup and diagnostic search preserve status, authority, validity flags, warning, and sync review state. An isolated future-named Order entity and OrderAudit entity remained retrievable when their test metadata was canonical.

## Order_A/B/C Results

Current Vault: `algorithm.order.a` is `canonical`/`normative`, accepted, and valid for reasoning. `algorithm.order.b` and `.c` are `pending-fix`/`non-canonical`, known-invalid, and invalid for reasoning. Default search excludes B/C entity records; explicit/diagnostic lookup returns them with warnings. Other canonical or source notes can still mention the terms in their prose.

## OrderAudit Result

No active OrderAudit entity exists in the current Vault index. The plugin does not blacklist that name: an isolated canonical test entity with that name was found normally.

## Fixture Handling

Fixture anchor validation uses Vault note title and declared source path/line/hash, not an ID pattern. Tests covered a matching source, an unexpected mismatch as error, a declared manual-review mismatch as known pending, and strict line/heading checks. The current full-data verification reported no fixture `known_pending` entries. Recorded expected output is not a fresh engine calculation.

## Dataset/RAW Results

Full-data verification passed with 7 registered datasets, 3 windows, complete physical inventory, and no unregistered RAW files or sidecars. Dataset retrieval reports availability. Window retrieval defaults to metadata; optional rows stream within the registered inclusive epoch range with a 1,000-row cap, `truncated`, and a clear statement that the row call did not verify the entire window. Full-data verification performs the registered byte/hash/window checks.

## Source Evidence Results

Captured source excerpts are constrained to Vault paths and checked against the source manifest SHA-256 before return. Current index check found 12 source snapshots; the full-data plugin verification counted 22 registered evidence pins across sources, optional references, and supporting files.

## Reference Evidence Results

Both current Bullish and Bearish external HPZR6 registry entries matched the configured Production checkout by size and SHA-256. The tool returns bounded lines and labels them external evidence. A mismatched or unavailable reference does not become canonical knowledge.

## Security Tests

Path traversal, stale note/index metadata, relation index omissions, captured-source hash drift, invalid Vault startup, structured error codes, and clean MCP stdout were covered by passing tests. Runtime retrieval writes neither Vault nor Production. The standalone Vault Git worktree remained clean.

## Unit Test Results

Before test-source cleanup, the final combined plugin and maintenance suite passed **54/54** tests with no skips using the Codex bundled Python:

```text
python -B -m unittest -v test_vault_reader test_vault_driven test_mcp_contract test_package_build test_config maintenance.test_sync_sources
```

Python source compilation, JSON metadata parsing, and `git diff --check` passed; Git emitted only line-ending conversion warnings.

## Integration Test Results

The Vault builder `--check --mode full-data` passed: 169 entities, 1,102 relations, 12 source snapshots, 2 optional references, and 10 supporting files. The Vault schema/index test module passed 8/8 tests. Knowledge-mode verification passed with `data_status=NOT_RUN`; full-data verification passed with `data_status=PASS` and `inventory_complete=true`.

## Maintenance Test Results

The combined plugin suite included clean source/reference sync, dirty-work preservation, rollback, and hook tests; all passed in temporary repositories. No maintainer synchronization ran against the real Vault or Production checkout.

## MCP Runtime Test

Real stdio `initialize`, tool listing, and invocation of all eight tools passed through the command declared in `mcp.json`. Invalid Vault startup exited with a diagnostic on stderr and no stdout traceback. The installed copy's `doctor` reported `mcp_dependency_available=true` and `ready=true`.

## Installed Package Test

Codex installed `tradingbot-intelligence@tradingbot-local` version `0.3.6`. The generated package and installed cache each contain exactly 24 files, with no missing, extra, or hash-different files. Git metadata, bytecode, tests, maintenance code, and development plans are absent. The older `plugin-creator` validator requires a legacy `.codex-plugin/plugin.json` and rejected the portable root manifest; actual Codex installation and MCP execution passed. The [current OpenAI packaging guide](https://developers.openai.com/plugins/build/plugins) supports root `plugin.json` packages.

## Codex Readiness

The local marketplace selects the generated package and `codex plugin add` returned version `0.3.6` with an installed path. Its installed-copy `doctor` passed. A new Codex task is needed for the app to load the refreshed skill/tool catalog into that task's context.

## MiMo Readiness

`config/mimo.mimocode.jsonc` parses as JSON and follows MiMo Code's documented project/global JSONC location and local MCP array-command shape; see the [MiMo Code configuration reference](https://github.com/XiaomiMiMo/MiMo-Code/blob/main/packages/opencode/src/skill/builtin/.bundle/mimocode-docs/reference/config.md). A MiMo executable was not available locally, so a live MiMo host connection is `NOT_TESTED_DEPENDENCY_UNAVAILABLE`.

## Version

Source manifest and installed package: `0.3.6`. The Vault and Production remain separate versioned repositories.

## Remaining Known Pending Items

Vault knowledge still marks Order_B and Order_C for rewrite. `_INDEX/sync-status.json` reports `needs_review` because the Production checkout has pre-existing dirty source/reference paths. These statuses do not appear in `verify_vault.known_pending`, which specifically reports declared fixture-source review mismatches. Live MiMo-host connection awaits a MiMo installation; its config syntax has been source-checked.

## Production Integrity

Production HEAD remained `822c5ce1c1e7f464d2e08085fd6d991ee1d5d8ed`. The SHA-256 recorded before plugin edits equals the final SHA-256 for every protected file below (one identical value is shown per row):

| Production path | Before = after SHA-256 |
| --- | --- |
| `engine/bridge/trading_pipeline.py` | `A14B00EF08E3E97260B856FFE0DAB8044CC70026D272E08E3D4350E9CFF249CD` |
| `engine/pipeline/reaction_engine.py` | `BEA0D5A5E95EE15AD54D024F6C01B8C777BA2ABCC3C8E671118F1AE2DF28F2A6` |
| `engine/pipeline/blue_line_detector.py` | `6FA01D94BC98060B62BC7E68DB0EC24A0B0159727D44043AFFEE7130A9C11448` |
| `engine/pipeline/a_zone_detector.py` | `D7C33DD619AD7E4590027667A2C4E984C83BE7B82FBFAFEB5D7F944DDD521097` |
| `engine/pipeline/s_zone_detector.py` | `7714025B3F43087B09844DF6FEEEF4EEF0EC72EEB841115293DF4C126FD202EE` |
| `engine/pipeline/e_zone_detector.py` | `6BECC792A17E40F572673BF65BC9818C9A957244DE811BE2823402D41C36E628` |
| `engine/pipeline/lifecycle_engine.py` | `330E26FFC04C24DEA952E9A1E8E39DA1A434936D0F80EF2233BD279FC32E8AF1` |
| `engine/pipeline/direction_policy.py` | `A27AC63C2F066311C9381E2EAD6FB44F0789F423A37B465DA65C80E6329397EA` |
| `engine/pipeline/core_utils.py` | `3DAE390AE77B72965F5799F7C132C4EBA203775D5E72761FD7DD60C90F8578DE` |
| `engine/algorithms/TradingBot_Bullish_Algorithm_Reference_V5.4.11_HPZR6_Forensic_Synchronized.md` | `FE9DE3F6AAAD68AEC5F4DE53437CB5D0D7398B9D35050D2C825CD0755C762EA0` |
| `engine/algorithms/TradingBot_Bearish_Algorithm_Reference_V5.4.11_HPZR6_Forensic_Synchronized.md` | `173814D4B964355B26DFE796C31436641E647D893C2D3D155C9AA5357926D06A` |

## Git Diff Summary

All changes are uncommitted in the plugin checkout. Source tests and development plans were removed after the recorded validation. The large documentation deletion replaced the obsolete 64 KB duplicated architecture catalog. Vault Git was clean at `429b913d9959465bec0bc67f6d03b4e6e37484b0`. No commit or remote push was made.

## Final Verdict

`PLUGIN_OPERATIONAL_WITH_KNOWN_PENDING_KNOWLEDGE`
