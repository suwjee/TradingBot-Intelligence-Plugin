"""Read-only readiness check, including a real stdio MCP round trip."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import vault_reader as reader
from integrity import strict_json_loads
from scripts.launch_mcp import candidates, has_mcp

ROOT = Path(__file__).resolve().parent


def doctor() -> dict:
    version = strict_json_loads((ROOT / "plugin.json").read_text(encoding="utf-8"))["version"]
    integrity = reader.verify_package("full-data")
    configured_engine = os.environ.get("TRADINGBOT_ENGINE_ROOT")
    references = integrity["local_references"]
    reference_mode = "vault_local_with_external_cross_check" if configured_engine else "vault_local_snapshot"
    smoke_environment = dict(os.environ)
    references_verified = bool(references) and all(state == "verified" for state in references.values())
    interpreter = next((path for path in candidates() if has_mcp(path)), None)
    mcp_smoke: dict = {"initialized": False, "error": "MCP dependency unavailable"}
    if interpreter is not None and references_verified:
        try:
            completed = subprocess.run(
                [str(interpreter), "-B", str(ROOT / "scripts/smoke_mcp.py")],
                cwd=ROOT, env=smoke_environment, capture_output=True, text=True, timeout=60)
            if completed.returncode == 0:
                mcp_smoke = strict_json_loads(completed.stdout)
            else:
                mcp_smoke = {"initialized": False, "error": completed.stderr.strip()[-500:]}
        except subprocess.TimeoutExpired:
            mcp_smoke = {"initialized": False, "error": "MCP smoke exceeded 60 seconds"}
    return {"plugin_version": version, "vault_root": str(reader.ROOT),
            "engine_root_configured": bool(os.environ.get("TRADINGBOT_ENGINE_ROOT")),
            "integrity": integrity, "references_verified": references_verified,
            "reference_mode": reference_mode, "reference_verification": references,
            "mcp_dependency_available": interpreter is not None,
            "mcp_smoke": mcp_smoke,
            "ready": bool(integrity["ok"] and references_verified and mcp_smoke["initialized"]
                          and set(mcp_smoke.get("called_tools", [])) == set(mcp_smoke.get("listed_tools", [])))}
