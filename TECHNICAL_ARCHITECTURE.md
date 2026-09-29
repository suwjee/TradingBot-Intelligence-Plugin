# Technical architecture

## Boundaries

The plugin is a read-only Python adapter over a separate TradingBot Knowledge Vault. It never imports or executes the trading engine. The Vault owns note text, entity metadata, relations, captured source files, reference registry, and RAW registration. The current production checkout is optional external Source/Reference evidence. The plugin does not decide which trading rules are correct.

```
MCP host -> scripts/launch_mcp.py -> mcp_server.py -> vault_reader.py -> Vault
CLI host -------------------------> vault_cli.py -----> vault_reader.py -> Vault
optional external reference --------------------------> configured Engine root
```

`TRADINGBOT_KNOWLEDGE_VAULT` takes precedence over the per-user configuration written by `scripts/configure_vault.py`; a sibling `TradingBot-Knowledge` is the last fallback. When `TRADINGBOT_ENGINE_ROOT` is configured, captured Engine sources must match their canonical repository-relative mapping and external bytes; registered References must also agree. `TRADINGBOT_PLUGIN_PYTHON` or the interpreter saved with `configure_vault.py --python` selects an interpreter containing the MCP dependency. Every bootstrap resource is resolved inside the selected Vault before existence/read checks. All later paths are normalized, resolved, and constrained to their allowed root/prefix.

## Retrieval and authority

`_INDEX/entities.json` supplies IDs, names/aliases, paths, type, status, authority, complete authored frontmatter and derived note SHA-256/byte count. Each indexed note is read as fresh bytes and checked against its full-note pin and all authored metadata. Only derived file/content_sha256/content_bytes fields are excluded from frontmatter equality. Parsed frontmatter caches immutable content, not query authority. Trusted JSON indexes/manifests are read afresh. A declared current_contract is enforced for closed inventory, entity constraints and empty types/selectors; compatible older manifests may omit it. Names and aliases resolve case-insensitively to stable IDs, with collisions rejected. `_INDEX/relations.json` edges must equal canonical typed metadata, and returned neighbors' evidence is checked. Default search/traversal excludes non-canonical, unresolved, historical and known-invalid records. Explicit diagnostic lookup preserves warnings and authority. No named trading object determines status in runtime code.

`get_knowledge` returns the complete note within a configurable byte cap and rejects oversized notes explicitly. `search_knowledge` returns scored excerpts with total-match and continuation metadata; single-letter queries use exact labels. `trace_relations` performs bounded, cycle-safe traversal. Captured Source excerpt IDs and paths use the same currentness guard as knowledge. Registered Reference paths routed through the Source tool delegate to Reference retrieval and retain documented authority, narrative status, conflict IDs, review entity and warnings. Local References require exact Registry/Manifest/hash/version/direction identity; a configured external root adds mandatory cross-verification. Evidence never silently overrides normative status or resolves documented semantic ambiguity.

## RAW and verification

`get_dataset` returns registered metadata and availability. `get_raw_window` returns metadata by default and optionally streams at most 1,000 rows from an inclusive requested epoch range; its row response explicitly says it did not verify the full registered window. `verify_vault(mode="knowledge")` checks indexes, note anchors, registry, and non-RAW pins without reading RAW bytes. `mode="full-data"` additionally checks retained RAW hashes, registered window bytes and counts, and unregistered physical RAW inventory. Fixture-source mismatches explicitly marked for manual review are reported as known pending; other mismatches fail. `doctor` requires local-reference identity and a real MCP stdio round trip invoking every discovered tool, and reports optional external cross-verification separately. Zero datasets/windows/fixtures report EMPTY_BY_DESIGN; missing data IDs return ENTITY_NOT_FOUND.

## Runtime and maintenance

The eight MCP tools are thin adapters around `vault_reader.py` and return stable error codes. The stdio server emits protocol messages on stdout; diagnostics go to stderr. Runtime code makes no writes to the Vault or production checkout. `scripts/build_package.py` copies an explicit runtime and documentation allowlist into `.plugin-package/tradingbot-intelligence`; the local marketplace installs from that generated directory, excluding tests, Git metadata, and maintenance code. `maintenance/sync_sources.py` and the maintainer hook are separate explicit write paths. They require the original checkout, check tracked clean source state, and do not grant changed source normative authority. See [Tool Catalog](Tool-Catalog.md), [MCP Contract](MCP-Contract.md), and [Operational Runbook](Operational-Runbook.md).

Trusted JSON uses a shared strict loader for nested duplicate keys and invalid numeric constants. Generic metadata integrity covers added, removed, nested and type-changed fields; schema validation prevents a matching malformed note/index pair from bypassing types. Root and allowed-prefix containment checks reject symlink/junction escape before external file reads.
