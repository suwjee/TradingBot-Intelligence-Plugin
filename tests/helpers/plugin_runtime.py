"""Load the Plugin reader against a process-local temporary Vault."""

from __future__ import annotations

from contextlib import contextmanager
import importlib
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Iterator


_ENV_KEYS = ("TRADINGBOT_KNOWLEDGE_VAULT", "TRADINGBOT_ENGINE_ROOT",
             "TRADINGBOT_PLUGIN_CONFIG")
_MODULES = ("vault_reader", "vault_cli", "mcp_server", "runtime_doctor")


@contextmanager
def plugin_reader(vault_root: Path, *, engine_root: Path | None = None) -> Iterator[ModuleType]:
    """Fresh import with restored environment and Plugin module cache on exit."""
    previous_env = {key: os.environ.get(key) for key in _ENV_KEYS}
    previous_modules = {key: sys.modules.get(key) for key in _MODULES}
    plugin_root = str(Path(__file__).resolve().parents[2])
    inserted = plugin_root not in sys.path
    if inserted:
        sys.path.insert(0, plugin_root)
    try:
        os.environ["TRADINGBOT_KNOWLEDGE_VAULT"] = str(Path(vault_root).resolve())
        os.environ["TRADINGBOT_PLUGIN_CONFIG"] = str(Path(vault_root) / "no-user-config.json")
        if engine_root is None:
            os.environ.pop("TRADINGBOT_ENGINE_ROOT", None)
        else:
            os.environ["TRADINGBOT_ENGINE_ROOT"] = str(Path(engine_root).resolve())
        for name in _MODULES:
            sys.modules.pop(name, None)
        yield importlib.import_module("vault_reader")
    finally:
        for name in _MODULES:
            sys.modules.pop(name, None)
            if previous_modules[name] is not None:
                sys.modules[name] = previous_modules[name]
        for key, value in previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if inserted:
            sys.path.remove(plugin_root)
