# Plugin contract

The reader resolves the Vault through `TRADINGBOT_KNOWLEDGE_VAULT`, a per-user path saved by `scripts/configure_vault.py`, or a sibling `TradingBot-Knowledge` directory. All knowledge, source evidence, and RAW paths are resolved within that Vault. Retrieval does not require the original TradingBot checkout. Rule answers must respect the Vault authority, retrieval policy, and sync review state; unresolved rules and unapproved computed output are not promoted to canonical truth.
