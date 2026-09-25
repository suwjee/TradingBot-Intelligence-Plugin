---
name: tradingbot-knowledge
description: Use the standalone TradingBot Knowledge Vault to answer source-grounded questions about Reaction, Blue, A, S, E, StopAll, Order_A, RAW provenance, and validation status.
---

# TradingBot Knowledge

Read the Vault through the `tradingbot_knowledge` MCP tools when available. Start with `system.authority` and `system.retrieval`; search for the requested entity, read its full note, and check `status`, `authority`, and `sync_review_state`. Trace relevant relations and use `read_source_evidence` for retained source lines before asserting an implemented rule.

Use `verify_vault` before a claim that the package is complete. Interpret `verified_pins_ok` as integrity of registered evidence and `inventory_complete` as absence of unregistered physical RAW files or sidecars. Overall `ok` is false if either fails. An integrity result does not prove the trading algorithms correct.

The Vault is a scoped snapshot. It excludes the pending Order routes beyond `Order_A` and their mixed source modules and comprehensive directional references. Treat `pending`, `pending-fix`, `non-canonical`, and `needs_review` as unresolved evidence, not as a validated algorithm. Fixture claims and saved RAW bytes do not prove a fresh engine calculation. Never claim the Vault matches a later project commit without checking that checkout separately.

If MCP tools are unavailable, use the plugin's `vault_cli.py` with a configured Vault location. The plugin and Vault require no original TradingBot project for retrieval. Cite Vault-relative note and source paths and distinguish a direct source fact from an inference.
