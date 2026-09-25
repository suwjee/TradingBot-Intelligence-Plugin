"""Start the bundled MCP server with an interpreter that has the MCP SDK."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).absolute().parents[1]


def candidates() -> list[Path]:
    configured = os.environ.get("TRADINGBOT_PLUGIN_PYTHON")
    return [
        *([Path(configured).expanduser()] if configured else []),
        Path(sys.executable),
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" /
        "dependencies" / "python" / "python.exe",
    ]


def has_mcp(executable: Path) -> bool:
    if not executable.is_file():
        return False
    check = subprocess.run([str(executable), "-B", "-c", "from mcp.server import MCPServer"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return check.returncode == 0


def main() -> int:
    server = ROOT / "mcp_server.py"
    for executable in candidates():
        if has_mcp(executable):
            os.execv(str(executable), [str(executable), "-B", str(server)])
    print("TradingBot MCP SDK missing. Install requirements.txt into a Python environment "
          "and set TRADINGBOT_PLUGIN_PYTHON to that interpreter.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
