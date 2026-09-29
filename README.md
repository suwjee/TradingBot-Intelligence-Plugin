# TradingBot Intelligence Plugin

A read-only, Vault-driven knowledge and evidence service for TradingBot. The standalone TradingBot Knowledge Vault contains the rules and their authority metadata; this package provides a Python CLI and eight MCP tools. Ordinary retrieval does not require the production TradingBot checkout.

Start with the [Quick Start](Quick-Start.md). The [Technical Architecture](TECHNICAL_ARCHITECTURE.md) explains trust boundaries, the [Tool Catalog](Tool-Catalog.md) lists operations, [Context Recipes](Context-Recipes.md) shows retrieval patterns, and the [Operational Runbook](Operational-Runbook.md) covers failures and updates. Host templates are in [config](config).

The Vault location is selected in this order: `TRADINGBOT_KNOWLEDGE_VAULT`, a per-user path saved by `scripts/configure_vault.py`, then a sibling `TradingBot-Knowledge`. Local Algorithm References are the default evidence source. Set `TRADINGBOT_ENGINE_ROOT` only for optional external cross-verification; local identity must always pass. The stdio MCP server needs the pinned dependency in [requirements.txt](requirements.txt); `scripts/launch_mcp.py` selects an interpreter from `TRADINGBOT_PLUGIN_PYTHON`, the optional per-user saved interpreter, or available local runtimes.

Default search excludes Vault entities marked non-canonical, unresolved, or invalid for reasoning. Explicit lookup and diagnostic filters preserve the metadata and warning. The plugin does not encode named Order statuses or approve fixture outputs. Use `python -B vault_cli.py doctor` for a full local readiness check and `verify --mode knowledge` when only the knowledge package can be checked.

Current physical Order routes are Order_A and Order_B, with first-class OrderAudit. The runtime derives membership/status from validated Vault metadata. RAW and Fixtures are EMPTY_BY_DESIGN; full-data verification is structurally valid without market inputs. For the 2026-09-29 Phase-1 Vault/Plugin verification, RAW, trading fixtures and market regression are NOT_REQUIRED_THIS_PHASE.

Canonical names and aliases resolve to stable IDs; single-letter names use exact search. Retrieval checks complete-note byte identity and declared local Source/Reference pins, and cross-verifies Engine evidence when configured. Source/Reference narrative scope discrepancies remain explicit warning metadata. The Plugin reads the canonical explanation and does not implement trading decisions.
