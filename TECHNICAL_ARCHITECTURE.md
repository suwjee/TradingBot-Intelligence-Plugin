# Technical architecture

## Boundaries

The plugin is a read-only Python adapter over a separate TradingBot Knowledge Vault. It never imports or executes the trading engine. The Vault owns note text, entity metadata, relations, captured source files, reference registry, and RAW registration. The current production checkout is optional for external algorithm-reference excerpts and maintainer synchronization. The plugin does not decide which trading rules are correct.

```
MCP host -> scripts/launch_mcp.py -> mcp_server.py -> vault_reader.py -> Vault
CLI host -------------------------> vault_cli.py -----> vault_reader.py -> Vault
optional external reference --------------------------> configured Engine root
```

`TRADINGBOT_KNOWLEDGE_VAULT` takes precedence over the per-user configuration written by `scripts/configure_vault.py`; a sibling `TradingBot-Knowledge` is the last fallback. `TRADINGBOT_ENGINE_ROOT` is only for external registered references. `TRADINGBOT_PLUGIN_PYTHON` or the interpreter saved with `configure_vault.py --python` selects an interpreter containing the MCP dependency. All Vault paths are normalized, resolved, and constrained to an allowed root. Registered source and reference excerpts are hash checked before return.

## Retrieval and authority

`_INDEX/entities.json` supplies IDs, file paths, type, status, authority, and validity flags. A note is loaded through a bounded file-metadata cache and its indexed metadata compared on every retrieval. Parsed frontmatter is also cached by content; changed file metadata selects new text. `_INDEX/relations.json` supplies edges; full verification compares these with note frontmatter. Default search and relation traversal exclude entities marked non-canonical, unresolved, or invalid for reasoning. Explicit lookup returns them with their warning and metadata. Filter flags expose diagnostic records without promoting their authority. No named Order, fixture, dataset, or reference ID determines status in plugin code.

`get_knowledge` returns the complete note within a configurable byte cap and rejects oversized notes explicitly. `search_knowledge` returns scored excerpts with total-match and continuation metadata; `trace_relations` performs bounded, cycle-safe traversal. Captured source excerpts describe executable evidence. Registered external references require a configured root and exact registry identity. Neither evidence type overrides the Vault's normative status. `sync_review_state` warns when the Vault snapshot needs review against a checkout.

## RAW and verification

`get_dataset` returns registered metadata and availability. `get_raw_window` returns metadata by default and optionally streams at most 1,000 rows from an inclusive requested epoch range; its row response explicitly says it did not verify the full registered window. `verify_vault(mode="knowledge")` checks indexes, note anchors, registry, and non-RAW pins without reading RAW bytes. `mode="full-data"` additionally checks retained RAW hashes, registered window bytes and counts, and unregistered physical RAW inventory. Fixture-source mismatches explicitly marked for manual review are reported as known pending; other mismatches fail. `doctor` adds external-reference availability and a real MCP stdio round trip.

## Runtime and maintenance

The eight MCP tools are thin adapters around `vault_reader.py` and return stable error codes. The stdio server emits protocol messages on stdout; diagnostics go to stderr. Runtime code makes no writes to the Vault or production checkout. `scripts/build_package.py` copies an explicit runtime and documentation allowlist into `.plugin-package/tradingbot-intelligence`; the local marketplace installs from that generated directory, excluding tests, Git metadata, and maintenance code. `maintenance/sync_sources.py` and the maintainer hook are separate explicit write paths. They require the original checkout, check tracked clean source state, and do not grant changed source normative authority. See [Tool Catalog](Tool-Catalog.md), [MCP Contract](MCP-Contract.md), and [Operational Runbook](Operational-Runbook.md).
