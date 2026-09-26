# Context recipes

Every recipe starts with Vault entities `system.authority` and `system.retrieval`. Read a note's metadata and prose, then verify source excerpts against `_INDEX/source-hashes.json`. Preserve status, authority, validity flags, and sync state. An excerpt describes implementation; it does not override the owner's acceptance decision. Use `verify_vault(mode="knowledge")` for the knowledge package and `mode="full-data"` for RAW claims. `NOT_RUN` is not a passing RAW check.

## 1. Accepted Order_A rule

Retrieve `algorithm.order.a` and `algorithm.order`; trace their source links. Read the pinned `s_zone_detector.py` and `e_zone_detector.py` excerpts named by those notes. Distinguish the accepted first stopped-A parent-stop rule from Order_B/C-dependent follow-on routes. Report physical First/Break identity, strict time boundaries, and provenance. Assert only the accepted rule as normative.

## 2. Current Order_B/Order_C diagnosis

Search with `include_quarantined=true` or request `algorithm.order.b`/`algorithm.order.c` explicitly. Keep `pending-fix`, `known-invalid`, `valid_for_reasoning=false`, and `rewrite_required=true` in the response. Inspect exact pinned S/E/bridge source anchors. Never use these routes as desired-result baselines or suggest that their current implementation is approved.

## 3. Reaction and directional mirror

Retrieve `algorithm.reaction`, `source.reaction_engine`, `mirror.algorithm`, and `mirror.exceptions`; follow edges to `source.direction_policy`. Read exact Bullish and Bearish branches, including reflected coordinates and the post-Reset same-Break asymmetry. If HPZR6 wording is needed, configure `TRADINGBOT_ENGINE_ROOT`, call `read_algorithm_reference_evidence`, and require its registry SHA to match. Label Order_B/C sections diagnostic.

## 4. Blue, A, and S dependency

Retrieve `algorithm.blue`, `algorithm.a`, `algorithm.s` and their source modules. Follow relations from `source.blue_line_detector`, `source.a_zone_detector`, and `source.s_zone_detector`; inspect chronology, Decimal thresholds, stop ownership, and color changes in pinned code. Identify any Order_B/C-dependent route as current executable behavior with known-invalid downstream validity.

## 5. E, StopAll, lifecycle, and visibility

Retrieve `algorithm.e`, `algorithm.stopall`, `algorithm.lifecycle`, `algorithm.reconciliation`, and `algorithm.visibility`; inspect `source.e_zone_detector`, `source.lifecycle_engine`, and `source.trading_pipeline`. Trace cause inheritance, family continuation, shared Order-stop reconciliation, owner priority, and final visibility. Preserve `affected_by_known_invalid_order_route` for these mixed modules. Serialized OrderAudit output has no active algorithm entity.

## 6. Fixture and RAW provenance

Retrieve the case and its `data.dataset_*` or `data.window_*` entities. Read fixture SHA, physical Order indexes, source module/function, RAW SHA, inclusive first/last epochs, row count, and sidecar identity. Run full-data verification. For a window, select exactly those inclusive epochs from its retained Vault parent and check its digest. Historical or pending fixtures describe evidence, not approved computed output.

## 7. A source change after project commit

Use the maintainer post-commit sync hook only with clean, tracked source paths in the manifest. Inspect `maintenance/sync_sources.py` output and `_INDEX/sync-status.json`; dirty or untracked paths require review. Rebuild indexes, check both verification modes, inspect affected notes and relations, and compare hashes to the new project checkout. A changed hash updates executable evidence but cannot automatically make a trading rule normative. Plugin consumers need only the Vault; this maintenance recipe requires the original checkout.

## 8. Regression or zero-difference claim

Retrieve `test.regression_policy`, `test.zero_difference`, `test.baseline_policy`, and `test.integration_test_policy`. Require identical complete RAW bytes, direction, timeframes, scope, flags, pinned source/reference identities, ordered stable output, lifecycle state, physical indexes/timestamps, causes, nulls, and visibility. Numeric timing telemetry is separate. Reject current B/C-dependent output and count-only checks as approved baselines. Without an approved baseline and fresh run, report `INCOMPLETE`.

## 9. Standalone deployment check

Run `vault_cli.py verify --mode knowledge` against a cloned Vault without the original project. Confirm all nine pinned Engine snapshots, note indexes, and reference registry. Run full-data verification when RAW files are present. Check the MCP handshake and eight tool names, then repeat accepted Order_A and quarantined B/C queries. The original project is optional only for external HPZR6 excerpts and maintainer synchronization.
