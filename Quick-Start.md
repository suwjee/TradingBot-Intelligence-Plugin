# Quick start (Windows PowerShell)

From a fresh plugin checkout, with a separately cloned Vault and Python 3.10+:

```powershell
cd <PLUGIN_ROOT>
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B scripts/configure_vault.py <VAULT_ROOT> --python .\.venv\Scripts\python.exe
$env:TRADINGBOT_PLUGIN_PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
.\.venv\Scripts\python.exe -B vault_cli.py verify --mode full-data
.\.venv\Scripts\python.exe -B vault_cli.py doctor
.\.venv\Scripts\python.exe -B scripts/build_package.py
.\.venv\Scripts\python.exe -B scripts/launch_mcp.py
```

The last command starts a stdio server and waits for an MCP host; run it under a host or use `scripts/smoke_mcp.py` to test. The configured interpreter path is saved outside the plugin, so Codex's installed copy can find the source checkout's virtual environment. Set `TRADINGBOT_ENGINE_ROOT` to an available TradingBot checkout when external algorithm-reference excerpts are needed. For Codex, add this directory as a local plugin marketplace, install `tradingbot-intelligence@tradingbot-local`, then start a new task:

```powershell
codex plugin marketplace add <PLUGIN_ROOT>
codex plugin add tradingbot-intelligence@tradingbot-local
```

Build the package again after source changes before reinstalling. The build contains only runtime and user documentation, and the per-user Vault configuration remains outside the installed plugin copy. For other hosts, see the [configuration templates](config/README.md).
