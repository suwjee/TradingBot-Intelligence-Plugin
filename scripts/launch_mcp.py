"""Start the bundled MCP server with an interpreter that has the MCP SDK."""
from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
from integrity import strict_json_loads


def candidates() -> list[Path]:
    configured = os.environ.get("TRADINGBOT_PLUGIN_PYTHON")
    config_path = Path(os.environ.get("TRADINGBOT_PLUGIN_CONFIG",
                                      Path.home() / ".config" / "tradingbot-intelligence" / "vault.json"))
    saved = None
    if config_path.is_file():
        try:
            value = strict_json_loads(config_path.read_text(encoding="utf-8-sig")).get("python_executable")
            saved = Path(value).expanduser() if isinstance(value, str) and value else None
        except (OSError, ValueError, TypeError):
            pass
    return [
        *([Path(configured).expanduser()] if configured else []),
        *([saved] if saved else []),
        Path(sys.executable),
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" /
        "dependencies" / "python" / "python.exe",
    ]


def has_mcp(executable: Path) -> bool:
    if not executable.is_file():
        return False
    check = subprocess.run([str(executable), "-B", "-c", "from mcp.server import MCPServer; from jsonschema import Draft202012Validator"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return check.returncode == 0


def main() -> int:
    server = ROOT / "mcp_server.py"
    for executable in candidates():
        if has_mcp(executable):
            os.chdir(server.parent)
            os.execv(str(executable), [str(executable), "-B", server.name])
    print("TradingBot runtime dependencies missing. Install requirements.txt into a Python environment "
          "and set TRADINGBOT_PLUGIN_PYTHON to that interpreter.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
