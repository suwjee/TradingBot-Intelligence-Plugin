"""Save a per-user Vault location for cached Codex plugin installations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import os


def config_path() -> Path:
    configured = os.environ.get("TRADINGBOT_PLUGIN_CONFIG")
    return (Path(configured).expanduser() if configured else
            Path.home() / ".config" / "tradingbot-intelligence" / "vault.json")


def configure(vault: Path, destination: Path | None = None) -> Path:
    root = vault.expanduser().resolve()
    if not (root / "_INDEX/entities.json").is_file() or not (root / "00_SYSTEM/AUTHORITY_MODEL.md").is_file():
        raise ValueError("Expected a cloned TradingBot Knowledge Vault")
    target = (destination or config_path()).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(json.dumps({"vault_root": str(root)}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    temporary.replace(target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path)
    args = parser.parse_args()
    print(configure(args.vault))
