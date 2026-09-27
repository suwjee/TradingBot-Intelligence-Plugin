"""Exercise a real local stdio MCP handshake and every registered tool."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import vault_reader as reader  # noqa: E402


def sample_ids() -> tuple[str, str, str, str, str]:
    entities = reader._entities()
    knowledge = next(entity_id for entity_id, row in entities.items()
                     if row.get("type") == "algorithm" and row.get("authority") == "normative"
                     and not reader._quarantined(entity_id, row))
    data = [(entity_id, reader._frontmatter(reader._read_indexed_note(entity_id, row))[0])
            for entity_id, row in entities.items() if row.get("type") == "data"]
    dataset = next(entity_id for entity_id, fields in data if fields.get("data_kind") == "dataset")
    window = next(entity_id for entity_id, fields in data if fields.get("data_kind") == "window")
    source = next(entity_id for entity_id, row in entities.items()
                  if row.get("type") == "source" and reader._frontmatter(
                      reader._read_indexed_note(entity_id, row))[0].get("source_path"))
    reference = reader._reference_registry()["references"][0]["id"]
    return knowledge, dataset, window, source, reference


async def smoke() -> dict:
    knowledge, dataset, window, source, reference = sample_ids()
    config = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))[
        "mcpServers"]["tradingbot_knowledge"]
    parameters = StdioServerParameters(
        command=config["command"],
        args=config["args"],
        cwd=str((ROOT / config.get("cwd", "./")).resolve()),
        env=dict(os.environ),
    )
    calls = {
        "search_knowledge": {"query": knowledge, "limit": 2},
        "get_knowledge": {"entity_id": knowledge},
        "trace_relations": {"entity_id": knowledge},
        "get_dataset": {"entity_id": dataset},
        "get_raw_window": {"entity_id": window},
        "read_source_evidence": {"path": source, "start_line": 1, "line_count": 1},
        "read_algorithm_reference_evidence": {"reference_id": reference,
                                              "start_line": 1, "line_count": 1},
        "verify_vault": {"mode": "knowledge"},
    }
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream, read_timeout_seconds=60) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            if set(names) != set(calls):
                raise RuntimeError(f"MCP tool catalog mismatch: {names}")
            called = []
            for name, arguments in calls.items():
                result = await session.call_tool(name, arguments)
                if getattr(result, "isError", False):
                    raise RuntimeError(f"MCP tool failed: {name}: {result}")
                content = " ".join(getattr(item, "text", "") for item in result.content)
                if '"ok": false' in content or '"error"' in content:
                    raise RuntimeError(f"MCP tool returned an operational error: {name}: {content[:300]}")
                called.append(name)
    return {"initialized": True, "listed_tools": names, "called_tools": called}


if __name__ == "__main__":
    try:
        print(json.dumps(asyncio.run(smoke()), ensure_ascii=False))
    except Exception as exc:
        print(f"MCP smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
