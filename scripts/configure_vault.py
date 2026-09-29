"""Save a per-user Vault location for cached Codex plugin installations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from integrity import strict_json_loads


def config_path() -> Path:
    configured = os.environ.get("TRADINGBOT_PLUGIN_CONFIG")
    return (Path(configured).expanduser() if configured else
            Path.home() / ".config" / "tradingbot-intelligence" / "vault.json")


def configure(vault: Path, destination: Path | None = None,
              python_executable: Path | None = None) -> Path:
    root = vault.expanduser().resolve()
    if not (root / "_INDEX/entities.json").is_file() or not (root / "00_SYSTEM/AUTHORITY_MODEL.md").is_file():
        raise ValueError("Expected a cloned TradingBot Knowledge Vault")
    target = (destination or config_path()).expanduser()
    settings = {"vault_root": str(root)}
    if python_executable is not None:
        executable = python_executable.expanduser().resolve()
        if not executable.is_file():
            raise ValueError("Configured Python executable does not exist")
        settings["python_executable"] = str(executable)
    elif target.is_file():
        try:
            previous = strict_json_loads(target.read_text(encoding="utf-8"))
            if isinstance(previous.get("python_executable"), str):
                settings["python_executable"] = previous["python_executable"]
        except (OSError, ValueError, TypeError):
            pass
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path)
    parser.add_argument("--python", dest="python_executable", type=Path)
    args = parser.parse_args()
    print(configure(args.vault, python_executable=args.python_executable))
