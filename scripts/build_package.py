"""Build a minimal installable plugin tree from the editable source checkout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = ROOT / ".plugin-package"
OUTPUT = OUTPUT_PARENT / "tradingbot-intelligence"
FILES = (
    "plugin.json", "mcp.json", "requirements.txt", "README.md", "Quick-Start.md",
    "Operational-Runbook.md", "TECHNICAL_ARCHITECTURE.md", "Tool-Catalog.md",
    "MCP-Contract.md", "Plugin-Contract.md", "Context-Recipes.md", "Version-Pinning.md",
    "vault_reader.py", "vault_cli.py", "mcp_server.py", "runtime_doctor.py",
    "scripts/configure_vault.py", "scripts/launch_mcp.py", "scripts/smoke_mcp.py",
    "skills/tradingbot-knowledge/SKILL.md", "config/README.md", "config/codex.ps1",
    "config/mimo.mimocode.jsonc", "config/generic-stdio.json",
)


def inventory(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


def build() -> dict:
    parent = OUTPUT_PARENT.resolve()
    target = OUTPUT.resolve()
    if target.parent != parent or target.name != "tradingbot-intelligence":
        raise RuntimeError("Package target escaped its fixed build directory")
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build-", dir=parent) as temp_name:
        temporary = Path(temp_name)
        for relative in FILES:
            source = ROOT / relative
            if not source.is_file():
                raise FileNotFoundError(source)
            destination = temporary / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        expected = inventory(temporary)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(temporary, target)
    if inventory(target) != expected:
        raise RuntimeError("Built package differs from editable source")
    return {"version": version, "path": str(target), "files": len(expected),
            "excluded": [".git", "__pycache__", "tests", "maintenance", "development plans"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build(), indent=2))
