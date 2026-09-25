# TradingBot Intelligence Plugin

For a self-contained English description of the plugin, standalone Vault, data model, source boundaries, maintenance flow, and every indexed knowledge entity, see [Technical Architecture](TECHNICAL_ARCHITECTURE.md).

This directory contains the plugin runtime, tests, and maintainer synchronization tools. It is separate from the TradingBot Knowledge Vault and from the TradingBot application. A consumer needs this plugin and a clone of the Vault only. The Vault currently contains a scoped subset of source evidence; excluded creation routes and their mixed modules await a fresh project rewrite.

Use Python 3.10 or newer. Clone the Vault separately. Run `python -B scripts/configure_vault.py <VAULT_ROOT>` once for cached Codex installations, set `TRADINGBOT_KNOWLEDGE_VAULT`, or place the Vault beside this directory with the name `TradingBot-Knowledge`. Then run `python -B vault_cli.py verify` and `python -B vault_cli.py search StopAll`. The CLI uses only Python's standard library.

`verify` distinguishes hash/index integrity of registered evidence (`verified_pins_ok`) from complete physical RAW inventory (`inventory_complete`). Its overall `ok` is false, and its CLI exit code is nonzero, when either check fails. The current Vault has three superseded smaller RAW files and sidecars still on disk, so `inventory_complete` remains false even though the registered bytes and windows verify. This does not prevent read-only retrieval; answers must disclose the incomplete inventory.

The root `plugin.json`, `mcp.json`, and `skills/tradingbot-knowledge/SKILL.md` package this directory as a local Codex plugin. Add this directory as a Codex plugin marketplace and install `tradingbot-intelligence@tradingbot-local`; the bundled launcher uses a Python interpreter with `mcp==2.2.0` available. If no such interpreter is found, install `requirements.txt` into a Python environment and set `TRADINGBOT_PLUGIN_PYTHON` to it. The per-user Vault path configuration is outside both the plugin and Vault, so an installed Codex cache copy still finds the cloned Vault. Restart Codex or start a new task after installation to load the skill and MCP tools.

For another MCP-capable host, register `python <PLUGIN_ROOT>/scripts/launch_mcp.py` as a local stdio server. GPT, Claude, GLM, Kimi, DeepSeek, and other model names alone do not define a plugin protocol; the host application must support MCP, CLI execution, or file access.

The plugin reads `_INDEX`, Markdown, pinned retained source snapshots, and RAW metadata from the Vault. It does not import or execute the trading engine and never needs the original TradingBot project during retrieval. `maintenance/sync_sources.py` and the installed post-commit hook are for maintainers with the original project; they synchronize only manifest-listed clean tracked paths, preserve working-tree bytes, flag semantic changes for review, and block excluded modules.

Maintainer synchronization additionally needs `jsonschema` for the Vault index builder; install `maintenance/requirements.txt` in the hook's Python environment. The hook installed on this workstation uses the Codex bundled Python with that dependency. Synchronization checks this dependency before modifying the Vault. The Vault and plugin remain separate local directories; GitHub publication of either directory is a separate step.
