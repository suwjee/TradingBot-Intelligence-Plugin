---
name: tradingbot-knowledge
description: Retrieve TradingBot rules, authority, source evidence, and RAW provenance from the configured standalone Knowledge Vault.
---

# TradingBot knowledge

Use the `tradingbot_knowledge` MCP tools. Start with `system.authority` and `system.retrieval`, then search for the requested subject, read its note, and trace relevant relations. Preserve the returned `status`, `authority`, validity flags, warning, and sync review state. Default search hides unresolved or invalid-for-reasoning entities; use an explicit ID or diagnostic flags when investigating them. Do not infer a named entity's current status from this skill.

Read captured source excerpts for implementation claims and distinguish them from normative Vault statements. External algorithm references require `TRADINGBOT_ENGINE_ROOT` and a registry hash match. Use `verify_vault(mode="full-data")` before claiming retained RAW integrity; `mode="knowledge"` does not read RAW bytes. Fixture expectations and source snapshots alone do not prove fresh engine output.

If MCP is unavailable, run the plugin's `vault_cli.py`. If the Vault cannot be located or verified, state the limitation rather than substituting remembered rules.
