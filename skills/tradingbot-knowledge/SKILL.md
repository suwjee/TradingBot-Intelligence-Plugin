---
name: tradingbot-knowledge
description: Use when retrieving TradingBot rules, authority, source evidence, current algorithm references, or data-store status from the configured standalone Knowledge Vault.
---

# TradingBot knowledge

Use the `tradingbot_knowledge` MCP tools. Start with `system.authority` and `system.retrieval`, then search for the requested subject, read its note, and trace relevant relations. Preserve the returned `status`, `authority`, validity flags, warning, and sync review state. Default search hides unresolved or invalid-for-reasoning entities; use an explicit ID or diagnostic flags when investigating them. Do not infer a named entity's current status from this skill.

Read captured source excerpts for implementation claims and distinguish them from normative Vault statements. Read algorithm references from the hash-pinned local Vault copies by default; this works without `TRADINGBOT_ENGINE_ROOT`. If an external Engine root is configured, also require its reference bytes to match the local registry and Source Manifest pins. Use `verify_vault(mode="full-data")` before claiming retained RAW integrity; `mode="knowledge"` does not read RAW bytes. Empty registered RAW and Fixture stores are valid `EMPTY_BY_DESIGN` state, with market regression `NOT_TESTED`. Fixture expectations and source snapshots alone do not prove fresh engine output.

If MCP is unavailable, run the plugin's `vault_cli.py`. If the Vault cannot be located or verified, state the limitation rather than substituting remembered rules.
