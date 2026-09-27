# MCP host templates

These examples contain no credentials. Replace `<PLUGIN_ROOT>` and `<PYTHON_EXECUTABLE>` with absolute paths. Configure the Vault and Python once with `scripts/configure_vault.py <VAULT_ROOT> --python <PYTHON_EXECUTABLE>`, or set `TRADINGBOT_KNOWLEDGE_VAULT` and `TRADINGBOT_PLUGIN_PYTHON` in the host process. Set `TRADINGBOT_ENGINE_ROOT` only for optional external references.

- Codex: run [codex.ps1](codex.ps1) with the plugin root to build the minimal package, register, and install it; restart with a new task.
- MiMo Code: copy the `mcp.tradingbot_knowledge` object from [mimo.mimocode.jsonc](mimo.mimocode.jsonc) into a project `.mimocode/mimocode.jsonc` or user `~/.config/mimocode/mimocode.jsonc`. MiMo Code uses an array-form `command` and `type: local`.
- Generic MCP host: adapt [generic-stdio.json](generic-stdio.json) to the host's server registry format. The host must launch a stdio child process.

Model names alone do not define an MCP configuration. Confirm the host's own configuration schema before use.
