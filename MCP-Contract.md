# MCP contract

`mcp.json` starts `scripts/launch_mcp.py`, which selects a Python interpreter with the SDK and runs `mcp_server.py` over stdio. Configure the cloned Vault with `scripts/configure_vault.py`, `TRADINGBOT_KNOWLEDGE_VAULT`, or a sibling `TradingBot-Knowledge` directory. The server reads only the Vault and writes no trading output. Each source excerpt is hash checked against the Vault manifest. Hosts without MCP can use `vault_cli.py` or read the Vault directly.
