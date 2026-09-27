# TradingBot Intelligence Plugin

A read-only, Vault-driven knowledge and evidence service for TradingBot. The standalone TradingBot Knowledge Vault contains the rules and their authority metadata; this package provides a Python CLI and eight MCP tools. Ordinary retrieval does not require the production TradingBot checkout.

Start with the [Quick Start](Quick-Start.md). The [Technical Architecture](TECHNICAL_ARCHITECTURE.md) explains trust boundaries, the [Tool Catalog](Tool-Catalog.md) lists operations, [Context Recipes](Context-Recipes.md) shows retrieval patterns, and the [Operational Runbook](Operational-Runbook.md) covers failures and updates. Host templates are in [config](config).

The Vault location is selected in this order: `TRADINGBOT_KNOWLEDGE_VAULT`, a per-user path saved by `scripts/configure_vault.py`, then a sibling `TradingBot-Knowledge`. Optional external algorithm-reference evidence needs `TRADINGBOT_ENGINE_ROOT`. The stdio MCP server needs the pinned dependency in [requirements.txt](requirements.txt); `scripts/launch_mcp.py` selects an interpreter from `TRADINGBOT_PLUGIN_PYTHON`, the optional per-user saved interpreter, or available local runtimes.

Default search excludes Vault entities marked non-canonical, unresolved, or invalid for reasoning. Explicit lookup and diagnostic filters preserve the metadata and warning. The plugin does not encode named Order statuses or approve fixture outputs. Use `python -B vault_cli.py doctor` for a full local readiness check and `verify --mode knowledge` when only the knowledge package can be checked.
