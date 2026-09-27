# MCP contract

`mcp.json` starts `scripts/launch_mcp.py` in stdio mode. The launcher finds an interpreter with `mcp==2.2.0` (preferring `TRADINGBOT_PLUGIN_PYTHON`, then the interpreter saved by `scripts/configure_vault.py --python`), changes to its own package directory, and execs `mcp_server.py`. The server writes protocol data to stdout and diagnostics to stderr. It exposes exactly the eight tools in [Tool Catalog](Tool-Catalog.md). Expected failures return `{"ok":false,"error":{"code":"...","message":"..."}}`.

Configure the Vault with `TRADINGBOT_KNOWLEDGE_VAULT` or `scripts/configure_vault.py`. Optional external references require `TRADINGBOT_ENGINE_ROOT`. The server does not require a Production checkout for Vault search or source retrieval. Use `scripts/smoke_mcp.py` for a real initialize/list/invoke transport test. See [config](config) for host examples.
