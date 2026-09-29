"""Exercise every MCP tool, including expected errors for empty data stores."""
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
from integrity import strict_json_loads  # noqa: E402


def sample_ids() -> tuple[str, str | None, str | None, str, str]:
    entities = reader._entities()
    knowledge = next(entity_id for entity_id, row in entities.items()
                     if row.get("type") == "algorithm" and not reader._quarantined(entity_id, row))
    data = [(entity_id, reader._frontmatter(reader._read_indexed_note(entity_id, row))[0])
            for entity_id, row in entities.items() if row.get("type") == "data"]
    dataset = next((entity_id for entity_id, fields in data if fields.get("data_kind") == "dataset"), None)
    window = next((entity_id for entity_id, fields in data if fields.get("data_kind") == "window"), None)
    source = next(
        entity_id
        for entity_id, row in entities.items()
        if row.get("type") == "source"
        for source_path in [reader._frontmatter(
            reader._read_indexed_note(entity_id, row))[0].get("source_path")]
        if source_path and reader._inside(source_path, "06_SOURCE/Code/").stat().st_size > 0
    )
    reference = reader._reference_registry()["references"][0]["id"]
    return knowledge, dataset, window, source, reference


async def smoke() -> dict:
    knowledge, dataset, window, source, reference = sample_ids()
    config = strict_json_loads((ROOT / "mcp.json").read_text(encoding="utf-8"))[
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
        "read_source_evidence": {"path": source, "start_line": 1, "line_count": 1},
        "read_algorithm_reference_evidence": {"reference_id": reference,
                                              "start_line": 1, "line_count": 1},
        "verify_vault": {"mode": "knowledge"},
    }
    expected_tools = {
        "search_knowledge", "get_knowledge", "trace_relations", "get_dataset",
        "get_raw_window", "read_source_evidence", "read_algorithm_reference_evidence",
        "verify_vault",
    }
    expected_empty = set()
    for tool, entity_id in (("get_dataset", dataset), ("get_raw_window", window)):
        if entity_id is None:
            entity_id = "data.empty_dataset" if tool == "get_dataset" else "data.empty_window"
            expected_empty.add(tool)
        calls[tool] = {"entity_id": entity_id}
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream, read_timeout_seconds=60) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            if set(names) != expected_tools:
                raise RuntimeError(f"MCP tool catalog mismatch: {names}")
            called = []
            empty_results = []
            for name, arguments in calls.items():
                result = await session.call_tool(name, arguments)
                if result.is_error:
                    raise RuntimeError(f"MCP tool failed: {name}: {result}")
                content = " ".join(getattr(item, "text", "") for item in result.content)
                payloads = [strict_json_loads(item.text) for item in result.content
                            if getattr(item, "text", "")]
                if not payloads:
                    raise RuntimeError(f"MCP tool returned no JSON content: {name}")
                if name in expected_empty:
                    if len(payloads) != 1 or payloads[0].get("error", {}).get("code") != "ENTITY_NOT_FOUND":
                        raise RuntimeError(f"MCP empty-store contract failed: {name}: {content[:300]}")
                    empty_results.append({"tool": name, "status": "EMPTY_BY_DESIGN", "error_code": "ENTITY_NOT_FOUND"})
                elif any(isinstance(payload, dict) and (payload.get("ok") is False or "error" in payload)
                         for payload in payloads):
                    raise RuntimeError(f"MCP tool returned an operational error: {name}: {content[:300]}")
                called.append(name)
    return {"initialized": True, "listed_tools": names, "called_tools": called,
            "empty_data_store": dataset is None and window is None,
            "dataset_store_empty": dataset is None, "window_store_empty": window is None,
            "expected_empty_results": empty_results,
            "tools_discovered": len(names), "tools_executed": len(called)}


if __name__ == "__main__":
    try:
        print(json.dumps(asyncio.run(smoke()), ensure_ascii=False))
    except Exception as exc:
        print(f"MCP smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
