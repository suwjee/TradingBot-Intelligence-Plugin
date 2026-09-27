"""Read-only readiness check, including a real stdio MCP round trip."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import vault_reader as reader
from scripts.launch_mcp import candidates, has_mcp

ROOT = Path(__file__).resolve().parent


def doctor() -> dict:
    version = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    integrity = reader.verify_package("full-data")
    references = integrity["external_references"]
    references_verified = bool(references) and all(state == "verified" for state in references.values())
    interpreter = next((path for path in candidates() if has_mcp(path)), None)
    mcp_smoke: dict = {"initialized": False, "error": "MCP dependency unavailable"}
    if interpreter is not None and references_verified:
        completed = subprocess.run(
            [str(interpreter), "-B", str(ROOT / "scripts/smoke_mcp.py")],
            cwd=ROOT, env=dict(os.environ), capture_output=True, text=True, timeout=120)
        if completed.returncode == 0:
            mcp_smoke = json.loads(completed.stdout)
        else:
            mcp_smoke = {"initialized": False, "error": completed.stderr.strip()[-500:]}
    return {"plugin_version": version, "vault_root": str(reader.ROOT),
            "engine_root_configured": bool(os.environ.get("TRADINGBOT_ENGINE_ROOT")),
            "integrity": integrity, "references_verified": references_verified,
            "mcp_dependency_available": interpreter is not None,
            "mcp_smoke": mcp_smoke,
            "ready": bool(integrity["ok"] and references_verified and mcp_smoke["initialized"])}
