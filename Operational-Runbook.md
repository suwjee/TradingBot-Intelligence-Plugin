# Operational runbook

Run `python -B vault_cli.py doctor` for full local readiness, or `verify --mode knowledge` when RAW is unavailable. Inspect `ok`, `known_pending`, `external_references`, and `mcp_smoke` separately. A knowledge-only PASS does not establish RAW integrity.

| Symptom | Check and resolution |
| --- | --- |
| Vault not found | Set `TRADINGBOT_KNOWLEDGE_VAULT` or run `scripts/configure_vault.py <VAULT_ROOT>`; confirm `_INDEX/entities.json` exists. |
| Index stale | Run the Vault's `_SCHEMA/build_indexes.py --check`; review the changed note and rebuild indexes with the Vault maintainer workflow only after resolving the source of drift. |
| Reference hash mismatch | Compare the configured `TRADINGBOT_ENGINE_ROOT` file with the Vault registry; use a matching checkout or update the registry through reviewed maintenance. Do not bypass the hash. |
| RAW unavailable | `get_dataset` and `get_raw_window` report availability. Restore the registered Vault RAW file and rerun full-data verification; use knowledge mode only for non-RAW claims. |
| MCP will not start | Install `requirements.txt` in a Python environment, set `TRADINGBOT_PLUGIN_PYTHON` to that interpreter, and run `scripts/smoke_mcp.py`; inspect stderr. |
| Codex cannot connect | Run `scripts/build_package.py` after source changes, reinstall the local plugin, start a new task, confirm the installed version and per-user Vault path, then run the installed copy's smoke script. |
| MiMo cannot connect | Confirm MiMo Code supports local stdio MCP, use the array-form command in `config/mimo.mimocode.jsonc`, set required environment in the host process, and run the same command manually with its interpreter. |
| Python dependency missing | Run `<PYTHON> -m pip install -r requirements.txt` and verify `<PYTHON> -c "from mcp.server import MCPServer"`. |

For updates, review source and Vault changes separately. Run the Vault index builder in check mode, both plugin verification modes, real MCP smoke, rebuild the minimal package, and run an installed-copy smoke before relying on a new version. Restore a separate test suite when a future code change needs regression coverage. Do not run maintainer synchronization as a normal retrieval operation.
